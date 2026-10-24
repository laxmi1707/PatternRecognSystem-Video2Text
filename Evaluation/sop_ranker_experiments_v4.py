"""Round 4: round 3 plus what arrived on screen together with each candidate.

Round 3 (run_038) added 8 features on how a string arrived and moved the shipped
ranker from 50.6% real / 26.4% found to 52.4% / 26.6% at 0.5. The typed strings still
missed mostly never grow between sampled frames (636 covered strings score below 0.05;
283 of them have a candidate reading exactly the logged text), so here 3 NOVELTY
features say whether the string arrived alone or with a whole new page.

Below, round 3's description, which still holds for the method.

Round 3: give the typing ranker new evidence - how each candidate's text arrived.

Rounds 1 and 2 (run_033, run_036) changed the features about the final string and the
way the rankers are trained; shipped run_037 finds 26.4% of logged typed strings at 50.6%
real, while 90% are matched by some candidate. Here v2k/sop_extras.py adds 8 features
from the frames (was the string on screen before it was typed, did it grow a few
characters at a time, is it still there afterwards, ...) and one from the fold's text
model (the candidate's text score ranked within its recording):

    D   shipped: 32 features, one ranker per application, routed by stage 1
    H   D + the 9 new features
    I   H, one pooled ranker for every application (no routing)

Same candidates, folds, nested text score and scoring as v2k/sop_detector.evaluate
(repeated reads collapsed, one to one). Saves H's out-of-fold scores in run_037's
format, so combined_sop can score the whole SOP with them.

    python sop_ranker_experiments_v3.py
"""
from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from v2k.env import frame_cache_dir, limit_cpu  # noqa: E402

if __name__ == "__main__":
    limit_cpu(16)

import numpy as np  # noqa: E402

from v2k import sop_detector as sd  # noqa: E402
from v2k.sop_extras import EXTRA as EXTRA3, NOVELTY, candidates_ext  # noqa: E402

EXTRA = EXTRA3 + NOVELTY
EXTRAS = sd.CACHE / f"sop_extras_v2_{sd.BACKEND_SNAPSHOT}.npz"
THRESHOLDS = (0.3, 0.5)


def _extras_for(job):
    app, path = job
    rec = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = candidates_ext(rec)
    base = [[r[f] for f in sd.FEATURES] for r in rows]
    return app, int(Path(path).stem), base, [[r[f] for f in EXTRA] for r in rows]


def build_extras(data: dict) -> np.ndarray:
    if EXTRAS.exists():
        with np.load(EXTRAS) as z:
            return z["E"]
    apps = sd.eligible_apps()
    jobs = [(a, str(p)) for a in apps for p in sorted((frame_cache_dir() / a).glob("*.json"))]
    print(f"extra features: {len(jobs)} recordings, {sd.WORKERS} workers", flush=True)
    E, B, A, T = [], [], [], []
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=sd.WORKERS) as pool:
        for n, (a, t, base, ex) in enumerate(pool.map(_extras_for, jobs, chunksize=16), 1):
            E += ex
            B += base
            A += [a] * len(ex)
            T += [t] * len(ex)
            if n % 500 == 0:
                print(f"  {n}/{len(jobs)}, {time.perf_counter() - t0:.0f}s", flush=True)
    # the same rows in the same order as the candidate cache, or nothing here means anything
    assert len(E) == len(data["X"]), (len(E), len(data["X"]))
    assert (np.asarray(T) == data["tid"]).all() and (np.asarray(A) == data["app"]).all()
    assert np.allclose(np.asarray(B, dtype=np.float32), data["X"], atol=1e-4)
    E = np.asarray(E, dtype=np.float32)
    np.savez_compressed(EXTRAS, E=E)
    print(f"cached {E.shape} to {EXTRAS.name} in {time.perf_counter() - t0:.0f}s", flush=True)
    return E


def rank_in_recording(v: np.ndarray, tid: np.ndarray) -> np.ndarray:
    out = np.zeros(len(v), dtype=np.float32)
    order = np.argsort(tid, kind="stable")
    for rows in np.split(order, np.flatnonzero(np.diff(tid[order])) + 1):
        if len(rows):
            out[rows] = np.argsort(np.argsort(-v[rows])) / max(len(rows) - 1, 1)
    return out


