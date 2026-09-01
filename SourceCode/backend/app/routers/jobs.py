from fastapi import APIRouter, HTTPException

from app.schemas.analysis import AnalysisResult, JobStatusResponse
from app.services.analysis_service import JobNotFound, JobNotReady, analysis_service

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> JobStatusResponse:
    try:
        job_status, progress = analysis_service.get_status(job_id)
    except JobNotFound:
        raise HTTPException(status_code=404, detail="Job not found") from None
    return JobStatusResponse(status=job_status, progress=progress)


@router.get("/{job_id}/results", response_model=AnalysisResult)
async def get_job_results(job_id: str) -> AnalysisResult:
    try:
        return analysis_service.get_result(job_id)
    except JobNotFound:
        raise HTTPException(status_code=404, detail="Job not found") from None
    except JobNotReady:
        raise HTTPException(status_code=409, detail="Analysis not yet complete") from None
