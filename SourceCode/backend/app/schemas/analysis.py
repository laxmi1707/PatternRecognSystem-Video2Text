from typing import Literal

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Base for schemas that must serialize as camelCase to match the frontend's
    types (src/types/analysis.ts) exactly."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class WorkflowStep(CamelModel):
    n: int
    time: str
    title: str
    description: str


class ClassificationResult(CamelModel):
    """Matches Eshwaran's real /jobs/{id}/results shape (label/confidence/
    probabilities) agreed on 2026-09-05 -- this is the classifier's raw
    output, not a narrative. See SopReport for the separate SOP writeup."""

    id: str
    name: str
    date: str
    duration: str
    status: Literal["Complete"]
    video_url: str | None = None
    label: str
    confidence: float
    probabilities: dict[str, float]


class SopReport(CamelModel):
    """The narrative writeup (summary + step-by-step breakdown), fetched
    separately via GET /jobs/{id}/sop. Prototype data until the real
    LLM/RAG generation stage exists (ReadMe.md timeline: Oct 15)."""

    summary: str
    steps: list[WorkflowStep]


class VideoUploadResponse(BaseModel):
    id: str


class JobStatusResponse(CamelModel):
    status: Literal["processing", "complete", "failed"]
    progress: float
    error: str | None = None
