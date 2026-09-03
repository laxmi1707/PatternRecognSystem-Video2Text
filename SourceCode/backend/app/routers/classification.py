import numpy as np
from fastapi import APIRouter, HTTPException

from app.schemas.classification import (
    ClassifyRequest,
    ClassifyBatchRequest,
    ClassificationResult,
    ClassifyBatchResponse,
)
from app.services.ml_service import ml_service

router = APIRouter(prefix="/api/v1/classification", tags=["classification"])


@router.post("/predict", response_model=ClassificationResult)
async def classify_single(req: ClassifyRequest):
    try:
        features = np.array([req.features])
        result = ml_service.classify(features, model_name=req.model_name)
        return result["results"][0]
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/predict/batch", response_model=ClassifyBatchResponse)
async def classify_batch(req: ClassifyBatchRequest):
    if not req.features:
        raise HTTPException(status_code=400, detail="Features list cannot be empty")
    try:
        features = np.array(req.features)
        result = ml_service.classify(features, model_name=req.model_name)
        return result
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
