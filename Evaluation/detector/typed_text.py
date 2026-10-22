"""Typing steps from a bare video, with the application named first.

    1. Read the video one frame per second, with the team backend's extractors (OCR at
       full resolution, UI detector, visual features, ResNet embedding).
    2. Name the application from those frames (run_029's stage-1 model).
    3. Keep OCR text that grows at the same place from frame to frame (a field being
       typed into), and score each candidate with that application's ranker (run_037);
       the ones above threshold, deduplicated, are "Type" steps.

The heavy lifting is in v2k.sop_detector, which also trains and evaluates the rankers.
"""
from __future__ import annotations

from pathlib import Path

from v2k.env import RUNS

RANKERS = RUNS / "run_037_sop-detector" / "sop_detector.joblib"


def typing_steps(video: Path, progress=lambda pct, stage: None) -> dict:
    """{app, app_confidence, duration, steps: [{t, action: "Type", text, score}]}."""
    import joblib
    from v2k import sop_detector as sd
    from v2k.frames import Extractors, extract_video
    bundle = joblib.load(RANKERS)
    app_bundle = joblib.load(sd.stage1_path(bundle))
    progress(5, "reading the screen (OCR, one frame per second)")
    ex = Extractors(with_cnn="cnn" in app_bundle["blocks"])
    arrays, record = extract_video(video, [], ex, grid=False, grid_ocr=False,
                                   native_ocr=True, parity_ocr="ocr" in app_bundle["blocks"])
    record.update(task_id=0, app="(input)", platform="", instruction="", keyword_label="")
    progress(28, "identifying the application and filtering typed text")
    res = sd.detect(bundle, arrays, record, None, app_bundle)
    res["duration"] = (record.get("video") or {}).get("duration_seconds")
    res["steps"] = [{"t": round(s["time"], 2), "action": "Type", "text": s["text"], "score": round(s["score"], 3)}
                    for s in res["steps"]]
    return res
