from pydantic import BaseModel

from app.schemas.classification import ClassificationResult


class JobResponse(BaseModel):
    id: int
    video_id: int
    status: str
    job_type: str
    model_name: str | None
    progress_pct: float
    error_message: str | None


class JobResultsResponse(BaseModel):
    job_id: int
    status: str
    results: list[ClassificationResult]
