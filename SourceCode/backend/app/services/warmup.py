"""Load the slow parts of the pipeline at startup, so the first job does not wait for them.

Creating ml_service downloads the models from S3 and loads them; the EasyOCR reader
loads its detection and recognition models (~10 s). Both are cached for the life of the
process. A job that arrives while this is still running waits on the same import / reader
lock instead of loading a second copy.
"""
from __future__ import annotations

import logging
import time

logger = logging.getLogger(__name__)


def warm_up() -> None:
    t0 = time.perf_counter()
    try:
        from app.services.ml_service import ml_service

        logger.info(f"Warm-up: {len(ml_service._trained_models)} models ready")
    except Exception as e:  # warm-up is best effort; a job retries the load itself
        logger.warning(f"Warm-up: loading the models failed: {e}")

    try:
        import torch

        from app.pipeline.ocr_extractor import OCRExtractor

        OCRExtractor(use_gpu=torch.cuda.is_available())._get_reader()
    except Exception as e:
        logger.warning(f"Warm-up: loading the OCR reader failed: {e}")

    logger.info(f"Warm-up finished in {time.perf_counter() - t0:.1f}s")
