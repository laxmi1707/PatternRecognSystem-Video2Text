"""Which model should the screen-reaction filter be? Stop-level comparison, held out.

The filter decides which pointer stops are clicks (8 features: screen change 1/2/3 s
after the stop, anywhere and near it, change in the second before, and dwell). It is a
logistic regression. Here four models get the same procedure:

    data       pointer_cnn_eval_v1.pkl, rule cnn@0.8 (bare_sop_v2's pointer), training
               recordings to fit, held-out recordings to score
    threshold  5-fold out-of-fold scores on the training recordings (grouped by
               recording), threshold keeping KEEP of the training recall - so a model
               that overfits its training rows is not flattered
    scored     on held-out stops: AUC, and at that threshold the stops kept, the share
               of them at a click, and the share of clicks with a kept stop

    python reaction_models_v1.py
"""
from __future__ import annotations

import pickle
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from v2k.env import limit_cpu  # noqa: E402

if __name__ == "__main__":
    limit_cpu(12)

import numpy as np  # noqa: E402

import pointer_cnn_eval_v1 as e1  # noqa: E402
import pointer_cnn_v1 as pc  # noqa: E402

RULE = "cnn@0.8"
KEEPS = (0.9, 0.75, 0.6)
OUT = e1.CACHE / "reaction_models_v1.pkl"


def models():
    from lightgbm import LGBMClassifier
    from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    return {
        "logistic (now)": lambda: make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=1000)),
        "LightGBM": lambda: LGBMClassifier(n_estimators=300, learning_rate=0.05, num_leaves=31,
                                           min_child_samples=40, subsample=0.8, subsample_freq=1,
                                           colsample_bytree=0.9, n_jobs=8, verbose=-1),
        "random forest": lambda: RandomForestClassifier(n_estimators=400, min_samples_leaf=20, n_jobs=8,
                                                        random_state=0),
        "hist gradient boosting": lambda: HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05,
                                                                         min_samples_leaf=40, random_state=0),
    }


def table(recs):
    """Per recording: (record, stops, features, labels)."""
    out = []
    for r in recs:
        st = e1.stops(r, RULE)
        _, used = e1.match(r["clicks"], st, [True] * len(st))
        X = np.array([e1.features(r, s) for s in st]) if st else np.zeros((0, 8))
        y = np.array([j in used for j in range(len(st))], dtype=int)
        out.append((r, st, X, y))
    return out


def clicks_hit(rows, scores, thr) -> tuple[int, int, int]:
    """(clicks with a kept stop, stops kept, kept stops at a click) over recordings."""
    hit = kept = used = 0
    for (r, st, _, _), p in zip(rows, scores):
        keep = list(p >= thr)
        h, u = e1.match(r["clicks"], st, keep)
        hit, kept, used = hit + h, kept + int(sum(keep)), used + len(u)
    return hit, kept, used


def main() -> None:
    from sklearn.metrics import roc_auc_score
    recs = pickle.loads(e1.OUT.read_bytes())
    tr = table([r for r in recs if r["train"]])
    te = table([r for r in recs if not r["train"]])
    n_tr = sum(len(r["clicks"]) for r, *_ in tr)
    n_te = sum(len(r["clicks"]) for r, *_ in te)
    Xtr = np.vstack([X for *_, X, _ in tr])
    ytr = np.concatenate([y for *_, y in tr])
    rec_of = np.concatenate([np.full(len(y), i) for i, (*_, y) in enumerate(tr)])
    Xte = np.vstack([X for *_, X, _ in te])
    yte = np.concatenate([y for *_, y in te])
    print(f"train: {len(tr)} recordings, {len(ytr)} stops ({ytr.mean():.1%} at a click), {n_tr} clicks")
    print(f"test:  {len(te)} recordings, {len(yte)} stops ({yte.mean():.1%} at a click), {n_te} clicks\n")

    folds = rec_of % 5
    results = {}
    for name, make in models().items():
        t0 = time.perf_counter()
        oof = np.zeros(len(ytr))
        for f in range(5):
            m = make().fit(Xtr[folds != f], ytr[folds != f])
            oof[folds == f] = m.predict_proba(Xtr[folds == f])[:, 1]
        split = np.cumsum([len(y) for *_, y in tr])[:-1]
        oof_by_rec = np.split(oof, split)
        full = clicks_hit(tr, oof_by_rec, -1)[0]
        grid = np.unique(np.quantile(oof, np.linspace(0, 1, 401)))
        thrs = {}
        for keep in KEEPS:
            # clicks hit only fall as the threshold rises: the highest grid value that
            # still keeps `keep` of the recall, by bisection
            lo, hi = 0, len(grid) - 1
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if clicks_hit(tr, oof_by_rec, grid[mid])[0] >= keep * full:
                    lo = mid
                else:
                    hi = mid - 1
            thrs[keep] = float(grid[lo])
        final = make().fit(Xtr, ytr)
        pte = final.predict_proba(Xte)[:, 1]
        te_by_rec = np.split(pte, np.cumsum([len(y) for *_, y in te])[:-1])
        auc = roc_auc_score(yte, pte)
        row = {"auc": auc, "oof_auc": roc_auc_score(ytr, oof), "thr": thrs, "model": final, "levels": {}}
        for keep, t in thrs.items():
            hit, kept, used = clicks_hit(te, te_by_rec, t)
            row["levels"][keep] = (kept, used / max(kept, 1), hit / n_te)
        results[name] = row
        print(f"{name:<24} held-out AUC {auc:.3f} (train out-of-fold {row['oof_auc']:.3f}), "
              f"{time.perf_counter() - t0:.0f}s")

    print(f"\nheld-out stops kept / at a click / clicks with a kept stop, threshold keeping a share of "
          f"the training recall")
    print(f"{'':<24}" + "".join(f"{f'keep {k:.0%}':>26}" for k in KEEPS))
    for name, row in results.items():
        cells = "".join(f"{kept:>8} {prec:>7.1%} {rec:>7.1%}  " for kept, prec, rec in
                        (row["levels"][k] for k in KEEPS))
        print(f"{name:<24}{cells}")
    OUT.write_bytes(pickle.dumps({k: {kk: vv for kk, vv in v.items()} for k, v in results.items()}))
    print(f"\n-> {OUT.name}")


if __name__ == "__main__":
    main()
