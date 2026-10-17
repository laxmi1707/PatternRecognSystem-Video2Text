"""The bare-video SOP detector as a small HTTP service for the team frontend.

The frontend sends the uploaded video here as well as to the backend, and shows
the steps this returns beside the backend's SOP (each SOP phase lists the clicks
and typing that fall in its time range). The backend is not changed.

    POST /sop-detector/jobs          multipart "file"  -> {"job_id": ...}
    GET  /sop-detector/jobs/{id}     {"status": running | completed | failed,
                                      "progress_pct", "stage", "error",
                                      "result": {"app", "app_confidence",
                                                 "duration", "steps": [
                                                 {"t", "action", "text"}, ...]}}

One video is processed at a time (a few minutes on CPU). A video that
bare_sop_v1.py has already processed (cache/demo_v1/<App>_<task>.json, matched
by file hash) is answered from that run at once.

    python sop_detector_service.py            port 8100; the frontend's dev server
                                              proxies /sop-detector to it
"""
from __future__ import annotations

import hashlib
import json
import sys
import threading
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from v2k.env import CACHE, limit_cpu  # noqa: E402

if __name__ == "__main__":
    limit_cpu(12)

from fastapi import FastAPI, File, HTTPException, UploadFile  # noqa: E402

STORED = CACHE / "demo_v1"
UPLOADS = CACHE / "sop_service" / "uploads"
PORT = 8100

app = FastAPI(title="SOP detector")
jobs: dict[str, dict] = {}
one_at_a_time = threading.Lock()


def sha1(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def stored_run(digest: str) -> dict | None:
    """A stored bare_sop_v1 run of the same video, if there is one."""
    for js in STORED.glob("*.json"):
        app_, tid = js.stem.rsplit("_", 1)
        video = ROOT / "data" / "VideoCUA" / app_ / tid / "video" / "video.mp4"
        if video.exists() and sha1(video) == digest:
            return json.loads(js.read_text(encoding="utf-8"))
    return None


def _public(result: dict) -> dict:
    return {"app": result["app"], "app_confidence": result.get("app_confidence"),
            "duration": result.get("duration"),
            "steps": [{"t": s["t"], "action": s["action"], "text": s["text"]} for s in result["steps"]]}


def _work(job: dict) -> None:
    try:
        result = stored_run(job["sha1"])
        if result is None:
            job.update(progress_pct=1, stage="waiting for the previous video")
            with one_at_a_time:
                import bare_sop_v1
                result = bare_sop_v1.run(
                    job["path"], lambda pct, stage: job.update(progress_pct=pct, stage=stage))
        job.update(status="completed", progress_pct=100, stage="done", result=_public(result))
    except Exception as e:  # shown in the frontend's panel
        job.update(status="failed", stage="failed", error=str(e))


@app.post("/sop-detector/jobs")
async def submit(file: UploadFile = File(...)):
    UPLOADS.mkdir(parents=True, exist_ok=True)
    job_id = uuid.uuid4().hex[:12]
    path = UPLOADS / f"{job_id}{Path(file.filename or 'video.mp4').suffix or '.mp4'}"
    path.write_bytes(await file.read())
    job = {"job_id": job_id, "path": path, "sha1": sha1(path), "status": "running",
           "progress_pct": 0, "stage": "starting", "result": None, "error": None}
    jobs[job_id] = job
    threading.Thread(target=_work, args=(job,), daemon=True).start()
    return {"job_id": job_id}


@app.get("/sop-detector/jobs/{job_id}")
def status(job_id: str):
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="No such detection job")
    return {k: job[k] for k in ("job_id", "status", "progress_pct", "stage", "result", "error")}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=PORT)
