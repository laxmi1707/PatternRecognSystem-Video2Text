"""Seeing the pointer without knowing its shape: a moving sprite matches itself.

pointer_miss_diag_v1 showed why 77 of 204 held-out clicks had no pointer seen
near them: over buttons and links the pointer is a hand, over text an I-beam,
and the harvested templates are almost all arrows. In 56 of the 77 a
pointer-sized region did change near the click; no template matched it.

A pointer that moves leaves two pointer-sized changed regions between frames,
where it was and where it is, and the picture at the new place in this frame is
the picture at the old place in the previous frame. So, besides the templates:

    self-match   two small changed regions of similar size whose changed
                 pixels, aligned at their top-left, read the same in
                 (frame t at one) and (frame t-1 at the other); the one that
                 matches as "now" is the new position

The hotspot of an unknown shape is taken at 30% across and 15% down its region
(an arrow's tip is at the corner, a hand's finger near the top, an I-beam's
middle is within NEAR of either).

    python pointer_selfmatch_v1.py extract [fps]   decode -> cache/pointer_selfmatch_v1.pkl
    python pointer_selfmatch_v1.py eval            reaction filter, click names, merged SOP,
                                                   where clicks are lost - all on this cache
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

import pointer_reaction_v1 as pr  # noqa: E402
import pointer_tracker_v1 as pt  # noqa: E402
from pointer_motion_v1 import DIFF, MATCH, frames  # noqa: E402

OUT = pt.CACHE / "pointer_selfmatch_v1.pkl"
SELF = 18.0            # mean absolute grey difference over the sprite's pixels that counts as "same picture"


def step(g: np.ndarray, prev: np.ndarray, templates: list[dict], scale: float):
    """(template hit or None, self-match hit or None, regions larger than a pointer)."""
    import cv2
    raw = (cv2.absdiff(g, prev) > DIFF).astype(np.uint8)
    m = cv2.dilate(raw, np.ones((5, 5), np.uint8))
    n, _, stats, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    big = 70 * scale
    best = None
    large, small = [], []
    for k in range(1, n):
        x, y, w, h, area = (int(v) for v in stats[k])
        if area < 15:
            continue
        if w > big or h > big:
            large.append((x, y, w, h, area))
            continue
        small.append((x, y, w, h))
        pad = int(8 * scale)
        x0, y0 = max(0, x - pad), max(0, y - pad)
        region = g[y0:min(g.shape[0], y + h + pad), x0:min(g.shape[1], x + w + pad)]
        for tp in templates:
            if tp["k"] != (2 if scale == 2.0 else 1):
                continue
            th, tw = tp["img"].shape
            if region.shape[0] < th or region.shape[1] < tw:
                continue
            res = cv2.matchTemplate(region, tp["img"], cv2.TM_SQDIFF, mask=tp["mask"])
            res = np.nan_to_num(res / max(int(tp["mask"].sum()), 1), nan=np.inf)
            _, _, mn, _ = cv2.minMaxLoc(res)
            v = float(res[mn[1], mn[0]])
            if v < MATCH and (best is None or v < best[0]):
                best = (v, x0 + mn[0] + tp["hot"][0], y0 + mn[1] + tp["hot"][1])

    selfhit = None
    if 2 <= len(small) <= 12:
        for i in range(len(small)):
            for j in range(len(small)):
                if i == j:
                    continue
                xa, ya, wa, ha = small[i]      # old position (sprite in prev)
                xb, yb, wb, hb = small[j]      # new position (sprite in g)
                if abs(wa - wb) > 0.4 * max(wa, wb) or abs(ha - hb) > 0.4 * max(ha, hb):
                    continue
                if np.hypot(xa - xb, ya - yb) < 4 * scale:
                    continue
                w, h = min(wa, wb), min(ha, hb)
                if w < 6 * scale or h < 10 * scale:
                    continue
                mb = raw[yb:yb + h, xb:xb + w].astype(bool)
                if mb.sum() < 20:
                    continue
                new = g[yb:yb + h, xb:xb + w].astype(np.float32)
                old = prev[ya:ya + h, xa:xa + w].astype(np.float32)
                if new.shape != old.shape:
                    continue
                d = float(np.abs(new - old)[mb].mean())
                # and the sprite really left the old place: there the frame now differs from it
                gone = float(np.abs(g[ya:ya + h, xa:xa + w].astype(np.float32) - old)[mb].mean()) \
                    if g[ya:ya + h, xa:xa + w].shape == old.shape else 0.0
                if d < SELF and gone > 2 * SELF and (selfhit is None or d < selfhit[0]):
                    selfhit = (d, xb + 0.3 * w, yb + 0.15 * h)
    return best, selfhit, large


def extract(fps: float) -> None:
    if pt.KEEP.exists():
        pt.KEEP.unlink()
    templates = pt.load_templates()
    t0 = time.perf_counter()
    recs = []
    n_tpl = n_self = n_both = 0
    for i, (app, tid) in enumerate(pt.recordings()):
        ev = pt.pointer_events(app, tid)
        if not ev:
            continue
        v = pt.Video(pt.video_of(app, tid))
        s = pt.coord_scale(ev, v.W)
        area = v.W * v.H
        v.close()
        prev = None
        moves, iv = [], []
        for t, g in frames(pt.video_of(app, tid), fps):
            if prev is not None and prev.shape == g.shape:
                hit, selfhit, large = step(g, prev, templates, s)
                iv.append((t, [(x / s, y / s, w / s, h / s, a / area) for x, y, w, h, a in large]))
                n_tpl += hit is not None
                n_self += selfhit is not None
                n_both += hit is not None and selfhit is not None
                h_ = hit if hit is not None else selfhit
                if h_ is not None:
                    moves.append((t, h_[1] / s, h_[2] / s))
            prev = g
        recs.append({"app": app, "tid": tid, "train": pt.is_train(tid), "fps": fps,
                     "clicks": [(e["t"], e["x"], e["y"]) for e in ev if e["type"] in pt.CLICKS],
                     "moves": moves, "iv": iv})
        if (i + 1) % 40 == 0:
            print(f"  {i + 1} recordings, {time.perf_counter() - t0:.0f}s", flush=True)
    OUT.write_bytes(pickle.dumps(recs))
    print(f"{len(recs)} recordings -> {OUT.name}, {time.perf_counter() - t0:.0f}s; frame pairs with "
          f"template {n_tpl}, self-match {n_self}, both {n_both}")


def evaluate() -> None:
    """Every downstream step of the click pipeline, pointed at this cache."""
    pr.OUT = OUT
    import click_labels_v1 as cl
    import combined_sop_v2 as cs2
    import missed_steps_v1 as ms
    print("=== stops, reaction filter (pointer_reaction_v1.evaluate) ===")
    pr.evaluate()
    print("\n=== click names (click_labels_v1) ===")
    cl.main()
    print("\n=== typing + clicks merged (combined_sop_v2) ===")
    cs2.OUT_MD = ROOT / "pointer_selfmatch_v1_examples.md"
    cs2.main()
    print("\n=== where clicks are lost (missed_steps_v1) ===")
    ms.main()


if __name__ == "__main__":
    if sys.argv[1] == "extract":
        extract(float(sys.argv[2]) if len(sys.argv) > 2 else 5.0)
    else:
        evaluate()
