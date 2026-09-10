from pydantic import BaseModel


class ModelComparisonRow(BaseModel):
    model_name: str
    tier: str
    accuracy: float
    precision_macro: float
    recall_macro: float
    f1_macro: float
    auc_macro: float
    latency_ms: float


class EvalReportResponse(BaseModel):
    comparison_table: list[ModelComparisonRow]
    generated_at: str


class CVResultRow(BaseModel):
    model_name: str
    tier: str
    n_folds: int
    mean_accuracy: float
    std_accuracy: float
    mean_f1: float
    std_f1: float
    mean_auc: float
    std_auc: float
    mean_latency_ms: float


class CVReportResponse(BaseModel):
    results: list[CVResultRow]


class AvailableModelsResponse(BaseModel):
    models: list[str]
    tiers: dict[str, list[str]]
