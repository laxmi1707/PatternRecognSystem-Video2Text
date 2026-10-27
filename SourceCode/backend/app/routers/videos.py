import json
import re
import uuid
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.schemas.video import VideoUploadResponse, VideoResponse
from app.services import video_service

router = APIRouter(prefix="/api/v1/videos", tags=["videos"])
limiter = Limiter(key_func=get_remote_address)

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_ACTION_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
CHUNK_SIZE = 64 * 1024  # 64 KB
ALLOWED_CONTENT_TYPES = {"video/mp4", "video/quicktime", "video/webm", "video/x-msvideo", "application/octet-stream"}
ALLOWED_EXTENSIONS = {".mp4", ".mov", ".webm", ".avi", ".mkv"}

_SAFE_FILENAME_RE = re.compile(r"[^a-zA-Z0-9._-]")


def _sanitize_filename(name: str) -> str:
    sanitized = _SAFE_FILENAME_RE.sub("_", name)
    return sanitized[:100] if sanitized else "video.mp4"


@router.post("/upload", response_model=VideoUploadResponse, status_code=201)
@limiter.limit("5/minute")
async def upload_video(
    request: Request,
    file: UploadFile = File(...),
    action_log: UploadFile | None = File(None, description="Optional action_log.json"),
    model_name: str | None = Query(None, description="Classifier model to use"),
    db: AsyncSession = Depends(get_db),
):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported content type '{file.content_type}'")

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_original = _sanitize_filename(file.filename or "video.mp4")
    safe_name = f"{uuid.uuid4().hex}_{safe_original}"
    file_path = upload_dir / safe_name

    total_size = 0
    async with aiofiles.open(file_path, "wb") as f:
        while True:
            chunk = await file.read(CHUNK_SIZE)
            if not chunk:
                break
            total_size += len(chunk)
            if total_size > MAX_FILE_SIZE:
                await f.close()
                file_path.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail=f"File too large. Maximum allowed size is {MAX_FILE_SIZE // (1024*1024)} MB")
            await f.write(chunk)

    action_log_path_str: str | None = None
    if action_log and action_log.filename:
        log_ext = Path(action_log.filename).suffix.lower()
        if log_ext != ".json":
            raise HTTPException(status_code=400, detail="Action log must be a .json file")

        log_content = await action_log.read()
        if len(log_content) > MAX_ACTION_LOG_SIZE:
            raise HTTPException(status_code=413, detail=f"Action log too large. Maximum size is {MAX_ACTION_LOG_SIZE // (1024*1024)} MB")

        try:
            json.loads(log_content)
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise HTTPException(status_code=400, detail="Action log is not valid JSON")

        log_name = f"{safe_name}.action_log.json"
        log_path = upload_dir / log_name
        async with aiofiles.open(log_path, "wb") as f:
            await f.write(log_content)
        action_log_path_str = str(log_path)

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
        file_size_bytes=total_size,
        model_name=model_name,
        file_path=str(file_path),
        duration_seconds=duration_seconds,
        action_log_path=action_log_path_str,
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
