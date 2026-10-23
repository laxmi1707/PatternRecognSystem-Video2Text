"""The reaction filter as LightGBM: delivered SOP steps against the logistic filter, held out.

reaction_models_v1.py found LightGBM (and other tree models) separate click stops from
the rest better than the logistic regression (held-out AUC 0.817 against 0.755). This
scores what users see - named, merged steps - on the same recordings and rules as
before:

    clicks      974 held-out recordings of all 87 applications (pointer_cnn_eval_v2)
    whole SOP   the 720 of them with typing scores (61 applications, combined_sop_v3)

for the logistic filter as shipped (bare_sop_v2_reaction.pkl, threshold 0.215) and for
LightGBM at the thresholds keeping 60% and 75% of the training recall (chosen out of
fold in reaction_models_v1). Stops not yet read are OCR'd first (3 workers, cached).

    python reaction_models_v2.py
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
import click_labels_v1 as cl  # noqa: E402
import combined_sop_v1 as cs  # noqa: E402
import pointer_cnn_eval_v1 as e1  # noqa: E402
from combined_sop_v4 import match_clicks, match_typed, typed_from  # noqa: E402
from v2k import sop_detector as sd  # noqa: E402

V1 = e1.CACHE / "reaction_models_v1.pkl"


def variants():
    """name -> (score function on a feature matrix, threshold)."""
    sc, lr, thr = b2.reaction_model()
    res = pickle.loads(V1.read_bytes())
    lgb = res["LightGBM"]
    return {
        "logistic (shipped)": (lambda X: lr.predict_proba(sc.transform(X))[:, 1], thr),
        "LightGBM, keep 60%": (lambda X: lgb["model"].predict_proba(X)[:, 1], lgb["thr"][0.6]),
        "LightGBM, keep 75%": (lambda X: lgb["model"].predict_proba(X)[:, 1], lgb["thr"][0.75]),
    }


def click_steps(r, st, p, thr, ocr) -> list[dict]:
    named = []
    for j, (t, x, y, _) in enumerate(st):
        if p[j] >= thr:
            lab = cl.label_at(ocr.get((r["app"], r["tid"], t, x, y), []), x, y, cl.NEAR_PX)
            if lab:
                named.append({"t": t, "x": x, "y": y, "text": lab})
    merged = []
    for k in named:
        if merged and k["t"] - merged[-1]["t"] <= b2.MERGE_S and cl.agree(k["text"], merged[-1]["text"]):
            merged[-1] = k
        else:
            merged.append(k)
    return merged


def main() -> None:
    recs = [r for r in pickle.loads(e1.OUT.read_bytes()) if not r["train"]]
    var = variants()
    rows = []
    for r in recs:
        st = e1.stops(r, b2.RULE)
        X = np.array([e1.features(r, s) for s in st]) if st else np.zeros((0, 8))
        rows.append((r, st, {name: (f(X) if len(st) else np.zeros(0)) for name, (f, _) in var.items()}))

    # OCR every stop any variant keeps that has not been read yet
    ocr = pickle.loads(e1.OCR.read_bytes())
    jobs = {}
    for r, st, ps in rows:
        for name, (_, thr) in var.items():
            for j, (t, x, y, _) in enumerate(st):
                if ps[name][j] >= thr and (r["app"], r["tid"], t, x, y) not in ocr:
                    jobs.setdefault((r["app"], r["tid"], r["scale"]), set()).add((t, x, y))
    todo = [(a, t, s, sorted(p)) for (a, t, s), p in jobs.items()]
    if todo:
        t0 = time.perf_counter()
        print(f"OCR around {sum(len(j[3]) for j in todo)} new stops in {len(todo)} recordings ...", flush=True)
        with ProcessPoolExecutor(max_workers=3, initializer=e1._ocr_worker_init) as ex:
            for k, part in enumerate(ex.map(e1._ocr_one, todo), 1):
                ocr.update(part)
                if k % 100 == 0:
                    e1.OCR.write_bytes(pickle.dumps(ocr))
                    print(f"  {k}/{len(todo)}, {time.perf_counter() - t0:.0f}s", flush=True)
        e1.OCR.write_bytes(pickle.dumps(ocr))

    # clicks on all 974 recordings
    n_clicks = sum(len(r["clicks"]) for r, *_ in rows)
    print(f"\nclick steps, {len(rows)} held-out recordings of 87 applications, {n_clicks} clicks")
    print(f"{'':<22}{'steps':>7}{'real':>8}{'found':>8}")
    for name, (_, thr) in var.items():
        steps = real = found = 0
        for r, st, ps in rows:
            cs_ = click_steps(r, st, ps[name], thr, ocr)
            ref = [{"t": t, "x": x, "y": y} for t, x, y in r["clicks"]]
            h = match_clicks(ref, cs_)
            steps, real, found = steps + len(cs_), real + h, found + h
        print(f"{name:<22}{steps:>7}{real / max(steps, 1):>8.1%}{found / n_clicks:>8.1%}")

    # whole SOP on the 720 with typing scores
    oof = dict(np.load(cs.OOF))
    apps = set(oof["app"].tolist())
    sub = [x for x in rows if x[0]["app"] in apps
           and (frame_cache_dir() / x[0]["app"] / f"{x[0]['tid']}.json").exists()]
    typed_by = {}
    tot_c = tot_t = 0
    for r, _, _ in sub:
        app, tid = r["app"], r["tid"]
        rec = json.loads((frame_cache_dir() / app / f"{tid}.json").read_text(encoding="utf-8"))
        with np.load(frame_cache_dir() / app / f"{tid}.npz") as z:
            ts = z["timestamp"]
        cand = sd.candidates(rec)
        m = np.flatnonzero((oof["tid"] == tid) & (oof["app"] == app))
        score = oof["score_predicted"][m]
        above = sorted((i for i in range(len(cand)) if score[i] >= sd.THRESHOLD), key=lambda i: -score[i])
        ref = cs.reference(app, tid, r["scale"])
        rc = [c for c in ref if c["kind"] == "click"]
        want = [x for x in ref if x["kind"] == "type"]
        typed = typed_from(cand, ts, above)
        typed_by[(app, tid)] = (rc, want, typed, match_typed(want, typed))
        tot_c, tot_t = tot_c + len(rc), tot_t + len(want)
    print(f"\nwhole SOP, {len(sub)} held-out recordings of {len({x[0]['app'] for x in sub})} applications, "
          f"{tot_c} clicks + {tot_t} typed strings")
    print(f"{'':<22}{'steps':>7}{'real':>8}{'found':>8}{'clicks real':>13}{'found':>8}")
    for name, (_, thr) in var.items():
        ec = oc = et = ot = 0
        for r, st, ps in sub:
            rc, want, typed, ok_t = typed_by[(r["app"], r["tid"])]
            cs_ = click_steps(r, st, ps[name], thr, ocr)
            ec, oc = ec + len(cs_), oc + match_clicks(rc, cs_)
            et, ot = et + len(typed), ot + ok_t
        print(f"{name:<22}{ec + et:>7}{(oc + ot) / (ec + et):>8.1%}{(oc + ot) / (tot_c + tot_t):>8.1%}"
              f"{oc / max(ec, 1):>13.1%}{oc / tot_c:>8.1%}")


if __name__ == "__main__":
    main()
