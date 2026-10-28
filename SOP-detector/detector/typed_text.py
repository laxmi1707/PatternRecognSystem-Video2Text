"""Typing steps from a bare video, with the application named first.

    1. Read the video one frame per second, with the team backend's extractors (OCR at
       full resolution, UI detector, visual features, ResNet embedding).
    2. Name the application from those frames (run_029's stage-1 model).
    3. Keep OCR text that grows at the same place from frame to frame (a field being
       typed into), and score each candidate with the mean of that application's ranker
       and a pooled one (run_040; design and out-of-fold scores in run_039); the ones
       above threshold, deduplicated, are "Type" steps.

The heavy lifting is in v2k.sop_detector and v2k.sop_extras, which also train and
evaluate the rankers. A run_037 bundle (version 1) still loads, through sop_detector.
"""
from __future__ import annotations

import os
from pathlib import Path

from v2k.env import RUNS

RANKERS = RUNS / "run_040_sop-detector-v2" / "sop_detector.joblib"
# SOP_DETECTOR_FAST_OCR=1 reads only what changed since the previous frame
# (detector/fast_ocr.py): 5.7x faster reading on 16 held-out recordings, but 10 of 19
# logged typed strings found against 12 with full reads (ocr_fast_eval_v2.py), so it
# is off by default.
FAST_OCR = os.environ.get("SOP_DETECTOR_FAST_OCR") == "1"


def typing_steps(video: Path, progress=lambda pct, stage: None) -> dict:
    """{app, app_confidence, duration, steps: [{t, action: "Type", text, score}]}."""
    import joblib
    from v2k import sop_detector as sd
    from v2k.frames import Extractors, extract_video
    from detector import model_file
    if model_file.PKL:                       # the one-file deployment (detector/model_file.py)
        bundle, app_bundle = model_file.load()["typing"], model_file.load()["stage1"]
    else:
        bundle = joblib.load(RANKERS)
        app_bundle = joblib.load(sd.stage1_path(bundle))
    progress(5, "reading the screen (OCR, one frame per second)")
    ex = Extractors(with_cnn="cnn" in app_bundle["blocks"])
    if FAST_OCR:
        from detector.fast_ocr import IncrementalOCR
        ex.ocr = IncrementalOCR(ex.ocr)
    arrays, record = extract_video(video, [], ex, grid=False, grid_ocr=False,
                                   native_ocr=True, parity_ocr="ocr" in app_bundle["blocks"])
    record.update(task_id=0, app="(input)", platform="", instruction="", keyword_label="")
    progress(28, "identifying the application and filtering typed text")
    if bundle.get("version") == 2:           # run_040 on: the round-4 ranker (v2k/sop_extras.py)
        from v2k import sop_extras
        res = sop_extras.detect(bundle, arrays, record, None, app_bundle)
    else:
        res = sd.detect(bundle, arrays, record, None, app_bundle)
    res["duration"] = (record.get("video") or {}).get("duration_seconds")
    res["steps"] = [{"t": round(s["time"], 2), "action": "Type", "text": s["text"], "score": round(s["score"], 3)}
                    for s in res["steps"]]
    return res
