"""Self-match v2: keep every pointer hit, decide stops offline.

pointer_selfmatch_v1 saw the pointer near many more clicks, but its spurious
self-matches elsewhere on the screen (small animations, blinking icons) broke
the stop rule, which needs no move *anywhere* in the next frame: clicks whose
only stops were more than 40 px away rose from 19 to 42 (median 155 px).

v2 stores, per frame pair, the template hit and up to three self-match hits
separately, so stop rules can be compared without decoding again:

    recurring    self-hits that land on the same 8 px cell three or more times
                 in a recording are a static animation, not the pointer - dropped
    global       a move with no (kept) move anywhere in the next frame (v1 rule)
    local D      a move with no kept move within D px in the next frame

The rule is chosen on the training recordings (stop-level F1 against logged
clicks) and only then scored on held-out ones, through the same downstream
chain as before (reaction filter, click names, merged SOP, missed steps).

    python pointer_selfmatch_v2.py extract [fps]
    python pointer_selfmatch_v2.py eval
"""
from __future__ import annotations

import collections
import pickle
import sys
import time
from concurrent.futures import ProcessPoolExecutor
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

OUT = pt.CACHE / "pointer_selfmatch_v2.pkl"
SELF = 18.0
WORKERS = 6
CELL = 8
RECUR = 3


def step(g, prev, templates, scale):
    """(template hit or None, up to 3 self hits as (d, x, y), regions larger than a pointer)."""
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

    hits = []
    if 2 <= len(small) <= 12:
        for i in range(len(small)):
            for j in range(len(small)):
                if i == j:
                    continue
                xa, ya, wa, ha = small[i]
                xb, yb, wb, hb = small[j]
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
                now_old = g[ya:ya + h, xa:xa + w].astype(np.float32)
                if new.shape != old.shape or now_old.shape != old.shape:
                    continue
                d = float(np.abs(new - old)[mb].mean())
                gone = float(np.abs(now_old - old)[mb].mean())
                if d < SELF and gone > 2 * SELF:
                    hits.append((d, xb + 0.3 * w, yb + 0.15 * h))
    hits.sort()
    return best, hits[:3], large


def _one(job):
    import cv2
    cv2.setNumThreads(2)
    app, tid, fps = job
    ev = pt.pointer_events(app, tid)
    if not ev:
        return None
    templates = pt.load_templates()
    v = pt.Video(pt.video_of(app, tid))
    s = pt.coord_scale(ev, v.W)
    area = v.W * v.H
    v.close()
    prev = None
    fr = []
    for t, g in frames(pt.video_of(app, tid), fps):
        if prev is not None and prev.shape == g.shape:
            hit, selfs, large = step(g, prev, templates, s)
            fr.append((t, None if hit is None else (hit[1] / s, hit[2] / s),
                       [(x / s, y / s) for _, x, y in selfs],
                       [(x / s, y / s, w / s, h / s, a / area) for x, y, w, h, a in large]))
        prev = g
    return {"app": app, "tid": tid, "train": pt.is_train(tid), "fps": fps,
            "clicks": [(e["t"], e["x"], e["y"]) for e in ev if e["type"] in pt.CLICKS],
            "frames": fr, "iv": [(t, lg) for t, _, _, lg in fr]}


def extract(fps: float) -> None:
    if pt.KEEP.exists():
        pt.KEEP.unlink()
    t0 = time.perf_counter()
    jobs = [(a, t, fps) for a, t in pt.recordings()]
    recs = []
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        for i, r in enumerate(pool.map(_one, jobs), 1):
            if r is not None:
                recs.append(r)
            if i % 40 == 0:
                print(f"  {i}/{len(jobs)} recordings, {time.perf_counter() - t0:.0f}s", flush=True)
    OUT.write_bytes(pickle.dumps(recs))
    print(f"{len(recs)} recordings -> {OUT.name}, {time.perf_counter() - t0:.0f}s")


# ------------------------------------------------------------------ stop rules

