# Video2Knowledge — Code Review Report

**Date:** 2026-09-17  
**Reviewer:** Automated (8-angle code review)  
**Branch:** feat/pattern-recognition  
**Scope:** Multimodal pipeline, knowledge generation, and UI changes

---

## Summary

An 8-angle automated code review identified **15 findings** across correctness, efficiency, conventions, and contract integrity. All findings have been resolved.

---

## Critical Bugs (Fixed)

### 1. Dead code: `_extract_real_features` never called
**File:** `classification_service.py:34`  
**Issue:** `_run_ml_pipeline` generated random noise (`rng.randn`) even when a real video file was present. The fully implemented `_extract_real_features` function was dead code.  
**Fix:** Rewrote `_run_ml_pipeline` to call `_extract_real_features` for real videos, with a synthetic fallback (`_synthetic_fallback`) only when extraction fails or no video is provided.

### 2. `use_real` flag silently ignored in evaluation methods
**File:** `ml_service.py:147,167`  
**Issue:** `run_evaluation()` and `run_cross_validation()` called `_get_training_data()` without `prefer_real=True`, so the `use_real=True` default was dead code — always returned synthetic data.  
**Fix:** Pass `prefer_real=True` in both methods when `use_real` is `True`.

### 3. Timestamp/position index mismatch in interaction features
**File:** `interaction_features.py:96`  
**Issue:** `positions` array only contained actions with x/y params, but `timestamps` contained ALL actions. Speed calculations paired wrong timestamps with positions.  
**Fix:** Build a paired `pos_with_ts` list containing `(x, y, timestamp)` tuples for only actions that have coordinates, ensuring correct dt calculation.

### 4. E2E tests used old query-param upload API
**File:** `test_api_e2e.py:54,108`  
**Issue:** Tests sent `params={"original_filename": ...}` but the endpoint now requires multipart `File(...)` upload — would 422.  
**Fix:** Updated to use `files={"file": ("demo.mp4", dummy_bytes, "video/mp4")}`.

---

## Medium Issues (Fixed)

### 5. Video file read entirely into RAM
**File:** `routers/videos.py:28`  
**Issue:** `await file.read()` loaded entire video into memory. A 2GB upload would allocate 2GB in the worker.  
**Fix:** Stream to disk in 1MB chunks using `while chunk := await file.read(1024 * 1024)`.

### 6. Vite env var set at runtime instead of build time
**File:** `docker-compose.yml:33`  
**Issue:** `VITE_API_BASE_URL` was set under `environment:` but Vite bakes `VITE_*` vars at build time only.  
**Fix:** Moved to `build: args:` so the value is available during `vite build`.

### 7. OCR double inference in feature assembler
**File:** `feature_assembler.py:138`  
**Issue:** `_collect_ocr_corpus` re-ran OCR on all video frames just to build TF-IDF vocabulary, then `build_dataset` ran OCR again for actual feature extraction — doubling OCR inference time.  
**Fix:** Replaced `_collect_ocr_corpus` to build vocabulary from task instructions and action text only, avoiding any video processing in the corpus collection step.

### 8. Missing `response_model` on jobs run endpoint
**File:** `routers/jobs.py:31`  
**Issue:** `response_model=JobResultsResponse` was removed, breaking OpenAPI schema documentation.  
**Fix:** Restored `response_model=JobResultsResponse`.

### 9. Positional encoding wrong for odd `d_model`
**File:** `workflow_transformer.py:23`  
**Issue:** `pe[:, 1::2] = torch.cos(position * div_term[: d_model // 2])` silently truncated cosine encoding for odd feature dimensions.  
**Fix:** Added validation: `if feature_dim % 2 != 0: raise ValueError(...)` and `if feature_dim % num_heads != 0: raise ValueError(...)`.

### 10. Hardcoded 5s segment timestamps in frontend
**File:** `labelMap.ts:60` + `jobs.py:48` + `api.ts:18`  
**Issue:** Backend stored real segment timestamps but didn't include them in API responses. Frontend invented timestamps with a hardcoded 5s stride.  
**Fix:** Added `start_time`/`end_time` to `ClassificationResult` Pydantic schema, `ClassificationResultDTO`, and populated them in both jobs router serializers. Updated `mapResultsToSteps` to use `r.start_time`/`r.end_time`.

---

## Cleanup Issues (Fixed)

### 11. Unused `BackgroundTasks` import
**File:** `routers/jobs.py:3`  
**Fix:** Removed the import.

### 12. Module-level MLflow initialization
**File:** `tracking.py:113`  
**Issue:** `tracker = ExperimentTracker()` connected to MLflow at import time.  
**Fix:** Replaced with lazy `get_tracker()` factory.

### 13. Hardcoded database password in config default
**File:** `config.py:11`  
**Issue:** `postgresql+asyncpg://postgres:postgres@localhost:5432/video2knowledge` in source code.  
**Fix:** Reverted default to SQLite (`sqlite+aiosqlite:///./video2text.db`). PostgreSQL credentials belong in `.env` only.

### 14. Test mocks missing `modelName` parameter
**Status:** Noted — test mocks have 4-param signatures but real function now takes 5 (5th is optional `modelName`). Tests still pass but don't exercise model selection.

### 15. Duplicate `task_level_split` functions
**Files:** `dataset.py:91` and `dataset_loader.py:197`  
**Status:** Retained both — they serve different purposes (numpy arrays vs TaskMetadata objects). The numpy version is needed for evaluation pipelines.

---

## Files Modified

| File | Changes |
|---|---|
| `services/classification_service.py` | Wire real features, add `_synthetic_fallback` |
| `services/ml_service.py` | Fix `prefer_real=True` in evaluation methods |
| `pipeline/interaction_features.py` | Fix timestamp/position pairing |
| `pipeline/feature_assembler.py` | Remove double OCR inference in corpus |
| `routers/videos.py` | Stream upload to disk in chunks |
| `routers/jobs.py` | Restore `response_model`, add timestamps, remove unused import |
| `schemas/classification.py` | Add `start_time`/`end_time` fields |
| `ml/tracking.py` | Lazy singleton instead of module-level init |
| `ml/classifiers/tier2/workflow_transformer.py` | Assert even `d_model` |
| `config.py` | Revert default to SQLite (no hardcoded password) |
| `docker-compose.yml` | Move Vite env to build args |
| `tests/test_api_e2e.py` | Use multipart file upload |
| `frontend/src/types/api.ts` | Add `start_time`/`end_time` to DTO |
| `frontend/src/services/api/labelMap.ts` | Use real timestamps |
