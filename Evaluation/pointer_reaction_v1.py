"""Does the screen react after a pointer stop? Filtering Plan A's stops to real clicks.

Plan A (pointer_motion_v1.py) finds 57.8% of held-out clicks, but only 33.5% of its
stops are followed by a click: people also stop to read or think. A click usually
makes the screen answer - a menu opens, a button lights up, a dialog appears - while
a stop to read leaves it still. So each stop gets features of what changed after it:

    big_after_W    changed area in regions larger than a pointer, (ts, ts+W]
    near_after_W   the same, only regions within 200 px of the stop point
    big_before     changed area larger than a pointer in the second before the stop
    dwell          seconds until the pointer is next seen moving

The pointer itself is excluded by size: regions no larger than a pointer are what
the pointer leaves when it moves on, after a click and after a pause alike.

    python pointer_reaction_v1.py extract [fps]    decode all recordings once -> cache
    python pointer_reaction_v1.py eval             features, AUC, filtered precision/recall

Thresholds and the small logistic model are fitted on the training recordings
(those the pointer templates were harvested from) and scored on held-out ones.
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

import pointer_tracker_v1 as pt  # noqa: E402
from pointer_motion_v1 import DIFF, MATCH, NEAR, BEFORE, AFTER, auc, frames  # noqa: E402

OUT = pt.CACHE / "pointer_reaction_v1.pkl"
WINDOWS = (1.0, 2.0, 3.0)
NEAR_REGION = 200      # logged px around the stop for near_after


def step(g: np.ndarray, prev: np.ndarray, templates: list[dict], scale: float):
    """One frame pair: (pointer hit or None, regions larger than a pointer as (x, y, w, h, area))."""
    import cv2
    d = cv2.absdiff(g, prev)
    m = (d > DIFF).astype(np.uint8)
    m = cv2.dilate(m, np.ones((5, 5), np.uint8))
    n, _, stats, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    big = 70 * scale
    best = None
    large = []
    for k in range(1, n):
        x, y, w, h, area = (int(v) for v in stats[k])
        if area < 15:
            continue
        if w > big or h > big:
            large.append((x, y, w, h, area))
            continue
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
    return best, large


def extract(fps: float) -> None:
    if pt.KEEP.exists():
        pt.KEEP.unlink()
    templates = pt.load_templates()
    t0 = time.perf_counter()
    recs = []
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
                hit, large = step(g, prev, templates, s)
                # regions in logged coordinates, area as a share of the frame
                iv.append((t, [(x / s, y / s, w / s, h / s, a / area) for x, y, w, h, a in large]))
                if hit is not None:
                    moves.append((t, hit[1] / s, hit[2] / s))
            prev = g
        recs.append({"app": app, "tid": tid, "train": pt.is_train(tid), "fps": fps,
                     "clicks": [(e["t"], e["x"], e["y"]) for e in ev if e["type"] in pt.CLICKS],
                     "moves": moves, "iv": iv})
        if (i + 1) % 20 == 0:
            print(f"  {i + 1} recordings, {time.perf_counter() - t0:.0f}s", flush=True)
    OUT.write_bytes(pickle.dumps(recs))
    print(f"{len(recs)} recordings -> {OUT.name}, {time.perf_counter() - t0:.0f}s")


def stops_of(rec: dict) -> list[tuple[float, float, float, float]]:
    """(t, x, y, dwell): a seen move not followed by another within 1.5 steps."""
    dt = 1.0 / rec["fps"]
    mv = rec["moves"]
    out = []
    for j, (t, x, y) in enumerate(mv):
        nxt = mv[j + 1][0] if j + 1 < len(mv) else None
        if nxt is None or nxt - t > 1.5 * dt:
            out.append((t, x, y, (nxt - t) if nxt is not None else 10.0))
    return out


def features(rec: dict, stop) -> list[float]:
    ts, sx, sy, dwell = stop
    f = []
    ivt = np.array([t for t, _ in rec["iv"]]) if rec["iv"] else np.zeros(0)

    def area(lo, hi, near):
        tot = 0.0
        for k in np.nonzero((ivt > lo) & (ivt <= hi))[0]:
            for x, y, w, h, a in rec["iv"][k][1]:
                if near:
                    dx = max(x - sx, 0, sx - (x + w))
                    dy = max(y - sy, 0, sy - (y + h))
                    if np.hypot(dx, dy) > NEAR_REGION:
                        continue
                tot += a
        return np.log1p(1000 * tot)

    for W in WINDOWS:
        f.append(area(ts, ts + W, False))
    for W in WINDOWS:
        f.append(area(ts, ts + W, True))
    f.append(area(ts - 1.0, ts, False))
    f.append(np.log1p(dwell))
    return f


NAMES = [f"big_after_{W:g}s" for W in WINDOWS] + [f"near_after_{W:g}s" for W in WINDOWS] \
    + ["big_before_1s", "dwell"]


def match(clicks, stops, keep) -> tuple[int, int, int, list[bool]]:
    """Greedy as in pointer_motion_v1: (clicks hit, stops kept, stops used, used flag per stop)."""
    used = [False] * len(stops)
    hit = 0
    for ct, cx, cy in clicks:
        cands = [j for j, (ts, x, y, _) in enumerate(stops)
                 if keep[j] and not used[j] and ct - BEFORE <= ts <= ct + AFTER
                 and np.hypot(x - cx, y - cy) <= NEAR]
        if cands:
            j = min(cands, key=lambda j: abs(stops[j][0] - ct))
            used[j] = True
            hit += 1
    return hit, sum(keep), sum(used), used


def evaluate() -> None:
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    recs = pickle.loads(OUT.read_bytes())
    rows = {True: [], False: []}
    for r in recs:
        st = stops_of(r)
        _, _, _, used = match(r["clicks"], st, [True] * len(st))
        X = [features(r, s) for s in st]
        rows[r["train"]].append((r, st, np.array(X).reshape(len(st), len(NAMES)), np.array(used, bool)))

    def stack(split):
        X = np.vstack([x for _, _, x, _ in rows[split]])
        y = np.concatenate([u for _, _, _, u in rows[split]])
        return X, y

    Xtr, ytr = stack(True)
    Xte, yte = stack(False)
    n_tr, n_te = sum(len(r["clicks"]) for r, *_ in rows[True]), sum(len(r["clicks"]) for r, *_ in rows[False])
    print(f"train: {len(rows[True])} recordings, {n_tr} clicks, {len(ytr)} stops, {ytr.mean():.1%} are clicks")
    print(f"held-out: {len(rows[False])} recordings, {n_te} clicks, {len(yte)} stops, {yte.mean():.1%} are clicks\n")

    print(f"{'feature':<16}{'AUC train':>10}{'AUC held-out':>14}")
    for k, nm in enumerate(NAMES):
        print(f"{nm:<16}{auc(Xtr[:, k], ytr):>10.3f}{auc(Xte[:, k], yte):>14.3f}")

    sc = StandardScaler().fit(Xtr)
    lr = LogisticRegression(C=1.0, max_iter=1000).fit(sc.transform(Xtr), ytr)
    ptr = lr.predict_proba(sc.transform(Xtr))[:, 1]
    pte = lr.predict_proba(sc.transform(Xte))[:, 1]
    print(f"{'logistic, all':<16}{auc(ptr, ytr):>10.3f}{auc(pte, yte):>14.3f}")
    print("  weights: " + ", ".join(f"{n} {w:+.2f}" for n, w in zip(NAMES, lr.coef_[0])))

    def filtered(split, score_fn, thr):
        hit = kept = good = clicks = 0
        for r, st, X, _ in rows[split]:
            keep = list(score_fn(X) >= thr) if len(st) else []
            h, k, g, _ = match(r["clicks"], st, keep)
            hit, kept, good, clicks = hit + h, kept + k, good + g, clicks + len(r["clicks"])
        return hit / max(clicks, 1), good / max(kept, 1), kept

    score = lambda X: lr.predict_proba(sc.transform(X))[:, 1] if len(X) else np.zeros(0)  # noqa: E731
    print(f"\n{'threshold (fitted on train)':<36}{'recall':>8}{'precision':>11}{'stops':>7}")
    r0, p0, k0 = filtered(False, score, -1)
    print(f"{'no filter (Plan A)':<36}{r0:>8.1%}{p0:>11.1%}{k0:>7}")
    best = None
    for thr in np.linspace(0.05, 0.9, 86):
        r, p, _ = filtered(True, score, thr)
        f1 = 2 * r * p / max(r + p, 1e-9)
        if best is None or f1 > best[0]:
            best = (f1, thr)
    rtr0, _, _ = filtered(True, score, -1)
    picks = [("best F1 on train", best[1])]
    for keep_share in (0.9, 0.8):
        for thr in np.linspace(0.9, 0.0, 181):
            if filtered(True, score, thr)[0] >= keep_share * rtr0:
                picks.append((f"keeps {keep_share:.0%} of train recall", thr))
                break
    for label, thr in picks:
        r, p, k = filtered(False, score, thr)
        print(f"{label + f' (p>={thr:.2f})':<36}{r:>8.1%}{p:>11.1%}{k:>7}")


if __name__ == "__main__":
    if sys.argv[1] == "extract":
        extract(float(sys.argv[2]) if len(sys.argv) > 2 else 5.0)
    else:
        evaluate()
