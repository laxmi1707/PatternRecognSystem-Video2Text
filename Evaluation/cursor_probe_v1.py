"""Step 1 of the cursor idea: is the mouse pointer even in the recordings?

Many screen recorders leave the pointer out. If it is there, a crop centred on
the logged click coordinate, taken just before the click, shows it every time;
a crop at a random point does not. Writes a contact sheet to look at.

    python cursor_probe_v1.py <out.png> [per_app]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from v2k.env import limit_cpu  # noqa: E402

if __name__ == "__main__":
    limit_cpu(8)

import numpy as np  # noqa: E402

from v2k.env import frame_cache_dir  # noqa: E402

APPS = ["VSCode", "Bash", "Eclipse", "KDevelop", "NetBeans"]
HALF = 48            # crop is 96 x 96 native pixels
CLICKS = {"CLICK", "DOUBLE_CLICK", "RIGHT_CLICK"}


def actions_of(app: str, tid: int) -> list[dict]:
    rec = json.loads((frame_cache_dir() / app / f"{tid}.json").read_text(encoding="utf-8"))
    return [a for seg in rec["segments"] for a in seg["actions"]]


def crop(frame: np.ndarray, x: float, y: float) -> np.ndarray:
    h, w = frame.shape[:2]
    pad = np.pad(frame, ((HALF, HALF), (HALF, HALF), (0, 0)), constant_values=40)
    xi, yi = int(round(x)) + HALF, int(round(y)) + HALF
    return pad[yi - HALF:yi + HALF, xi - HALF:xi + HALF]


def main(out: Path, per_app: int) -> None:
    import cv2

    rng = np.random.RandomState(0)
    rows = []
    for app in APPS:
        got = []
        for p in sorted((frame_cache_dir() / app).glob("*.json")):
            if len(got) >= per_app:
                break
            video = ROOT / "data" / "VideoCUA" / app / p.stem / "video" / "video.mp4"
            if not video.exists():
                continue
            clicks = [a for a in actions_of(app, int(p.stem))
                      if (a.get("action_type") or "").upper() in CLICKS
                      and (a.get("action_params") or {}).get("x") is not None]
            if not clicks:
                continue
            c = clicks[len(clicks) // 2]
            cap = cv2.VideoCapture(str(video))
            W, H = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            cap.set(cv2.CAP_PROP_POS_MSEC, max(0.0, c["timestamp"] - 0.15) * 1000)
            ok, frame = cap.read()
            cap.release()
            if not ok:
                continue
            x, y = float(c["action_params"]["x"]), float(c["action_params"]["y"])
            at = crop(frame, x, y)
            rx, ry = rng.uniform(HALF, W - HALF), rng.uniform(HALF, H - HALF)
            ra = crop(frame, rx, ry)
            # a small red cross marks the logged coordinate, drawn next to (not on) the crop
            mark = at.copy()
            cv2.drawMarker(mark, (HALF, HALF), (0, 0, 255), cv2.MARKER_CROSS, 10, 1)
            got.append(np.hstack([at, mark, ra, np.full((2 * HALF, 6, 3), 255, np.uint8)]))
            print(f"  {app}/{p.stem}: frame {int(W)}x{int(H)}, click at ({x:.0f},{y:.0f}) t={c['timestamp']:.2f}s")
        if got:
            rows.append(np.hstack(got))
    width = max(r.shape[1] for r in rows)
    sheet = np.vstack([np.pad(r, ((0, 6), (0, width - r.shape[1]), (0, 0)), constant_values=255)
                       for r in rows])
    big = cv2.resize(sheet, None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST)
    cv2.imwrite(str(out), big)
    print(f"wrote {out}  (each triple: at the click, same with the logged point marked, random spot)")


if __name__ == "__main__":
    main(Path(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else 3)
