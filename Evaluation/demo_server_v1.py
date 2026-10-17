"""Local demo: Eshwaran's frontend (main, unmodified) on top of the bare-video SOP detector.

Implements only the endpoints SourceCode/frontend calls, with his response
shapes (app/routers/knowledge.py SOPResponse / RunbookResponse), so his UI runs
as it is. Nothing here touches the team repo or its backend.

    POST /api/v1/videos/upload         save the file, open a job
    POST /api/v1/jobs/{id}/run         run bare_sop_v1 on it (one at a time)
    GET  /api/v1/jobs/{id}             progress for his analyzing page
    GET  /api/v1/jobs/{id}/results     one classification row: stage 1's application
    POST /api/v1/knowledge/sop/{id}    the detector's Click / Type steps as his SOP
    POST /api/v1/knowledge/runbook/{id}
    GET  /api/v1/videos/ , /api/v1/evaluation/models , /health

A video that bare_sop_v1 has already processed (cache/demo_v1/<App>_<task>.json,
matched by file hash) is answered from that run, its progress replayed in a few
seconds; any other video is processed live, which takes a few minutes on CPU.

    python demo_server_v1.py        then, in SourceCode/frontend: npm run dev
"""
from __future__ import annotations

import hashlib
import json
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from v2k.env import CACHE, limit_cpu  # noqa: E402

if __name__ == "__main__":
    limit_cpu(12)

from fastapi import FastAPI, File, HTTPException, UploadFile  # noqa: E402

DEMO = CACHE / "demo_v1"
UPLOADS = DEMO / "uploads"
ACTIVITY = {"bash": "terminal_ops", "vscode": "coding_editing", "eclipse": "coding_editing",
            "netbeans": "coding_editing", "kdevelop": "coding_editing", "pycharm": "coding_editing",
            "chromium": "web_browsing", "mozillafirefox": "web_browsing"}
STAGES = [(5, "reading the screen (OCR, one frame per second)"),
          (28, "identifying the application and filtering typed text"),
          (45, "tracking the mouse pointer"),
          (70, "reading the controls under the pointer"),
          (90, "writing the SOP")]

app = FastAPI(title="Video2Knowledge SOP detector demo")
jobs: dict[int, dict] = {}
live_lock = threading.Lock()


