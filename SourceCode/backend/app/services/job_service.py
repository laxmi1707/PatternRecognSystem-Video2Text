from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import AnalysisJob
from app.models.result import ClassificationResult


async def get_job(db: AsyncSession, job_id: int) -> AnalysisJob | None:
    result = await db.execute(select(AnalysisJob).where(AnalysisJob.id == job_id))
    return result.scalar_one_or_none()


async def get_job_results(db: AsyncSession, job_id: int) -> list[ClassificationResult]:
    result = await db.execute(
        select(ClassificationResult)
        .where(ClassificationResult.job_id == job_id)
        .order_by(ClassificationResult.segment_index)
    )
    return list(result.scalars().all())


async def update_job_status(
    db: AsyncSession,
    job_id: int,
    status: str,
    progress_pct: float = 0.0,
    error_message: str | None = None,
) -> AnalysisJob | None:
    job = await get_job(db, job_id)
    if job is None:
        return None
    job.status = status
    job.progress_pct = progress_pct
    if error_message is not None:
        job.error_message = error_message
    await db.commit()
    return job
