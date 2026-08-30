# Backend — Video2Knowledge

**Layer 2 (API & Backend) + Layer 4 (Multi-Tier Classifier)**

Owner: Muneeswaran

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.11+ |
| Framework | FastAPI + Uvicorn |
| ORM | SQLAlchemy (async) |
| Database | SQLite (local) / PostgreSQL (AWS) |
| ML | PyTorch, scikit-learn, XGBoost, LightGBM |
| Testing | pytest, pytest-asyncio, httpx |
| Linting | ruff, mypy |
| Container | Docker (multi-stage build) |
| Deployment | AWS ECS Fargate + SageMaker |

## Setup

    python3.11 -m venv .venv
    source .venv/bin/activate
    cp .env.example .env
    pip install -e ".[ml,dev]"
    uvicorn app.main:app --reload --port 8000
    # API docs: http://localhost:8000/docs

## Directory Structure

    backend/
    +-- app/
    |   +-- main.py                  # App factory (create_app), lifespan
    |   +-- config.py                # Pydantic settings
    |   +-- database.py              # Async SQLAlchemy engine + session
    |   +-- dependencies.py          # DI: get_db, get_ml_pipeline
    |   |
    |   +-- routers/                 # API endpoints (thin, delegate to services)
    |   |   +-- health.py            # GET  /health
    |   |   +-- videos.py            # POST /api/v1/videos/upload
    |   |   |                          GET  /api/v1/videos/{id}
    |   |   +-- jobs.py              # GET  /api/v1/jobs/{id}
    |   |   +-- classifications.py   # POST /api/v1/videos/{id}/classify
    |   |   |                          GET  /api/v1/jobs/{id}/results
    |   |   +-- evaluation.py        # POST /api/v1/evaluation/run
    |   |                              GET  /api/v1/evaluation/reports/{id}
    |   |
    |   +-- schemas/                 # Pydantic v2 request/response models
    |   |   +-- common.py            # ErrorResponse, PaginatedResponse
    |   |   +-- video.py             # VideoUploadResponse, VideoResponse
    |   |   +-- job.py               # JobResponse, JobStatus enum
    |   |   +-- features.py          # SegmentFeatures, VideoFeatures
    |   |   +-- classification.py    # ActivityLabel enum, ClassificationResult
    |   |   +-- evaluation.py        # EvalReport, ModelComparisonRow
    |   |
    |   +-- models/                  # SQLAlchemy ORM models
    |   |   +-- base.py              # Declarative base, TimestampMixin
    |   |   +-- video.py             # Video table
    |   |   +-- job.py               # AnalysisJob table
    |   |   +-- result.py            # ClassificationResult, EvalRun tables
    |   |
    |   +-- services/                # Business logic layer
    |   |   +-- video_service.py
    |   |   +-- job_service.py
    |   |   +-- classification_service.py
    |   |   +-- evaluation_service.py
    |   |
    |   +-- ml/                      # ML Pipeline (Layer 4)
    |       +-- base.py              # BaseClassifier ABC + PredictionResult
    |       +-- registry.py          # Model registry
    |       +-- pipeline.py          # ClassificationPipeline orchestrator
    |       +-- feature_engineering.py
    |       +-- dataset.py           # Synthetic + PyTorch datasets
    |       +-- config.py            # MLConfig (seeds, hyperparams)
    |       |
    |       +-- classifiers/
    |       |   +-- tier1/           # Classical ML
    |       |   |   svm, naive_bayes, decision_tree, random_forest,
    |       |   |   knn, xgboost, lightgbm
    |       |   +-- tier2/           # Deep Learning
    |       |   |   cnn, lstm, transformer, vit, mlp
    |       |   +-- tier3/           # Ensemble + Fusion
    |       |       voting, stacking, late_fusion
    |       |
    |       +-- evaluation/          # Evaluation Framework
    |           metrics, confusion, roc_curves, cross_validation,
    |           ablation, feature_importance, embeddings,
    |           error_analysis, report
    |
    +-- tests/                       # Mirrors app/ structure
        +-- conftest.py              # In-memory SQLite, async client
        +-- ml/
            +-- conftest.py          # Synthetic dataset fixtures
            +-- test_tier1/ test_tier2/ test_tier3/ test_evaluation/

## BaseClassifier Contract

Every classifier (15+ models) implements:

    name       -> "svm", "cnn", "voting_ensemble"
    tier       -> "tier1", "tier2", "tier3"
    fit(X, y)  -> Train the model
    predict(X) -> PredictionResult(labels, probabilities, latency_ms)
    save/load  -> Checkpoint to/from disk
    get_params -> Hyperparameters for reproducibility

## Preprocessing Contract (from Layer 3)

    SegmentFeatures:
      segment_id:      str
      start_time:      float (seconds)
      end_time:        float (seconds)
      transcript_text: str           # from Whisper/Transcribe
      ocr_text:        str           # from Textract/EasyOCR
      ui_labels:       list[str]     # from YOLOv11
      audio_mfcc:      list[list[float]]  # from librosa
      scene_labels:    list[str]     # from scene classifier

## Commands

    pytest tests/ -v                          # Run tests
    pytest tests/ -v --cov=app --cov-report=html  # Coverage
    ruff check app/ tests/                    # Lint
    mypy app/                                 # Type check
    docker build -t v2t-backend .             # Build container
    docker run -p 8000:8000 v2t-backend       # Run container
