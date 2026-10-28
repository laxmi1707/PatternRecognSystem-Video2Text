from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.knowledge.sop_generator import SOPGenerator
from app.knowledge.runbook_generator import RunbookGenerator
from app.services import job_service

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])

sop_gen = SOPGenerator()
runbook_gen = RunbookGenerator()


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

    segments = [
        {
            "start_time": r.start_time,
            "end_time": r.end_time,
            "predicted_label": r.predicted_label,
            "confidence": r.confidence,
        }
        for r in results
    ]

    sop = sop_gen.generate_from_segments(
        task_instruction=f"Analysis job #{job_id}",
        platform="Screen Recording",
        segments=segments,
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

    activity_sequence = [
        {
            "label": r.predicted_label,
            "start_time": r.start_time,
            "end_time": r.end_time,
            "confidence": r.confidence,
        }
        for r in results
    ]

    total_duration = max(r.end_time for r in results) - min(r.start_time for r in results)

    runbook = runbook_gen.generate_from_workflow(
        workflow_description=f"Analysis job #{job_id}",
        platform="Screen Recording",
        duration_seconds=total_duration,
        activity_sequence=activity_sequence,
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
