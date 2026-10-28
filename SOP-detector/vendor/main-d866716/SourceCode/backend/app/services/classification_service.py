from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from app.ml.config import ACTIVITY_LABELS
from app.ml.dataset import generate_synthetic_dataset
from app.models.job import AnalysisJob
from app.models.result import ClassificationResult
from app.services.job_service import update_job_status

logger = logging.getLogger(__name__)


def _run_ml_pipeline(
    video_path: Path | None, action_log_path: Path | None, model_name: str
) -> tuple[list[dict], list[dict]]:
    from app.pipeline.feature_assembler import TOTAL_FEATURES
    from app.pipeline.temporal_encoder import TemporalEncoder

    if video_path and video_path.exists():
        try:
            X, segments = _extract_real_features(video_path, action_log_path)

            if X.shape[0] > 1:
                encoder = TemporalEncoder(window_size=1)
                X = encoder.encode_sequence(X)

            logger.info(
                f"Real pipeline: {video_path.name} → {X.shape[0]} segments, "
                f"{X.shape[1]} features"
            )
        except Exception as e:
            logger.warning(f"Real feature extraction failed, falling back to synthetic: {e}")
            X, _ = generate_synthetic_dataset(n_samples=10, n_features=TOTAL_FEATURES)
            segments = [{"start_time": i * 5.0, "end_time": (i + 1) * 5.0} for i in range(10)]
    else:
        logger.info("No video file available, using synthetic features")
        X, _ = generate_synthetic_dataset(n_samples=10, n_features=TOTAL_FEATURES)
        segments = [{"start_time": i * 5.0, "end_time": (i + 1) * 5.0} for i in range(10)]

    # Lazy import: ml_service must load AFTER pipeline runs to avoid
    # torch/YOLO OpenMP segfault on macOS
    from app.services.ml_service import ml_service
    classify_result = ml_service.classify(X, model_name=model_name)
    return classify_result["results"], segments


async def run_classification_job(
    db: AsyncSession,
    job: AnalysisJob,
    video_path: Path | None = None,
    action_log_path: Path | None = None,
) -> list[ClassificationResult]:
    await update_job_status(db, job.id, status="processing", progress_pct=0.0)

    try:
        model_name = job.model_name or "svm"
        # Run synchronously — YOLO/OpenCV segfault on macOS in background threads
        predictions, segments = _run_ml_pipeline(video_path, action_log_path, model_name)

        results: list[ClassificationResult] = []
        for i, pred in enumerate(predictions):
            seg = segments[i] if i < len(segments) else {"start_time": i * 5.0, "end_time": (i + 1) * 5.0}
            cr = ClassificationResult(
                job_id=job.id,
                segment_index=i,
                start_time=seg["start_time"],
                end_time=seg["end_time"],
                predicted_label=pred["label"],
                confidence=pred["confidence"],
                probabilities=pred["probabilities"],
                model_name=pred["model_name"],
                latency_ms=pred["latency_ms"],
            )
            results.append(cr)

        db.add_all(results)
        await update_job_status(db, job.id, status="completed", progress_pct=100.0)

        return results

    except Exception as e:
        await update_job_status(db, job.id, status="failed", error_message=str(e))
        raise


def _extract_real_features(
    video_path: Path, action_log_path: Path | None = None
) -> tuple[np.ndarray, list[dict]]:
    from app.pipeline.feature_assembler import FeatureAssembler, get_default_assembler
    from app.pipeline.video_processor import VideoProcessor

    actions: list[dict] = []
    if action_log_path and action_log_path.exists():
        with open(action_log_path) as f:
            data = json.load(f)
        actions = data.get("action_log", [])

    assembler = get_default_assembler()
    processor = VideoProcessor()
    segments = processor.extract_segments(video_path, actions)

    X = np.array([assembler.extract_segment_features(seg) for seg in segments])

    segment_info = [
        {"start_time": seg.start_time, "end_time": seg.end_time}
        for seg in segments
    ]

    return X, segment_info
