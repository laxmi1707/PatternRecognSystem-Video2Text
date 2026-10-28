"""Click steps from a bare video: find the mouse pointer, where it stops, and what is under it.

    1. Five frames a second, the regions that changed since the previous frame.
    2. The pointer CNN scores 32x32 crops around each small region (any pointer shape:
       arrow, hand, I-beam); the best spot at p >= 0.8 is the pointer in that frame.
    3. A stop is the last frame of a run of frames with the pointer seen.
    4. The click filter (LightGBM) keeps the stops that look like clicks: how the screen
       changed after the stop, anywhere and near it, and before it; how long the
       pointer rested; and what the pointer did - the CNN's confidence, how far and
       how fast it moved before stopping, how long it was tracked, where on the screen
       it stopped, the time since the previous stop.
    5. OCR around each kept stop names it by the text under the pointer, or the nearest
       text within 70 px. A stop with no text there (an icon) is kept with an empty name
       when ICONS is on, and shown as "Click (icon)". Two stops within 2 s are one click
       when they are within 20 px of each other (the earlier kept, taking the later's
       name if it had none: OCR may read one press two ways, "Open" and "Onen") or carry
       the same name (the later kept).

Coordinates are in logical pixels: a frame wider than 2000 px (Retina) is halved.
The models were fitted by the research scripts pointer_cnn_v1.py (the CNN) and
reaction_features_v1.py (the filter; reaction_models_v1.py chose LightGBM over
bare_sop_v2.py's logistic regression); see Evaluation/README.md for how they were scored.
"""
from __future__ import annotations

import difflib
import pickle
import re
from pathlib import Path

import numpy as np

from v2k.env import CACHE

POINTER_MODEL = CACHE / "pointer_cnn_v1.pt"
REACTION_MODEL = CACHE / "reaction_lgbm_v2.pkl"          # {model, threshold, features, ...}

FPS = 5.0
DIFF = 25                  # grey-level change counted as changed
MIN_AREA = 15              # changed regions smaller than this are noise
POINTER_MAX = 70           # logical px; a larger changed region is not the pointer
SIZE, HOT = 32, 12         # CNN crop size, and where the pointer's tip sits in it
STRIDE = 3                 # logical px between candidate tip positions
P_POINTER = 0.8
WINDOWS = (1.0, 2.0, 3.0)  # seconds after a stop the reaction filter looks at
NEAR_REGION = 200          # logical px around a stop for the "near" reaction features
NEAR_LABEL = 70            # logical px from the pointer to the text that names it
HALF_W, HALF_H = 260, 150  # OCR crop around a stop, logical px
MERGE_S = 2.0
SAME_PLACE_PX = 20        # logical px: two stops this close within MERGE_S are one click
ICONS = True              # keep stops with no text under them, as clicks on an icon


# --- the pointer CNN ---------------------------------------------------------------------

def _net():
    import torch.nn as nn

    def block(i, o):
        return nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(),
                             nn.Conv2d(o, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(), nn.MaxPool2d(2))
    return nn.Sequential(block(1, 16), block(16, 32), block(32, 64),       # 32 -> 4
                         nn.Flatten(), nn.Linear(64 * 4 * 4, 64), nn.ReLU(), nn.Dropout(0.2),
                         nn.Linear(64, 1))


def load_pointer_model(path: Path = POINTER_MODEL):
    import torch
    from detector import model_file
    m = _net()
    if model_file.PKL and path == POINTER_MODEL:      # the one-file deployment (detector/model_file.py)
        m.load_state_dict({k: torch.from_numpy(v) for k, v in model_file.load()["pointer_cnn"].items()})
    else:
        m.load_state_dict(torch.load(path, map_location="cpu"))
    m.eval()
    return m


def pointer_at(model, grey: np.ndarray, regions) -> tuple[float, int, int] | None:
    """Best (p, x, y) over candidate tip positions around each small changed region."""
    import torch
    crops, where = [], []
    H, W = grey.shape
    for bx, by, bw, bh in regions[:12]:
        for cy in np.arange(by - 4, by + bh + 4, STRIDE):
            for cx in np.arange(bx - 4, bx + bw + 4, STRIDE):
                x0, y0 = int(cx) - HOT, int(cy) - HOT
                if x0 < 0 or y0 < 0 or x0 + SIZE > W or y0 + SIZE > H:
                    continue
                crops.append(grey[y0:y0 + SIZE, x0:x0 + SIZE])
                where.append((int(cx), int(cy)))
    if not crops:
        return None
    batch = torch.from_numpy(np.stack(crops).astype(np.float32) / 255.0).unsqueeze(1)
    with torch.no_grad():
        p = torch.sigmoid(model(batch).squeeze(1)).numpy()
    k = int(p.argmax())
    return (float(p[k]), *where[k]) if p[k] >= P_POINTER else None


