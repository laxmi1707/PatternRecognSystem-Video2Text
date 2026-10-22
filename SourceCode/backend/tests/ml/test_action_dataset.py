from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

from app.ml.action_dataset import (
    ACTION_FEATURE_DIM,
    FINE_LABELS,
    build_action_dataset,
    extract_events,
    to_granularity,
)
from app.ml.dataset_loader import ActionRecord, TaskMetadata, discover_tasks, task_level_split_3way
from app.pipeline.change_features import CHANGE_SCALARS, change_features, to_compare_gray

IDX = {name: i for i, name in enumerate(CHANGE_SCALARS)}


def _task(task_id: int, actions: list[tuple[str, float]], platform: str = "Bash",
          video_path: Path | None = None) -> TaskMetadata:
    return TaskMetadata(
        task_id=task_id, instruction="test", platform=platform, video_path=video_path,
        actions=[ActionRecord(action_type=a, timestamp=t) for a, t in actions],
        video_meta=None, activity_label="terminal_ops", workflow="test",
    )


# ── events ──────────────────────────────────────────────────────────────────────

def test_simple_actions_map_to_fine_labels():
    task = _task(1, [("MOVE_TO", 0.5), ("CLICK", 1.0), ("TYPING", 2.0),
                     ("PRESS", 3.0), ("HOTKEY", 4.0), ("KEY_DOWN", 5.0), ("KEY_UP", 5.1)])
    labels = [e.label for e in extract_events(task)]
    assert labels == ["move", "click", "type", "press_key", "hotkey", "press_key"]


def test_drag_sequence_becomes_one_drag_at_drag_to_time():
    task = _task(1, [("CLICK", 2.6), ("MOUSE_DOWN", 5.5), ("DRAG_TO", 7.8),
                     ("MOUSE_UP", 8.5), ("CLICK", 10.0)])
    events = extract_events(task)
    assert [(e.label, e.timestamp) for e in events] == [
        ("click", 2.6), ("drag", 7.8), ("click", 10.0)]


def test_mouse_down_up_without_drag_is_a_click():
    events = extract_events(_task(1, [("MOUSE_DOWN", 1.0), ("MOUSE_UP", 1.2)]))
    assert [(e.label, e.timestamp) for e in events] == [("click", 1.0)]


def test_unpaired_drag_to_and_ignored_types():
    events = extract_events(_task(1, [("DRAG_TO", 1.0), ("MOUSE_UP", 1.5), ("SCROLL", 2.0),
                                      ("AFTER_LAST_ACTION", 9.0)]))
    assert [e.label for e in events] == ["drag"]


def test_coarse_mapping_covers_every_fine_label():
    assert {to_granularity(lab, "coarse") for lab in FINE_LABELS} == {"pointer", "click", "keyboard", "drag"}


# ── split ───────────────────────────────────────────────────────────────────────

def test_three_way_split_is_disjoint_stratified_and_deterministic():
    tasks = [_task(p * 100 + i, [], platform=plat) for p, plat in enumerate(("Bash", "VSCode", "OpenShot"))
             for i in range(20)]
    tasks += [_task(900 + i, [], platform="OPENSHOT") for i in range(10)]  # same app, other spelling

    train, val, test = task_level_split_3way(tasks, ratios=(0.7, 0.2, 0.1), seed=1)

    ids = [set(t.task_id for t in part) for part in (train, val, test)]
    assert not (ids[0] & ids[1] or ids[0] & ids[2] or ids[1] & ids[2])
    assert sum(len(s) for s in ids) == len(tasks)
    assert (len(train), len(val), len(test)) == (49, 14, 7)
    for part in (train, val, test):  # every app appears in every split
        assert {t.platform.lower() for t in part} == {"bash", "vscode", "openshot"}
    again = task_level_split_3way(tasks, ratios=(0.7, 0.2, 0.1), seed=1)
    assert [t.task_id for t in again[2]] == [t.task_id for t in test]


def test_three_way_split_rejects_bad_ratios():
    with pytest.raises(ValueError):
        task_level_split_3way([], ratios=(0.8, 0.2, 0.1))


# ── change features ─────────────────────────────────────────────────────────────

