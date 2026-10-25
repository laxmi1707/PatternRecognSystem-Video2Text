"""Level 1 dataset: one sample per user action, labelled from the action log.

Each logged action (click, typing, key press, pointer move, drag) becomes one
sample. Its label comes from the action log, which is recorded ground truth, not
a heuristic. Its features come from the video only: frames around the action's
timestamp, described by frame-to-frame change features plus the visual state at
the action. The action log is deliberately *not* used for features (unlike
``InteractionFeatureExtractor``), because at inference an uploaded video has no
log, and its action-type counts would leak the label.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from app.ml.dataset_loader import ActionRecord, TaskMetadata
from app.pipeline.change_features import (
    CHANGE_FEATURE_DIM,
    COMPARE_WIDTH,
    change_features,
    to_compare_gray,
)
from app.pipeline.visual_features import VISUAL_FEATURE_DIM, VisualFeatureExtractor

logger = logging.getLogger(__name__)

# Fine classes map one-to-one to SOP step templates ("Type `ls`", "Press Enter").
FINE_LABELS: tuple[str, ...] = ("move", "click", "type", "press_key", "hotkey", "drag")
# Coarse classes are the proposal's four Level 1 interaction types.
COARSE_LABELS: tuple[str, ...] = ("pointer", "click", "keyboard", "drag")
FINE_TO_COARSE = {
    "move": "pointer",
    "click": "click",
    "type": "keyboard",
    "press_key": "keyboard",
    "hotkey": "keyboard",
    "drag": "drag",
}

_SIMPLE_ACTIONS = {
    "MOVE_TO": "move",
    "CLICK": "click",
    "TYPING": "type",
    "PRESS": "press_key",
    "KEY_DOWN": "press_key",
    "HOTKEY": "hotkey",
}
# KEY_UP repeats its KEY_DOWN; SCROLL is too rare to learn (1 in the local data);
# AFTER_LAST_ACTION is an end marker, not an action.
_IGNORED_ACTIONS = {"KEY_UP", "SCROLL", "AFTER_LAST_ACTION"}

# Frames sampled around each action, in seconds relative to its timestamp. The
# visible effect often lags the logged time (Enter at 3.23 s, output at 4.00 s).
FRAME_OFFSETS: tuple[float, ...] = (-0.5, 0.0, 0.5, 1.0)
STATE_FRAME_SIZE = (640, 480)  # matches VideoProcessor's target_size
ACTION_FEATURE_DIM = (len(FRAME_OFFSETS) - 1) * CHANGE_FEATURE_DIM + VISUAL_FEATURE_DIM


@dataclass(frozen=True)
class ActionEvent:
    task_id: int
    timestamp: float
    label: str  # one of FINE_LABELS


def labels_for(granularity: str) -> tuple[str, ...]:
    if granularity == "fine":
        return FINE_LABELS
    if granularity == "coarse":
        return COARSE_LABELS
    raise ValueError(f"granularity must be 'fine' or 'coarse', got {granularity!r}")


def to_granularity(fine_label: str, granularity: str) -> str:
    return fine_label if granularity == "fine" else FINE_TO_COARSE[fine_label]


def extract_events(task: TaskMetadata) -> list[ActionEvent]:
    """Turn a task's action log into labelled events.

    A drag is logged as MOUSE_DOWN -> DRAG_TO -> MOUSE_UP; it becomes one ``drag``
    event at the DRAG_TO time, and its MOUSE_DOWN / MOUSE_UP are not separate
    samples. A MOUSE_DOWN / MOUSE_UP pair without a DRAG_TO is a ``click``.
    """
    actions: list[ActionRecord] = sorted(task.actions, key=lambda a: a.timestamp)
    events: list[ActionEvent] = []
    i = 0
    while i < len(actions):
        a = actions[i]
        kind = a.action_type.upper()
        if kind in _SIMPLE_ACTIONS:
            events.append(ActionEvent(task.task_id, a.timestamp, _SIMPLE_ACTIONS[kind]))
        elif kind == "DRAG_TO":
            events.append(ActionEvent(task.task_id, a.timestamp, "drag"))
        elif kind == "MOUSE_DOWN":
            j = i + 1
            drag_at: float | None = None
            while j < len(actions) and actions[j].action_type.upper() != "MOUSE_UP":
                if actions[j].action_type.upper() == "DRAG_TO" and drag_at is None:
                    drag_at = actions[j].timestamp
                j += 1
            label = "drag" if drag_at is not None else "click"
            events.append(ActionEvent(task.task_id, drag_at if drag_at is not None else a.timestamp, label))
            i = j + 1  # skip the inner DRAG_TO(s) and the MOUSE_UP
            continue
        elif kind not in _IGNORED_ACTIONS and kind != "MOUSE_UP":
            logger.debug(f"task {task.task_id}: ignoring unknown action type {kind}")
        i += 1
    return events


def _read_frames(video_path: Path, timestamps: list[float]) -> dict[float, np.ndarray]:
    """Read the frame nearest each timestamp in one sequential pass over the video."""
    cap = cv2.VideoCapture(str(video_path))
    try:
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
        wanted: dict[int, list[float]] = {}
        for ts in timestamps:
            idx = min(max(int(round(ts * fps)), 0), n_frames - 1)
            wanted.setdefault(idx, []).append(ts)

        frames: dict[float, np.ndarray] = {}
        last_idx = max(wanted)
        last_frame: np.ndarray | None = None
        idx = 0
        while idx <= last_idx:
            if idx in wanted:
                ok, frame = cap.read()
            else:
                ok = cap.grab()
                frame = None
            if not ok:
                break
            if frame is not None:
                # Keep frames small: a long task needs 100+ of them, and full-size
                # 2940x1912 frames would take ~17 MB each.
                h, w = frame.shape[:2]
                frame = cv2.resize(frame, (COMPARE_WIDTH, max(1, round(h * COMPARE_WIDTH / w))),
                                   interpolation=cv2.INTER_AREA)
                last_frame = frame
                for ts in wanted[idx]:
                    frames[ts] = frame
            idx += 1
        # Frame counts in metadata can overshoot; reuse the last decoded frame.
        if last_frame is not None:
            for ts in timestamps:
                frames.setdefault(ts, last_frame)
        return frames
    finally:
        cap.release()


def event_features(frames: list[np.ndarray], visual: VisualFeatureExtractor) -> np.ndarray:
    """Features for one event from its frames at FRAME_OFFSETS.

    Change features for each consecutive pair (in time order, so a model can see
    e.g. "small change, then a large one"), plus the visual state at the action.
    """
    grays = [to_compare_gray(f) for f in frames]
    parts = [change_features(grays[k], grays[k + 1]) for k in range(len(grays) - 1)]
    at_action = frames[FRAME_OFFSETS.index(0.0)]
    parts.append(visual.extract(cv2.resize(at_action, STATE_FRAME_SIZE)))
    return np.concatenate(parts).astype(np.float32)


def build_action_dataset(
    tasks: list[TaskMetadata],
    granularity: str = "fine",
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return (X, y, task_ids, timestamps) for every event in tasks that have a video.

    ``y`` holds indices into ``labels_for(granularity)``.
    """
    label_names = labels_for(granularity)
    label_idx = {name: i for i, name in enumerate(label_names)}
    visual = VisualFeatureExtractor()

    X: list[np.ndarray] = []
    y: list[int] = []
    task_ids: list[int] = []
    times: list[float] = []

    usable = [t for t in tasks if t.video_path is not None and t.video_path.exists()]
    for n, task in enumerate(usable, 1):
        events = extract_events(task)
        if not events:
            continue
        wanted = sorted({max(e.timestamp + off, 0.0) for e in events for off in FRAME_OFFSETS})
        frames = _read_frames(task.video_path, wanted)
        if not frames:
            logger.warning(f"task {task.task_id}: no frames decoded from {task.video_path}")
            continue
        for e in events:
            ev_frames = [frames[max(e.timestamp + off, 0.0)] for off in FRAME_OFFSETS]
            X.append(event_features(ev_frames, visual))
            y.append(label_idx[to_granularity(e.label, granularity)])
            task_ids.append(task.task_id)
            times.append(e.timestamp)
        if n % 25 == 0 or n == len(usable):
            logger.info(f"  [{n}/{len(usable)}] tasks featurized, {len(y)} events so far")

    if not X:
        return (
            np.zeros((0, ACTION_FEATURE_DIM), dtype=np.float32),
            np.zeros(0, dtype=np.int64),
            np.zeros(0, dtype=np.int64),
            np.zeros(0, dtype=np.float32),
        )
    return (
        np.vstack(X),
        np.array(y, dtype=np.int64),
        np.array(task_ids, dtype=np.int64),
        np.array(times, dtype=np.float32),
    )
