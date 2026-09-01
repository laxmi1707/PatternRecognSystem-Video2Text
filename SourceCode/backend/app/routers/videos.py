from typing import Annotated

from fastapi import APIRouter, File, UploadFile, status

from app.schemas.analysis import VideoUploadResponse
from app.services.analysis_service import analysis_service

router = APIRouter(prefix="/api/v1/videos", tags=["videos"])

UploadedFile = Annotated[UploadFile, File(...)]


@router.post("/upload", response_model=VideoUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_video(file: UploadedFile) -> VideoUploadResponse:
    job_id = analysis_service.create(file.filename or "upload")
    return VideoUploadResponse(id=job_id)
