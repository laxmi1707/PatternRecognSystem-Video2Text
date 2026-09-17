from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.job import JobResponse, JobResultsResponse
from app.schemas.classification import ClassificationResult
from app.services import job_service, video_service
from app.services.classification_service import run_classification_job

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


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

    return JobResultsResponse(
        job_id=job.id,
        status="completed",
        results=[
            ClassificationResult(
                label=r.predicted_label,
                confidence=r.confidence,
                probabilities=r.probabilities,
                model_name=r.model_name,
                latency_ms=r.latency_ms,
            )
            for r in results
        ],
    )


@router.get("/{job_id}/results", response_model=JobResultsResponse)
async def get_job_results(job_id: int, db: AsyncSession = Depends(get_db)):
    job = await job_service.get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    results = await job_service.get_job_results(db, job_id)

    return JobResultsResponse(
        job_id=job.id,
        status=job.status,
        results=[
            ClassificationResult(
                label=r.predicted_label,
                confidence=r.confidence,
                probabilities=r.probabilities,
                model_name=r.model_name,
                latency_ms=r.latency_ms,
            )
            for r in results
        ],
    )
