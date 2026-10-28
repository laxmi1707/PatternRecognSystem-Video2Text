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
the detector has already processed (cache/demo_v6/<App>_<task>.json, matched
by file hash) is answered from that run at once. The detector is the `detector`
package (typing + clicks found with the pointer CNN).

    python sop_detector_service.py            port 8100; the frontend's dev server
                                              proxies /sop-detector to it
    python sop_detector_service.py index      write cache/demo_v6/index.json (video
                                              hash -> stored run), so stored runs are
                                              found without the videos (the container)

Settings from the environment, for the container (deploy/sop-detector):
SOP_DETECTOR_HOST (127.0.0.1), SOP_DETECTOR_PORT (8100), SOP_DETECTOR_THREADS (12),
SOP_DETECTOR_UPLOADS, ALLOWED_ORIGINS (JSON list; the local dev server by default).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import threading
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from v2k.env import CACHE, limit_cpu  # noqa: E402

if __name__ == "__main__":
    limit_cpu(int(os.environ.get("SOP_DETECTOR_THREADS", "12")))

from fastapi import FastAPI, File, HTTPException, UploadFile  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

STORED = CACHE / "demo_v6"
INDEX = STORED / "index.json"
UPLOADS = Path(os.environ.get("SOP_DETECTOR_UPLOADS", str(CACHE / "sop_service" / "uploads")))
HOST = os.environ.get("SOP_DETECTOR_HOST", "127.0.0.1")
PORT = int(os.environ.get("SOP_DETECTOR_PORT", "8100"))
ORIGINS = json.loads(os.environ.get("ALLOWED_ORIGINS", '["http://localhost:5173", "http://127.0.0.1:5173"]'))

app = FastAPI(title="SOP detector")
app.add_middleware(CORSMiddleware, allow_origins=ORIGINS, allow_methods=["GET", "POST", "OPTIONS"],
                   allow_headers=["*"])
jobs: dict[str, dict] = {}
one_at_a_time = threading.Lock()


def sha1(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_index() -> None:
    """index.json: {video sha1: stored run file}, from the videos on this machine."""
    index = {}
    for js in sorted(STORED.glob("*_*.json")):
        app_, tid = js.stem.rsplit("_", 1)
        video = ROOT / "data" / "VideoCUA" / app_ / tid / "video" / "video.mp4"
        if video.exists():
            index[sha1(video)] = js.name
    INDEX.write_text(json.dumps(index, indent=1), encoding="utf-8")
    print(f"{len(index)} stored runs -> {INDEX}")


def stored_run(digest: str) -> dict | None:
    """A stored detector run of the same video, if there is one."""
    if INDEX.exists():
        name = json.loads(INDEX.read_text(encoding="utf-8")).get(digest)
        if name and (STORED / name).exists():
            return json.loads((STORED / name).read_text(encoding="utf-8"))
    for js in STORED.glob("*_*.json"):
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
                import detector
                result = detector.run(
                    job["path"], lambda pct, stage: job.update(progress_pct=pct, stage=stage))
        job.update(status="completed", progress_pct=100, stage="done", result=_public(result))
    except Exception as e:  # shown in the frontend's panel
        job.update(status="failed", stage="failed", error=str(e))


@app.get("/sop-detector/health")
def health():
    return {"status": "ok", "busy": one_at_a_time.locked()}


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
    if sys.argv[1:] == ["index"]:
        write_index()
    else:
        import uvicorn
        uvicorn.run(app, host=HOST, port=PORT)
