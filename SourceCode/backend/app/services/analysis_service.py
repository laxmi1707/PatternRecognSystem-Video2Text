import time
import uuid
import zlib
from dataclasses import dataclass, field
from typing import Literal

from app.schemas.analysis import ClassificationResult, SopReport, WorkflowStep

# Stub: no real video processing yet. Progress is simulated purely from elapsed
# wall-clock time so the frontend has a real endpoint to poll against. Swap the
# internals of get_status/get_result for a real pipeline (video_processing/ml/rag)
# later -- the JobStatusResponse/ClassificationResult/SopReport contracts are
# what the frontend actually depends on.
SIMULATED_DURATION_SECONDS = 3.0

# Matches ReadMe.md's "Target Classes (10)" list for the multi-tier classifier.
LABELS = [
    "git_operations", "docker_workflow", "kubernetes_ops", "terraform_iac",
    "aws_console", "jenkins_ci_cd", "coding_editing", "debugging",
    "documentation", "other",
]

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

_SAMPLE_SUMMARY = (
    "The recording shows a developer pulling the latest changes, "
    "installing dependencies, and verifying the app in the browser."
)


def _fake_prediction(filename: str) -> tuple[str, float, dict[str, float]]:
    """Deterministic per filename so the same job always gets the same
    label/confidence -- not a real classifier, just enough to demo the shape."""
    label = LABELS[zlib.crc32(filename.encode()) % len(LABELS)]
    confidence = round(0.55 + (zlib.crc32(filename.encode()) % 41) / 100, 4)
    others = [lbl for lbl in LABELS if lbl != label]
    weights = [(zlib.crc32(f"{filename}:{lbl}".encode()) % 100) + 1 for lbl in others]
    total_weight = sum(weights)
    remaining = round(1.0 - confidence, 4)
    probabilities = {label: confidence}
    for lbl, weight in zip(others, weights):
        probabilities[lbl] = round(remaining * weight / total_weight, 4)
    return label, confidence, probabilities


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

    def _require_completed_job(self, job_id: str) -> _Job:
        job = self._jobs.get(job_id)
        if job is None:
            raise JobNotFound(job_id)
        job_status, _ = self._progress(job)
        if job_status != "complete":
            raise JobNotReady(job_id)
        return job

    def get_result(self, job_id: str) -> ClassificationResult:
        job = self._require_completed_job(job_id)
        return self._to_result(job)

    def get_sop_report(self, job_id: str) -> SopReport:
        """Prototype SOP writeup -- not produced by a real LLM/RAG stage yet
        (ReadMe.md timeline: Oct 15). Same canned content for every job."""
        self._require_completed_job(job_id)
        return SopReport(summary=_SAMPLE_SUMMARY, steps=_SAMPLE_STEPS)

    def list_results(self) -> list[ClassificationResult]:
        """Completed jobs, most recently started first."""
        jobs = sorted(self._jobs.values(), key=lambda j: j.started_at, reverse=True)
        return [self._to_result(job) for job in jobs if self._progress(job)[0] == "complete"]

    def _to_result(self, job: _Job) -> ClassificationResult:
        label, confidence, probabilities = _fake_prediction(job.filename)
        return ClassificationResult(
            id=job.id,
            name=job.filename,
            date="Today",
            duration=_SAMPLE_STEPS[-1].time.split("-")[1],
            status="Complete",
            video_url=None,
            label=label,
            confidence=confidence,
            probabilities=probabilities,
        )


analysis_service = AnalysisService()
