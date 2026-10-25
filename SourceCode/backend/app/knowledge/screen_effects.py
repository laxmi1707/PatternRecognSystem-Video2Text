"""What each user action did on screen: when the screen reacted and what text appeared.

For every user action in an action log (click, typing, key press, hotkey, drag) this
compares the screen just before the action with the screen once it has settled
(just before the next action, at most ``SETTLE_WINDOW_S`` later):

- ``delay_s``: when at least half of the final change was visible, e.g. ``ls`` output
  appearing 0.77 s after Enter. Measuring "half of the final change" rather than "any
  change" ignores the blinking text cursor.
- ``appeared``: OCR lines of the settled screen inside the changed area (command output,
  a dialog that opened), in reading order.
- ``disappeared``: OCR lines of the earlier screen inside the changed area (a dialog
  that closed, a tooltip that went away).
- ``target``: for clicks and drags, the text under or next to the pointer.

These become the SOP steps: "Typed `ls` and pressed Enter" -> "After 0.77 s the screen
showed: Desktop Documents ...".
"""
from __future__ import annotations

import functools
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger(__name__)

SETTLE_WINDOW_S = 3.0  # how long after an action to look for its effect
PROBE_FPS = 15  # frames per second checked when timing the effect
PIXEL_THRESHOLD = 25  # grey-level change that counts as "changed"
MIN_CHANGED_PX = 300  # below this (at MASK_WIDTH) the screen did not visibly change
MASK_WIDTH = 960  # change masks are computed at this width
OCR_MAX_WIDTH = 1920  # colour frames are kept at most this wide
TEXT_IN_CHANGE = 0.08  # an OCR box counts as changed if this fraction of it changed
TARGET_RADIUS_PX = 40  # click target: OCR text within this distance of the pointer
ROW_GAP_PX = 12  # OCR boxes whose tops differ by more than this start a new line
MIN_REGION_AREA = 600  # changed area (dilated, at MASK_WIDTH) worth reading; skips cursor blink
MAX_REGIONS = 8  # read at most this many changed areas per action
CROP_PAD = 6  # pixels added around each area before OCR
UPSCALE_BELOW_PX = 120  # areas shorter than this (a few text lines) are enlarged 2x for OCR
TARGET_CROP = (360, 100)  # half-width, half-height of the area read around the pointer

# Shell prompts ("user@host:~$") reappear after every command; they are not output.
# OCR often misreads the "@", so any short "something: ~$" line counts as a prompt.
_PROMPT = re.compile(r"^\S+\s*:\s*\S{0,40}\s*[$#]\s*$")

# An OCR function returns (bbox (x1, y1, x2, y2), text, confidence) per text region.
OcrFn = Callable[[np.ndarray], list[tuple[tuple[int, int, int, int], str, float]]]


@dataclass
class ScreenEffect:
    changed: bool
    delay_s: float | None = None
    appeared: list[str] = field(default_factory=list)
    disappeared: list[str] = field(default_factory=list)


@dataclass
class UserAction:
    kind: str  # click | double_click | right_click | type | press | hotkey | drag | scroll
    timestamp: float  # when the effect is measured from (Enter time for "type + Enter")
    text: str = ""  # typed text, or the key(s) pressed
    x: int | None = None
    y: int | None = None
    pressed_enter: bool = False  # typing that ended with Enter, merged into one step
    target: str = ""  # text under/next to the pointer (clicks, drag destinations)
    effect: ScreenEffect = field(default_factory=lambda: ScreenEffect(changed=False))