# --- frames, pointer and stops ------------------------------------------------------------

def read_frames(video: Path, fps: float = FPS):
    """(t, grey frame) every (native fps / fps)-th frame; only the kept frames are decoded."""
    import cv2
    cap = cv2.VideoCapture(str(video))
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


def track(video: Path, model, progress=lambda pct, stage: None) -> tuple[list, float, float, float]:
    """Per frame (t, pointer (p, x, y) or None, large changed regions); the scale; and the
    screen's logical width and height."""
    import cv2
    cap = cv2.VideoCapture(str(video))
    W, H = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / max(cap.get(cv2.CAP_PROP_FPS), 1)
    cap.release()
    s = 2.0 if W > 2000 else 1.0
    prev, out = None, []
    for t, g in read_frames(video):
        if prev is not None and prev.shape == g.shape:
            changed = cv2.dilate((cv2.absdiff(g, prev) > DIFF).astype(np.uint8), np.ones((5, 5), np.uint8))
            _, _, stats, _ = cv2.connectedComponentsWithStats(changed, connectivity=8)
            small, large = [], []
            for x, y, w, h, a in (tuple(int(v) for v in row) for row in stats[1:]):
                if a < MIN_AREA:
                    continue
                if w > POINTER_MAX * s or h > POINTER_MAX * s:
                    large.append((x / s, y / s, w / s, h / s, a / (W * H)))
                else:
                    small.append((x / s, y / s, w / s, h / s))
            pointer = None
            if small:
                grey = g if s == 1.0 else cv2.resize(g, (int(W / s), int(H / s)), interpolation=cv2.INTER_AREA)
                pointer = pointer_at(model, grey, small)
            out.append((t, pointer, large))
            if len(out) % 25 == 0:
                progress(min(60, 30 + int(30 * t / max(duration, 1))), "tracking the mouse pointer")
        prev = g
    return out, s, W / s, H / s


def stops(frames: list, fps: float = FPS) -> list[tuple[float, float, float, float]]:
    """(t, x, y, dwell): the pointer seen, and not seen in the next frame."""
    seen = [(t, p[1], p[2]) for t, p, _ in frames if p is not None]
    out = []
    for j, (t, x, y) in enumerate(seen):
        nxt = seen[j + 1][0] if j + 1 < len(seen) else None
        if nxt is None or nxt - t > 1.5 / fps:
            out.append((t, x, y, (nxt - t) if nxt is not None else 10.0))
    return out


# --- the screen-reaction filter -----------------------------------------------------------

def reaction_features(frames: list, stop) -> list[float]:
    """How much of the screen changed after the stop (anywhere, and near it), before it,
    and how long the pointer rested."""
    ts, sx, sy, dwell = stop
    times = np.array([t for t, _, _ in frames]) if frames else np.zeros(0)

    def area(lo, hi, near):
        tot = 0.0
        for k in np.nonzero((times > lo) & (times <= hi))[0]:
            for x, y, w, h, a in frames[k][2]:
                if near:
                    dx = max(x - sx, 0, sx - (x + w))
                    dy = max(y - sy, 0, sy - (y + h))
                    if np.hypot(dx, dy) > NEAR_REGION:
                        continue
                tot += a
        return np.log1p(1000 * tot)

    f = [area(ts, ts + w, False) for w in WINDOWS]
    f += [area(ts, ts + w, True) for w in WINDOWS]
    f.append(area(ts - 1.0, ts, False))
    f.append(np.log1p(dwell))
    return f


def pointer_features(frames: list, st: list, W: float, H: float, fps: float = FPS) -> np.ndarray:
    """Per stop: the CNN's confidence at it and over the last 3 frames seen, frames tracked
    without a break, px moved in the last frame and in the last second, the stop's place
    on the screen, seconds since the previous stop, large changed regions in the next second."""
    seen = [(t, p) for t, p, _ in frames if p is not None]
    times = np.array([t for t, _ in seen]) if seen else np.zeros(0)
    big = [(t, len(large)) for t, _, large in frames]
    dt = 1.0 / fps
    out = []
    for i, (ts, x, y, _) in enumerate(st):
        k = int(np.searchsorted(times, ts + 1e-6)) - 1
        p_stop = seen[k][1][0] if k >= 0 else 0.0
        last = [seen[j][1][0] for j in range(max(0, k - 2), k + 1)] if k >= 0 else [0.0]
        n, j = 0, k
        while j > 0 and seen[j][0] - seen[j - 1][0] <= 1.5 * dt:
            n, j = n + 1, j - 1
        speed = float(np.hypot(seen[k][1][1] - seen[k - 1][1][1], seen[k][1][2] - seen[k - 1][1][2]))             if k >= 1 and seen[k][0] - seen[k - 1][0] <= 1.5 * dt else 0.0
        path, j = 0.0, k
        while j > 0 and seen[j - 1][0] >= ts - 1.0:
            path += float(np.hypot(seen[j][1][1] - seen[j - 1][1][1], seen[j][1][2] - seen[j - 1][1][2]))
            j -= 1
        gap = ts - st[i - 1][0] if i > 0 else 10.0
        big_n = sum(c for t, c in big if ts < t <= ts + 1.0)
        out.append([p_stop, float(np.mean(last)), n, speed, path, x / max(W, 1), y / max(H, 1), gap, big_n])
    return np.array(out, dtype=float).reshape(-1, 9)


