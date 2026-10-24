import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.models.base import Base
from app.database import get_db


@pytest.fixture
async def client(monkeypatch):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    test_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with test_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    # /jobs/{id}/run runs the pipeline in a background task that opens its own
    # session instead of using get_db, so point that at the test database too.
    monkeypatch.setattr("app.routers.jobs.async_session", test_session)

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

    # The pipeline runs as a background task; with ASGITransport it finishes
    # before this request returns, so the job is done when we query it next.
    r = await client.post(f"/api/v1/jobs/{job_id}/run")
    assert r.status_code == 200
    assert r.json() == {"job_id": job_id, "status": "processing"}

    r = await client.get(f"/api/v1/jobs/{job_id}/results")
    assert r.status_code == 200
    results = r.json()["results"]
    assert len(results) >= 1
    for result in results:
        assert "label" in result
        assert "confidence" in result
        assert result["confidence"] > 0.0

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


@pytest.mark.asyncio
async def test_sop_and_runbook_titles_from_labels(client: AsyncClient):
    # "video.mp4" is a generic name and there is no action log, so both endpoints
    # fall back to a title derived from the predicted labels. The runbook endpoint
    # used to raise NameError here (_title_from_labels was local to generate_sop).
    r = await client.post(
        "/api/v1/videos/upload",
        files={"file": ("video.mp4", b"\x00" * 1024, "video/mp4")},
        params={"model_name": "svm"},
    )
    job_id = r.json()["job_id"]
    await client.post(f"/api/v1/jobs/{job_id}/run")

    for kind in ("sop", "runbook"):
        r = await client.post(f"/api/v1/knowledge/{kind}/{job_id}")
        assert r.status_code == 200, f"{kind}: {r.text}"
        assert r.json()["title"]


def test_title_from_labels_uses_dominant_label():
    from app.routers.knowledge import _title_from_labels

    segs = [{"predicted_label": "terminal_ops"}] * 2 + [{"predicted_label": "other"}]
    assert _title_from_labels(segs, "Bash", 7) == "Terminal Operations on Bash"
    assert _title_from_labels(segs, "Screen Recording", 7) == "Terminal Operations"
    assert _title_from_labels([], "Bash", 7) == "Screen Activity Analysis #7"


def test_upload_limit_allows_typical_screen_recordings():
    from app.routers import videos

    # A 26 MB screen recording was rejected by the previous 10 MB limit.
    assert videos.MAX_FILE_SIZE == 100 * 1024 * 1024


@pytest.mark.asyncio
async def test_oversized_upload_is_rejected_and_not_kept(client: AsyncClient, monkeypatch, tmp_path):
    from app.config import settings
    from app.routers import videos

    monkeypatch.setattr(videos, "MAX_FILE_SIZE", 1024)
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    r = await client.post(
        "/api/v1/videos/upload",
        files={"file": ("big.mp4", b"\x00" * 4096, "video/mp4")},
    )
    assert r.status_code == 413
    assert list(tmp_path.iterdir()) == []
