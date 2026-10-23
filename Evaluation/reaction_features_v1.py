"""More features for the screen-reaction filter: what the pointer itself did.

The filter's 8 features describe the screen (how much changed after a stop, anywhere
and near it, and before it) plus how long the pointer rested. This adds 9 about the
pointer and the stop's context, all from the same per-frame record:

    p_stop        the pointer CNN's confidence at the stop
    p_mean3       its mean over the last 3 frames the pointer was seen
    track_len     frames the pointer had been seen without a break up to the stop
    speed_in      px moved between the last two frames seen before the stop
    path_1s       px moved in the second before the stop
    x_rel, y_rel  where on the screen (a menu bar, a dialog's buttons)
    gap_prev      seconds since the previous stop
    big_count_1s  changed regions larger than a pointer in the second after

Same procedure as reaction_models_v1 (LightGBM; fitted on training recordings;
threshold from grouped out-of-fold scores keeping 60% / 75% of the training recall;
scored on held-out recordings), then delivered steps as click_variants_v1 ("same place"
merging, with and without icon clicks), OCR'ing any newly kept stop first.

    python reaction_features_v1.py
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

import bare_sop_v2 as b2  # noqa: E402
import combined_sop_v1 as cs  # noqa: E402
import pointer_cnn_eval_v1 as e1  # noqa: E402
import pointer_cnn_v1 as pc  # noqa: E402
from click_variants_v1 import steps_of  # noqa: E402
from combined_sop_v4 import match_clicks, match_typed, typed_from  # noqa: E402
from reaction_models_v1 import clicks_hit  # noqa: E402
from v2k import sop_detector as sd  # noqa: E402

SIZES = e1.CACHE / "reaction_features_v1_sizes.json"
OUT = e1.CACHE / "reaction_features_v1.pkl"
NEW = ["p_stop", "p_mean3", "track_len", "speed_in", "path_1s", "x_rel", "y_rel", "gap_prev", "big_count_1s"]


def screen_sizes(recs) -> dict:
    import cv2
    sizes = json.loads(SIZES.read_text()) if SIZES.exists() else {}
    for r in recs:
        k = f"{r['app']}/{r['tid']}"
        if k not in sizes:
            cap = cv2.VideoCapture(str(pc.VIDEOS / r["app"] / str(r["tid"]) / "video" / "video.mp4"))
            sizes[k] = [cap.get(cv2.CAP_PROP_FRAME_WIDTH) / r["scale"], cap.get(cv2.CAP_PROP_FRAME_HEIGHT) / r["scale"]]
            cap.release()
    SIZES.write_text(json.dumps(sizes))
    return sizes


def pointer_features(r, st, size) -> np.ndarray:
    """The 9 new features for each stop of one recording."""
    W, H = size
    seen = [(f[0], f[3]) for f in r["frames"] if f[3] is not None and f[3][0] >= 0.8]
    times = np.array([t for t, _ in seen]) if seen else np.zeros(0)
    big = [(f[0], len(f[4])) for f in r["frames"]]
    dt = 1.0 / r["fps"]
    out = []
    for i, (ts, x, y, _) in enumerate(st):
        k = int(np.searchsorted(times, ts + 1e-6)) - 1          # the stop's own frame
        p_stop = seen[k][1][0] if k >= 0 else 0.0
        last = [seen[j][1][0] for j in range(max(0, k - 2), k + 1)] if k >= 0 else [0.0]
        n = 0
        j = k
        while j > 0 and seen[j][0] - seen[j - 1][0] <= 1.5 * dt:
            n, j = n + 1, j - 1
        speed = float(np.hypot(seen[k][1][1] - seen[k - 1][1][1], seen[k][1][2] - seen[k - 1][1][2])) \
            if k >= 1 and seen[k][0] - seen[k - 1][0] <= 1.5 * dt else 0.0
        path = 0.0
        j = k
        while j > 0 and seen[j - 1][0] >= ts - 1.0:
            path += float(np.hypot(seen[j][1][1] - seen[j - 1][1][1], seen[j][1][2] - seen[j - 1][1][2]))
            j -= 1
        gap = ts - st[i - 1][0] if i > 0 else 10.0
        big_n = sum(c for t, c in big if ts < t <= ts + 1.0)
        out.append([p_stop, float(np.mean(last)), n, speed, path, x / max(W, 1), y / max(H, 1), gap, big_n])
    return np.array(out, dtype=float).reshape(-1, len(NEW))


def table(recs, sizes):
    rows = []
    for r in recs:
        st = e1.stops(r, b2.RULE)
        _, used = e1.match(r["clicks"], st, [True] * len(st))
        base = np.array([e1.features(r, s) for s in st]) if st else np.zeros((0, 8))
        extra = pointer_features(r, st, sizes[f"{r['app']}/{r['tid']}"]) if st else np.zeros((0, len(NEW)))
        y = np.array([j in used for j in range(len(st))], dtype=int)
        rows.append((r, st, np.hstack([base, extra]), y))
    return rows


def fit_and_threshold(tr, cols):
    from lightgbm import LGBMClassifier

    def make():
        return LGBMClassifier(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=40,
                              subsample=0.8, subsample_freq=1, colsample_bytree=0.9, n_jobs=8, verbose=-1)
    X = np.vstack([x[:, cols] for *_, x, _ in tr])
    y = np.concatenate([y for *_, y in tr])
    rec_of = np.concatenate([np.full(len(y_), i) for i, (*_, y_) in enumerate(tr)])
    folds = rec_of % 5
    oof = np.zeros(len(y))
    for f in range(5):
        oof[folds == f] = make().fit(X[folds != f], y[folds != f]).predict_proba(X[folds == f])[:, 1]
    by_rec = np.split(oof, np.cumsum([len(y_) for *_, y_ in tr])[:-1])
    full = clicks_hit(tr, by_rec, -1)[0]
    grid = np.unique(np.quantile(oof, np.linspace(0, 1, 401)))
    thrs = {}
    for keep in (0.6, 0.75):
        lo, hi = 0, len(grid) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if clicks_hit(tr, by_rec, grid[mid])[0] >= keep * full:
                lo = mid
            else:
                hi = mid - 1
        thrs[keep] = float(grid[lo])
    return make().fit(X, y), thrs


def main() -> None:
    from sklearn.metrics import roc_auc_score
    recs = pickle.loads(e1.OUT.read_bytes())
    t0 = time.perf_counter()
    sizes = screen_sizes(recs)
    tr = table([r for r in recs if r["train"]], sizes)
    te = table([r for r in recs if not r["train"]], sizes)
    print(f"features for {sum(len(y) for *_, y in tr)} training and {sum(len(y) for *_, y in te)} "
          f"held-out stops, {time.perf_counter() - t0:.0f}s")
    yte = np.concatenate([y for *_, y in te])
    sets = {"8 screen features (shipped)": list(range(8)), "+ 9 pointer features": list(range(8 + len(NEW)))}
    models = {}
    for name, cols in sets.items():
        model, thrs = fit_and_threshold(tr, cols)
        pte = model.predict_proba(np.vstack([x[:, cols] for *_, x, _ in te]))[:, 1]
        models[name] = (model, thrs, cols, np.split(pte, np.cumsum([len(y) for *_, y in te])[:-1]))
        print(f"{name:<30} held-out AUC {roc_auc_score(yte, pte):.3f}")
    imp = sorted(zip(["big_after_1s", "big_after_2s", "big_after_3s", "near_after_1s", "near_after_2s",
                      "near_after_3s", "big_before_1s", "dwell"] + NEW,
                     models["+ 9 pointer features"][0].feature_importances_), key=lambda t: -t[1])
    print("importance (splits):", ", ".join(f"{n} {v}" for n, v in imp[:8]))

    # OCR any stop a new threshold keeps that was never read
    ocr = pickle.loads(e1.OCR.read_bytes())
    jobs = {}
    for name, (_, thrs, _, ps) in models.items():
        for (r, st, _, _), p in zip(te, ps):
            for thr in thrs.values():
                for j, (t, x, y, _) in enumerate(st):
                    if p[j] >= thr and (r["app"], r["tid"], t, x, y) not in ocr:
                        jobs.setdefault((r["app"], r["tid"], r["scale"]), set()).add((t, x, y))
    todo = [(a, t, s, sorted(p)) for (a, t, s), p in jobs.items()]
    if todo:
        t1 = time.perf_counter()
        print(f"OCR around {sum(len(j[3]) for j in todo)} new stops ...", flush=True)
        with ProcessPoolExecutor(max_workers=3, initializer=e1._ocr_worker_init) as ex:
            for part in ex.map(e1._ocr_one, todo):
                ocr.update(part)
        e1.OCR.write_bytes(pickle.dumps(ocr))
        print(f"  {time.perf_counter() - t1:.0f}s")

    # whole SOP on the 720 with typing scores
    oof = dict(np.load(cs.OOF))
    apps = set(oof["app"].tolist())
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
        m = np.flatnonzero((oof["tid"] == tid) & (oof["app"] == app))
        sc_ = oof["score_predicted"][m]
        above = sorted((k for k in range(len(cand)) if sc_[k] >= sd.THRESHOLD), key=lambda k: -sc_[k])
        ref = cs.reference(app, tid, r["scale"])
        ty = typed_from(cand, ts, above)
        want = [x for x in ref if x["kind"] == "type"]
        typed[i] = ([c for c in ref if c["kind"] == "click"], len(want), len(ty), match_typed(want, ty))
    total = sum(len(v[0]) + v[1] for v in typed.values())
    n_clicks = sum(len(r["clicks"]) for r, *_ in te)
    print(f"\n{'':<30}{'keep':>6}{'icons':>7}{'clicks real':>13}{'found':>8}{'whole real':>12}{'found':>8}")
    for name, (_, thrs, _, ps) in models.items():
        for keep, thr in thrs.items():
            for icons in (False, True):
                n = hit = 0
                for (r, st, _, _), p in zip(te, ps):
                    s_ = steps_of(r, st, p, thr, ocr, True, icons)
                    n += len(s_)
                    hit += match_clicks([{"t": t, "x": x, "y": y} for t, x, y in r["clicks"]], s_)
                wn = wok = 0
                for i in keep_idx:
                    r, st, _, _ = te[i]
                    rc, _, nt, okt = typed[i]
                    s_ = steps_of(r, st, ps[i], thr, ocr, True, icons)
                    wn, wok = wn + len(s_) + nt, wok + match_clicks(rc, s_) + okt
                print(f"{name:<30}{keep:>6.0%}{'yes' if icons else 'no':>7}{hit / n:>13.1%}{hit / n_clicks:>8.1%}"
                      f"{wok / wn:>12.1%}{wok / total:>8.1%}")
    OUT.write_bytes(pickle.dumps({name: (m, thrs, cols) for name, (m, thrs, cols, _) in models.items()}))


if __name__ == "__main__":
    main()
