"""/sop-detector/*: forwarded to the SOP detector that runs beside the backend in its
container (app/routers/sop_detector.py, start.sh). The detector is replaced by an
httpx.MockTransport, so these tests need neither it nor the database."""
import httpx
import pytest
from fastapi import FastAPI

from app.config import settings
from app.routers import sop_detector

JOB_ID = "0123456789ab"


def make_app(handler) -> FastAPI:
    app = FastAPI()
    app.include_router(sop_detector.router)

    async def mock_detector():
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport, base_url="http://detector") as client:
            yield client

    app.dependency_overrides[sop_detector.detector_client] = mock_detector
    return app


async def call(app: FastAPI, method: str, url: str, **kwargs) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.request(method, url, **kwargs)


def not_running(request: httpx.Request) -> httpx.Response:
    raise httpx.ConnectError("connection refused", request=request)


@pytest.fixture
def no_api_key(monkeypatch):
    monkeypatch.setattr(settings, "api_key", "")


async def test_upload_reaches_the_detector_unchanged(no_api_key):
    seen = {}

    def detector(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["type"] = request.headers["content-type"]
        seen["body"] = request.content
        return httpx.Response(200, json={"job_id": JOB_ID})

    files = {"file": ("clip.mp4", b"fake video bytes", "video/mp4")}
    r = await call(make_app(detector), "POST", "/sop-detector/jobs", files=files)

    assert r.status_code == 200
    assert r.json() == {"job_id": JOB_ID}
    assert seen["path"] == "/sop-detector/jobs"
    assert seen["type"].startswith("multipart/form-data; boundary=")
    assert b"fake video bytes" in seen["body"]


async def test_job_status_comes_back_from_the_detector(no_api_key):
    job = {"job_id": JOB_ID, "status": "running", "progress_pct": 40, "stage": "clicks",
           "result": None, "error": None}

    def detector(request: httpx.Request) -> httpx.Response:
        assert request.url.path == f"/sop-detector/jobs/{JOB_ID}"
        return httpx.Response(200, json=job)

    r = await call(make_app(detector), "GET", f"/sop-detector/jobs/{JOB_ID}")
    assert r.status_code == 200
    assert r.json() == job


async def test_detector_errors_are_passed_on(no_api_key):
    def detector(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "No such detection job"})

    r = await call(make_app(detector), "GET", f"/sop-detector/jobs/{JOB_ID}")
    assert r.status_code == 404
    assert r.json() == {"detail": "No such detection job"}


async def test_a_malformed_job_id_never_reaches_the_detector(no_api_key):
    def detector(request: httpx.Request) -> httpx.Response:
        raise AssertionError(f"forwarded {request.url}")

    for job_id in ("not-a-job", "0123456789AB", "0123456789abc", "..%2Fhealth"):
        r = await call(make_app(detector), "GET", f"/sop-detector/jobs/{job_id}")
        assert r.status_code == 404, job_id


async def test_a_detector_that_is_not_running_answers_503(no_api_key):
    app = make_app(not_running)
    files = {"file": ("clip.mp4", b"x", "video/mp4")}
    assert (await call(app, "GET", "/sop-detector/health")).status_code == 503
    assert (await call(app, "POST", "/sop-detector/jobs", files=files)).status_code == 503
    assert (await call(app, "GET", f"/sop-detector/jobs/{JOB_ID}")).status_code == 503


async def test_a_video_over_the_limit_is_refused(no_api_key, monkeypatch):
    monkeypatch.setattr(sop_detector, "MAX_FILE_SIZE", 1000)

    def detector(request: httpx.Request) -> httpx.Response:
        raise AssertionError("an oversized upload was forwarded")

    files = {"file": ("clip.mp4", b"x" * 2000, "video/mp4")}
    r = await call(make_app(detector), "POST", "/sop-detector/jobs", files=files)
    assert r.status_code == 413


async def test_jobs_need_the_api_key_when_one_is_set(monkeypatch):
    monkeypatch.setattr(settings, "api_key", "secret")

    def detector(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/health"):
            return httpx.Response(200, json={"status": "ok", "busy": False})
        return httpx.Response(200, json={"job_id": JOB_ID})

    app = make_app(detector)
    files = {"file": ("clip.mp4", b"x", "video/mp4")}
    assert (await call(app, "POST", "/sop-detector/jobs", files=files)).status_code == 401
    assert (await call(app, "GET", f"/sop-detector/jobs/{JOB_ID}")).status_code == 401

    key = {"X-API-Key": "secret"}
    r = await call(app, "POST", "/sop-detector/jobs", files=files, headers=key)
    assert r.status_code == 200
    assert (await call(app, "GET", "/sop-detector/health")).status_code == 200
