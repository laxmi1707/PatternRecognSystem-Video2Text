from typing import Literal

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Base for schemas that must serialize as camelCase to match the frontend's
    AnalysisResult/WorkflowStep types (src/types/analysis.ts) exactly."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class WorkflowStep(CamelModel):
    n: int
    time: str
    title: str
    description: str


class AnalysisResult(CamelModel):
    id: str
    name: str
    date: str
    duration: str
    step_count: int
    status: Literal["Complete"]
    video_url: str | None = None
    summary: str
    steps: list[WorkflowStep]
    # One of the 10 classes in ReadMe.md's "Target Classes" list. The stub
    # assigns this deterministically from the filename -- the real classifier
    # (app/ml/ on feat/pattern-recognition) will replace it once it's wired up.
    category: str


class VideoUploadResponse(BaseModel):
    id: str


class JobStatusResponse(CamelModel):
    status: Literal["processing", "complete", "failed"]
    progress: float
    error: str | None = None
