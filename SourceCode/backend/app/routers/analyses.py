from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.schemas.analysis import AnalysisCreateResponse, AnalysisStatusResponse
from app.services.analysis_service import analysis_service

router = APIRouter(prefix="/api/v1/analyses", tags=["analyses"])

UploadedFile = Annotated[UploadFile, File(...)]


@router.post("", response_model=AnalysisCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_analysis(file: UploadedFile) -> AnalysisCreateResponse:
    job_id = analysis_service.create(file.filename or "upload")
    return AnalysisCreateResponse(id=job_id)


@router.get("/{analysis_id}", response_model=AnalysisStatusResponse)
async def get_analysis(analysis_id: str) -> AnalysisStatusResponse:
    outcome = analysis_service.get_status(analysis_id)
    if outcome is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    job_status, progress, result = outcome
    return AnalysisStatusResponse(status=job_status, progress=progress, result=result)
