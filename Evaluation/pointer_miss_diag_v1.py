"""Why is the pointer never seen near 77 of the 204 held-out clicks?

For each held-out click with no detected pointer move within 40 px, at 5 fps
over [click - 2 s, click + 0.3 s]:

    changed       any pixel within 40 px of the click changed between frames
    blob size     the changed region touching that neighbourhood: pointer-sized
                  (what Plan A matches inside) or larger (skipped, e.g. the
                  pointer moving over a menu that lights up under it)
    template      best masked template score in a 160 px window around the
                  click on the last frame before it, with no blob constraint:
                  below MATCH means a known pointer shape is there

and writes a contact sheet of crops around the click for looking at.

    python pointer_miss_diag_v1.py
"""
from __future__ import annotations

import collections
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from v2k.env import limit_cpu  # noqa: E402

if __name__ == "__main__":
    limit_cpu(8)

import numpy as np  # noqa: E402

import pointer_reaction_v1 as pr  # noqa: E402
import pointer_tracker_v1 as pt  # noqa: E402
from pointer_motion_v1 import DIFF, MATCH  # noqa: E402

SHEET = ROOT / "pointer_miss_diag_v1.png"


def best_template(g, X, Y, templates, s, half=80):
    import cv2
    h = int(half * s)
    x0, y0 = max(0, int(X) - h), max(0, int(Y) - h)
    region = g[y0:int(Y) + h, x0:int(X) + h]
    best = np.inf
    for tp in templates:
        if tp["k"] != (2 if s == 2.0 else 1):
            continue
        th, tw = tp["img"].shape
        if region.shape[0] < th or region.shape[1] < tw:
            continue
        res = cv2.matchTemplate(region, tp["img"], cv2.TM_SQDIFF, mask=tp["mask"])
        res = np.nan_to_num(res / max(int(tp["mask"].sum()), 1), nan=np.inf)
        best = min(best, float(res.min()))
    return best


def main() -> None:
    import cv2
    if pt.KEEP.exists():
        pt.KEEP.unlink()
    templates = pt.load_templates()
    recs = pickle.loads(pr.OUT.read_bytes())
    stats = collections.Counter()
    tscores, crops = [], []
    for r in recs:
        if r["train"]:
            continue
        missed = [c for c in r["clicks"]
                  if not any(t <= c[0] + pr.AFTER and np.hypot(x - c[1], y - c[2]) <= pr.NEAR
                             for t, x, y in r["moves"])]
        if not missed:
            continue
        ev = pt.pointer_events(r["app"], r["tid"])
        cap = cv2.VideoCapture(str(pt.video_of(r["app"], r["tid"])))
        W = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        s = pt.coord_scale(ev, W)
        for ct, cx, cy in missed:
            X, Y = cx * s, cy * s
            fr = []
            for t in np.arange(ct - 2.0, ct + 0.31, 0.2):
                cap.set(cv2.CAP_PROP_POS_MSEC, max(0, t) * 1000)
                ok, f = cap.read()
                if ok:
                    fr.append((t, cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)))
            if len(fr) < 2:
                continue
            changed, big, small = False, False, False
            R = int(40 * s)
            for (_, a), (_, b) in zip(fr, fr[1:]):
                m = (cv2.absdiff(a, b) > DIFF).astype(np.uint8)
                m = cv2.dilate(m, np.ones((5, 5), np.uint8))
                n, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
                y0, y1, x0, x1 = max(0, int(Y) - R), int(Y) + R, max(0, int(X) - R), int(X) + R
                ids = set(np.unique(lab[y0:y1, x0:x1]).tolist()) - {0}
                if ids:
                    changed = True
                for k in ids:
                    if st[k][2] > 70 * s or st[k][3] > 70 * s:
                        big = True
                    else:
                        small = True
            last = [g for t, g in fr if t <= ct - 0.05][-1] if any(t <= ct - 0.05 for t, _ in fr) else fr[0][1]
            sc = best_template(last, X, Y, templates, s)
            tscores.append(sc)
            stats["clicks"] += 1
            stats["no change near the click at all"] += not changed
            stats["change near: only regions larger than a pointer"] += changed and big and not small
            stats["change near: pointer-sized region (template failed)"] += changed and small
            stats["known pointer shape at the click (score < MATCH)"] += sc < MATCH
            if len(crops) < 24:
                h = int(60 * s)
                c = last[max(0, int(Y) - h):int(Y) + h, max(0, int(X) - h):int(X) + h]
                c = cv2.resize(c, (160, 160))
                c = cv2.cvtColor(c, cv2.COLOR_GRAY2BGR)
                cv2.drawMarker(c, (80, 80), (0, 0, 255), cv2.MARKER_CROSS, 14, 1)
                cv2.putText(c, f"{r['app'][:7]} {sc:.0f}", (3, 154), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 160, 0), 1)
                crops.append(c)
        cap.release()
    n = stats.pop("clicks")
    print(f"{n} held-out clicks with no pointer move seen within 40 px")
    for k, v in stats.items():
        print(f"  {k:<56}{v:>5}{v / n:>8.1%}")
    print("template score at the click, percentiles 10/25/50/75/90:",
          np.percentile(tscores, [10, 25, 50, 75, 90]).round(0), f"(MATCH = {MATCH})")
    rows = [np.hstack(crops[i:i + 6] + [np.zeros_like(crops[0])] * (6 - len(crops[i:i + 6])))
            for i in range(0, len(crops), 6)]
    cv2.imwrite(str(SHEET), np.vstack(rows))
    print(f"contact sheet -> {SHEET.name}")


if __name__ == "__main__":
    main()
