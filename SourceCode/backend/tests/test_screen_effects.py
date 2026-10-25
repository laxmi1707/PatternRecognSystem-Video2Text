from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from app.knowledge.screen_effects import (
    ScreenEffect,
    UserAction,
    _keys,
    _lines_in_change,
    action_sentence,
    capture_screen_effects,
    effect_sentence,
    user_actions,
)
from app.knowledge.sop_generator import SOPGenerator

FPS = 10
W, H = 640, 360
BLUE = (200, 90, 40)  # BGR: blue text, which barely changes grayscale on a dark screen


def _log(*entries: tuple) -> list[dict]:
    return [{"action_type": kind, "timestamp": t, "action_params": params} for kind, t, params in entries]


def _write(path: Path, frame_at, seconds: float = 6.0) -> Path:
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))
    for i in range(int(seconds * FPS)):
        writer.write(frame_at(i / FPS))
    writer.release()
    return path


def _fake_ocr(img: np.ndarray):
    """One text region per bright or blue block, named by its colour."""
    regions = []
    for name, colour in (("OUTPUT", (255, 255, 255)), ("BLUE", BLUE)):
        hit = np.all(np.abs(img.astype(int) - colour) < 40, axis=2)
        ys, xs = np.nonzero(hit)
        if len(xs) > 20:
            regions.append(((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1), name, 0.9))
    return regions


# ── turning the log into actions ────────────────────────────────────────────────

def test_typing_then_enter_becomes_one_action_timed_from_enter():
    actions = user_actions(_log(("MOVE_TO", 0.5, {"x": 1, "y": 1}),
                                ("TYPING", 1.0, {"text": "ls"}),
                                ("PRESS", 2.0, {"text": "enter"})))
    assert len(actions) == 1
    a = actions[0]
    assert (a.kind, a.text, a.pressed_enter, a.timestamp) == ("type", "ls", True, 2.0)
    assert action_sentence(a) == "Typed `ls` and pressed Enter."


def test_click_variants_drag_and_keys():
    actions = user_actions(_log(
        ("CLICK", 1.0, {"x": 10, "y": 20, "text": "Left", "numClicks": 1}),
        ("CLICK", 2.0, {"x": 10, "y": 20, "text": "Left", "numClicks": 2}),
        ("CLICK", 3.0, {"x": 10, "y": 20, "text": "Right", "numClicks": 1}),
        ("MOUSE_DOWN", 4.0, {"text": "Left"}),
        ("DRAG_TO", 4.5, {"x": 300, "y": 200}),
        ("MOUSE_UP", 4.6, {"text": "Left"}),
        ("HOTKEY", 5.0, {"text": "ctrl + s"}),
        ("PRESS", 6.0, {"text": "Tab"}),
    ))
    assert [(a.kind, a.timestamp) for a in actions] == [
        ("click", 1.0), ("double_click", 2.0), ("right_click", 3.0), ("drag", 4.5),
        ("hotkey", 5.0), ("press", 6.0)]
    assert (actions[3].x, actions[3].y) == (300, 200)
    assert action_sentence(actions[4]) == "Pressed Ctrl+S."
    assert action_sentence(actions[1]) == "Double-clicked at (10, 20)."


def test_key_names_are_normalised():
    assert _keys("enter") == "Enter"
    assert _keys("Ctrl + Shift + n") == "Ctrl+Shift+N"
    assert _keys("Alt+Right arrow") == "Alt+Right arrow"


# ── what happened on screen ─────────────────────────────────────────────────────

def test_output_after_enter_is_captured_with_its_delay(tmp_path):
    def frame(t: float) -> np.ndarray:
        f = np.full((H, W, 3), 30, np.uint8)
        if t >= 2.8:  # command output appears 0.8 s after Enter, in blue and white
            cv2.rectangle(f, (20, 100), (300, 130), BLUE, -1)
            cv2.rectangle(f, (20, 150), (300, 180), (255, 255, 255), -1)
        return f

    video = _write(tmp_path / "v.mp4", frame)
    actions = user_actions(_log(("TYPING", 1.0, {"text": "ls"}), ("PRESS", 2.0, {"text": "Enter"})))

    (a,) = capture_screen_effects(video, actions, ocr=_fake_ocr)

    assert a.effect.changed
    assert a.effect.delay_s == pytest.approx(0.8, abs=0.15)
    assert a.effect.appeared == ["BLUE", "OUTPUT"]  # top line first; blue text is not missed
    assert a.effect.disappeared == []


def test_dialog_closing_is_reported_as_disappeared_text(tmp_path):
    def frame(t: float) -> np.ndarray:
        f = np.full((H, W, 3), 30, np.uint8)
        if t < 3.3:
            cv2.rectangle(f, (200, 100), (440, 220), (255, 255, 255), -1)
        return f

    video = _write(tmp_path / "v.mp4", frame)
    (a,) = capture_screen_effects(video, user_actions(_log(("CLICK", 3.0, {"x": 320, "y": 160}))),
                                  ocr=_fake_ocr)

    assert a.target == "OUTPUT"  # text under the pointer before the click
    assert a.effect.appeared == []
    assert a.effect.disappeared == ["OUTPUT"]
    assert "removed" in effect_sentence(a.effect)


def test_no_visible_change(tmp_path):
    video = _write(tmp_path / "v.mp4", lambda t: np.full((H, W, 3), 30, np.uint8))
    (a,) = capture_screen_effects(video, user_actions(_log(("PRESS", 1.0, {"text": "Escape"}))),
                                  ocr=_fake_ocr)
    assert not a.effect.changed
    assert effect_sentence(a.effect) == "No visible change on screen."


def test_shell_prompt_is_not_reported_as_output():
    mask = np.ones((100, 400), bool)
    regions = [((0, 0, 200, 10), "/home/user", 0.9),
               ((0, 30, 300, 40), "userdworkstation-abc: $", 0.9)]
    lines = _lines_in_change(regions, mask)
    assert lines == ["/home/user", "userdworkstation-abc: $"]
    from app.knowledge.screen_effects import _PROMPT
    assert [ln for ln in lines if not _PROMPT.search(ln)] == ["/home/user"]


# ── SOP ─────────────────────────────────────────────────────────────────────────

def test_sop_from_actions_has_one_step_per_action_with_screen_text():
    a = UserAction("type", 2.0, text="pwd", pressed_enter=True,
                   effect=ScreenEffect(changed=True, delay_s=0.35, appeared=["/home/user"]))
    b = UserAction("click", 5.0, target="Done", effect=ScreenEffect(changed=False))

    sop = SOPGenerator().generate_from_actions("Check your current directory.", "Bash", [a, b],
                                               source_recording="clip.mp4", generated_at="2026-10-23 10:00")

    assert (sop.platform, sop.source_recording, sop.purpose) == ("Bash", "clip.mp4", "Check your current directory.")
    assert [s.title for s in sop.steps] == ["Typed `pwd` and pressed Enter.", 'Clicked "Done".']
    assert sop.steps[0].description == "After 0.35 s the screen showed new text."
    assert sop.steps[0].screen_output == ["/home/user"]
    assert sop.steps[1].description == "No visible change on screen."
    assert sop.expected_outcome == "The screen shows: /home/user"
