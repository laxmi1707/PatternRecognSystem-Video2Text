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


class ModelSummary(BaseModel):
    model_name: str
    tier: str
    avg_confidence: float
    latency_ms: float


class JobResultsResponse(BaseModel):
    job_id: int
    status: str
    results: list[ClassificationResult]
    model_comparison: list[ModelSummary] = []
    best_model: str | None = None
