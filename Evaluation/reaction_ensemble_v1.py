"""Does an ensemble decide "was this pointer stop a click?" better than LightGBM alone?

The click filter ships as one LightGBM on 17 features (reaction_features_v1.py). Here,
on the same stops, features and procedure, four filters:

    lgbm        the shipped LightGBM settings
    rf          random forest
    hgb         histogram gradient boosting (scikit-learn)
    mean3       the mean of the three probabilities

Each is fitted on the training recordings; its threshold keeps 60% of the training
recall, chosen on grouped out-of-fold scores (for mean3, the mean of the members'
out-of-fold scores). Scored on the 974 held-out recordings as shipped: named steps,
same-place merging, icon clicks kept; whole SOP on the 720 with typing scores, typing as
combined_sop_v10 (run_039, mean of per-application and pooled, 0.5). Stops a threshold
keeps that were never read are OCR'd first (3 workers, cached).

    python reaction_ensemble_v1.py
"""
from __future__ import annotations

import json
import pickle
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from v2k.env import frame_cache_dir, limit_cpu  # noqa: E402

if __name__ == "__main__":
    limit_cpu(12)

import numpy as np  # noqa: E402

import combined_sop_v1 as cs  # noqa: E402
import combined_sop_v10 as c10  # noqa: E402
import pointer_cnn_eval_v1 as e1  # noqa: E402
from click_variants_v1 import steps_of  # noqa: E402
from combined_sop_v4 import match_clicks, match_typed, typed_from  # noqa: E402
from reaction_features_v1 import clicks_hit, screen_sizes, table  # noqa: E402
from v2k import sop_detector as sd  # noqa: E402

KEEP = 0.6


def makers():
    from lightgbm import LGBMClassifier
    from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
    return {
        "lgbm": lambda: LGBMClassifier(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=40,
                                       subsample=0.8, subsample_freq=1, colsample_bytree=0.9, n_jobs=8, verbose=-1),
        "rf": lambda: RandomForestClassifier(n_estimators=400, min_samples_leaf=5, max_features=0.5,
                                             n_jobs=8, random_state=0),
        "hgb": lambda: HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=31,
                                                      min_samples_leaf=40, random_state=0),
    }


def threshold(tr, oof) -> float:
    """The highest threshold whose out-of-fold scores keep KEEP of the training recall."""
    by_rec = np.split(oof, np.cumsum([len(y_) for *_, y_ in tr])[:-1])
    full = clicks_hit(tr, by_rec, -1)[0]
    grid = np.unique(np.quantile(oof, np.linspace(0, 1, 401)))
    lo, hi = 0, len(grid) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if clicks_hit(tr, by_rec, grid[mid])[0] >= KEEP * full:
            lo = mid
        else:
            hi = mid - 1
    return float(grid[lo])


