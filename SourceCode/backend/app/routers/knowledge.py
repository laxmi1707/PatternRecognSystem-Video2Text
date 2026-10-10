from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.knowledge.sop_generator import SOPGenerator
from app.knowledge.runbook_generator import RunbookGenerator
from app.models.video import Video
from app.services import job_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])

sop_gen = SOPGenerator()
runbook_gen = RunbookGenerator()

# Tier priority for selecting the best model result per segment
_TIER_PRIORITY = {"tier3": 0, "tier2": 1, "tier1": 2}
_MODEL_TIER = {
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
    return [
        {
            "start_time": r.start_time,
            "end_time": r.end_time,
            "predicted_label": r.predicted_label,
            "confidence": r.confidence,
        }
        for r in [by_segment[k] for k in sorted(by_segment)]
    ]


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


class RunbookResponse(BaseModel):
    title: str
    description: str
    when_to_use: str
    prerequisites: list[str]
    steps: list[dict]
    verification: list[str]
    rollback: list[str]


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
    action_log = _load_action_log(video.action_log_path if video else None)

    task_instruction = action_log.get("task_instruction") or (
        video.original_filename if video else f"Analysis job #{job_id}"
    )
    platform = action_log.get("platform") or "Screen Recording"

    # One best-model row per segment
    segments = _best_segments(results)

    # Enrich each segment with action log events for meaningful descriptions
    ocr_texts = []
    for seg in segments:
        actions = _actions_in_range(action_log, seg["start_time"], seg["end_time"])
        ocr_texts.append("; ".join(actions) if actions else "")

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
            }
            for s in sop.steps
        ],
        expected_outcome=sop.expected_outcome,
        troubleshooting=sop.troubleshooting,
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
    action_log = _load_action_log(video.action_log_path if video else None)

    task_instruction = action_log.get("task_instruction") or (
        video.original_filename if video else f"Analysis job #{job_id}"
    )
    platform = action_log.get("platform") or "Screen Recording"

    # One best-model row per segment
    segments = _best_segments(results)
    total_duration = segments[-1]["end_time"] - segments[0]["start_time"] if segments else 0

    runbook = runbook_gen.generate_from_workflow(
        workflow_description=task_instruction,
        platform=platform,
        duration_seconds=total_duration,
        activity_sequence=segments,
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
