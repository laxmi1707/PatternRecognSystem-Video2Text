import time
import uuid
from dataclasses import dataclass, field
from typing import Literal

from app.schemas.analysis import AnalysisResult, WorkflowStep

# Stub: no real video processing yet. Progress is simulated purely from elapsed
# wall-clock time so the frontend has a real endpoint to poll against. Swap the
# internals of get_status/get_result for a real pipeline (video_processing/ml/rag)
# later -- the JobStatusResponse/AnalysisResult contracts are what the frontend
# actually depends on.
SIMULATED_DURATION_SECONDS = 3.0

_SAMPLE_STEPS = [
    WorkflowStep(
        n=1, time="0:00-0:07", title="Opened the code editor",
        description="The project folder loads in the editor with the file tree visible in the sidebar.",
    ),
    WorkflowStep(
        n=2, time="0:07-0:16", title="Opened the integrated terminal",
        description="A terminal panel opens at the bottom of the editor window.",
    ),
    WorkflowStep(
        n=3, time="0:16-0:29", title="Ran a shell command",
        description='"git pull origin main" is typed and run, pulling the latest changes.',
    ),
    WorkflowStep(
        n=4, time="0:29-0:58", title="Installed dependencies",
        description='"npm install" runs in the terminal, updating the project\'s packages.',
    ),
]


class JobNotFound(Exception):
    """No job exists with the given id."""


class JobNotReady(Exception):
    """The job exists but hasn't finished processing yet."""


@dataclass
class _Job:
    id: str
    filename: str
    started_at: float = field(default_factory=time.monotonic)


class AnalysisService:
    def __init__(self) -> None:
        self._jobs: dict[str, _Job] = {}

    def create(self, filename: str) -> str:
        job_id = uuid.uuid4().hex
        self._jobs[job_id] = _Job(id=job_id, filename=filename)
        return job_id

    def _progress(self, job: _Job) -> tuple[Literal["processing", "complete"], float]:
        elapsed = time.monotonic() - job.started_at
        progress = min(100.0, (elapsed / SIMULATED_DURATION_SECONDS) * 100)
        return ("complete", 100.0) if progress >= 100 else ("processing", progress)

    def get_status(self, job_id: str) -> tuple[Literal["processing", "complete"], float]:
        job = self._jobs.get(job_id)
        if job is None:
            raise JobNotFound(job_id)
        return self._progress(job)

    def get_result(self, job_id: str) -> AnalysisResult:
        job = self._jobs.get(job_id)
        if job is None:
            raise JobNotFound(job_id)
        job_status, _ = self._progress(job)
        if job_status != "complete":
            raise JobNotReady(job_id)

        return AnalysisResult(
            id=job.id,
            name=job.filename,
            date="Today",
            step_count=len(_SAMPLE_STEPS),
            duration=_SAMPLE_STEPS[-1].time.split("-")[1],
            status="Complete",
            video_url=None,
            summary=(
                "The recording shows a developer pulling the latest changes, "
                "installing dependencies, and verifying the app in the browser."
            ),
            steps=_SAMPLE_STEPS,
        )


analysis_service = AnalysisService()
