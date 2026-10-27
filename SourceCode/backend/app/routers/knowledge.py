from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.knowledge.sop_generator import SOPGenerator
from app.knowledge.runbook_generator import RunbookGenerator
from app.knowledge import report_generator, anomaly_detector
from app.models.video import Video
from app.services import job_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])

sop_gen = SOPGenerator()
runbook_gen = RunbookGenerator()

# Tier priority for selecting the best model result per segment
_TIER_PRIORITY = {"decision": -1, "tier3": 0, "tier2": 1, "tier1": 2}
_MODEL_TIER = {
    "decision": "decision",
    "voting": "tier3", "stacking": "tier3", "late_fusion": "tier3",
    "mlp": "tier2", "cnn1d": "tier2", "lstm": "tier2", "transformer": "tier2",
    "workflow_lstm": "tier2", "workflow_transformer": "tier2",
    "svm": "tier1", "naive_bayes": "tier1", "decision_tree": "tier1",
    "random_forest": "tier1", "knn": "tier1", "xgboost": "tier1", "lightgbm": "tier1",
}


def _best_segments(results) -> list[dict]:
    """Pick one row per segment_index using tier priority then confidence."""
    by_segment: dict[int, object] = {}
    for r in results:
        idx = r.segment_index
        if idx not in by_segment:
            by_segment[idx] = r
        else:
            existing = by_segment[idx]
            ep = _TIER_PRIORITY.get(_MODEL_TIER.get(existing.model_name, ""), 99)
            rp = _TIER_PRIORITY.get(_MODEL_TIER.get(r.model_name, ""), 99)
            if rp < ep or (rp == ep and r.confidence > existing.confidence):
                by_segment[idx] = r
    segs = []
    for r in [by_segment[k] for k in sorted(by_segment)]:
        probs = r.probabilities or {}
        # OCR text is stored in probs['_ocr'] — use any result row for this segment
        ocr = probs.get("_ocr", "")
        segs.append({
            "start_time": r.start_time,
            "end_time": r.end_time,
            "predicted_label": r.predicted_label,
            "confidence": r.confidence,
            "ocr_text": ocr,
            "operations": list(probs.get("_operations") or []),
        })
    return segs


_ECLIPSE_OCR_KEYS = [
    "eclipse", "echpse", "echpze", "ccliosc", "ccipre", "idipre",
    "worecpece", "worerpace", "woricpoce", "worespece", "window help",
]


def _detect_platform(ocr_texts: list[str], fallback: str) -> str:
    """Detect IDE/platform from OCR text; returns fallback if nothing recognised."""
    if fallback != "Screen Recording":
        return fallback
    all_ocr = " ".join(ocr_texts).lower()
    if any(kw in all_ocr for kw in _ECLIPSE_OCR_KEYS):
        return "Eclipse IDE"
    if any(kw in all_ocr for kw in ["vscode", "visual studio code"]):
        return "VS Code"
    if any(kw in all_ocr for kw in ["intellij", "pycharm"]):
        return "IntelliJ / PyCharm"
    if any(kw in all_ocr for kw in ["parallels", "ubuntu", "bash", "terminal", "gnome-terminal", "konsole", "zsh", "$ ", "% "]):
        return "Bash Terminal"
    if any(kw in all_ocr for kw in ["powershell", "cmd.exe", "windows terminal", "c:\\", "ps c:\\"]):
        return "PowerShell / CMD"
    if any(kw in all_ocr for kw in ["docker", "kubectl", "helm"]):
        return "Terminal"
    return fallback


def _load_action_log(action_log_path: str | None) -> dict:
    """Load action log JSON; return empty dict on failure."""
    if not action_log_path:
        return {}
    p = Path(action_log_path)
    if not p.exists():
        return {}
    try:
        with open(p) as f:
            return json.load(f)
    except Exception:
        return {}


