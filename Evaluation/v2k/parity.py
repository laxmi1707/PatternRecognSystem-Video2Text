"""Check that the cache reproduces the backend's own segment vectors.

Runs FeatureAssembler.extract_segment_features live on one task (OCR and all)
and compares it block by block with the vector rebuilt from the frame cache,
using the same TF-IDF vocabulary on both sides.
"""
from __future__ import annotations

import logging

import numpy as np

from v2k.frames import action_dicts, cache_paths, yolo_weights
from v2k.segments import FeatureBuilder, load_cached
from v2k.tasks import discover

log = logging.getLogger("v2k.parity")


def check(app: str, task_id: int) -> float:
    from app.pipeline.feature_assembler import MODALITY_MAP, FeatureAssembler
    from app.pipeline.interaction_features import InteractionFeatureExtractor
    from app.pipeline.ocr_extractor import OCRExtractor
    from app.pipeline.ui_detector import UIDetector
    from app.pipeline.video_processor import VideoProcessor
    from app.pipeline.visual_features import VisualFeatureExtractor

    if not cache_paths(app, task_id)[1].exists():
        raise SystemExit(f"{app}/{task_id} is not cached yet")
    task = next((t for a, t in discover([app]) if t.task_id == task_id), None)
    if task is None:
        raise SystemExit(f"task {task_id} not found under {app}")

    table = load_cached([app])
    rows = np.flatnonzero(table.task_id == task_id)
    builder = FeatureBuilder(("ocr", "ui", "visual", "interaction"), scale=False).fit(table, rows)
    cached = builder.transform(table, rows)

    assembler = FeatureAssembler(
        ocr=OCRExtractor(), ui=UIDetector(model_name=str(yolo_weights())),
        visual=VisualFeatureExtractor(), interaction=InteractionFeatureExtractor(),
        video_processor=VideoProcessor(),
    )
    assembler._ocr._tfidf = builder._ocr["ocr"]._tfidf  # same vocabulary on both sides
    assembler._ocr._fitted = builder._ocr["ocr"]._fitted
    segments = VideoProcessor().extract_segments(task.video_path, action_dicts(task))
    live = np.array([assembler.extract_segment_features(s) for s in segments])

    log.info(f"{app}/{task_id}: {len(segments)} segments live, {len(rows)} from cache")
    if live.shape != cached.shape:
        raise SystemExit(f"shape mismatch: live {live.shape} vs cached {cached.shape}")
    worst = 0.0
    for name, (s, e) in MODALITY_MAP.items():
        diff = float(np.max(np.abs(live[:, s:e] - cached[:, s:e]))) if len(live) else 0.0
        worst = max(worst, diff)
        nonzero = float(np.mean(np.abs(live[:, s:e]) > 0))
        log.info(f"  {name:<12} max |live - cached| = {diff:.2e}   (non-zero entries: {nonzero:.0%})")
    log.info("  match" if worst < 1e-4 else "  MISMATCH - the cache does not reproduce the backend")
    return worst