def sha1(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def known_runs() -> dict[str, Path]:
    out = {}
    for js in DEMO.glob("*.json"):
        app_, tid = js.stem.rsplit("_", 1)
        video = ROOT / "data" / "VideoCUA" / app_ / tid / "video" / "video.mp4"
        if video.exists():
            out[sha1(video)] = js
    return out


KNOWN: dict[str, Path] = {}


def _work(job: dict) -> None:
    try:
        js = KNOWN.get(job["sha1"])
        if js is not None:
            for pct, stage in STAGES:
                job.update(progress_pct=pct, progress_stage=stage)
                time.sleep(1.2)
            job["result"] = json.loads(js.read_text(encoding="utf-8"))
            job["source"] = f"stored run of the same detector on this video ({js.name})"
        else:
            job.update(progress_pct=1, progress_stage="waiting for the previous video to finish")
            with live_lock:
                import bare_sop_v1
                job["result"] = bare_sop_v1.run(
                    job["path"], lambda pct, stage: job.update(progress_pct=pct, progress_stage=stage))
            job["source"] = "processed live"
        job.update(status="completed", progress_pct=100, progress_stage="analysis complete")
    except Exception as e:  # surface the reason on the analyzing page
        job.update(status="failed", progress_stage=f"failed: {e}", error_message=str(e))


def _job(job_id: int) -> dict:
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


def _done(job_id: int) -> dict:
    job = _job(job_id)
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not yet completed")
    return job


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/v1/videos/upload")
async def upload(file: UploadFile = File(...)):
    UPLOADS.mkdir(parents=True, exist_ok=True)
    jid = len(jobs) + 1
    path = UPLOADS / f"{jid}_{Path(file.filename or 'video.mp4').name}"
    path.write_bytes(await file.read())
    digest = sha1(path)
    if digest not in KNOWN:
        KNOWN.update(known_runs())          # pick up runs stored since start-up
    jobs[jid] = {"id": jid, "video_id": jid, "path": path, "filename": file.filename, "sha1": digest,
                 "status": "pending", "progress_pct": 0, "progress_stage": "uploaded",
                 "size": path.stat().st_size}
    return {"id": jid, "filename": path.name, "original_filename": file.filename, "status": "uploaded",
            "job_id": jid}


@app.post("/api/v1/jobs/{job_id}/run")
def run_job(job_id: int):
    job = _job(job_id)
    if job["status"] == "pending":
        job["status"] = "processing"
        threading.Thread(target=_work, args=(job,), daemon=True).start()
    return {"job_id": job_id, "status": job["status"]}


@app.get("/api/v1/jobs/{job_id}")
def job_status(job_id: int):
    job = _job(job_id)
    return {"id": job_id, "video_id": job["video_id"], "status": job["status"], "job_type": "sop_detector",
            "model_name": "sop-detector", "progress_pct": job["progress_pct"],
            "progress_stage": job["progress_stage"], "error_message": job.get("error_message")}


def _app_key(name: str) -> str:
    return "".join(c for c in name.lower() if c.isalnum())


@app.get("/api/v1/jobs/{job_id}/results")
def job_results(job_id: int):
    job = _done(job_id)
    r = job["result"]
    model = f"sop-detector (application: {r['app']})"
    return {"job_id": job_id, "status": "completed", "best_model": model, "model_comparison": [],
            "results": [{"label": ACTIVITY.get(_app_key(r["app"]), "other"),
                         "confidence": r["app_confidence"] or 0.0, "probabilities": {},
                         "model_name": model, "latency_ms": r.get("seconds_taken", 0) * 1000,
                         "start_time": 0.0, "end_time": r["duration"] or 0.0}]}


def _clock(t: float) -> str:
    return f"{t:.1f}s"


@app.post("/api/v1/knowledge/sop/{job_id}")
def sop(job_id: int):
    job = _done(job_id)
    r = job["result"]
    terminal = _app_key(r["app"]) == "bash"
    steps = []
    for i, s in enumerate(r["steps"], 1):
        if s["action"] == "Click":
            title = f"Click '{s['text']}'"
            desc = f"Click the control labelled \"{s['text']}\" (read under the mouse pointer)."
        else:
            title = f"Type \"{s['text']}\""
            desc = (f"Type the command \"{s['text']}\" in the terminal." if terminal
                    else f"Type \"{s['text']}\" into the field.")
        steps.append({"number": i, "title": title, "description": desc, "time_range": _clock(s["t"])})
    mins, secs = divmod(int(r["duration"] or 0), 60)
    return {
        "title": f"SOP: {r['app']} procedure ({mins}:{secs:02d} recording)",
        "purpose": (f"Reproduce the procedure shown in this {r['app']} screen recording. The application "
                    f"and every step below were recovered from the video alone; no action log was read."),
        "prerequisites": [f"Access to {r['app']}", "Required permissions and credentials"],
        "steps": steps,
        "expected_outcome": "The same end state as at the end of the recording.",
        "troubleshooting": [
            "Steps are read from the screen: on unseen recordings about half of them are real actions, "
            "so compare a step that looks wrong with the recording at its time.",
            "Keyboard shortcuts, Enter presses and drags are not detected yet.",
        ],
    }


@app.post("/api/v1/knowledge/runbook/{job_id}")
def runbook(job_id: int):
    job = _done(job_id)
    r = job["result"]
    steps = [{"number": i, "action": f"{s['action']} '{s['text']}'" if s["action"] == "Click" else "Type",
              "details": (f"At {_clock(s['t'])}, click the control labelled \"{s['text']}\"."
                          if s["action"] == "Click" else f"At {_clock(s['t'])}, type:"),
              "command": s["text"] if s["action"] == "Type" else ""}
             for i, s in enumerate(r["steps"], 1)]
    return {"title": f"Runbook: {r['app']} procedure",
            "description": f"Operational steps recovered from a {r['app']} screen recording, without an action log.",
            "when_to_use": "When repeating the task shown in the recording.",
            "prerequisites": [f"Access to {r['app']}"], "steps": steps,
            "verification": ["Compare the final screen with the end of the recording."], "rollback": []}


@app.get("/api/v1/videos/")
def videos():
    return [{"id": j["id"], "filename": j["path"].name, "original_filename": j["filename"],
             "file_size_bytes": j["size"], "duration_seconds": (j.get("result") or {}).get("duration"),
             "status": j["status"]} for j in jobs.values()]


@app.get("/api/v1/evaluation/models")
def models():
    return {"models": ["sop-detector"], "tiers": {}, "recommended": None}


if __name__ == "__main__":
    import uvicorn
    KNOWN.update(known_runs())
    print(f"{len(KNOWN)} stored runs: {', '.join(p.stem for p in KNOWN.values())}")
    uvicorn.run(app, host="127.0.0.1", port=8000)