def user_actions(action_log: list[dict]) -> list[UserAction]:
    """Turn raw action-log entries into the actions a person would describe.

    Pointer moves are dropped. MOUSE_DOWN -> DRAG_TO -> MOUSE_UP becomes one drag (to
    the DRAG_TO point). Typing immediately followed by Enter becomes one "type" action
    with ``pressed_enter``, timed from the Enter, because that is when output appears.
    """
    entries = sorted(action_log, key=lambda a: float(a.get("timestamp", 0)))
    actions: list[UserAction] = []
    i = 0
    while i < len(entries):
        a = entries[i]
        kind = str(a.get("action_type", "")).upper()
        p = a.get("action_params") or a.get("params") or {}
        t = float(a.get("timestamp", 0))
        if kind == "CLICK":
            button = str(p.get("text", "")).lower()
            clicks = int(p.get("numClicks", 1) or 1)
            name = "right_click" if button == "right" else "double_click" if clicks >= 2 else "click"
            actions.append(UserAction(name, t, x=_int(p.get("x")), y=_int(p.get("y"))))
        elif kind == "TYPING":
            actions.append(UserAction("type", t, text=str(p.get("text", ""))))
        elif kind in ("PRESS", "KEY_DOWN"):
            key = str(p.get("text", "")).strip()
            prev = actions[-1] if actions else None
            if key.lower() == "enter" and prev and prev.kind == "type" and not prev.pressed_enter:
                prev.pressed_enter = True
                prev.timestamp = t
            else:
                actions.append(UserAction("press", t, text=key))
        elif kind == "HOTKEY":
            actions.append(UserAction("hotkey", t, text=str(p.get("text", ""))))
        elif kind == "SCROLL":
            actions.append(UserAction("scroll", t))
        elif kind == "MOUSE_DOWN":
            j = i + 1
            drag: dict | None = None
            while j < len(entries) and str(entries[j].get("action_type", "")).upper() != "MOUSE_UP":
                if str(entries[j].get("action_type", "")).upper() == "DRAG_TO" and drag is None:
                    drag = entries[j]
                j += 1
            if drag is not None:
                dp = drag.get("action_params") or {}
                actions.append(UserAction("drag", float(drag.get("timestamp", t)),
                                          x=_int(dp.get("x")), y=_int(dp.get("y"))))
            else:
                actions.append(UserAction("click", t))
            i = j + 1
            continue
        elif kind == "DRAG_TO":
            actions.append(UserAction("drag", t, x=_int(p.get("x")), y=_int(p.get("y"))))
        i += 1
    return actions


def _int(v) -> int | None:
    try:
        return int(round(float(v)))
    except (TypeError, ValueError):
        return None


@functools.cache  # the EasyOCR model takes seconds to load; load it once
def default_ocr() -> OcrFn:
    from app.pipeline.ocr_extractor import OCRExtractor

    extractor = OCRExtractor(use_gpu=False)

    def run(image: np.ndarray):
        return [(r.bbox, r.text, r.confidence) for r in extractor.extract_text(image).regions]

    return run


def _read_frames(
    video_path: Path, color_idx: set[int], gray_idx: set[int]
) -> tuple[dict[int, np.ndarray], dict[int, np.ndarray]]:
    """Decode the wanted frames in one sequential pass.

    ``color_idx`` frames are kept at up to OCR_MAX_WIDTH wide for OCR; every wanted frame,
    including the many ``gray_idx`` probes used for timing, is also kept MASK_WIDTH wide.
    """
    cap = cv2.VideoCapture(str(video_path))
    color: dict[int, np.ndarray] = {}
    gray: dict[int, np.ndarray] = {}
    try:
        wanted = color_idx | gray_idx
        last = max(wanted) if wanted else -1
        idx = 0
        while idx <= last:
            if idx in wanted:
                ok, frame = cap.read()
                if not ok:
                    break
                gray[idx] = _small(frame)
                if idx in color_idx:
                    h, w = frame.shape[:2]
                    if w > OCR_MAX_WIDTH:
                        frame = cv2.resize(frame, (OCR_MAX_WIDTH, round(h * OCR_MAX_WIDTH / w)),
                                           interpolation=cv2.INTER_AREA)
                    color[idx] = frame
            elif not cap.grab():
                break
            idx += 1
    finally:
        cap.release()
    return color, gray


def _small(frame: np.ndarray) -> np.ndarray:
    h, w = frame.shape[:2]
    return cv2.resize(frame, (MASK_WIDTH, max(1, round(h * MASK_WIDTH / w))), interpolation=cv2.INTER_AREA)