def main() -> None:
    from sklearn.metrics import roc_auc_score
    recs = pickle.loads(e1.OUT.read_bytes())
    sizes = screen_sizes(recs)
    tr = table([r for r in recs if r["train"]], sizes)
    te = table([r for r in recs if not r["train"]], sizes)
    X = np.vstack([x for *_, x, _ in tr])
    y = np.concatenate([y_ for *_, y_ in tr])
    Xte = np.vstack([x for *_, x, _ in te])
    yte = np.concatenate([y_ for *_, y_ in te])
    folds = np.concatenate([np.full(len(y_), i) for i, (*_, y_) in enumerate(tr)]) % 5
    print(f"{len(y)} training stops, {len(yte)} held-out stops", flush=True)

    oof, pte = {}, {}
    for name, make in makers().items():
        t0 = time.perf_counter()
        o = np.zeros(len(y))
        for f in range(5):
            o[folds == f] = make().fit(X[folds != f], y[folds != f]).predict_proba(X[folds == f])[:, 1]
        oof[name] = o
        pte[name] = make().fit(X, y).predict_proba(Xte)[:, 1]
        print(f"  {name}: fitted, {time.perf_counter() - t0:.0f}s", flush=True)
    oof["mean3"] = np.mean([oof[k] for k in ("lgbm", "rf", "hgb")], axis=0)
    pte["mean3"] = np.mean([pte[k] for k in ("lgbm", "rf", "hgb")], axis=0)
    thr = {k: threshold(tr, oof[k]) for k in oof}
    split = np.cumsum([len(y_) for *_, y_ in te])[:-1]
    ps = {k: np.split(v, split) for k, v in pte.items()}
    for k in pte:
        print(f"  {k:<6} held-out AUC {roc_auc_score(yte, pte[k]):.3f}, threshold {thr[k]:.3f}", flush=True)

    ocr = pickle.loads(e1.OCR.read_bytes())
    jobs = {}
    for k in pte:
        for (r, st, _, _), p in zip(te, ps[k]):
            for j, (t, x, y_, _) in enumerate(st):
                if p[j] >= thr[k] and (r["app"], r["tid"], t, x, y_) not in ocr:
                    jobs.setdefault((r["app"], r["tid"], r["scale"]), set()).add((t, x, y_))
    todo = [(a, t, s, sorted(p)) for (a, t, s), p in jobs.items()]
    if todo:
        t1 = time.perf_counter()
        print(f"OCR around {sum(len(j[3]) for j in todo)} new stops ...", flush=True)
        with ProcessPoolExecutor(max_workers=3, initializer=e1._ocr_worker_init) as ex:
            for part in ex.map(e1._ocr_one, todo):
                ocr.update(part)
        e1.OCR.write_bytes(pickle.dumps(ocr))
        print(f"  {time.perf_counter() - t1:.0f}s", flush=True)

    # typing as shipped (combined_sop_v10)
    oo = dict(np.load(c10.OOF))
    H, I = oo["score_predicted"], oo["score_no_routing"]
    oo["score_typing"] = np.where(H > 0, (H + I) / 2, I)
    apps = set(oo["app"].tolist())
    keep_idx = [i for i, (r, *_) in enumerate(te) if r["app"] in apps
                and (frame_cache_dir() / r["app"] / f"{r['tid']}.json").exists()]
    typed = {}
    for i in keep_idx:
        r = te[i][0]
        app, tid = r["app"], r["tid"]
        rec = json.loads((frame_cache_dir() / app / f"{tid}.json").read_text(encoding="utf-8"))
        with np.load(frame_cache_dir() / app / f"{tid}.npz") as z:
            ts = z["timestamp"]
        cand = sd.candidates(rec)
        m = np.flatnonzero((oo["tid"] == tid) & (oo["app"] == app))
        sc_ = oo["score_typing"][m]
        above = sorted((k for k in range(len(cand)) if sc_[k] >= 0.5), key=lambda k: -sc_[k])
        ref = cs.reference(app, tid, r["scale"])
        ty = typed_from(cand, ts, above)
        want = [x for x in ref if x["kind"] == "type"]
        typed[i] = ([c for c in ref if c["kind"] == "click"], len(want), len(ty), match_typed(want, ty))
    total = sum(len(v[0]) + v[1] for v in typed.values())
    n_clicks = sum(len(r["clicks"]) for r, *_ in te)

    print(f"\n{'filter':<8}{'AUC':>7}{'clicks':>8}{'real':>8}{'found':>8}{'whole':>8}{'real':>8}{'found':>8}")
    res = {}
    for k in pte:
        n = hit = 0
        for (r, st, _, _), p in zip(te, ps[k]):
            s_ = steps_of(r, st, p, thr[k], ocr, True, True)
            n += len(s_)
            hit += match_clicks([{"t": t, "x": x, "y": y_} for t, x, y_ in r["clicks"]], s_)
        wn = wok = 0
        for i in keep_idx:
            r, st, _, _ = te[i]
            rc, _, nt, okt = typed[i]
            s_ = steps_of(r, st, ps[k][i], thr[k], ocr, True, True)
            wn, wok = wn + len(s_) + nt, wok + match_clicks(rc, s_) + okt
        res[k] = dict(auc=roc_auc_score(yte, pte[k]), threshold=thr[k], clicks=n, clicks_real=hit / n,
                      clicks_found=hit / n_clicks, whole=wn, whole_real=wok / wn, whole_found=wok / total)
        print(f"{k:<8}{res[k]['auc']:>7.3f}{n:>8}{hit / n:>8.1%}{hit / n_clicks:>8.1%}"
              f"{wn:>8}{wok / wn:>8.1%}{wok / total:>8.1%}", flush=True)
    (e1.CACHE / "reaction_ensemble_v1.json").write_text(json.dumps(res, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
