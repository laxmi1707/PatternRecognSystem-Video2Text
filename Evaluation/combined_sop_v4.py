"""The whole SOP detector v2 against two chance baselines, on the same recordings and rules.

combined_sop_v3 scores the detector on 720 held-out recordings (61 applications). This
adds, per recording and with the SAME number of click and typing steps as the detector
wrote there:

    random            clicks at uniformly random times and screen positions (typing: a
                      random string never matches a logged one, so 0 by construction)
    random candidate  clicks: random picks among all of the recording's pointer stops
                      (cnn@0.8, no reaction filter, no naming); typing: random picks
                      among the growing-text candidates (no ranker), deduplicated
    detector          as combined_sop_v3

Scoring as combined_sop_v3 (one to one; a click within 2 s before / 0.3 s after and
40 px; typed text by sop_detector's text match). Baselines averaged over 20 seeds.

    python combined_sop_v4.py
"""
from __future__ import annotations

import json
import pickle
import random
import sys
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
import pointer_cnn_v1 as pc  # noqa: E402
from v2k import sop_detector as sd  # noqa: E402

BEFORE, AFTER, NEAR = 2.0, 0.3, 40
SEEDS = 20


def match_clicks(ref_clicks, steps) -> int:
    used, hit = set(), 0
    for c in ref_clicks:
        cands = [j for j, k in enumerate(steps) if j not in used
                 and c["t"] - BEFORE <= k["t"] <= c["t"] + AFTER
                 and np.hypot(k["x"] - c["x"], k["y"] - c["y"]) <= NEAR]
        if cands:
            used.add(min(cands, key=lambda j: abs(steps[j]["t"] - c["t"])))
            hit += 1
    return hit


def match_typed(want, typed) -> int:
    taken = set()
    for k in typed:
        hit = [i for i, w in enumerate(want) if i not in taken and sd._matches(k["text"], w["text"])]
        if hit:
            taken.add(hit[0])
    return len(taken)


def typed_from(rows, ts, order) -> list[dict]:
    """Typed steps from candidate indices in priority order, deduplicated, timed as the detector."""
    out = []
    for i in sd.dedupe(order, [r["text"] for r in rows]):
        k = max(min(rows[i]["start"], len(ts) - 1) - 1, 0)
        out.append({"t": float(ts[k]), "text": rows[i]["text"]})
    return out


def screen_size(app: str, tid: int, s: float) -> tuple[float, float]:
    import cv2
    cap = cv2.VideoCapture(str(pc.VIDEOS / app / str(tid) / "video" / "video.mp4"))
    W, H = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    cap.release()
    return W / s, H / s


