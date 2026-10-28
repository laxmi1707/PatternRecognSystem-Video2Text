"""Feature extraction shortcuts: skip OCR on unchanged frames, cache features per video."""
from __future__ import annotations

import numpy as np

from app.pipeline.ocr_extractor import OCRExtractor
from app.pipeline.video_processor import FrameData
from app.services import classification_service as cs


class _CountingReader:
    def __init__(self) -> None:
        self.calls = 0

    def readtext(self, image, **kwargs):
        self.calls += 1
        return [([[0, 0], [10, 0], [10, 10], [0, 10]], f"text {self.calls}", 0.9)]


def _frame(value: int) -> FrameData:
    return FrameData(frame_index=0, timestamp=0.0, image=np.full((480, 640, 3), value, dtype=np.uint8))


def test_unchanged_keyframes_reuse_the_text_instead_of_running_ocr_again():
    ocr = OCRExtractor()
    reader = _CountingReader()
    ocr._easyocr_reader = reader

    # same screen three times, then a different screen
    _, text = ocr.extract_segment([_frame(100), _frame(100), _frame(100)])
    _, text2 = ocr.extract_segment([_frame(100), _frame(200)])

    assert reader.calls == 2
    assert (ocr.frames_read, ocr.frames_reused) == (2, 3)
    assert text == "text 1"
    assert text2 == "text 1\ntext 2"


def test_a_new_terminal_line_is_read_again_although_most_of_the_screen_is_unchanged():
    # risk_test_video: each new command adds one thin line of text (400-900 changed pixels
    # of 640x480), too little to move a whole-screen average but more than a blinking cursor.
    ocr = OCRExtractor()
    reader = _CountingReader()
    ocr._easyocr_reader = reader

    before = _frame(30)
    after_typing = _frame(30)
    after_typing.image[100:108, 20:120] = 220  # an 8 x 100 px line of new text
    cursor_blink = _frame(30)
    cursor_blink.image[100:106, 20:24] = 220  # a 6 x 4 px cursor

    ocr.extract_segment([before, cursor_blink])
    assert reader.calls == 1

    ocr.extract_segment([after_typing])
    assert reader.calls == 2


def test_second_run_of_the_same_video_comes_from_the_feature_cache(tmp_path, monkeypatch):
    monkeypatch.setattr("app.config.settings.upload_dir", str(tmp_path))
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"not really a video")

    calls = []

    def fake_extract(video_path, action_log_path=None, on_progress=None):
        calls.append(video_path)
        for i in range(3):
            if on_progress:
                on_progress(i + 1, 3)
        X = np.arange(3 * 4, dtype=np.float32).reshape(3, 4)
        segments = [{"start_time": i * 5.0, "end_time": (i + 1) * 5.0, "ocr_text": f"seg {i}"} for i in range(3)]
        return X, segments

    monkeypatch.setattr(cs, "_extract_real_features", fake_extract)

    progress: list[tuple[int, int]] = []
    X1, seg1, _ = cs._extract_features(video, None, lambda d, t: progress.append((d, t)))
    X2, seg2, _ = cs._extract_features(video, None, lambda d, t: progress.append((d, t)))

    assert len(calls) == 1
    np.testing.assert_array_equal(X1, X2)
    assert seg1 == seg2
    assert progress == [(1, 3), (2, 3), (3, 3), (3, 3)]
    assert len(list((tmp_path / "feature_cache").glob("*.npz"))) == 1


def test_a_different_video_is_not_served_from_the_cache(tmp_path, monkeypatch):
    monkeypatch.setattr("app.config.settings.upload_dir", str(tmp_path))
    a, b = tmp_path / "a.mp4", tmp_path / "b.mp4"
    a.write_bytes(b"video a")
    b.write_bytes(b"video b")

    calls = []

    def fake_extract(video_path, action_log_path=None, on_progress=None):
        calls.append(video_path.name)
        return np.zeros((1, 4), dtype=np.float32), [{"start_time": 0.0, "end_time": 5.0, "ocr_text": ""}]

    monkeypatch.setattr(cs, "_extract_real_features", fake_extract)
    cs._extract_features(a, None)
    cs._extract_features(b, None)

    assert calls == ["a.mp4", "b.mp4"]