def score_rows(scores, covers, tid, texts, n_targets, mask=None):
    rows = []
    for t in THRESHOLDS:
        keep = scores >= t
        if mask is not None:
            keep &= mask
        kd = sd._dedupe_mask(keep, scores, tid, texts)
        p, r = sd._strict(kd, covers, tid, n_targets)
        rows.append({"threshold": t, "steps": int(kd.sum()), "precision": p, "recall": r})
    return rows


def main() -> None:
    from v2k.evaluate import new_run_dir

    data = sd.build_candidates()
    X, app, tid = data["X"], data["app"], data["tid"]
    E = build_extras(data)
    label, covers = sd.labels_at(data, sd.MIN_LEN)
    n_targets = int((data["want_len"] >= sd.MIN_LEN).sum())
    pred, fold_of = sd.stage1_oof()
    fold = np.array([fold_of[int(t)] for t in tid])
    apps = sorted(set(app.tolist()))
    texts = sd.texts_of(data)
    lex = np.array([sd.lexical(t) for t in texts], dtype=np.float32)
    ctx = sd.context(X, tid, texts)
    print(f"{len(X)} candidates, {n_targets} logged strings, {len(apps)} applications", flush=True)

    S = {v: np.zeros(len(X)) for v in ("D", "H", "I")}
    t0 = time.perf_counter()
    imp = np.zeros(len(sd.ALL_FEATURES) + len(EXTRA) + 1)
    for k in range(5):
        tr, te = fold != k, fold == k
        ts = sd.oof_text_scores(texts, label, tid, np.flatnonzero(tr), np.flatnonzero(te))
        M = sd.ranker_matrix(X, lex, ts, ctx)
        M2 = np.hstack([M, E, rank_in_recording(ts, tid)[:, None]]).astype(np.float32)
        pooled = sd._fit_pooled(M2[tr], label[tr])
        S["I"][te] = pooled.predict_proba(M2[te])[:, 1]
        imp += pooled.feature_importances_
        routed: dict[str, list[int]] = {}
        for i in np.flatnonzero(te):
            routed.setdefault(pred[int(tid[i])][1], []).append(i)
        n_r = 0
        for a in apps:
            m = tr & (app == a)
            if not (m.sum() >= sd.MIN_ROWS and label[m].sum() >= sd.MIN_POS):
                continue
            n_r += 1
            rows_i = np.asarray(routed.get(a, []), dtype=np.int64)
            if not len(rows_i):
                continue
            S["D"][rows_i] = sd._fit_app(M[m], label[m]).predict_proba(M[rows_i])[:, 1]
            S["H"][rows_i] = sd._fit_app(M2[m], label[m]).predict_proba(M2[rows_i])[:, 1]
        print(f"  fold {k}: {n_r} application rankers, {time.perf_counter() - t0:.0f}s", flush=True)

    names = {"D": "per-application rankers, 32 features (shipped)",
             "H": "per-application rankers, 32 + 12 new features",
             "I": "one pooled ranker, 32 + 12 new features"}
    res = {"n_candidates": int(len(X)), "n_targets": n_targets, "n_apps": len(apps)}
    print(f"\n{'':<52}{'thr':>5}{'steps':>7}{'real':>8}{'found':>8}")
    for v, nm in names.items():
        res[v] = {"name": nm, "rows": score_rows(S[v], covers, tid, texts, n_targets)}
        for r in res[v]["rows"]:
            print(f"{nm:<52}{r['threshold']:>5.1f}{r['steps']:>7}{r['precision']:>8.1%}{r['recall']:>8.1%}")
    feats = sd.ALL_FEATURES + EXTRA + ["ts_rank"]
    res["importance_I"] = sorted(zip(feats, (imp / 5).round(1).tolist()), key=lambda t: -t[1])
    print("\npooled importance:", ", ".join(f"{f} {v:.0f}" for f, v in res["importance_I"][:12]))

    out = new_run_dir("sop-ranker-experiments-4")
    (out / "results.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    np.savez_compressed(out / "oof_scores.npz", app=app, tid=tid, label=label, fold=fold,
                        score_predicted=S["H"], score_shipped=S["D"], score_no_routing=S["I"])
    print(f"saved to {out}")


if __name__ == "__main__":
    main()
