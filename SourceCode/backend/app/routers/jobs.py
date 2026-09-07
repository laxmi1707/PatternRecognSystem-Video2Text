from fastapi import APIRouter, HTTPException

from app.schemas.analysis import ClassificationResult, JobStatusResponse, SopReport
from app.services.analysis_service import JobNotFound, JobNotReady, analysis_service

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.get("", response_model=list[ClassificationResult])
async def list_jobs() -> list[ClassificationResult]:
    return analysis_service.list_results()


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> JobStatusResponse:
    try:
        job_status, progress = analysis_service.get_status(job_id)
    except JobNotFound:
        raise HTTPException(status_code=404, detail="Job not found") from None
    return JobStatusResponse(status=job_status, progress=progress)


@router.get("/{job_id}/results", response_model=ClassificationResult)
async def get_job_results(job_id: str) -> ClassificationResult:
    try:
        return analysis_service.get_result(job_id)
    except JobNotFound:
        raise HTTPException(status_code=404, detail="Job not found") from None
    except JobNotReady:
        raise HTTPException(status_code=409, detail="Analysis not yet complete") from None


@router.get("/{job_id}/sop", response_model=SopReport)
async def get_job_sop(job_id: str) -> SopReport:
    """Prototype endpoint -- see AnalysisService.get_sop_report's docstring."""
    try:
        return analysis_service.get_sop_report(job_id)
    except JobNotFound:
        raise HTTPException(status_code=404, detail="Job not found") from None
    except JobNotReady:
        raise HTTPException(status_code=409, detail="Analysis not yet complete") from None