def _screen(h: int = 808, w: int = 1908) -> np.ndarray:
    img = np.full((h, w, 3), 30, dtype=np.uint8)
    cv2.rectangle(img, (0, 30), (w // 4, 50), (180, 180, 180), -1)
    return img


def test_no_change_gives_zero_features():
    g = to_compare_gray(_screen())
    assert np.all(change_features(g, g.copy()) == 0)


def test_small_change_is_located_and_resolution_independent():
    def pair(h: int, w: int) -> np.ndarray:
        before = _screen(h, w)
        after = before.copy()
        cv2.rectangle(after, (w // 2, h // 2), (w // 2 + w // 20, h // 2 + h // 20), (255, 255, 255), -1)
        return change_features(to_compare_gray(before), to_compare_gray(after))

    low, high = pair(808, 1908), pair(1912, 2940)
    assert 0 < low[IDX["changed_ratio"]] < 0.01
    assert low[IDX["centroid_x"]] == pytest.approx(0.525, abs=0.02)
    assert low[: len(CHANGE_SCALARS)] == pytest.approx(high[: len(CHANGE_SCALARS)], abs=0.01)


# ── features from video ─────────────────────────────────────────────────────────

def _write_video(path: Path, seconds: float = 4.0, fps: int = 10) -> None:
    """A dark screen where a white bar grows from t=1s, like text being typed."""
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (320, 160))
    for i in range(int(seconds * fps)):
        frame = np.full((160, 320, 3), 30, dtype=np.uint8)
        if i >= fps:
            cv2.rectangle(frame, (20, 20), (20 + 8 * (i - fps), 40), (255, 255, 255), -1)
        writer.write(frame)
    writer.release()


def test_features_come_from_video_not_action_log(tmp_path):
    video = tmp_path / "video.mp4"
    _write_video(video)
    times = [0.5, 1.5, 2.5]
    as_clicks = _task(1, [("CLICK", t) for t in times], video_path=video)
    as_typing = _task(2, [("TYPING", t) for t in times], video_path=video)

    X1, y1, tids, ts = build_action_dataset([as_clicks])
    X2, y2, _, _ = build_action_dataset([as_typing])

    assert X1.shape == (3, ACTION_FEATURE_DIM)
    assert list(tids) == [1, 1, 1] and list(ts) == pytest.approx(times)
    assert list(y1) == [FINE_LABELS.index("click")] * 3
    assert list(y2) == [FINE_LABELS.index("type")] * 3
    np.testing.assert_array_equal(X1, X2)  # same video + times => same features, whatever the label
    assert X1[0, IDX["changed_ratio"]] == 0  # t=0.0 -> 0.5: nothing on screen yet


def test_tasks_without_video_are_skipped():
    X, y, _, _ = build_action_dataset([_task(1, [("CLICK", 1.0)], video_path=None)])
    assert X.shape == (0, ACTION_FEATURE_DIM) and len(y) == 0


# ── end to end ──────────────────────────────────────────────────────────────────

def test_train_actions_end_to_end(tmp_path, monkeypatch):
    from app import train_actions

    dataset = tmp_path / "dataset"
    fine_actions = ["MOVE_TO", "CLICK", "TYPING", "PRESS", "HOTKEY", "DRAG_TO"]
    task_id = 1000
    for plat in ("Bash", "VSCode"):
        for _ in range(10):
            task_id += 1
            d = dataset / plat / str(task_id)
            (d / "video").mkdir(parents=True)
            _write_video(d / "video" / "video.mp4", seconds=4.0)
            log = [{"action_type": a, "timestamp": 0.4 + 0.5 * k, "action_params": {}}
                   for k, a in enumerate(fine_actions)]
            (d / "action_log.json").write_text(json.dumps(
                {"task_id": task_id, "task_instruction": "x", "platform": plat, "action_log": log}))

    assert len(discover_tasks(dataset)) == 20
    out = tmp_path / "models"
    monkeypatch.setattr(sys, "argv", ["train_actions", "--dataset-root", str(dataset),
                                      "--model-dir", str(out), "--models", "naive_bayes,decision_tree"])
    train_actions.main()

    labels = json.loads((out / "labels.json").read_text())
    assert labels["labels"] == list(FINE_LABELS) and labels["n_features"] == ACTION_FEATURE_DIM
    split = json.loads((out / "split.json").read_text())
    assert [len(split[s]) for s in ("train", "val", "test")] == [14, 4, 2]
    metrics = json.loads((out / "metrics.json").read_text())
    assert set(metrics["results"]) == {"naive_bayes", "decision_tree"}
    for name in ("naive_bayes", "decision_tree", "scaler"):
        assert (out / f"{name}.pkl").exists()
    assert "Test results" in (out / "results.md").read_text(encoding="utf-8")

    # A second run reuses the feature cache and must give the same split sizes.
    monkeypatch.setattr(sys, "argv", ["train_actions", "--model-dir", str(out), "--load-features",
                                      "--models", "naive_bayes"])
    train_actions.main()
    assert json.loads((out / "metrics.json").read_text())["meta"]["splits"]["test"]["tasks"] == 2