def main() -> None:
    oof = dict(np.load(cs.OOF))
    typed_apps = set(oof["app"].tolist())
    sc, lr, thr = b2.reaction_model()
    ocr = pickle.loads(e1.OCR.read_bytes())
    recs = [r for r in pickle.loads(e1.OUT.read_bytes()) if not r["train"]]
    recs = [r for r in recs if r["app"] in typed_apps
            and (frame_cache_dir() / r["app"] / f"{r['tid']}.json").exists()]
    print(f"{len(recs)} held-out recordings, {len({r['app'] for r in recs})} applications")

    rows_out = {name: {"emit_c": 0, "ok_c": 0, "emit_t": 0, "ok_t": 0}
                for name in ("random", "random candidate", "detector")}
    tot = {"ref_c": 0, "ref_t": 0, "ref_all": 0}
    rngs = [random.Random(seed) for seed in range(SEEDS)]
    for r in recs:
        app, tid, s = r["app"], r["tid"], r["scale"]
        ref = cs.reference(app, tid, s)
        rc = [c for c in ref if c["kind"] == "click"]
        want = [x for x in ref if x["kind"] == "type"]
        tot["ref_c"] += len(rc)
        tot["ref_t"] += len(want)
        tot["ref_all"] += len(ref)

        # the detector's click steps, as combined_sop_v3
        st = e1.stops(r, b2.RULE)
        p = lr.predict_proba(sc.transform(np.array([e1.features(r, x) for x in st])))[:, 1] if st else []
        named = []
        for j, (t, x, y, _) in enumerate(st):
            if p[j] >= thr:
                lab = cl.label_at(ocr.get((app, tid, t, x, y), []), x, y, cl.NEAR_PX)
                if lab:
                    named.append({"t": t, "x": x, "y": y, "text": lab})
        clicks = []
        for k in named:
            if clicks and k["t"] - clicks[-1]["t"] <= b2.MERGE_S and cl.agree(k["text"], clicks[-1]["text"]):
                clicks[-1] = k
            else:
                clicks.append(k)

        # the detector's typed steps, and the candidates they were chosen from
        rec = json.loads((frame_cache_dir() / app / f"{tid}.json").read_text(encoding="utf-8"))
        with np.load(frame_cache_dir() / app / f"{tid}.npz") as z:
            ts = z["timestamp"]
        cand = sd.candidates(rec)
        m = np.flatnonzero((oof["tid"] == tid) & (oof["app"] == app))
        score = oof["score_predicted"][m]
        above = sorted((i for i in range(len(cand)) if score[i] >= sd.THRESHOLD), key=lambda i: -score[i])
        typed = typed_from(cand, ts, above)

        d = rows_out["detector"]
        d["emit_c"] += len(clicks)
        d["ok_c"] += match_clicks(rc, clicks)
        d["emit_t"] += len(typed)
        d["ok_t"] += match_typed(want, typed)          # highest score first, as combined_sop_v3

        n_c, n_t = len(clicks), len(typed)
        dur = max((f[0] for f in r["frames"]), default=1.0)
        W, H = screen_size(app, tid, s) if n_c else (1, 1)
        for rng in rngs:
            rnd = [{"t": rng.uniform(0, dur), "x": rng.uniform(0, W), "y": rng.uniform(0, H)} for _ in range(n_c)]
            rows_out["random"]["emit_c"] += n_c
            rows_out["random"]["ok_c"] += match_clicks(rc, sorted(rnd, key=lambda k: k["t"]))
            rows_out["random"]["emit_t"] += n_t           # random strings: no match by construction

            pick = rng.sample(st, min(n_c, len(st)))
            rc_steps = [{"t": t, "x": x, "y": y} for t, x, y, _ in sorted(pick)]
            rows_out["random candidate"]["emit_c"] += len(rc_steps)
            rows_out["random candidate"]["ok_c"] += match_clicks(rc, rc_steps)
            order = list(range(len(cand)))
            rng.shuffle(order)
            rt = typed_from(cand, ts, order)[:n_t]
            rows_out["random candidate"]["emit_t"] += len(rt)
            rows_out["random candidate"]["ok_t"] += match_typed(want, rt)   # in the random order

    print(f"log steps: {tot['ref_all']} ({tot['ref_c']} clicks, {tot['ref_t']} typed strings)")
    print(f"\n{'':<18}{'clicks real':>12}{'found':>8}{'typing real':>13}{'found':>8}{'whole real':>12}{'found':>8}")
    for name, v in rows_out.items():
        k = SEEDS if name != "detector" else 1
        ec, oc, et, ot = (v[x] / k for x in ("emit_c", "ok_c", "emit_t", "ok_t"))
        print(f"{name:<18}{oc / max(ec, 1):>12.1%}{oc / tot['ref_c']:>8.1%}{ot / max(et, 1):>13.1%}"
              f"{ot / max(tot['ref_t'], 1):>8.1%}{(oc + ot) / max(ec + et, 1):>12.1%}"
              f"{(oc + ot) / (tot['ref_c'] + tot['ref_t']):>8.1%}")


if __name__ == "__main__":
    main()
