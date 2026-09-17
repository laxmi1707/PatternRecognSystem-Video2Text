import uuid
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.schemas.video import VideoUploadResponse, VideoResponse
from app.services import video_service

router = APIRouter(prefix="/api/v1/videos", tags=["videos"])


@router.post("/upload", response_model=VideoUploadResponse, status_code=201)
async def upload_video(
    file: UploadFile = File(...),
    model_name: str | None = Query(None, description="Classifier model to use"),
    db: AsyncSession = Depends(get_db),
):
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_name = f"{uuid.uuid4().hex}_{file.filename or 'video.mp4'}"
    file_path = upload_dir / safe_name

    content = await file.read()
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    duration_seconds = None
    try:
        from app.pipeline.video_processor import VideoProcessor
        vp = VideoProcessor()
        meta = vp.get_metadata(file_path)
        duration_seconds = meta.get("duration_seconds")
    except Exception:
        pass

    video, job = await video_service.create_video(
        db,
        original_filename=file.filename or "video.mp4",
        file_size_bytes=len(content),
        model_name=model_name,
        file_path=str(file_path),
        duration_seconds=duration_seconds,
    )
    return VideoUploadResponse(
        id=video.id,
        filename=video.filename,
        original_filename=video.original_filename,
        status=video.status,
        job_id=job.id,
    )


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(video_id: int, db: AsyncSession = Depends(get_db)):
    video = await video_service.get_video(db, video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    return VideoResponse(
        id=video.id,
        filename=video.filename,
        original_filename=video.original_filename,
        file_size_bytes=video.file_size_bytes,
        duration_seconds=video.duration_seconds,
        status=video.status,
    )


@router.get("/", response_model=list[VideoResponse])
async def list_videos(db: AsyncSession = Depends(get_db)):
    videos = await video_service.list_videos(db)
    return [
        VideoResponse(
            id=v.id,
            filename=v.filename,
            original_filename=v.original_filename,
            file_size_bytes=v.file_size_bytes,
            duration_seconds=v.duration_seconds,
            status=v.status,
        )
        for v in videos
    ]
