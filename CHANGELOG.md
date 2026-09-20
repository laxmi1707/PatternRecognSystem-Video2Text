# Changelog

All notable changes to Video2Knowledge will be documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- AWS architecture diagram (6-layer, multi-tier classifier) — Muneeswaran
- Network diagram (VPC, subnets, security groups) — Muneeswaran
- Data-flow diagram (9-stage pipeline) — Muneeswaran
- Project documentation and README files — Muneeswaran
- Implementation architecture doc (`Architecture/PIPELINE.md`) covering the actual data pipeline,
  classifier tiers, and training/serving wiring, distinct from the target AWS design — Lakshmi
- Training pipeline implementation — Lakshmi
  - `app/training/boosting.py::BoostingEnsemble` — SAMME multiclass AdaBoost over
    `BaseActivityClassifier` weak learners (sample-weighted training, weighted-error-based learner
    weights, per-round reweighting)
  - `app/training/final_activity_model.py::FinalActivityModel` — `predict_activity`, `save`, `load`
  - `app/training/pipeline.py::train_final_activity_model` — wires `DatasetSplits` →
    `featurize.extract_frame_feature` → label encoding against `ACTIVITY_LABELS` → fitted ensemble
  - `tests/training/test_training_pipeline.py` (8 tests: fit/predict, error cases, save/load
    round-trip, end-to-end from synthetic images) — **not yet run**; this repo's venv has a broken
    PyTorch install (`ImportError: DLL load failed while importing _C`), unrelated to this change

### Known Issues
- Backend venv's PyTorch install is broken (DLL load failure) — blocks running any torch-dependent
  test (tier2, tier3, training). Pre-existing, not caused by the training pipeline work above.

## [0.1.0] - 2026-08-27

### Added
- Project proposal and initial documentation — Muneeswaran
- FastAPI backend scaffold with health endpoint — Lakshmi
- React frontend scaffold (Vite + TypeScript) — Lakshmi
- Docker/K8s deployment infra and CI workflows — Lakshmi
- AWS deployment scaffolding (backend + frontend) — Lakshmi
- GitHub Actions deploy workflow scoped to dev — Lakshmi
- .gitignore and project structure — Muneeswaran
