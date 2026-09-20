# Implementation Architecture — video2Text

This documents what is **actually implemented** in `SourceCode/backend/app` today: the data pipeline,
the multi-tier classifier techniques, and the FastAPI serving layer. For the target AWS deployment
design (proposal-stage, not yet built), see `Architecture/README.md`.

## System Overview

    Raw videos --> [Data Pipeline] --> Labeled dataset (train/val/test)
                                              |
                                              v
                                  [Training pipeline] --> saved models
                                              |
                                              v
    Video upload --> FastAPI --> [ML Service: multi-tier classifier] --> ClassificationResult --> DB
                                              ^
                                              |
                                    [Evaluation module] (metrics, CV, ablation, error analysis)

React SPA (Vite) talks to FastAPI over `services/api/analysisService.ts`.

## 1. Data Pipeline (`app/data_pipeline/`)

Orchestrated end-to-end by `pipeline.py::run_data_pipeline`. Stages, in order:

1. **Ingestion** (`ingestion.py`) — `discover_videos()` scans a raw video directory into `VideoRecord`s.
2. **Frame extraction** (`frame_extraction.py`) — `extract_frames()` samples a video into `Frame`s.
3. **Cleaning** (`cleaning.py`) — `clean_frames()` drops unusable frames (blank/corrupt/duplicate).
4. **Evidence extraction** (`evidence/`) — per usable frame, two independent evidence sources run:
   - `ocr.py::extract_ocr_evidence` — OCR text extracted from the frame.
   - `ui_object_detection.py::detect_ui_objects` — detected UI elements/widgets.
5. **Weak-label fusion** (`labeling/evidence_fusion.py`) — `fuse_evidence()` combines OCR + UI evidence
   through two heuristic classifiers (`OcrKeywordClassifier`, `UiHeuristicClassifier`, both registered
   in `pipeline.CLASSIFIERS`) into a single `CandidateLabel` per frame. Keyword matching lives in
   `labeling/keywords.py`; `labeling/candidate_labels.py` defines the candidate structure.
6. **Agreement / confidence gating** (`labeling/confidence_agreement.py`) — `check_agreement()` scores
   how much the evidence sources agree, producing an `AgreementResult` with a `needs_human_review` flag.
7. **Human review loop** (`labeling/human_review.py`) — items that fail the agreement gate are queued
   for manual labeling (see `SourceCode/backend/review_queue.jsonl`) rather than auto-labeled.
8. **Quality control** (`dataset/quality_control.py`) — `to_quality_controlled_dataset()` turns
   agreement results into final `LabeledExample`s, filtering out low-confidence/unresolved items.
9. **Dataset splitting** (`dataset/splits.py`) — `split_dataset()` produces the final `DatasetSplits`
   (train/validation/test).

**Augmentation** (`augmentation/`) is a separate, composable set of frame transforms applied to
training data: `brightness_contrast.py`, `crop_scale.py`, `noise_blur.py`, `compression.py` (simulates
video compression artifacts), and `ui_layout.py` (UI-specific layout perturbation). All extend a shared
`base.py` interface and produce `AugmentedFrame`s.

**Featurization** (`featurize.py`) converts frames/labeled examples into the feature vectors consumed
by the classifiers (feeds `app/ml/dataset.py` and the training pipeline).

Core dataclasses for the whole pipeline live in `types.py`: `VideoRecord → Frame → AugmentedFrame`,
`EvidenceRecord → CandidateLabel → AgreementResult → LabeledExample → DatasetSplits`.

**Design intent (weak supervision):** labels are not hand-annotated per frame; they're derived by
fusing multiple weak/heuristic evidence sources and only auto-accepted when those sources agree,
with disagreement routed to human review. This is a programmatic/weak-supervision labeling strategy,
not manual annotation.

## 2. ML Layer — Multi-Tier Classifier (`app/ml/`)

Ten activity classes are the target label space (`ml/config.py::ACTIVITY_LABELS`): `git_operations`,
`docker_workflow`, `kubernetes_ops`, `terraform_iac`, `aws_console`, `jenkins_ci_cd`, `coding_editing`,
`debugging`, `documentation`, `other`.

All classifiers implement `BaseClassifier` (`ml/base.py`): `fit`, `predict` (returns a timed
`PredictionResult` with labels/probabilities/latency), `save`, `load`, tagged with a `name` and `tier`.
A `ModelRegistry` (`ml/registry.py`) holds instances keyed by name and can list by tier.

**Tier 1 — classical ML** (`ml/classifiers/tier1/`): SVM, Random Forest, Decision Tree, k-NN, Naive
Bayes, XGBoost, LightGBM. Trained on hand/auto-engineered features from the data pipeline.

**Tier 2 — deep learning** (`ml/classifiers/tier2/`): CNN (1D, for sequential/temporal signal), LSTM,
MLP, and a Transformer classifier, all sharing a common PyTorch wrapper (`_torch_base.py`).

**Tier 3 — ensemble/fusion** (`ml/classifiers/tier3/`): combines Tier 1 + Tier 2 outputs via
`voting.py` (hard/soft voting), `stacking.py` (meta-learner over base-model outputs), and
`late_fusion.py` (fuses per-modality/per-tier scores).

