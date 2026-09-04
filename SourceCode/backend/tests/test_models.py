import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import Base, Video, AnalysisJob, ClassificationResult, EvaluationRun


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_video(db_session: AsyncSession):
    video = Video(filename="test_uuid.mp4", original_filename="demo.mp4", file_size_bytes=1024)
    db_session.add(video)
    await db_session.commit()

    result = await db_session.execute(select(Video).where(Video.id == video.id))
    fetched = result.scalar_one()

    assert fetched.filename == "test_uuid.mp4"
    assert fetched.original_filename == "demo.mp4"
    assert fetched.status == "uploaded"


@pytest.mark.asyncio
async def test_create_job_with_video(db_session: AsyncSession):
    video = Video(filename="v.mp4", original_filename="v.mp4", file_size_bytes=512)
    db_session.add(video)
    await db_session.commit()

    job = AnalysisJob(video_id=video.id, status="queued", model_name="svm")
    db_session.add(job)
    await db_session.commit()

    result = await db_session.execute(select(AnalysisJob).where(AnalysisJob.video_id == video.id))
    fetched = result.scalar_one()

    assert fetched.status == "queued"
    assert fetched.model_name == "svm"
    assert fetched.video_id == video.id


@pytest.mark.asyncio
async def test_create_classification_result(db_session: AsyncSession):
    video = Video(filename="v.mp4", original_filename="v.mp4", file_size_bytes=256)
    db_session.add(video)
    await db_session.commit()

    job = AnalysisJob(video_id=video.id)
    db_session.add(job)
    await db_session.commit()

    cr = ClassificationResult(
        job_id=job.id,
        segment_index=0,
        start_time=0.0,
        end_time=5.0,
        predicted_label="docker_workflow",
        confidence=0.87,
        probabilities={"docker_workflow": 0.87, "git_operations": 0.05},
        model_name="svm",
        latency_ms=12.5,
    )
    db_session.add(cr)
    await db_session.commit()

    result = await db_session.execute(
        select(ClassificationResult).where(ClassificationResult.job_id == job.id)
    )
    fetched = result.scalar_one()

    assert fetched.predicted_label == "docker_workflow"
    assert fetched.confidence == 0.87
    assert fetched.probabilities["docker_workflow"] == 0.87


@pytest.mark.asyncio
async def test_create_evaluation_run(db_session: AsyncSession):
    run = EvaluationRun(
        run_type="comparative",
        n_models=14,
        n_samples=500,
        comparison_table={"svm": {"f1": 0.95}, "rf": {"f1": 0.93}},
        best_model="svm",
        best_f1=0.95,
    )
    db_session.add(run)
    await db_session.commit()

    result = await db_session.execute(select(EvaluationRun).where(EvaluationRun.id == run.id))
    fetched = result.scalar_one()

    assert fetched.n_models == 14
    assert fetched.best_model == "svm"
    assert fetched.comparison_table["svm"]["f1"] == 0.95


@pytest.mark.asyncio
async def test_video_job_relationship(db_session: AsyncSession):
    video = Video(filename="v.mp4", original_filename="v.mp4", file_size_bytes=100)
    db_session.add(video)
    await db_session.commit()

    job1 = AnalysisJob(video_id=video.id, status="completed", job_type="classification")
    job2 = AnalysisJob(video_id=video.id, status="queued", job_type="evaluation")
    db_session.add_all([job1, job2])
    await db_session.commit()

    result = await db_session.execute(
        select(AnalysisJob).where(AnalysisJob.video_id == video.id)
    )
    jobs = result.scalars().all()

    assert len(jobs) == 2
