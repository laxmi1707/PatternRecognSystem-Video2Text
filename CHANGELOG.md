# Changelog

All notable changes to Video2Knowledge (TRACE) will be documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
No release has been tagged since 0.1.0, so later changes are grouped by date, newest first,
with the pull request that brought them into `main` where there was one.

## [Unreleased]

### Changed
- EfficientNet-B0 weights are baked into the backend image, one CNN feature model is shared by all
  jobs, and the startup warm-up loads it: the first job no longer downloads ~20 MB of weights, and a
  failed download can no longer turn every CNN feature into zeros — Lakshmi
- SOP detector switched off by default: uploads are not sent to it and the "Steps read from the
  video" panel is hidden unless the frontend is built with `VITE_SOP_DETECTOR_ENABLED=true`;
  docker compose starts it only with `--profile sop-detector` (see HowToRun.md) — Lakshmi
- `models/v3` is the default model version everywhere (`MODEL_S3_PREFIX`, `.env.example`, Terraform,
  docs). Production already ran v3 through the ECS task's environment, but `main` still defaulted to
  v2, so a `terraform apply` or a fresh setup would have gone back to v2 — Lakshmi
- The local model folder is named after the version (`./models/v3`, from `MODEL_S3_PREFIX`) unless
  `MODEL_DIR` is set. It was always `./models/v2`, so v3 was downloaded into a folder named v2, and a
  laptop that still held v2 models loaded the v2-only ones next to v3 — Lakshmi

### Fixed
- Activity names: v3's `label_names.json` named the classes `git_operations`, `docker_workflow`, ...
  although class 0 holds the IDEs, 2 Bash, 4 the browsers, 5 draw.io and 6 OpenShot, so a File
  Explorer recording came out as "Git Operations" and "Docker Workflow". `train.py --load-features`
  read the cached, already renumbered class indices as indices into `ACTIVITY_LABELS`; it now names
  them from `feature_labels.json`, written with the cache, and stops rather than guess. The S3 model
  sync now also downloads `.json`, so production loads `label_names.json` at all. `models/v3/label_names.json`
  in S3 is corrected (classes 7 and 8, `file_management` and `image_editing`, are inferred) — Lakshmi
- Production extracted 151 HOG features while the v3 models expect 1391 CNN features, so SVM, KNN,
  Random Forest and Stacking failed on every job ("X has 151 features, but SVC is expecting 1391")
  and CNN1D/LSTM ran on the wrong input. The ECS task now sets `FEATURE_BACKEND` (Terraform
  variable `feature_backend`, default `cnn`) — Lakshmi

## 2026-10-28 — Demo readiness: SOP quality, speed, SOP detector