This mirrors the target AWS design in `Architecture/README.md` (L4: SageMaker → Tier1 → Tier2 → Tier3),
implemented here as local, framework-agnostic Python classes rather than SageMaker jobs.

**Evaluation** (`ml/evaluation/`) is a full offline evaluation suite independent of serving:
`metrics.py` (precision/recall/F1/accuracy), `confusion.py`, `cross_validation.py`, `roc_curves.py`,
`feature_importance.py`, `embeddings.py` (embedding-space diagnostics), `ablation.py` (component
ablation studies), `error_analysis.py`, and `report.py` (aggregates the above into a report).

`ml/dataset.py::generate_synthetic_dataset` produces synthetic feature matrices — currently used to
exercise the serving path end-to-end before the real featurized dataset is wired in (see Known Gaps).

## 3. Training (`app/training/`)

`training/pipeline.py::train_final_activity_model(splits: DatasetSplits)` is the entry point from
data-pipeline output to a trained `FinalActivityModel`. It featurizes `splits.train` via
`featurize.extract_frame_feature`, encodes each `LabeledExample.activity` string against
`ml/config.ACTIVITY_LABELS`, and fits a `BoostingEnsemble`.

`training/boosting.py::BoostingEnsemble` implements SAMME (multiclass AdaBoost): each round trains a
fresh `BaseActivityClassifier` (`base_classifier.py`'s small PyTorch MLP head) via a sample-weighted
cross-entropy loss, scores it by weighted training error, derives a learner weight (alpha), and
upweights samples the ensemble still gets wrong before the next round. `predict()` does weighted
majority voting across the boosted learners.

`training/final_activity_model.py::FinalActivityModel` wraps a fitted ensemble with the activity label
tuple (`predict_activity` maps a feature vector to a label string) and supports `save`/`load`
(`torch.save`/`torch.load` of learner state dicts + configs, matching the pattern in
`ml/classifiers/tier2/_torch_base.py`).

Covered by `tests/training/test_training_pipeline.py`. **Not yet executed in this environment** — the
project venv's PyTorch install fails with `ImportError: DLL load failed while importing _C` (pre-existing,
unrelated to this code); run the tests once that's fixed to confirm.

## 4. Serving / API (`app/routers/`, `app/services/`)

FastAPI app (`main.py`) wires up CORS, creates DB tables on startup (SQLAlchemy async engine,
`database.py`), and exposes:

- `routers/videos.py` — video upload/management (`models/video.py`, `schemas/video.py`)
- `routers/jobs.py` — analysis job lifecycle (`models/job.py`, `schemas/job.py`)
- `routers/classification.py` — triggers/retrieves classification results (`models/result.py`,
  `schemas/classification.py`)
- `routers/evaluation.py` — exposes evaluation/metrics endpoints (`schemas/evaluation.py`)

**Request flow:** `services/video_service.py` handles upload → `services/job_service.py` tracks an
`AnalysisJob` → `services/classification_service.py::run_classification_job` drives inference by
calling `services/ml_service.py` (wraps the `ModelRegistry`, selects a model by `job.model_name`,
default `"svm"`) → writes one `ClassificationResult` per video segment → job marked `completed`/`failed`.

## 5. Frontend (`SourceCode/frontend/src`)

React + TypeScript (Vite). Pages: `UploadPage` → `AnalyzingPage` → `ResultsPage`, plus `HistoryPage`.
Key components: `VideoDropzone`, `AnalyzingProgress`, `WorkflowSteps`, `VideoResults`. State/data
fetching via `hooks/useVideoAnalysis.ts` calling `services/api/analysisService.ts`. Mirrors the backend
job lifecycle (upload → processing → results) in the UI.

## Known Gaps (as of last read)

Verified via `grep -r "NotImplementedError" app/`:

- **All 5 augmentation transforms are stubs** (`data_pipeline/augmentation/brightness_contrast.py`,
  `crop_scale.py`, `noise_blur.py`, `compression.py`, `ui_layout.py`) — each is only a config
  dataclass; `.apply()` raises `NotImplementedError`. The augmentation stage is currently a no-op.
- ~~Training-side assembly stubbed~~ — **implemented**: `boosting.py`, `final_activity_model.py`, and
  `training/pipeline.py::train_final_activity_model()` now have real logic (SAMME boosting over
  `BaseActivityClassifier` weak learners). Untested in this environment — see note in section 3 above.
- `classification_service.py` calls `generate_synthetic_dataset` instead of the real
  featurized-video pipeline — end-to-end wiring from uploaded video → `featurize.py` output →
  classifier is not yet connected; today it demonstrates the serving contract with synthetic feature
  vectors.
- AWS deployment (`Architecture/README.md`) is a design/proposal; the current implementation runs
  locally (`localDataset/`, local FastAPI + SQLAlchemy), with no SageMaker/Lambda/Textract wiring yet.

**Confirmed implemented (no stubs found):** all 9 data-pipeline stages (ingestion through splits) and
`featurize.py`; all Tier 1/2/3 classifiers and the full `ml/evaluation/` suite.

Re-derive this file by reading the current code rather than trusting it blindly — it reflects a snapshot
and will drift as the stub areas above get filled in.