def _changed(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    # Largest change in any colour channel. Grayscale weights blue at 11%, so blue text
    # appearing on a dark theme (directory names in `ls` output) barely registers in it.
    return cv2.absdiff(a, b).max(axis=2) > PIXEL_THRESHOLD


def _ocr_box(frame: np.ndarray, box: tuple[int, int, int, int], ocr: OcrFn):
    """OCR one area of the frame; returns regions in frame coordinates.

    Small areas are enlarged 2x first: screen text is small, and OCR reads enlarged
    crops far better (and faster) than the same text inside a whole 1920 px screenshot.
    """
    h, w = frame.shape[:2]
    x1, y1 = max(box[0] - CROP_PAD, 0), max(box[1] - CROP_PAD, 0)
    x2, y2 = min(box[2] + CROP_PAD, w), min(box[3] + CROP_PAD, h)
    crop = frame[y1:y2, x1:x2]
    if crop.size == 0:
        return []
    f = 2.0 if (y2 - y1) < UPSCALE_BELOW_PX else 1.0
    if f != 1.0:
        crop = cv2.resize(crop, None, fx=f, fy=f, interpolation=cv2.INTER_CUBIC)
    return [
        ((int(bx1 / f) + x1, int(by1 / f) + y1, int(bx2 / f) + x1, int(by2 / f) + y1), text, conf)
        for (bx1, by1, bx2, by2), text, conf in ocr(crop)
    ]


def _change_boxes(final: np.ndarray, frame_w: int) -> list[tuple[int, int, int, int]]:
    """Bounding boxes (frame coordinates) of the changed areas, largest first.

    The mask is dilated wider than tall so the glyphs of one line, or one dialog, join
    into a single area; specks such as a blinking cursor stay below MIN_REGION_AREA.
    """
    joined = cv2.dilate(final.astype(np.uint8), np.ones((7, 31), np.uint8))
    n, _, stats, _ = cv2.connectedComponentsWithStats(joined)
    areas = sorted(
        (stats[i] for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] >= MIN_REGION_AREA),
        key=lambda st: -st[cv2.CC_STAT_AREA],
    )[:MAX_REGIONS]
    s = frame_w / MASK_WIDTH
    boxes = [(int(x * s), int(y * s), int((x + bw) * s), int((y + bh) * s)) for x, y, bw, bh, _ in areas]
    return _merge_overlapping(boxes)


def _merge_overlapping(boxes: list[tuple[int, int, int, int]]) -> list[tuple[int, int, int, int]]:
    # Overlapping areas would be OCR'd twice and their text listed twice.
    merged = list(boxes)
    changed = True
    while changed:
        changed = False
        for i in range(len(merged)):
            for j in range(i + 1, len(merged)):
                a, b = merged[i], merged[j]
                if a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]:
                    merged[i] = (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))
                    del merged[j]
                    changed = True
                    break
            if changed:
                break
    return merged


