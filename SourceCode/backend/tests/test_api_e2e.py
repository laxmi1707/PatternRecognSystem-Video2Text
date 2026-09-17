import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.models.base import Base
from app.database import get_db


@pytest.fixture
async def client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    test_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with test_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_list_models(client: AsyncClient):
    r = await client.get("/api/v1/evaluation/models")
    assert r.status_code == 200
    data = r.json()
    assert len(data["models"]) >= 14
    assert "tier1" in data["tiers"]
    assert "tier2" in data["tiers"]
    assert "tier3" in data["tiers"]


@pytest.mark.asyncio
async def test_upload_and_classify_flow(client: AsyncClient):
    dummy_video = b"\x00" * 1024
    r = await client.post(
        "/api/v1/videos/upload",
        files={"file": ("demo.mp4", dummy_video, "video/mp4")},
        params={"model_name": "svm"},
    )
    assert r.status_code == 201
    upload = r.json()
    assert upload["original_filename"] == "demo.mp4"
    assert upload["status"] == "uploaded"
    video_id = upload["id"]
    job_id = upload["job_id"]

    r = await client.get(f"/api/v1/videos/{video_id}")
    assert r.status_code == 200
    assert r.json()["original_filename"] == "demo.mp4"

    r = await client.get(f"/api/v1/jobs/{job_id}")
    assert r.status_code == 200
    assert r.json()["status"] == "queued"

    r = await client.post(f"/api/v1/jobs/{job_id}/run")
    assert r.status_code == 200
    run_data = r.json()
    assert run_data["status"] == "completed"
    assert len(run_data["results"]) >= 1

    for result in run_data["results"]:
        assert "label" in result
        assert "confidence" in result
        assert result["confidence"] > 0.0

    r = await client.get(f"/api/v1/jobs/{job_id}/results")
    assert r.status_code == 200
    assert len(r.json()["results"]) >= 1

    r = await client.get(f"/api/v1/jobs/{job_id}")
    assert r.status_code == 200
    assert r.json()["status"] == "completed"
    assert r.json()["progress_pct"] == 100.0


@pytest.mark.asyncio
async def test_video_not_found(client: AsyncClient):
    r = await client.get("/api/v1/videos/9999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_job_not_found(client: AsyncClient):
    r = await client.get("/api/v1/jobs/9999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_list_videos(client: AsyncClient):
    await client.post(
        "/api/v1/videos/upload",
        files={"file": ("vid1.mp4", b"\x00" * 100, "video/mp4")},
    )
    await client.post(
        "/api/v1/videos/upload",
        files={"file": ("vid2.mp4", b"\x00" * 200, "video/mp4")},
    )

    r = await client.get("/api/v1/videos/")
    assert r.status_code == 200
    videos = r.json()
    assert len(videos) >= 2
