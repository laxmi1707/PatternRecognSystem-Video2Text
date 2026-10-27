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


@pytest.fixture
def svm_model(monkeypatch):
    # The pipeline only runs models that have a .pkl in model_dir, and CI has none
    # (no S3 access, no local models). Give it one SVM fitted on synthetic data.
    from app.services import classification_service
    from app.services.ml_service import ml_service

    if "svm" not in ml_service._trained_models:
        X, y = ml_service._get_synth_data(n_samples=200)
        ml_service.get_model("svm").fit(X, y)
        monkeypatch.setattr(ml_service, "_trained_models", ml_service._trained_models | {"svm"})
    monkeypatch.setattr(classification_service, "_get_available_models", lambda: ["svm"])


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
async def test_upload_and_classify_flow(client: AsyncClient, svm_model):
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
async def test_sop_and_runbook_titles_from_labels(client: AsyncClient, svm_model):
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


@pytest.mark.asyncio
async def test_sop_with_action_log_has_one_step_per_action(client: AsyncClient, tmp_path, monkeypatch, svm_model):
    import json

    import cv2
    import numpy as np

    from app.knowledge import screen_effects

    # A dark screen where output appears 0.8 s after Enter at t=2.0.
    video = tmp_path / "clip.mp4"
    writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"mp4v"), 10, (320, 180))
    for i in range(50):
        frame = np.full((180, 320, 3), 30, np.uint8)
        if i >= 28:
            cv2.rectangle(frame, (10, 60), (200, 80), (255, 255, 255), -1)
        writer.write(frame)
    writer.release()
    log = {"task_instruction": "Check your current directory.", "platform": "Bash",
           "action_log": [{"action_type": "TYPING", "timestamp": 1.0, "action_params": {"text": "pwd"}},
                          {"action_type": "PRESS", "timestamp": 2.0, "action_params": {"text": "Enter"}}]}
    monkeypatch.setattr(screen_effects, "default_ocr",
                        lambda: lambda img: [((0, 0, img.shape[1], img.shape[0]), "/home/user", 0.9)]
                        if img.max() > 200 else [])

    r = await client.post(
        "/api/v1/videos/upload",
        files={"file": ("clip.mp4", video.read_bytes(), "video/mp4"),
               "action_log": ("action_log.json", json.dumps(log).encode(), "application/json")},
        params={"model_name": "svm"},
    )
    assert r.status_code == 201, r.text
    job_id = r.json()["job_id"]
    await client.post(f"/api/v1/jobs/{job_id}/run")

    r = await client.post(f"/api/v1/knowledge/sop/{job_id}")
    assert r.status_code == 200, r.text
    sop = r.json()
    assert sop["platform"] == "Bash" and sop["source_recording"] == "clip.mp4" and sop["generated_at"]
    assert sop["purpose"] == "Check your current directory."
    (step,) = sop["steps"]
    assert step["title"] == "Typed `pwd` and pressed Enter."
    assert step["screen_output"] == ["/home/user"]
    assert 0.6 <= step["delay_s"] <= 1.0