def _actions_in_range(action_log: dict, start: float, end: float) -> list[str]:
    """Return human-readable action strings within a time range."""
    events = []
    for action in action_log.get("action_log", []):
        t = action.get("timestamp", -1)
        if start <= t <= end:
            atype = action.get("action_type", "")
            params = action.get("action_params", {})
            if atype == "CLICK":
                text = params.get("text", "")
                events.append(f"Click{' ' + text if text else ''}")
            elif atype == "TYPE":
                typed = params.get("text", "")[:40]
                events.append(f'Type "{typed}"')
            elif atype == "SCROLL":
                events.append("Scroll")
            elif atype == "KEY":
                events.append(f"Press {params.get('text', '')}")
            elif atype not in ("MOVE_TO",):
                events.append(atype.replace("_", " ").title())
    return events


class SOPResponse(BaseModel):
    title: str
    purpose: str
    prerequisites: list[str]
    steps: list[dict]
    expected_outcome: str
    troubleshooting: list[str]
    # Set for action-based SOPs (recordings with an action log)
    platform: str = ""
    source_recording: str = ""
    generated_at: str = ""


class RunbookResponse(BaseModel):
    title: str
    description: str
    when_to_use: str
    prerequisites: list[str]
    steps: list[dict]
    verification: list[str]
    rollback: list[str]


_LABEL_TITLES = {
    "coding_editing":  "Code Editing Session",
    "terminal_ops":    "Terminal Operations",
    "debugging":       "Debugging Session",
    "git_operations":  "Git Operations",
    "docker_workflow": "Docker Workflow",
    "web_browsing":    "Web Browsing Session",
    "system_config":   "System Configuration",
    "aws_console":     "AWS Console Operations",
    "kubernetes_ops":  "Kubernetes Operations",
    "terraform_iac":   "Terraform Infrastructure Setup",
    "jenkins_ci_cd":   "CI/CD Pipeline",
    "documentation":   "Documentation Session",
}


def _title_from_labels(segs: list[dict], plat: str, job_id: int) -> str:
    """Derive a title from the classified activity labels when no action_log is available.

    Module level because both the SOP and the runbook endpoints use it.
    """
    label_counts: dict[str, int] = {}
    for s in segs:
        lbl = s.get("predicted_label", "other")
        label_counts[lbl] = label_counts.get(lbl, 0) + 1
    if not label_counts:
        return f"Screen Activity Analysis #{job_id}"
    dominant = max(label_counts, key=label_counts.__getitem__)
    activity_title = _LABEL_TITLES.get(dominant, dominant.replace("_", " ").title())
    return f"{activity_title} on {plat}" if plat and plat != "Screen Recording" else activity_title


@router.post("/sop/{job_id}", response_model=SOPResponse)
async def generate_sop(job_id: int, db: AsyncSession = Depends(get_db)):
    job = await job_service.get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Job not yet completed")

    results = await job_service.get_job_results(db, job_id)
    if not results:
        raise HTTPException(status_code=404, detail="No results found")

    # Load video metadata for task context
    video_result = await db.execute(select(Video).where(Video.id == job.video_id))
    video = video_result.scalar_one_or_none()

    # Auto-detect action_log.json next to the video file (dataset videos have one)
    action_log_path = video.action_log_path if video else None
    if not action_log_path and video and video.file_path:
        candidate = Path(video.file_path).parent / "action_log.json"
        if candidate.exists():
            action_log_path = str(candidate)

    action_log = _load_action_log(action_log_path)

    raw_filename = video.original_filename if video else ""
    # "video.mp4" is the generic CUA dataset name — not useful as a title
    generic_names = {"video.mp4", "video", "recording.mp4", "screen.mp4"}

    platform = action_log.get("platform") or "Screen Recording"

    # One best-model row per segment
    segments = _best_segments(results)

    task_instruction = (
        action_log.get("task_instruction")
        or (raw_filename if raw_filename and raw_filename.lower() not in generic_names else None)
        or _title_from_labels(segments, platform, job_id)
    )

    video_file = Path(video.file_path) if video and video.file_path else None
    if action_log.get("action_log") and video_file and video_file.exists():
        # One step per user action, with what the screen showed afterwards. OCR of the
        # frames around every action is slow CPU work, so it runs off the event loop.
        from app.knowledge.screen_effects import capture_screen_effects, user_actions

        actions = await asyncio.to_thread(
            capture_screen_effects, video_file, user_actions(action_log["action_log"])
        )
        sop = sop_gen.generate_from_actions(
            task_instruction=task_instruction,
            platform=platform,
            actions=actions,
            source_recording=raw_filename or video_file.name,
            generated_at=datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M SGT"),
        )
    else:
        # No action log: one step per classified activity segment.
        ocr_texts = []
        for seg in segments:
            ocr = seg.get("ocr_text", "").strip()
            if not ocr:
                actions_text = _actions_in_range(action_log, seg["start_time"], seg["end_time"])
                ocr = "; ".join(actions_text)
            ocr_texts.append(ocr)

        sop = sop_gen.generate_from_segments(
            task_instruction=task_instruction,
            platform=platform,
            segments=segments,
            ocr_texts=ocr_texts,
        )

    return SOPResponse(
        title=sop.title,
        purpose=sop.purpose,
        prerequisites=sop.prerequisites,
        steps=[
            {
                "number": s.number,
                "title": s.title,
                "description": s.description,
                "time_range": s.time_range,
                "delay_s": s.delay_s,
                "screen_output": s.screen_output,
                "screen_removed": s.screen_removed,
                "risk_level": s.risk_level,
                "risk_reason": s.risk_reason,
            }
            for s in sop.steps
        ],
        expected_outcome=sop.expected_outcome,
        troubleshooting=sop.troubleshooting,
        platform=sop.platform,
        source_recording=sop.source_recording,
        generated_at=sop.generated_at,
    )


