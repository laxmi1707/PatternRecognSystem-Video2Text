import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.video import Video
from app.models.job import AnalysisJob


async def create_video(
    db: AsyncSession,
    original_filename: str,
    file_size_bytes: int,
    model_name: str | None = None,
) -> tuple[Video, AnalysisJob]:
    filename = f"{uuid.uuid4().hex}_{original_filename}"

    video = Video(
        filename=filename,
        original_filename=original_filename,
        file_size_bytes=file_size_bytes,
    )
    db.add(video)
    await db.flush()

    job = AnalysisJob(
        video_id=video.id,
        status="queued",
        job_type="classification",
        model_name=model_name,
    )
    db.add(job)
    await db.commit()

    return video, job


async def get_video(db: AsyncSession, video_id: int) -> Video | None:
    result = await db.execute(select(Video).where(Video.id == video_id))
    return result.scalar_one_or_none()


async def list_videos(db: AsyncSession) -> list[Video]:
    result = await db.execute(select(Video).order_by(Video.id.desc()))
    return list(result.scalars().all())
