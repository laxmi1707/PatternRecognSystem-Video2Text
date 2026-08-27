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


async def test_unknown_analysis_returns_404(client: AsyncClient):
    resp = await client.get("/api/v1/analyses/does-not-exist")
    assert resp.status_code == 404


async def test_upload_then_poll_to_completion(client: AsyncClient):
    files = {"file": ("clip.mp4", b"fake video bytes", "video/mp4")}
    create_resp = await client.post("/api/v1/analyses", files=files)
    assert create_resp.status_code == 202
    job_id = create_resp.json()["id"]

    status_resp = await client.get(f"/api/v1/analyses/{job_id}")
    assert status_resp.status_code == 200
    body = status_resp.json()
    assert body["status"] in ("processing", "complete")

    await asyncio.sleep(0.1)

    final_resp = await client.get(f"/api/v1/analyses/{job_id}")
    final = final_resp.json()
    assert final["status"] == "complete"
    assert final["progress"] == 100.0
    result = final["result"]
    assert result["name"] == "clip.mp4"
    assert result["stepCount"] == len(result["steps"])
    assert result["status"] == "Complete"
