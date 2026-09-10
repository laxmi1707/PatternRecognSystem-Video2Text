import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from app.ml.config import ACTIVITY_LABELS
from app.ml.dataset import generate_synthetic_dataset
from app.models.job import AnalysisJob
from app.models.result import ClassificationResult
from app.services.job_service import update_job_status
from app.services.ml_service import ml_service


async def run_classification_job(db: AsyncSession, job: AnalysisJob) -> list[ClassificationResult]:
    await update_job_status(db, job.id, status="processing", progress_pct=0.0)

    try:
        n_segments = 10
        n_features = 50
        X, _ = generate_synthetic_dataset(n_samples=n_segments, n_features=n_features)

        model_name = job.model_name or "svm"
        classify_result = ml_service.classify(X, model_name=model_name)

        results: list[ClassificationResult] = []
        for i, pred in enumerate(classify_result["results"]):
            cr = ClassificationResult(
                job_id=job.id,
                segment_index=i,
                start_time=i * 5.0,
                end_time=(i + 1) * 5.0,
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
