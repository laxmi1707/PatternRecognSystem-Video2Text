import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services import analysis_service as analysis_service_module


@pytest.fixture(autouse=True)
def _fast_simulation(monkeypatch):
    # Keep the simulated "processing" window short so tests don't sleep for real.
    monkeypatch.setattr(analysis_service_module, "SIMULATED_DURATION_SECONDS", 0.05)


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def test_unknown_job_status_returns_404(client: AsyncClient):
    resp = await client.get("/api/v1/jobs/does-not-exist")
    assert resp.status_code == 404


async def test_unknown_job_results_returns_404(client: AsyncClient):
    resp = await client.get("/api/v1/jobs/does-not-exist/results")
    assert resp.status_code == 404


async def test_results_not_ready_returns_409(client: AsyncClient):
    files = {"file": ("clip.mp4", b"fake video bytes", "video/mp4")}
    upload_resp = await client.post("/api/v1/videos/upload", files=files)
    assert upload_resp.status_code == 202
    job_id = upload_resp.json()["id"]

    results_resp = await client.get(f"/api/v1/jobs/{job_id}/results")
    assert results_resp.status_code == 409


async def test_list_jobs_only_includes_completed(client: AsyncClient):
    files = {"file": ("clip.mp4", b"fake video bytes", "video/mp4")}
    upload_resp = await client.post("/api/v1/videos/upload", files=files)
    job_id = upload_resp.json()["id"]

    list_resp = await client.get("/api/v1/jobs")
    assert list_resp.status_code == 200
    assert job_id not in [item["id"] for item in list_resp.json()]

    await asyncio.sleep(0.1)

    list_resp = await client.get("/api/v1/jobs")
    ids = [item["id"] for item in list_resp.json()]
    assert job_id in ids


async def test_upload_then_poll_then_fetch_results(client: AsyncClient):
    files = {"file": ("clip.mp4", b"fake video bytes", "video/mp4")}
    upload_resp = await client.post("/api/v1/videos/upload", files=files)
    assert upload_resp.status_code == 202
    job_id = upload_resp.json()["id"]

    status_resp = await client.get(f"/api/v1/jobs/{job_id}")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] in ("processing", "complete")

    await asyncio.sleep(0.1)

    status_resp = await client.get(f"/api/v1/jobs/{job_id}")
    assert status_resp.json()["status"] == "complete"
    assert status_resp.json()["progress"] == 100.0

    results_resp = await client.get(f"/api/v1/jobs/{job_id}/results")
    assert results_resp.status_code == 200
    result = results_resp.json()
    assert result["name"] == "clip.mp4"
    assert result["stepCount"] == len(result["steps"])
    assert result["status"] == "Complete"
