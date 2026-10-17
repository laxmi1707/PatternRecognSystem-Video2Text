"""Step 3 first: if we knew where the pointer was, would clicks show?

The earlier probe looked at the loudest change anywhere on screen and scored AUC
0.512 for "an action happened in this interval" - chance - because cursor blink,
scrolling and animation outweigh a click. The idea here is to look only next to
the pointer: a click changes what is under it (a button presses, a menu opens),
while background churn has nothing to do with where the pointer is.

This uses the LOGGED pointer position, an oracle tracker, to ask whether the
signal exists at all before building a real tracker. If an oracle cannot separate
clicks, no tracker will; if it can, tracking is worth building.

Note (15 Oct 2026): its 'pointer moved' AUC of 0.927 does not show that pointer
motion predicts clicks. The log records a MOVE_TO at the click itself (median gap
0.00 s, 84% within 0.25 s), so that score is the log restating the click. The
pixel-only result is in pointer_motion_v1.py.

For each 1/fps interval, with the pointer at its last logged position:
    local      mean change in a box around the pointer, its own sprite masked out
    global     mean change over the whole frame
    contrast   local - global
Label: a click was logged in the interval. Scored on all intervals, and on
intervals where the pointer did not move (where a deployable tracker would also
know it was still).

    python cursor_click_probe_v1.py <fps> <per_app>
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
    limit_cpu(8)

import numpy as np  # noqa: E402

from v2k.env import frame_cache_dir  # noqa: E402

APPS = ["VSCode", "Bash", "Eclipse", "KDevelop", "NetBeans"]
CLICKS = {"CLICK", "DOUBLE_CLICK", "RIGHT_CLICK"}
MOVES = {"MOVE_TO", "DRAG_TO"}
BOX = 70                          # half-size of the box around the pointer, native px
SPRITE = (-6, 30, -6, 40)         # x0, x1, y0, y1 around the tip: the pointer's own pixels
SMALL_W = 960                     # global change computed at this width


def actions_of(app: str, tid: int) -> list[dict]:
    rec = json.loads((frame_cache_dir() / app / f"{tid}.json").read_text(encoding="utf-8"))
    acts = [a for seg in rec["segments"] for a in seg["actions"]]
    return sorted([a for a in acts if a.get("timestamp") is not None], key=lambda a: a["timestamp"])


def coord_scale(acts: list[dict], W: float) -> float:
    """Retina recordings log logical points: the frame is twice the logged space."""
    xs = [float((a.get("action_params") or {}).get("x")) for a in acts
          if (a.get("action_params") or {}).get("x") is not None]
    return 2.0 if xs and W > 2000 and max(xs) < W / 2 + 40 else 1.0


def auc(score: np.ndarray, label: np.ndarray) -> float:
    order = np.argsort(score, kind="stable")
    ranks = np.empty(len(score))
    ranks[order] = np.arange(1, len(score) + 1)
    n1 = label.sum()
    n0 = len(label) - n1
    if not n1 or not n0:
        return float("nan")
    return float((ranks[label == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def main(fps: float, per_app: int) -> None:
    import cv2

    rows = []                     # (app, local, global, peak_tile, moved, label)
    t0 = time.perf_counter()
    nvid = 0
    for app in APPS:
        done = 0
        for p in sorted((frame_cache_dir() / app).glob("*.json")):
            if done >= per_app:
                break
            video = ROOT / "data" / "VideoCUA" / app / p.stem / "video" / "video.mp4"
            if not video.exists():
                continue
            acts = actions_of(app, int(p.stem))
            pos = [(a["timestamp"], (a.get("action_params") or {})) for a in acts
                   if (a.get("action_type") or "").upper() in MOVES | CLICKS
                   and (a.get("action_params") or {}).get("x") is not None]
            if not pos:
                continue
            cap = cv2.VideoCapture(str(video))
            W, H = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            dur = cap.get(cv2.CAP_PROP_FRAME_COUNT) / max(cap.get(cv2.CAP_PROP_FPS), 1)
            s = coord_scale(acts, W)
            prev, prev_t = None, None
            for k in range(int(dur * fps) + 1):
                ts = k / fps
                cap.set(cv2.CAP_PROP_POS_MSEC, ts * 1000)
                ok, frame = cap.read()
                if not ok:
                    continue
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                if prev is not None:
                    d = cv2.absdiff(gray, prev)
                    last = [q for t, q in pos if t < ts]
                    if last:
                        cx, cy = float(last[-1]["x"]) * s, float(last[-1]["y"]) * s
                        x0, x1 = int(max(0, cx - BOX)), int(min(W, cx + BOX))
                        y0, y1 = int(max(0, cy - BOX)), int(min(H, cy + BOX))
                        patch = d[y0:y1, x0:x1].astype(np.float32)
                        m = np.ones_like(patch, dtype=bool)
                        sx0, sx1 = int(cx + SPRITE[0] - x0), int(cx + SPRITE[1] - x0)
                        sy0, sy1 = int(cy + SPRITE[2] - y0), int(cy + SPRITE[3] - y0)
                        m[max(0, sy0):max(0, sy1), max(0, sx0):max(0, sx1)] = False
                        local = float(patch[m].mean()) if m.any() else 0.0
                        small = cv2.resize(d, (SMALL_W, int(H * SMALL_W / W)), interpolation=cv2.INTER_AREA)
                        glob = float(small.mean())
                        g = 8
                        hh, ww = small.shape[0] // g, small.shape[1] // g
                        peak = float(small[:hh * g, :ww * g].reshape(g, hh, g, ww).mean(axis=(1, 3)).max())
                        inside = [a for a in acts if prev_t <= a["timestamp"] < ts]
                        moved = any((a.get("action_type") or "").upper() in MOVES for a in inside) or \
                            any((a.get("action_type") or "").upper() in MOVES
                                for a in acts if prev_t - 1 / fps <= a["timestamp"] < prev_t)
                        label = int(any((a.get("action_type") or "").upper() in CLICKS for a in inside))
                        rows.append((app, local, glob, peak, int(moved), label))
                prev, prev_t = gray, ts
            cap.release()
            done += 1
            nvid += 1
        print(f"  {app}: {done} recordings, {time.perf_counter() - t0:.0f}s", flush=True)

    app_a = np.array([r[0] for r in rows])
    local, glob, peak, moved, label = (np.array([r[i] for r in rows], dtype=float) for i in range(1, 6))
    label = label.astype(int)
    contrast = local - glob
    print(f"\n{nvid} recordings, {len(rows)} intervals, {label.sum()} with a click "
          f"({time.perf_counter() - t0:.0f}s)")
    print(f"\n{'signal':44s}{'all intervals':>15s}{'pointer still':>15s}")
    still = moved == 0
    for name, sc in (("loudest tile anywhere (the earlier probe)", peak),
                     ("mean change over the whole frame", glob),
                     ("change next to the pointer", local),
                     ("next to the pointer minus whole frame", contrast)):
        print(f"{name:44s}{auc(sc, label):15.3f}{auc(sc[still], label[still]):15.3f}")
    print(f"\n(still intervals: {still.sum()}, clicks among them: {label[still].sum()} of {label.sum()})")

    # The confound: a pointer that just moved into the box changes the box by itself.
    # Compare only intervals where the pointer moved - with a click and without.
    mv = moved == 1
    print(f"\nonly intervals where the pointer moved: {mv.sum()}, of which {label[mv].sum()} hold a click")
    for name, sc in (("change next to the pointer", local), ("next to the pointer minus whole frame", contrast),
                     ("loudest tile anywhere", peak)):
        print(f"   {name:42s} AUC {auc(sc[mv], label[mv]):.3f}")
    print(f"   'the pointer moved' alone, as a click detector: AUC {auc(moved.astype(float), label):.3f}")

    # what an operating point would look like
    print(f"\nprecision at a given recall, 'next to the pointer minus whole frame', all intervals "
          f"(base rate {label.mean():.1%}):")
    order = np.argsort(-contrast)
    tp = np.cumsum(label[order])
    for r in (0.1, 0.25, 0.5):
        k = int(np.searchsorted(tp, r * label.sum())) + 1
        print(f"   recall {r:.0%}: precision {tp[k - 1] / k:.1%}  ({k} intervals flagged)")

    print(f"\nby application, all intervals:")
    for a in APPS:
        m = app_a == a
        if m.any():
            print(f"   {a:10s} intervals {m.sum():5d}  clicks {label[m].sum():4d}  "
                  f"pointer-minus-frame AUC {auc(contrast[m], label[m]):.3f}   earlier method {auc(peak[m], label[m]):.3f}")
    np.savez_compressed(ROOT / "cursor_click_probe_v1_rows.npz", app=app_a, local=local, glob=glob,
                        peak=peak, moved=moved, label=label)


if __name__ == "__main__":
    main(float(sys.argv[1]), int(sys.argv[2]))
