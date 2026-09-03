from fastapi import APIRouter

from app.schemas.evaluation import (
    EvalReportResponse,
    ModelComparisonRow,
    CVReportResponse,
    CVResultRow,
    AvailableModelsResponse,
)
from app.services.ml_service import ml_service

router = APIRouter(prefix="/api/v1/evaluation", tags=["evaluation"])


@router.get("/models", response_model=AvailableModelsResponse)
async def list_models():
    return {
        "models": ml_service.list_models(),
        "tiers": {
            "tier1": ml_service.list_by_tier("tier1"),
            "tier2": ml_service.list_by_tier("tier2"),
            "tier3": ml_service.list_by_tier("tier3"),
        },
    }


@router.post("/run", response_model=EvalReportResponse)
async def run_evaluation():
    report = ml_service.run_evaluation()
    return {
        "comparison_table": [
            ModelComparisonRow(
                model_name=m.model_name,
                tier=m.tier,
                accuracy=m.accuracy,
                precision_macro=m.precision_macro,
                recall_macro=m.recall_macro,
                f1_macro=m.f1_macro,
                auc_macro=m.auc_macro,
                latency_ms=m.latency_ms,
            )
            for m in report.comparison_table
        ],
        "generated_at": report.generated_at,
    }


@router.post("/cross-validation", response_model=CVReportResponse)
async def run_cross_validation():
    results = ml_service.run_cross_validation()
    return {
        "results": [
            CVResultRow(
                model_name=r.model_name,
                tier=r.tier,
                n_folds=r.n_folds,
                mean_accuracy=r.mean_accuracy,
                std_accuracy=r.std_accuracy,
                mean_f1=r.mean_f1,
                std_f1=r.std_f1,
                mean_auc=r.mean_auc,
                std_auc=r.std_auc,
                mean_latency_ms=r.mean_latency_ms,
            )
            for r in results
        ],
    }