@router.post("/runbook/{job_id}", response_model=RunbookResponse)
async def generate_runbook(job_id: int, db: AsyncSession = Depends(get_db)):
    job = await job_service.get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Job not yet completed")

    results = await job_service.get_job_results(db, job_id)
    if not results:
        raise HTTPException(status_code=404, detail="No results found")

    # Load video metadata
    video_result = await db.execute(select(Video).where(Video.id == job.video_id))
    video = video_result.scalar_one_or_none()

    action_log_path = video.action_log_path if video else None
    if not action_log_path and video and video.file_path:
        candidate = Path(video.file_path).parent / "action_log.json"
        if candidate.exists():
            action_log_path = str(candidate)

    action_log = _load_action_log(action_log_path)

    raw_filename = video.original_filename if video else ""
    generic_names = {"video.mp4", "video", "recording.mp4", "screen.mp4"}
    platform = action_log.get("platform") or "Screen Recording"

    # One best-model row per segment
    segments = _best_segments(results)
    total_duration = segments[-1]["end_time"] - segments[0]["start_time"] if segments else 0

    task_instruction = (
        action_log.get("task_instruction")
        or (raw_filename if raw_filename and raw_filename.lower() not in generic_names else None)
        or _title_from_labels(segments, platform, job_id)
    )

    ocr_texts_rb = [seg.get("ocr_text", "").strip() for seg in segments]
    detected_platform_rb = _detect_platform(ocr_texts_rb, platform)

    runbook = runbook_gen.generate_from_workflow(
        workflow_description=task_instruction,
        platform=detected_platform_rb,
        duration_seconds=total_duration,
        activity_sequence=segments,
        ocr_texts=ocr_texts_rb,
    )

    return RunbookResponse(
        title=runbook.title,
        description=runbook.description,
        when_to_use=runbook.when_to_use,
        prerequisites=runbook.prerequisites,
        steps=[
            {
                "number": s.number,
                "action": s.action,
                "details": s.details,
                "command": s.command,
            }
            for s in runbook.steps
        ],
        verification=runbook.verification,
        rollback=runbook.rollback,
    )


