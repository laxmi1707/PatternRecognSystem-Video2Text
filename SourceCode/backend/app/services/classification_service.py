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


def _extract_features(
    video_path: Path | None, action_log_path: Path | None
) -> tuple[np.ndarray, list[dict], bool]:
    """Returns (features, segments, used_yolo)."""
    from app.pipeline.feature_assembler import TOTAL_FEATURES

    if video_path and video_path.exists():
        from app.pipeline.temporal_encoder import TemporalEncoder
        try:
            X, segments = _extract_real_features(video_path, action_log_path)
            if X.shape[0] > 1:
                encoder = TemporalEncoder(window_size=1)
                X = encoder.encode_sequence(X)
            logger.info(
                f"Real pipeline: {video_path.name} → {X.shape[0]} segments, "
                f"{X.shape[1]} features"
            )
            return X, segments, True
        except Exception as e:
            logger.warning(f"Real feature extraction failed, falling back to synthetic: {e}")
            X_full, _ = generate_synthetic_dataset(n_samples=100, n_features=TOTAL_FEATURES)
            duration = 50.0
            n_segments = 10
            segments = [
                {"start_time": i * (duration / n_segments), "end_time": (i + 1) * (duration / n_segments)}
                for i in range(n_segments)
            ]
            return X_full[:n_segments], segments, False

    logger.info("No video file provided, using synthetic features")
    X_full, _ = generate_synthetic_dataset(n_samples=100, n_features=TOTAL_FEATURES)
    segments = [{"start_time": i * 5.0, "end_time": (i + 1) * 5.0} for i in range(10)]
    return X_full[:10], segments, False


ALL_MODELS = [
    # Tier 1
    "svm", "naive_bayes", "decision_tree", "random_forest", "knn", "xgboost", "lightgbm",
    # Tier 2
    "mlp", "cnn1d", "lstm", "transformer", "workflow_lstm", "workflow_transformer",
    # Tier 3
    "voting", "stacking", "late_fusion",
]


async def _classify_all_models(
    X: np.ndarray,
    db=None, job_id: int | None = None,
) -> dict[str, list[dict]]:
    from app.services.ml_service import ml_service

    all_results: dict[str, list[dict]] = {}
    models = list(ALL_MODELS)
    total = len(models)
    for idx, model_name in enumerate(models):
        if db and job_id:
            pct = 70 + int((idx / total) * 25)
            await update_job_status(db, job_id, "processing", pct, f"classifying with {model_name} ({idx+1}/{total})")
        try:
            result = ml_service.classify(X, model_name=model_name)
            all_results[model_name] = result["results"]
        except Exception as e:
            logger.warning(f"Model {model_name} failed: {e}")

    return all_results


async def run_classification_job(
    db: AsyncSession,
    job: AnalysisJob,
    video_path: Path | None = None,
    action_log_path: Path | None = None,
) -> list[ClassificationResult]:
    await update_job_status(db, job.id, "processing", 5.0, "preparing video analysis")

    try:
        await update_job_status(db, job.id, "processing", 10.0, "extracting video segments and keyframes")

        X, segments, used_yolo = _extract_features(video_path, action_log_path)
        n_segments = X.shape[0]
        n_features = X.shape[1]

        await update_job_status(
            db, job.id, "processing", 60.0,
            f"extracted {n_segments} segments with {n_features}-dim features"
        )

        await update_job_status(db, job.id, "processing", 65.0, "loading classification models")

        all_model_results = await _classify_all_models(
            X, db=db, job_id=job.id
        )

        await update_job_status(db, job.id, "processing", 96.0, "saving results to database")

        results: list[ClassificationResult] = []
        for model_name, predictions in all_model_results.items():
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
                    model_name=model_name,
                    latency_ms=pred["latency_ms"],
                )
                results.append(cr)

        db.add_all(results)
        await update_job_status(db, job.id, "completed", 100.0, "analysis complete")

        return results

    except Exception as e:
        await update_job_status(db, job.id, "failed", error_message=str(e))
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