def _lines_in_change(ocr_regions, mask_full: np.ndarray) -> list[str]:
    """OCR text whose box lies in the changed area, grouped into lines in reading order."""
    boxes = []
    seen: set[tuple[str, int, int]] = set()
    for (x1, y1, x2, y2), text, conf in ocr_regions:
        text = text.strip()
        if conf < 0.3 or not text:
            continue
        key = (text, y1 // 8, x1 // 8)  # overlapping crops can read the same text twice
        if key in seen:
            continue
        seen.add(key)
        roi = mask_full[max(y1, 0):max(y2, 0), max(x1, 0):max(x2, 0)]
        if roi.size and roi.mean() >= TEXT_IN_CHANGE:
            boxes.append((y1, x1, text))
    # Group boxes into lines by their top edge, then read each line left to right.
    rows: list[list[tuple[int, int, str]]] = []
    for box in sorted(boxes):
        if rows and box[0] - rows[-1][0][0] <= ROW_GAP_PX:
            rows[-1].append(box)
        else:
            rows.append([box])
    return [" ".join(text for _, _, text in sorted(row, key=lambda b: b[1])) for row in rows]


def _text_near(ocr_regions, px: float, py: float, radius: float) -> str:
    """OCR text under the point, or the closest text within ``radius``."""
    best, best_d = "", float("inf")
    for (x1, y1, x2, y2), text, conf in ocr_regions:
        if conf < 0.3 or not text.strip():
            continue
        dx = max(x1 - px, 0, px - x2)
        dy = max(y1 - py, 0, py - y2)
        d = (dx * dx + dy * dy) ** 0.5
        if d < best_d:
            best, best_d = text.strip(), d
    return best if best_d <= radius else ""


def capture_screen_effects(
    video_path: Path,
    actions: list[UserAction],
    ocr: OcrFn | None = None,
) -> list[UserAction]:
    """Fill in ``effect`` (and ``target`` for clicks/drags) for each action, in place."""
    if not actions:
        return actions
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    video_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1
    cap.release()
    duration = n_frames / fps

    def idx(t: float) -> int:
        return min(max(int(round(t * fps)), 0), n_frames - 1)

    probe_step = max(1, round(fps / PROBE_FPS))
    windows = []
    color_idx: set[int] = set()
    gray_idx: set[int] = set()
    for k, a in enumerate(actions):
        t_next = actions[k + 1].timestamp if k + 1 < len(actions) else duration
        end = min(max(t_next, a.timestamp), a.timestamp + SETTLE_WINDOW_S)
        before, after = idx(a.timestamp - 0.1), max(idx(end) - 1, idx(a.timestamp))
        probes = list(range(idx(a.timestamp), after + 1, probe_step)) + [after]
        windows.append((before, after, probes))
        color_idx.update([before, after])
        gray_idx.update(probes)

    frames, grays = _read_frames(video_path, color_idx, gray_idx)
    if not frames:
        logger.warning(f"no frames decoded from {video_path}")
        return actions
    last_color, last_gray = frames[max(frames)], grays[max(grays)]

    def get(i: int) -> np.ndarray:
        return frames.get(i, last_color)  # a frame count in metadata can overshoot

    def gray(i: int) -> np.ndarray:
        return grays.get(i, last_gray)

    ocr = ocr or default_ocr()

    for a, (before, after, probes) in zip(actions, windows):
        final = _changed(gray(before), gray(after))
        total = int(final.sum())
        frame_h, frame_w = get(after).shape[:2]
        if a.x is not None and a.y is not None:
            # A click target is read before the click; a drag destination after the drop.
            s = frame_w / video_w
            px, py = a.x * s, a.y * s
            area = (int(px - TARGET_CROP[0]), int(py - TARGET_CROP[1]),
                    int(px + TARGET_CROP[0]), int(py + TARGET_CROP[1]))
            regions = _ocr_box(get(after if a.kind == "drag" else before), area, ocr)
            a.target = _text_near(regions, px, py, TARGET_RADIUS_PX * s)
        if total < MIN_CHANGED_PX:
            a.effect = ScreenEffect(changed=False)
            continue
        delay = next(
            (i / fps - a.timestamp for i in probes
             if int((_changed(gray(before), gray(i)) & final).sum()) >= 0.5 * total),
            None,
        )
        mask_full = cv2.resize(final.astype(np.uint8), (frame_w, frame_h),
                               interpolation=cv2.INTER_NEAREST).astype(bool)
        boxes = _change_boxes(final, frame_w)
        after_regions = [r for b in boxes for r in _ocr_box(get(after), b, ocr)]
        before_regions = [r for b in boxes for r in _ocr_box(get(before), b, ocr)]
        appeared = [ln for ln in _lines_in_change(after_regions, mask_full) if not _PROMPT.search(ln)]
        if a.kind == "type" and not a.pressed_enter:
            # The typed text itself appearing is not a result worth reporting.
            appeared = [ln for ln in appeared if ln.strip() != a.text.strip()]
        a.effect = ScreenEffect(
            changed=True,
            delay_s=round(max(delay, 0.0), 2) if delay is not None else None,
            appeared=appeared,
            disappeared=_lines_in_change(before_regions, mask_full),
        )
    return actions


# ── Wording ─────────────────────────────────────────────────────────────────────

def _keys(text: str) -> str:
    """'ctrl + s' -> 'Ctrl+S', 'enter' -> 'Enter', 'Alt+Right arrow' -> 'Alt+Right arrow'."""
    parts = [p.strip() for p in re.split(r"\s*\+\s*", text) if p.strip()]
    if not parts:  # the key itself is "+"
        return text.strip()
    return "+".join(p.upper() if len(p) == 1 else p[0].upper() + p[1:] for p in parts)


def _where(a: UserAction) -> str:
    if a.target:
        return f'"{a.target}"'
    if a.x is not None and a.y is not None:
        return f"at ({a.x}, {a.y})"
    return ""


def action_sentence(a: UserAction) -> str:
    verb = {"click": "Clicked", "double_click": "Double-clicked", "right_click": "Right-clicked"}
    if a.kind in verb:
        return f"{verb[a.kind]} {_where(a)}".strip() + "."
    if a.kind == "type":
        return f"Typed `{a.text}`" + (" and pressed Enter." if a.pressed_enter else ".")
    if a.kind == "press":
        return f"Pressed {_keys(a.text)}."
    if a.kind == "hotkey":
        return f"Pressed {_keys(a.text)}."
    if a.kind == "drag":
        where = _where(a)
        return (f"Dragged onto {where}." if a.target else f"Dragged to {where}.") if where else "Dragged."
    if a.kind == "scroll":
        return "Scrolled."
    return a.kind.replace("_", " ").capitalize() + "."


def effect_sentence(e: ScreenEffect) -> str:
    if not e.changed:
        return "No visible change on screen."
    when = f"After {e.delay_s:.2f} s" if e.delay_s is not None else "Afterwards"
    if e.appeared and e.disappeared:
        return f"{when} the screen changed: new text appeared and some text was removed."
    if e.appeared:
        return f"{when} the screen showed new text."
    if e.disappeared:
        return f"{when} text was removed from the screen."
    return f"{when} the screen changed (no readable text)."