@router.post("/report/{job_id}")
async def export_report(job_id: int, db: AsyncSession = Depends(get_db)):
    job = await job_service.get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Job not yet completed")

    results = await job_service.get_job_results(db, job_id)
    if not results:
        raise HTTPException(status_code=404, detail="No results found")

    video_result = await db.execute(select(Video).where(Video.id == job.video_id))
    video = video_result.scalar_one_or_none()

    action_log_path = video.action_log_path if video else None
    if not action_log_path and video and video.file_path:
        candidate = Path(video.file_path).parent / "action_log.json"
        if candidate.exists():
            action_log_path = str(candidate)

    action_log = _load_action_log(action_log_path)
    raw_filename = video.original_filename if video else ""
    generic_names = {"video.mp4", "video", "recording.mp4", "screen.mp4"}
    platform = action_log.get("platform") or "Screen Recording"

    segments = _best_segments(results)

    # Add model_name to each segment dict for the report table
    by_segment_model: dict[int, str] = {}
    for r in results:
        idx = r.segment_index
        if idx not in by_segment_model:
            by_segment_model[idx] = r.model_name
    for i, seg in enumerate(segments):
        seg["model_name"] = by_segment_model.get(i, "")

    def _title_from_labels(segs: list[dict], plat: str) -> str:
        label_counts: dict[str, int] = {}
        for s in segs:
            lbl = s.get("predicted_label", "other")
            label_counts[lbl] = label_counts.get(lbl, 0) + 1
        if not label_counts:
            return f"Screen Activity Analysis #{job_id}"
        dominant = max(label_counts, key=label_counts.__getitem__)
        label_titles = {
            "coding_editing": "Code Editing Session",
            "terminal_ops": "Terminal Operations",
            "debugging": "Debugging Session",
            "git_operations": "Git Operations",
            "docker_workflow": "Docker Workflow",
            "web_browsing": "Web Browsing Session",
            "system_config": "System Configuration",
            "aws_console": "AWS Console Operations",
            "kubernetes_ops": "Kubernetes Operations",
            "terraform_iac": "Terraform Infrastructure Setup",
            "jenkins_ci_cd": "CI/CD Pipeline",
            "documentation": "Documentation Session",
        }
        activity_title = label_titles.get(dominant, dominant.replace("_", " ").title())
        return f"{activity_title} on {plat}" if plat and plat != "Screen Recording" else activity_title

    task_instruction = (
        action_log.get("task_instruction")
        or (raw_filename if raw_filename and raw_filename.lower() not in generic_names else None)
        or _title_from_labels(segments, platform)
    )

    ocr_texts = [seg.get("ocr_text", "").strip() for seg in segments]
    detected_platform = _detect_platform(ocr_texts, platform)

    # Generate SOP steps for the report
    from app.knowledge.sop_generator import SOPGenerator as _SOPGen
    _sop = _SOPGen().generate_from_segments(
        task_instruction=task_instruction,
        platform=detected_platform,
        segments=segments,
        ocr_texts=ocr_texts,
    )
    sop_steps = [
        {"number": s.number, "title": s.title, "description": s.description, "time_range": s.time_range}
        for s in _sop.steps
    ]

    video_path = video.file_path if video else None

    # Run anomaly detection on OCR text + action_log typed commands per segment
    anomalies_by_segment: dict[int, list] = {}
    for i, seg in enumerate(segments):
        # Combine OCR text with actual typed commands from action_log for this time range
        ocr = seg.get("ocr_text", "")
        action_texts = " ".join(
            a.get("action_params", {}).get("text", "")
            for a in action_log.get("action_log", [])
            if seg["start_time"] <= a.get("timestamp", -1) <= seg["end_time"]
            and a.get("action_type") in ("TYPING", "TYPE", "PRESS", "HOTKEY", "KEY_DOWN")
        )
        combined = f"{ocr} {action_texts}".strip()
        found = anomaly_detector.detect(combined)
        if found:
            anomalies_by_segment[i] = found

    try:
        docx_bytes = report_generator.generate_report(
            job_id=job_id,
            video_path=video_path,
            segments=segments,
            task_instruction=task_instruction,
            platform=detected_platform,
            sop_steps=sop_steps,
            anomalies_by_segment=anomalies_by_segment if anomalies_by_segment else None,
        )
    except Exception as exc:
        logger.exception("Report generation failed: %s", exc)
        raise HTTPException(status_code=500, detail="Report generation failed") from exc

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="report_{job_id}.docx"'},
    )
