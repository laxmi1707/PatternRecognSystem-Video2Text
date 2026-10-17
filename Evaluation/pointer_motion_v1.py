"""Plan A: find the pointer only where the screen changed, then clicks where it stops.

Tracking the pointer frame by frame (pointer_tracker_v1.py) picked arrow-like
icons instead of the pointer too often: 42.7% of resting pointers placed within
25 px. Clicks do not need the pointer in every frame, only when it moved and
where it stopped. A moving pointer leaves two small pointer-shaped blobs in the
difference of consecutive frames - where it was and where it is - while a
static icon never appears in a difference at all. So the pointer templates are
matched only inside small changed blobs of the current frame.

    moved at t     a changed blob in frame t matches a pointer template
    stop event     a move at t, then no move at t+1: the pointer rests where it
                   was matched at t - the predicted click point

Scored on recordings whose pointer templates were never harvested from:
    interval AUC   "the pointer moved here or one step earlier" against
                   "a click was logged here" (the logged-move oracle's 0.927 is a
                   logging artefact - see cursor_click_probe_v1.py)
    events         stops matched to logged clicks: stop at most 2 s before the
                   click and within 40 logged pixels of it

    python pointer_motion_v1.py [fps]
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
    limit_cpu(12)

import numpy as np  # noqa: E402

import pointer_tracker_v1 as pt  # noqa: E402

DIFF = 25            # grey-level change counted as changed
MATCH = 900          # masked mean squared difference that counts as "this blob is the pointer"
NEAR = 40            # logged px between a stop and a click
BEFORE, AFTER = 2.0, 0.3


def auc(score: np.ndarray, label: np.ndarray) -> float:
    order = np.argsort(score, kind="stable")
    ranks = np.empty(len(score))
    ranks[order] = np.arange(1, len(score) + 1)
    n1 = label.sum()
    n0 = len(label) - n1
    return float((ranks[label == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)) if n1 and n0 else float("nan")


def pointer_in_blobs(g: np.ndarray, prev: np.ndarray, templates: list[dict], scale: float):
    """Best pointer match inside small changed regions of g, or None."""
    import cv2
    d = cv2.absdiff(g, prev)
    m = (d > DIFF).astype(np.uint8)
    m = cv2.dilate(m, np.ones((5, 5), np.uint8))
    n, _, stats, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    big = 70 * scale
    best = None
    for k in range(1, n):
        x, y, w, h, area = stats[k]
        if w > big or h > big or area < 15:
            continue                                   # typing lines, scrolling, windows: too large
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
    return best


def frames(path: Path, fps: float):
    """Sequential read, every (native fps / fps)-th frame: grab is cheap, decode only kept ones."""
    import cv2
    cap = cv2.VideoCapture(str(path))
    native = cap.get(cv2.CAP_PROP_FPS) or 30
    step = max(1, int(round(native / fps)))
    i = 0
    while True:
        if not cap.grab():
            break
        if i % step == 0:
            ok, f = cap.retrieve()
            if ok:
                yield i / native, cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        i += 1
    cap.release()


def main(fps: float) -> None:
    if pt.KEEP.exists():
        pt.KEEP.unlink()
    templates = pt.load_templates()
    t0 = time.perf_counter()
    iv_score, iv_label = [], []
    n_click = n_click_hit = n_stop = n_stop_hit = 0
    stop_err = []
    recs = [r for r in pt.recordings() if not pt.is_train(r[1])]
    for app, tid in recs:
        ev = pt.pointer_events(app, tid)
        if not ev:
            continue
        clicks = [e for e in ev if e["type"] in pt.CLICKS]
        v = pt.Video(pt.video_of(app, tid))
        s = pt.coord_scale(ev, v.W)
        v.close()
        prev, prev_t = None, None
        moves: list[tuple[float, float, float]] = []     # (t, x, y) where the pointer was seen moving
        times = []
        moved_flags = []
        for t, g in frames(pt.video_of(app, tid), fps):
            if prev is not None and prev.shape == g.shape:
                hit = pointer_in_blobs(g, prev, templates, s)
                moved_flags.append(hit is not None)
                times.append((prev_t, t))
                if hit is not None:
                    moves.append((t, hit[1] / s, hit[2] / s))
            prev, prev_t = g, t
        # interval score: moved here or one step earlier (the oracle's definition)
        for i, (a, b) in enumerate(times):
            sc = moved_flags[i] or (i > 0 and moved_flags[i - 1])
            lab = any(a <= c["t"] < b for c in clicks)
            iv_score.append(float(sc))
            iv_label.append(int(lab))
        # stop events: a seen move not followed by another within one step
        dt = 1.0 / fps
        stops = [m for j, m in enumerate(moves)
                 if j + 1 == len(moves) or moves[j + 1][0] - m[0] > 1.5 * dt]
        used = set()
        for c in clicks:
            n_click += 1
            cands = [j for j, (ts, x, y) in enumerate(stops)
                     if c["t"] - BEFORE <= ts <= c["t"] + AFTER and np.hypot(x - c["x"], y - c["y"]) <= NEAR
                     and j not in used]
            if cands:
                j = min(cands, key=lambda j: abs(stops[j][0] - c["t"]))
                used.add(j)
                n_click_hit += 1
                stop_err.append(np.hypot(stops[j][1] - c["x"], stops[j][2] - c["y"]))
        n_stop += len(stops)
        n_stop_hit += len(used)
    iv_score, iv_label = np.array(iv_score), np.array(iv_label)
    print(f"{len(recs)} held-out recordings at {fps:g} fps, {len(iv_score)} intervals, "
          f"{iv_label.sum()} with a click, {time.perf_counter() - t0:.0f}s")
    print(f"\ninterval AUC, 'pointer moved here or one step earlier': {auc(iv_score, iv_label):.3f}"
          f"   (screen change alone 0.55)")
    if iv_score.sum():
        print(f"  flagged intervals: {int(iv_score.sum())}, of which hold a click "
              f"{iv_label[iv_score == 1].mean():.1%}; clicks inside flagged intervals "
              f"{iv_score[iv_label == 1].mean():.1%}")
    print(f"\nclick events: {n_click} logged clicks, {n_stop} predicted stops")
    print(f"  clicks with a matching stop (recall)   : {n_click_hit / max(n_click, 1):.1%}")
    print(f"  stops that match a click (precision)   : {n_stop_hit / max(n_stop, 1):.1%}")
    if stop_err:
        print(f"  distance stop -> click, matched pairs  : median {np.median(stop_err):.1f} px")


if __name__ == "__main__":
    main(float(sys.argv[1]) if len(sys.argv) > 1 else 5.0)
