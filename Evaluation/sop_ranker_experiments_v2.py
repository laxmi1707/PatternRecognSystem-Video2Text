"""Round 2: same 32 features, different ways of training the ranker.

Round 1 (run_033) showed the text and context features carry across
applications: a single pooled ranker went from 9.8% to 18.3% recall. That makes
the shipped design - one LightGBM per application, some trained on a few dozen
positives - worth questioning.

    D  shipped: one ranker per application, routed by stage 1
    E  one pooled ranker that is told the application: stage 1's answer is a
       categorical feature (true application while training, stage 1's guess at
       test time, exactly as routing uses it)
    F  per-application rankers, more conservative: shallower trees, larger
       leaves, row and feature subsampling - fixed in advance, not tuned on
       the test folds
    G  the mean of D's and E's scores

Same folds, same nested text score, scored as the SOP is delivered.

    python sop_ranker_experiments_v2.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from v2k.env import limit_cpu  # noqa: E402

if __name__ == "__main__":
    limit_cpu(16)

import numpy as np  # noqa: E402

from v2k import sop_detector as sd  # noqa: E402
from v2k.evaluate import new_run_dir  # noqa: E402

THRESHOLDS = (0.3, 0.5)


def fit_conservative(X, y):
    import lightgbm as lgb
    return lgb.LGBMClassifier(n_estimators=300, learning_rate=0.03, num_leaves=15,
                              min_child_samples=40, subsample=0.8, subsample_freq=1,
                              colsample_bytree=0.8, reg_lambda=1.0, verbose=-1,
                              n_jobs=8).fit(X, y)


def fit_pooled_with_app(X, app_code, y):
    import lightgbm as lgb
    M = np.hstack([X, app_code[:, None].astype(np.float32)])
    return lgb.LGBMClassifier(n_estimators=500, learning_rate=0.05, num_leaves=63,
                              min_child_samples=20, cat_smooth=10, verbose=-1,
                              n_jobs=8).fit(M, y, categorical_feature=[M.shape[1] - 1])


def score_pooled_with_app(model, X, app_code):
    return model.predict_proba(np.hstack([X, app_code[:, None].astype(np.float32)]))[:, 1]


def delivered(s, tid, texts, covers, n_targets, t) -> dict:
    kd = sd._dedupe_mask(s >= t, s, tid, texts)
    p, r = sd._strict(kd, covers, tid, n_targets)
    return {"threshold": float(t), "steps": int(kd.sum()), "precision": p, "recall": r}


def main() -> None:
    t0 = time.perf_counter()
    data = sd.build_candidates()
    X, app, tid = data["X"], data["app"], data["tid"]
    texts = sd.texts_of(data)
    label, covers = sd.labels_at(data, sd.MIN_LEN)
    n_t = int((data["want_len"] >= sd.MIN_LEN).sum())
    pred, fold_of = sd.stage1_oof()
    fold = np.array([fold_of[int(t)] for t in tid])
    apps = sorted(set(app.tolist()))
    code = {a: i for i, a in enumerate(apps)}
    true_code = np.array([code[a] for a in app.tolist()], dtype=np.int64)
    pred_code = np.array([code.get(pred[int(t)][1], -1) for t in tid], dtype=np.int64)
    lex = np.array([sd.lexical(t) for t in texts], dtype=np.float32)
    ctx = sd.context(X, tid, texts)
    print(f"{len(X)} candidates, {n_t} targets; features in {time.perf_counter() - t0:.0f}s",
          flush=True)

    S = {v: np.zeros(len(X)) for v in "DEF"}
    for k in range(5):
        tr, te = fold != k, fold == k
        ts = sd.oof_text_scores(texts, label, tid, np.flatnonzero(tr), np.flatnonzero(te))
        M = sd.ranker_matrix(X, lex, ts, ctx)
        routed: dict[str, list[int]] = {}
        for i in np.flatnonzero(te):
            routed.setdefault(pred[int(tid[i])][1], []).append(i)
        for v, fitter in (("D", sd._fit_app), ("F", fit_conservative)):
            per_app = {}
            for a in apps:
                m = tr & (app == a)
                if m.sum() >= sd.MIN_ROWS and label[m].sum() >= sd.MIN_POS:
                    per_app[a] = fitter(M[m], label[m])
            for a, rows in routed.items():
                if a in per_app:
                    rows = np.asarray(rows)
                    S[v][rows] = per_app[a].predict_proba(M[rows])[:, 1]
        e = fit_pooled_with_app(M[tr], true_code[tr], label[tr])
        S["E"][te] = score_pooled_with_app(e, M[te], pred_code[te])
        print(f"  fold {k} done, {time.perf_counter() - t0:.0f}s", flush=True)
    S["G"] = (S["D"] + S["E"]) / 2

    names = {"D": "per-application rankers (shipped)", "E": "one ranker told the application",
             "F": "per-application, conservative", "G": "mean of D and E"}
    out = {}
    ref = None
    print(f"\n{'':3s}{'variant':36s}{'thr':>5s}{'steps':>7s}{'precision':>11s}{'recall':>9s}")
    for v in "DEFG":
        rows = [delivered(S[v], tid, texts, covers, n_t, t) for t in THRESHOLDS]
        curve = [delivered(S[v], tid, texts, covers, n_t, t)
                 for t in np.round(np.arange(0.05, 0.96, 0.05), 2) if (S[v] >= t).any()]
        out[v] = {"name": names[v], "rows": rows, "curve": curve}
        ref = ref if ref is not None else rows[1]["recall"]
        for r in rows:
            print(f"{v:3s}{names[v]:36s}{r['threshold']:5.1f}{r['steps']:7d}"
                  f"{r['precision']:11.1%}{r['recall']:9.1%}")
    print(f"\nprecision at recall >= {ref:.1%} (D at 0.5), and recall at precision >= 47.9%:")
    for v in "DEFG":
        c = out[v]["curve"]
        p_at = max([x["precision"] for x in c if x["recall"] >= ref], default=None)
        r_at = max([x["recall"] for x in c if x["precision"] >= 0.479], default=None)
        out[v]["precision_at_ref_recall"], out[v]["recall_at_ref_precision"] = p_at, r_at
        print(f"   {v}  precision {p_at:.1%}" if p_at is not None else f"   {v}  precision -", end="")
        print(f"   recall {r_at:.1%}" if r_at is not None else "   recall -")

    run = new_run_dir("sop-ranker-experiments-2")
    (run / "results.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    np.savez_compressed(run / "oof_scores.npz", **{f"score_{v}": s for v, s in S.items()})
    print(f"\nsaved to {run}  ({time.perf_counter() - t0:.0f}s)")


if __name__ == "__main__":
    main()