def load_reaction_model(path: Path = REACTION_MODEL):
    """(score function on the 17 features, threshold). An older file - the 8-feature
    LightGBM, or bare_sop_v2's (scaler, logistic, threshold) tuple - scores the first 8."""
    from detector import model_file
    if model_file.PKL and path == REACTION_MODEL:
        saved = model_file.load()["reaction"]
    else:
        saved = pickle.loads(path.read_bytes())
    if isinstance(saved, dict):
        model, n = saved["model"], len(saved.get("features", range(8)))
        return (lambda X: model.predict_proba(X[:, :n])[:, 1]), saved["threshold"]
    scaler, logistic, threshold = saved
    return (lambda X: logistic.predict_proba(scaler.transform(X[:, :8]))[:, 1]), threshold


# --- naming ---------------------------------------------------------------------------------

def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def same_name(a: str, b: str) -> bool:
    a, b = _norm(a), _norm(b)
    return bool(a and b and (a == b or a in b or b in a or difflib.SequenceMatcher(None, a, b).ratio() >= 0.8))


def label_at(regions, x: float, y: float, near: float) -> str:
    """The OCR text under (x, y), else the nearest within `near` px (as v2k/sop.py names clicks)."""
    best, best_d = "", float("inf")
    for text, x1, y1, x2, y2, conf in regions or []:
        if not text or conf < 0.4:
            continue
        if x1 <= x <= x2 and y1 <= y <= y2:
            return text
        d = float(np.hypot((x1 + x2) / 2 - x, (y1 + y2) / 2 - y))
        if d < best_d:
            best, best_d = text, d
    return best if best_d <= near else ""


def merge_clicks(stops_named: list[dict], icons: bool = ICONS) -> list[dict]:
    """Kept stops in time order, each {t, x, y, text, ...} (text "" when nothing was read),
    to click steps: unnamed ones dropped unless `icons`; one press read twice merged."""
    out = []
    for k in stops_named:
        if not k["text"] and not icons:
            continue
        k = dict(k)
        if out and k["t"] - out[-1]["t"] <= MERGE_S:
            prev = out[-1]
            if np.hypot(k["x"] - prev["x"], k["y"] - prev["y"]) <= SAME_PLACE_PX:
                if not prev["text"] and k["text"]:
                    prev["text"] = k["text"]           # the same press; keep the earlier, named
                continue
            if k["text"] and prev["text"] and same_name(k["text"], prev["text"]):
                out[-1] = k
                continue
        out.append(k)
    return out


# --- all together -----------------------------------------------------------------------------

def click_steps(video: Path, ocr, progress=lambda pct, stage: None) -> list[dict]:
    """[{t, action: "Click", text, x, y, score}] in time order."""
    import cv2
    frames, s, W, H = track(video, load_pointer_model(), progress)
    st = stops(frames)
    if not st:
        return []
    score, threshold = load_reaction_model()
    X = np.hstack([np.array([reaction_features(frames, x) for x in st]), pointer_features(frames, st, W, H)])
    p = score(X)
    kept = [(stop, float(pj)) for stop, pj in zip(st, p) if pj >= threshold]
    progress(62, "reading the controls under the pointer")

    named = []
    cap = cv2.VideoCapture(str(video))
    for i, ((t, x, y, _), pj) in enumerate(kept):
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, f = cap.read()
        if not ok:
            continue
        X, Y = x * s, y * s
        x0, y0 = int(max(0, X - HALF_W * s)), int(max(0, Y - HALF_H * s))
        crop = f[y0:int(min(f.shape[0], Y + HALF_H * s)), x0:int(min(f.shape[1], X + HALF_W * s))]
        regions = [[g.text, g.bbox[0] + x0, g.bbox[1] + y0, g.bbox[2] + x0, g.bbox[3] + y0, g.confidence]
                   for g in ocr.extract_text(crop).regions]
        named.append({"t": t, "x": x, "y": y, "text": label_at(regions, X, Y, NEAR_LABEL * s), "score": pj})
        progress(62 + int(18 * (i + 1) / max(len(kept), 1)), "reading the controls under the pointer")
    cap.release()

    return [{"t": round(k["t"], 2), "action": "Click", "text": k["text"], "x": round(k["x"]), "y": round(k["y"]),
             "score": round(k["score"], 3)} for k in merge_clicks(named)]
