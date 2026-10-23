"""Two quick changes to how kept pointer stops become click steps, scored as delivered.

With the shipped LightGBM filter (detector/clicks.py), on the same held-out recordings
and rules as reaction_models_v2 (974 recordings / 87 applications for clicks; the 720 /
61 with typing scores for the whole SOP):

    shipped        named stops; the same name within 2 s is one click (the later kept)
    same place     also one click when two stops within 2 s are within 20 px, whatever
                   OCR read (a press read twice as "Open" and "Onen"); the earlier kept,
                   since a stop comes just before the press
    + icons        unnamed kept stops are not dropped but written as "Click (icon)"
                   (their names cannot be checked; they count when time and place match)

    python click_variants_v1.py
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
from detector.clicks import load_reaction_model  # noqa: E402
from v2k import sop_detector as sd  # noqa: E402

SAME_PLACE_PX = 20


def steps_of(r, st, p, thr, ocr, same_place: bool, icons: bool) -> list[dict]:
    kept = []
    for j, (t, x, y, _) in enumerate(st):
        if p[j] < thr:
            continue
        lab = cl.label_at(ocr.get((r["app"], r["tid"], t, x, y), []), x, y, cl.NEAR_PX)
        if lab or icons:
            kept.append({"t": t, "x": x, "y": y, "text": lab})
    out = []
    for k in kept:
        if out and k["t"] - out[-1]["t"] <= b2.MERGE_S:
            prev = out[-1]
            if same_place and np.hypot(k["x"] - prev["x"], k["y"] - prev["y"]) <= SAME_PLACE_PX:
                if not prev["text"] and k["text"]:
                    prev["text"] = k["text"]          # keep the earlier stop, with a name if any
                continue
            if k["text"] and prev["text"] and cl.agree(k["text"], prev["text"]):
                out[-1] = k
                continue
        out.append(k)
    return out


def main() -> None:
    score, thr = load_reaction_model()
    ocr = pickle.loads(e1.OCR.read_bytes())
    recs = [r for r in pickle.loads(e1.OUT.read_bytes()) if not r["train"]]
    rows = []
    for r in recs:
        st = e1.stops(r, b2.RULE)
        p = score(np.array([e1.features(r, s) for s in st])) if st else np.zeros(0)
        rows.append((r, st, p))
    missing = sum(1 for r, st, p in rows for j, (t, x, y, _) in enumerate(st)
                  if p[j] >= thr and (r["app"], r["tid"], t, x, y) not in ocr)
    print(f"kept stops without an OCR read: {missing}")

    variants = {"shipped": (False, False), "same place": (True, False),
                "+ icons": (False, True), "same place + icons": (True, True)}
    n_clicks = sum(len(r["clicks"]) for r, *_ in rows)
    print(f"\nclick steps, {len(rows)} held-out recordings of 87 applications, {n_clicks} clicks")
    print(f"{'':<22}{'steps':>7}{'icons':>7}{'real':>8}{'found':>8}")
    for name, (sp, ic) in variants.items():
        n = icons = hit = 0
        for r, st, p in rows:
            s_ = steps_of(r, st, p, thr, ocr, sp, ic)
            ref = [{"t": t, "x": x, "y": y} for t, x, y in r["clicks"]]
            n, icons, hit = n + len(s_), icons + sum(1 for k in s_ if not k["text"]), hit + match_clicks(ref, s_)
        print(f"{name:<22}{n:>7}{icons:>7}{hit / n:>8.1%}{hit / n_clicks:>8.1%}")

    oof = dict(np.load(cs.OOF))
    apps = set(oof["app"].tolist())
    sub = [x for x in rows if x[0]["app"] in apps
           and (frame_cache_dir() / x[0]["app"] / f"{x[0]['tid']}.json").exists()]
    typed = {}
    for r, _, _ in sub:
        app, tid = r["app"], r["tid"]
        rec = json.loads((frame_cache_dir() / app / f"{tid}.json").read_text(encoding="utf-8"))
        with np.load(frame_cache_dir() / app / f"{tid}.npz") as z:
            ts = z["timestamp"]
        cand = sd.candidates(rec)
        m = np.flatnonzero((oof["tid"] == tid) & (oof["app"] == app))
        sc_ = oof["score_predicted"][m]
        above = sorted((i for i in range(len(cand)) if sc_[i] >= sd.THRESHOLD), key=lambda i: -sc_[i])
        ref = cs.reference(app, tid, r["scale"])
        ty = typed_from(cand, ts, above)
        want = [x for x in ref if x["kind"] == "type"]
        typed[(app, tid)] = ([c for c in ref if c["kind"] == "click"], len(want), len(ty), match_typed(want, ty))
    tot = sum(len(v[0]) + v[1] for v in typed.values())
    print(f"\nwhole SOP, {len(sub)} recordings of 61 applications")
    print(f"{'':<22}{'steps':>7}{'real':>8}{'found':>8}")
    for name, (sp, ic) in variants.items():
        n = ok = 0
        for r, st, p in sub:
            rc, _, nt, okt = typed[(r["app"], r["tid"])]
            s_ = steps_of(r, st, p, thr, ocr, sp, ic)
            n, ok = n + len(s_) + nt, ok + match_clicks(rc, s_) + okt
        print(f"{name:<22}{n:>7}{ok / n:>8.1%}{ok / tot:>8.1%}")


if __name__ == "__main__":
    main()
