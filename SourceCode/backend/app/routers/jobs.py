from collections import defaultdict
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.job import JobResponse, JobResultsResponse, ModelSummary
from app.schemas.classification import ClassificationResult
from app.services import job_service, video_service
from app.services.classification_service import run_classification_job

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


def _build_model_comparison(results) -> tuple[list[ModelSummary], str | None]:
    from app.services.ml_service import ml_service

    by_model: dict[str, list] = defaultdict(list)
    latency_by_model: dict[str, float] = {}

    for r in results:
        name = r.model_name if hasattr(r, 'model_name') else r.get('model_name', '')
        conf = r.confidence if hasattr(r, 'confidence') else r.get('confidence', 0)
        lat = r.latency_ms if hasattr(r, 'latency_ms') else r.get('latency_ms', 0)
        by_model[name].append(conf)
        latency_by_model[name] = lat

    comparison = []
    for name, confidences in by_model.items():
        try:
            tier = ml_service.get_model_tier(name)
        except Exception:
            tier = "unknown"
        comparison.append(ModelSummary(
            model_name=name,
            tier=tier,
            avg_confidence=round(sum(confidences) / len(confidences), 4),
            latency_ms=round(latency_by_model.get(name, 0), 2),
        ))

    comparison.sort(key=lambda m: (-m.avg_confidence, m.latency_ms))
    best = comparison[0].model_name if comparison else None
    return comparison, best


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, db: AsyncSession = Depends(get_db)):
    job = await job_service.get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse(
        id=job.id,
        video_id=job.video_id,
        status=job.status,
        job_type=job.job_type,
        model_name=job.model_name,
        progress_pct=job.progress_pct,
        error_message=job.error_message,
    )


@router.post("/{job_id}/run")
async def run_job(job_id: int, db: AsyncSession = Depends(get_db)):
    job = await job_service.get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status == "completed":
        raise HTTPException(status_code=409, detail="Job already completed")

    video = await video_service.get_video(db, job.video_id)
    video_path = Path(video.file_path) if video and video.file_path else None

    action_log_path = None
    if video and video.action_log_path:
        action_log_path = Path(video.action_log_path)
    elif video_path:
        candidate = video_path.parent / "action_log.json"
        if candidate.exists():
            action_log_path = candidate

    results = await run_classification_job(
        db, job, video_path=video_path, action_log_path=action_log_path
    )

    classification_results = [
        ClassificationResult(
            label=r.predicted_label,
            confidence=r.confidence,
            probabilities=r.probabilities,
            model_name=r.model_name,
            latency_ms=r.latency_ms,
        )
        for r in results
    ]

    comparison, best = _build_model_comparison(results)

    return JobResultsResponse(
        job_id=job.id,
        status="completed",
        results=classification_results,
        model_comparison=comparison,
        best_model=best,
    )


@router.get("/{job_id}/results", response_model=JobResultsResponse)
async def get_job_results(job_id: int, db: AsyncSession = Depends(get_db)):
    job = await job_service.get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    results = await job_service.get_job_results(db, job_id)

    classification_results = [
        ClassificationResult(
            label=r.predicted_label,
            confidence=r.confidence,
            probabilities=r.probabilities,
            model_name=r.model_name,
            latency_ms=r.latency_ms,
        )
        for r in results
    ]

    comparison, best = _build_model_comparison(results)

    return JobResultsResponse(
        job_id=job.id,
        status=job.status,
        results=classification_results,
        model_comparison=comparison,
        best_model=best,
    )