def moves_of(r: dict, drop_recurring: bool) -> list[tuple[float, float, float]]:
    """One position per frame pair: the template hit, else the best self hit not on a recurring cell."""
    bad = set()
    if drop_recurring:
        cnt = collections.Counter((int(x // CELL), int(y // CELL)) for _, _, ss, _ in r["frames"] for x, y in ss)
        bad = {c for c, n in cnt.items() if n >= RECUR}
    out = []
    for t, hit, ss, _ in r["frames"]:
        if hit is not None:
            out.append((t, *hit))
            continue
        ok = [(x, y) for x, y in ss if (int(x // CELL), int(y // CELL)) not in bad]
        if ok:
            out.append((t, *ok[0]))
    return out


def make_stops(r: dict, rule: str, drop_recurring: bool):
    """(t, x, y, dwell) stops under a rule: 'global' or 'local:<D>'."""
    mv = moves_of(r, drop_recurring)
    dt = 1.0 / r["fps"]
    D = None if rule == "global" else float(rule.split(":")[1])
    out = []
    for j, (t, x, y) in enumerate(mv):
        later = [m for m in mv[j + 1:j + 6] if m[0] - t <= 1.5 * dt]
        if D is not None:
            later = [m for m in later if np.hypot(m[1] - x, m[2] - y) <= D]
        if not later:
            nxt = next((m[0] for m in mv[j + 1:] if D is None or np.hypot(m[1] - x, m[2] - y) <= D), None)
            out.append((t, x, y, (nxt - t) if nxt is not None else 10.0))
    return out, mv


def stop_scores(recs, split, rule, drop):
    hit = kept = used = clicks = 0
    for r in recs:
        if r["train"] != split:
            continue
        st, _ = make_stops(r, rule, drop)
        h, k, u, _ = pr.match(r["clicks"], st, [True] * len(st))
        hit, kept, used, clicks = hit + h, kept + k, used + u, clicks + len(r["clicks"])
    rec, prec = hit / max(clicks, 1), used / max(kept, 1)
    return rec, prec, kept, 2 * rec * prec / max(rec + prec, 1e-9)


def evaluate() -> None:
    recs = pickle.loads(OUT.read_bytes())
    rules = ["global"] + [f"local:{d}" for d in (60, 120, 250, 500)]
    print(f"{'stop rule':<16}{'drop recurring':>15}{'train recall':>14}{'prec':>7}{'F1':>7}"
          f"{'held-out recall':>17}{'prec':>7}{'stops':>7}")
    best = None
    for rule in rules:
        for drop in (False, True):
            r_tr, p_tr, _, f_tr = stop_scores(recs, True, rule, drop)
            r_te, p_te, k_te, _ = stop_scores(recs, False, rule, drop)
            print(f"{rule:<16}{str(drop):>15}{r_tr:>14.1%}{p_tr:>7.1%}{f_tr:>7.3f}{r_te:>17.1%}{p_te:>7.1%}{k_te:>7}")
            if best is None or f_tr > best[0]:
                best = (f_tr, rule, drop)
    _, rule, drop = best
    print(f"\nchosen on train: {rule}, drop recurring = {drop}")

    # hand the chosen rule to the downstream chain, which reads pr.OUT and pr.stops_of
    derived = []
    for r in recs:
        st, mv = make_stops(r, rule, drop)
        derived.append({**{k: v for k, v in r.items() if k != "frames"}, "moves": mv, "_stops": st})
    tmp = pt.CACHE / "pointer_selfmatch_v2_derived.pkl"
    tmp.write_bytes(pickle.dumps(derived))
    pr.OUT = tmp
    pr.stops_of = lambda rec: rec["_stops"]
    import click_labels_v1 as cl
    import combined_sop_v2 as cs2
    import missed_steps_v1 as ms
    print("\n=== reaction filter ===")
    pr.evaluate()
    print("\n=== click names ===")
    cl.main()
    print("\n=== typing + clicks merged ===")
    cs2.OUT_MD = ROOT / "pointer_selfmatch_v2_examples.md"
    cs2.main()
    print("\n=== where clicks are lost ===")
    ms.main()


if __name__ == "__main__":
    if sys.argv[1] == "extract":
        extract(float(sys.argv[2]) if len(sys.argv) > 2 else 5.0)
    else:
        evaluate()