### Added
- SOP detector (`SOP-detector/`): clicks and typing read from a bare screen recording, as its own
  service (port 8100), with a "Steps read from the video" panel on the results page and the detected
  actions listed under each SOP step; the panel says when the detector is not running (#11, #14) — Yuan Zilin
- Feature cache keyed by the video's SHA-256 (`uploads/feature_cache/`): a video analysed before skips
  OCR and returns in seconds (#13) — Lakshmi
- Startup warm-up: the models and the EasyOCR reader load in a background thread when the backend
  starts, not on the first job (`WARMUP_ON_STARTUP`) (#13) — Lakshmi
- `scripts/prewarm_demo.py`: runs the demo videos against a deployed backend so the live demo is
  served from the cache (#13) — Lakshmi
- Terminal recordings: one SOP step per newly typed command ("Typed `git push --force ...`"), with risk
  judged on the new commands only (#15) — Lakshmi

### Changed
- Progress bar follows the real work ("segment i of n") instead of a fixed timer that stopped at 92% (#13) — Lakshmi
- OCR reads each screen once: unchanged keyframes reuse the previous text, the EasyOCR reader is shared
  by all jobs, and `readtext` batches 16 boxes (#13, #15) — Lakshmi
- OCR reads full-resolution keyframes instead of the 640x480 copy (confidence ~0.1 → ~0.8 on screen
  recordings) and keeps the screen's line breaks, so a command is not merged with its output (#15) — Lakshmi
- The SOP endpoint detects the platform from screen text when there is no action log, as the runbook
  and report already did (#15) — Lakshmi
- Upload page: "Processing Pipeline" card removed (#12) — Lakshmi
- ECS `desired_count` must be 1 (no cold start; SQLite lives in the task) (#13) — Lakshmi

### Fixed
- Duplicate-frame check compared a whole-screen average, so a new terminal line was missed and
  `risk_test_video.mp4` was read on 2 of 24 keyframes; it now counts changed pixels (#15) — Lakshmi
- History list gained a `null` entry after every analysis (`useVideoAnalysis.onAnimationDone`) (#12) — Lakshmi
- "2 anomalyies detected" in the anomaly timeline (#12) — Lakshmi
- 10 out-of-date frontend tests brought in line with the current UI (vitest 57/57) (#12) — Lakshmi

## 2026-10-19 – 2026-10-27 — v3 models, documents, risk detection, security

### Added
- v3 training: 4 new activity classes (diagram design, media editing, file management, image editing),
  130+ app-to-activity mappings; "other" reduced from 22.7% to under 1% — Muneeswaran
- AWS Console and cloud-platform label mappings — Muneeswaran
- Level 1 action-type classifier (move, click, type, press key, hotkey, drag) with a 70/20/10 split by
  recording, and a Colab notebook to train it (#8) — Lakshmi
- SOP steps from the action log: one step per user action, with what the screen showed afterwards (#8) — Lakshmi
- Word report export with keyframes, classification table and SOP steps — Muneeswaran
- Anomaly detection of dangerous commands (`rm -rf`, `sudo`, `chmod 777`, `DROP TABLE`, ...) in the
  report, including OCR misreads such as `suco` for `sudo` — Muneeswaran
- Rule-based risk flagging on SOP steps, shown as badges in the Screen View timeline — Muneeswaran
- Security: API key authentication, rate limiting, upload hardening and database lockdown — Muneeswaran
- Video stream endpoint, used for history playback — Muneeswaran
- Demo videos and a Playwright demo script (normal and anomaly flows) — Muneeswaran
- TRACE branding: banner and architecture SVGs, README rewrite, final presentation — Muneeswaran

### Changed
- Models are discovered from the `.pkl` files and never trained on demand at inference — Muneeswaran
- Stacking uses RF + MLP as base models (SVM removed to avoid running out of memory on 25K samples) — Muneeswaran
- Knowledge generation is rule-based only; the LLM path was removed — Muneeswaran
- Upload limit settled at 100 MB (briefly 10 MB) — Muneeswaran, Lakshmi
- UI: front-page tagline and anomaly callout, brighter text, smaller timeline fonts, SOP display shows
  the steps only, SGT timestamps in reports — Muneeswaran
- PyTorch inference runs in batches to avoid running out of memory on long videos — Muneeswaran

### Fixed
- Runbook `NameError`, and SQLite not generating IDs for uploads (#8) — Lakshmi
- CI was red from run #78 to #98: duplicate dictionary keys failed ruff (#9), and the e2e tests had no
  model once inference stopped training on demand (#10) — Lakshmi
- SOP terminal commands: shell prompts, `user@host` artifacts, taskbar noise and garbled text no longer
  appear as commands; steps keep their own segments, merged same-label steps are capped at 12 s — Muneeswaran
- PyTorch checkpoints store `num_classes` and `feature_dim`, fixing load mismatches — Muneeswaran
- Frontend passes `VITE_API_KEY` and `VITE_API_BASE_URL` through to the build — Muneeswaran

### Removed
- Tesseract OCR fallback (worse on terminal text than EasyOCR) — Muneeswaran
- SageMaker from the documented tech stack (not implemented) — Muneeswaran

## 2026-10-05 – 2026-10-18 — Training at scale, AWS deployment

### Added
- MLflow tracking; all 16 models registered by level and tier — Muneeswaran
- EfficientNet CNN feature backend (1391 features) alongside HOG (151) — Muneeswaran
- `retrain_tier3.py` to rebuild the ensembles without re-extracting features, and separate
  extraction and training stages in `train.py` — Muneeswaran
- OCR text per segment, used in SOP step descriptions; SOP generated automatically on the results page — Muneeswaran
- TRACE UI: NUS ISS theme, neural background, per-task analysis progress — Muneeswaran
- Models served from S3 (`models/vN/`), downloaded at startup with a local fallback — Lakshmi
- Backend on ECS Fargate behind an ALB and CloudFront, as a Terraform stack, with IAM policies;
  CPU-only Dockerfile for Fargate, GPU build in `Dockerfile.gpu` — Lakshmi
- Local setup guide and model reference for all 16 classifiers — Muneeswaran

### Changed
- Video analysis runs in a worker thread, so `/health` and job polling stay responsive — Lakshmi
- Three keyframes per segment (25/50/75%) instead of the midpoint only — Muneeswaran
- Fast/full analysis toggle removed; every analysis runs in full — Muneeswaran
- Pre-trained `.pkl` files are no longer kept in git — Muneeswaran

### Fixed
- Training failures across the 16 models: class counts, feature dimensions, KNN sample weights,
  Naive Bayes priors, ensemble save/load, CUDA-to-CPU loading on Mac — Muneeswaran
- Labels remapped to contiguous indices for XGBoost and LightGBM, with `task_ids` saved per split — Muneeswaran
- Activity mapping reduced "other" from 72% to about 15% — Muneeswaran
- Best-model selection, segment timestamps and step descriptions in SOP and runbook — Muneeswaran
- Database IDs as BigInteger for timestamp-based IDs — Muneeswaran

## 2026-08-30 – 2026-09-30 — Multi-tier classifier and first presentation

### Added
- Evaluation framework, `BaseClassifier` contract and synthetic dataset — Muneeswaran
- Tier 1: 7 classical classifiers (SVM, Naive Bayes, Decision Tree, Random Forest, KNN, XGBoost, LightGBM) — Muneeswaran
- Tier 2: MLP, CNN1D, LSTM and Transformer on a shared PyTorch base — Muneeswaran
- Tier 3: voting, stacking and late-fusion ensembles — Muneeswaran
- 5-fold stratified cross-validation, feature importance, ablation, t-SNE and error analysis — Muneeswaran
- Classification and evaluation API, async SQLAlchemy models, and the upload → classify → results flow — Muneeswaran
- Multimodal pipeline and UI (#4), model training, comparison UI and Docker setup — Muneeswaran
- GPU training image (CUDA) with GPU auto-detection for EasyOCR and YOLO — Muneeswaran
- Real-time progress reporting during analysis — Muneeswaran
- AWS architecture (6-layer, multi-tier classifier), network and data-flow diagrams — Muneeswaran
- Project documentation, technical guide, proposal drafts and presentations (NUS ISS template) — Muneeswaran

### Changed
- Architecture: speech/audio pipelines replaced with screen-recording ones — Muneeswaran
- OCR vocabulary built from task text instead of video frames — Muneeswaran

### Fixed
- `action_log.json` inside dataset zip files, ensemble probability shapes, class-count mismatches
  between models and labels, SOP job ID — Muneeswaran

## [0.1.0] - 2026-08-27

### Added
- Project proposal and initial documentation — Muneeswaran
- FastAPI backend scaffold with health endpoint — Lakshmi
- React frontend scaffold (Vite + TypeScript) — Lakshmi
- Docker/K8s deployment infra and CI workflows — Lakshmi
- AWS deployment scaffolding (backend + frontend) — Lakshmi
- GitHub Actions deploy workflow scoped to dev — Lakshmi
- .gitignore and project structure — Muneeswaran
