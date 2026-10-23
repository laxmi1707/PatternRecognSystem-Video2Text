"""The whole SOP detector v2 scored from a reader's point of view, beside the strict score.

Strict (combined_sop_v3): a click counts only within 2 s before / 0.3 s after a logged
click and within 40 px of it. Reader's view: a click counts when a logged click within
WINDOW s either side has a name that agrees with the detected one (click_labels_v1.agree)
- position is not checked, since a reader of the SOP sees the name and the order, not
coordinates. Logged clicks with no name (icons) cannot match by name and stay missed.
Typing is scored as before (the logged text must match). Both are one to one. Same 720
held-out recordings of 61 applications as combined_sop_v3.

    python combined_sop_v5.py
"""
from __future__ import annotations

import json
import pickle
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
from combined_sop_v4 import match_clicks, match_typed, typed_from  # noqa: E402
from v2k import sop_detector as sd  # noqa: E402

WINDOWS = (2.0, 3.0, 5.0)


def match_clicks_by_name(ref_clicks, steps, window: float) -> int:
    used, hit = set(), 0
    for c in ref_clicks:
        if not c["text"]:
            continue
        cands = [j for j, k in enumerate(steps) if j not in used
                 and abs(k["t"] - c["t"]) <= window and cl.agree(k["text"], c["text"])]
        if cands:
            used.add(min(cands, key=lambda j: abs(steps[j]["t"] - c["t"])))
            hit += 1
    return hit


def main() -> None:
    oof = dict(np.load(cs.OOF))
    typed_apps = set(oof["app"].tolist())
    sc, lr, thr = b2.reaction_model()
    ocr = pickle.loads(e1.OCR.read_bytes())
    recs = [r for r in pickle.loads(e1.OUT.read_bytes()) if not r["train"]]
    recs = [r for r in recs if r["app"] in typed_apps
            and (frame_cache_dir() / r["app"] / f"{r['tid']}.json").exists()]
    print(f"{len(recs)} held-out recordings, {len({r['app'] for r in recs})} applications")

    tot = dict(ref_c=0, ref_c_named=0, ref_t=0, emit_c=0, emit_t=0, ok_t=0, strict_c=0)
    reader = {w: 0 for w in WINDOWS}
    for r in recs:
        app, tid, s = r["app"], r["tid"], r["scale"]
        ref = cs.reference(app, tid, s)
        rc = [c for c in ref if c["kind"] == "click"]
        want = [x for x in ref if x["kind"] == "type"]

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

        rec = json.loads((frame_cache_dir() / app / f"{tid}.json").read_text(encoding="utf-8"))
        with np.load(frame_cache_dir() / app / f"{tid}.npz") as z:
            ts = z["timestamp"]
        cand = sd.candidates(rec)
        m = np.flatnonzero((oof["tid"] == tid) & (oof["app"] == app))
        score = oof["score_predicted"][m]
        above = sorted((i for i in range(len(cand)) if score[i] >= sd.THRESHOLD), key=lambda i: -score[i])
        typed = typed_from(cand, ts, above)

        tot["ref_c"] += len(rc)
        tot["ref_c_named"] += sum(1 for c in rc if c["text"])
        tot["ref_t"] += len(want)
        tot["emit_c"] += len(clicks)
        tot["emit_t"] += len(typed)
        tot["ok_t"] += match_typed(want, typed)
        tot["strict_c"] += match_clicks(rc, clicks)
        for w in WINDOWS:
            reader[w] += match_clicks_by_name(rc, clicks, w)

    emit = tot["emit_c"] + tot["emit_t"]
    target = tot["ref_c"] + tot["ref_t"]
    print(f"logged: {tot['ref_c']} clicks ({tot['ref_c_named']} with a name on screen), "
          f"{tot['ref_t']} typed strings; detector wrote {tot['emit_c']} click and "
          f"{tot['emit_t']} typing steps")
    print(f"\n{'':<36}{'clicks real':>12}{'found':>8}{'whole real':>12}{'found':>8}")
    rows = [("strict (-2/+0.3 s, 40 px)", tot["strict_c"])] + \
           [(f"reader's view (name, +-{w:g} s)", reader[w]) for w in WINDOWS]
    for name, ok_c in rows:
        print(f"{name:<36}{ok_c / tot['emit_c']:>12.1%}{ok_c / tot['ref_c']:>8.1%}"
              f"{(ok_c + tot['ok_t']) / emit:>12.1%}{(ok_c + tot['ok_t']) / target:>8.1%}")
    print(f"\nnamed clicks found, reader's view +-3 s: {reader[3.0] / tot['ref_c_named']:.1%} "
          f"of {tot['ref_c_named']}")


if __name__ == "__main__":
    main()
