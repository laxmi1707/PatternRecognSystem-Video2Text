# Video2Knowledge: AI-Powered Enterprise Workflow Understanding and Documentation System

A Multimodal Pattern Recognition Approach for Software Engineering Workflows

NUS M.Tech AIS — Pattern Recognition Systems | Semester 2 | 2026

---

## 1. Project Title

Video2Knowledge: A Multi-Tier Ensemble Approach for Multimodal Workflow Recognition and Automated Documentation from Software Engineering Screen Recordings

## 2. Team Members

Group ID: [Canvas Group ID]

| Name | Student ID | Role |
|------|-----------|------|
| Joshua | [ID] | Frontend + UI/UX |
| Muneeswaran | [ID] | Backend + Pattern Recognition |
| Stalin | [ID] | Preprocessing + Feature Extraction |
| Lakshmi Barthwal Chamoli | [ID] | Infrastructure + Data + CI/CD |

## 3. Sponsor / Client

Academic Project — NUS M.Tech in Artificial Intelligence Systems.
Potential industry applicability: DevOps, Cloud Engineering, IT Operations, Financial Services, Healthcare IT.

## 4. Background

Organizations record software engineering activities such as cloud deployments, infrastructure provisioning, CI/CD execution, troubleshooting, and production support. These recordings contain rich operational knowledge — terminal commands, deployment sequences, configuration changes, and troubleshooting steps.

Existing transcription tools convert speech into text but cannot understand engineering workflows, UI interactions, terminal commands, or deployment intent. Video2Knowledge addresses this gap through multimodal AI that combines speech recognition, OCR, computer vision, pattern recognition, and LLMs to automatically understand workflows and generate structured documentation.

## 5. Problem Statement

Recorded engineering sessions are difficult to search and reuse. Manual SOP creation is expensive, onboarding is slow, and operational knowledge remains locked inside videos. A 30-minute screen recording of a Docker deployment contains valuable step-by-step knowledge, but extracting it manually takes hours.

## 6. Project Aim

Develop an AI-powered workflow understanding system capable of recognizing software engineering activities from screen recordings and automatically generating structured documentation, searchable via natural language queries.

## 7. Project Objectives

1. Process recorded screen recordings to extract multimodal features.
2. Extract speech (Whisper), OCR text (Textract/EasyOCR), terminal commands, UI context (YOLO), and cursor/click events.
3. Recognize 10 categories of DevOps activities using a multi-tier classifier.
4. Compare 14 classifiers across Classical ML, Deep Learning, and Ensemble methods.
5. Evaluate all models using 5-fold cross-validation, confusion matrices, ROC/AUC, feature importance, ablation, and error analysis.
6. Generate SOPs, timelines, and knowledge articles via LLM (Claude on AWS Bedrock).
7. Provide searchable knowledge retrieval via RAG (pgvector + Bedrock).
8. Build an agentic AI orchestrator that reasons over the knowledge base to answer complex queries.

## 8. Research Questions

- RQ1: Can software engineering workflows be automatically recognized from screen recordings using multimodal pattern recognition?
- RQ2: Does multimodal analysis (OCR + UI + cursor + speech) outperform single-modality approaches?
- RQ3: Which pattern recognition algorithm performs best for workflow classification, and does ensembling improve accuracy?
- RQ4: Can an AI system reduce documentation effort while maintaining SOP quality?
- RQ5: Does an agentic AI approach improve knowledge retrieval over standard RAG?

## 9. Novelty

1. Multimodal analysis combining video, OCR, UI detection, cursor tracking, and speech — not just audio transcription.
2. Multi-tier classifier architecture (Classical ML → Deep Learning → Ensemble) with 14 models and a shared BaseClassifier contract.
3. Multimodal late fusion that trains separate branches per modality with a meta-learner fusion layer.
4. Comprehensive 8-module evaluation framework (metrics, confusion, ROC, cross-validation, feature importance, ablation, t-SNE, error analysis).
5. Automatic SOP generation grounded in classified workflow segments, not generic LLM output.
6. RAG-powered enterprise knowledge repository searchable via natural language.
7. Agentic AI orchestrator using Claude tool-use to reason over classifiers, RAG, and SOP generation.
8. End-to-end pipeline from raw screen recording to searchable knowledge base — no manual annotation required.

## 10. Proposed Solution

The system processes screen recordings through a 6-layer architecture:

1. **Video Ingestion** — Upload or capture screen recordings
2. **Preprocessing** — Extract frames, audio, OCR text, UI elements, cursor events
3. **Feature Engineering** — Build multimodal feature vectors from extracted data
4. **Multi-Tier Classification** — Recognize activities using 14 classifiers across 3 tiers
5. **SOP Generation** — LLM converts classified segments into structured documentation
6. **Knowledge Retrieval** — RAG + Agentic AI for natural language search over generated SOPs

## 11. System Architecture (6 Layers on AWS)

    L1: Presentation        — React SPA → CloudFront CDN → Route 53
    L2: API & Backend       — API Gateway → ECS Fargate (FastAPI) → Cognito → SQS
    L3: Preprocessing       — Lambda → Textract/OCR → YOLO → Cursor/Click → Window
    L4: Multi-Tier Classifier — SageMaker → Tier1 (ML) → Tier2 (DL) → Tier3 (Ensemble)
    L5: Data & Storage      — S3 → RDS PostgreSQL → pgvector → Redis → DynamoDB
    L6: Monitoring & CI/CD  — CloudWatch → IAM → GitHub Actions → WAF

Key AWS decisions:
- ECS Fargate over EKS (simpler, cheaper, academic project fit)
- Bedrock Claude for LLM (managed, no GPU infrastructure needed)
- pgvector on RDS for vector search (no extra service, integrated with PostgreSQL)
- Step Functions for ML pipeline orchestration

## 12. Multi-Tier Classifier Architecture

### Tier 1 — Classical ML (7 models)

| Classifier | Algorithm | Key Strength |
|------------|-----------|-------------|
| SVM | Support Vector Machine | Optimal decision boundary |
| Naive Bayes | Gaussian NB | Fast probabilistic baseline |
| Decision Tree | Single tree | Interpretable if/else rules |
| Random Forest | 100 trees voting | Robust to noise |
| KNN | K-Nearest Neighbors | No training needed |
| XGBoost | Gradient-boosted trees | Competition-winning accuracy |
| LightGBM | Fast gradient boosting | Production speed |

### Tier 2 — Deep Learning (4 models)

| Classifier | Architecture | What It Captures |
|------------|-------------|-----------------|
| MLP | Fully-connected layers | Non-linear feature interactions |
| CNN1D | 1D convolutions | Local patterns in adjacent features |
| LSTM | Recurrent network | Sequential/temporal dependencies |
| Transformer | Self-attention | Long-range feature interactions |

All share a TorchBaseClassifier providing the training loop, prediction, and PyTorch serialization.

### Tier 3 — Ensemble + Fusion (3 models)

| Classifier | Strategy | Why |
|------------|----------|-----|
| Voting | Average base model probabilities | Simple, robust |
| Stacking | Meta-learner over base outputs | Learns which model to trust per class |
| Late Fusion | Modality-specific branches + meta-learner | Handles multimodal data |

### Target Classes (10)

git_operations, docker_workflow, kubernetes_ops, terraform_iac, aws_console, jenkins_ci_cd, coding_editing, debugging, documentation, other

### BaseClassifier Contract

Every classifier implements: name, tier, fit(X, y), predict(X) → PredictionResult(labels, probabilities, latency_ms), save(path), load(path), get_params().

## 13. Detailed System Modules

**Video Ingestion Module** — Capture live screen or upload recorded video; extract audio; split video into frames. Technologies: Python, OpenCV, FFmpeg, FastAPI Upload API.

**Audio Processing Module** — Extract narration, speaker segmentation, timestamps. Technologies: Whisper (via AWS Transcribe), librosa.

**OCR & Terminal Understanding Module** — Read terminal commands, logs, configuration files, and browser text. Technologies: AWS Textract, EasyOCR.

**UI & Application Recognition Module** — Detect VS Code, Terminal, Browser, AWS Console, Jenkins, Kubernetes Dashboard. Technologies: YOLOv11, OpenCV.

**Cursor & Click Detection Module** — Track mouse movements, click locations, window focus changes. Technologies: OpenCV.

**Feature Engineering Module** — Build feature vectors from OCR, speech, UI, cursor, and scene data. Technologies: NumPy, pandas, sentence-transformers.

**Pattern Recognition Module** — Classify activities using 14 models across 3 tiers. Technologies: scikit-learn, PyTorch, XGBoost, LightGBM.

**Evaluation Module** — 8-module framework: metrics, confusion matrix, ROC curves, cross-validation, feature importance, ablation study, t-SNE/UMAP, error analysis. Technologies: scikit-learn, NumPy.

**SOP Generation Module** — Convert classified workflow segments into structured documentation. Technologies: Claude via AWS Bedrock, LangChain.

**Knowledge Repository Module** — Store embeddings and enable semantic search. Technologies: PostgreSQL, pgvector, sentence-transformers.

**Agentic AI Module** — LLM orchestrator with tool-use for multi-step reasoning. Technologies: Claude tool-use API via AWS Bedrock.

**API & Dashboard Module** — REST API and user interface. Technologies: FastAPI, React, TypeScript.

**Infrastructure Module** — Cloud deployment, CI/CD, monitoring. Technologies: AWS ECS Fargate, GitHub Actions, CloudWatch.

## 14. End-to-End Data Flow

    Screen Recording → S3 Upload (presigned URL)
        → Lambda trigger → Step Functions orchestration
            → Frame extraction (OpenCV + FFmpeg)
            → AWS Textract (screen → OCR text)
            → Cursor & click detection (OpenCV)
            → Window state detection (OpenCV)
        → Feature Engineering (combine all modalities)
        → SageMaker Endpoint (Multi-Tier Classifier)
            → Tier 1: SVM, RF, XGBoost (scikit-learn)
            → Tier 2: CNN, LSTM, Transformer (PyTorch)
            → Tier 3: Voting, Stacking, Fusion (ensemble)
        → AWS Bedrock (LLM → generate SOP)
        → RDS PostgreSQL (metadata + results)
        → pgvector (embeddings for RAG)
        → S3 (generated documents)

## 15. Pattern Recognition Techniques

**Classical ML (Tier 1):** SVM, Naive Bayes, Decision Tree, Random Forest, KNN, XGBoost, LightGBM — 7 algorithms covering linear, probabilistic, tree-based, and instance-based families.

**Deep Learning (Tier 2):** MLP, CNN1D, LSTM, Transformer — 4 architectures capturing non-linear, local, sequential, and long-range patterns respectively.

**Ensemble (Tier 3):** Voting (soft/hard), Stacking (meta-learner), Late Fusion (multimodal) — 3 methods combining base models for maximum accuracy.

## 16. Technology Stack

| Layer | Technologies |
|-------|-------------|
| Frontend | React, TypeScript, Vite |
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2 |
| ML | PyTorch, scikit-learn, XGBoost, LightGBM |
| Database | PostgreSQL, pgvector, Redis, SQLite (local dev) |
| LLM | Claude via AWS Bedrock |
| Vector Search | pgvector (RDS extension) |
| Cloud | AWS (ECS Fargate, SageMaker, S3, Lambda, Step Functions, Textract, Bedrock) |
| CI/CD | GitHub Actions, Docker, ECR |
| Monitoring | CloudWatch, IAM, WAF |

## 17. Dataset

**Development Phase:** Synthetic dataset with configurable samples and features per class, generated with fixed seed (42) for reproducibility. 10 classes with distinct cluster centers + Gaussian noise.

**Production Phase:** Custom-recorded DevOps workflows covering all 10 target classes. Public DevOps tutorial videos for augmentation. Real preprocessing pipeline extracts OCR, UI, cursor, and scene features per video segment.

## 18. Evaluation Strategy

| Metric | Purpose |
|--------|---------|
| Accuracy, Precision, Recall, F1 (macro) | Classification performance |
| AUC-ROC (per-class and macro) | Ranking quality, robust to class imbalance |
| 5-fold stratified cross-validation | Statistical robustness (mean ± std) |
| Confusion matrix | Per-class error patterns |
| Permutation feature importance | Which features drive predictions |
| Ablation study | Which modalities contribute most |
| t-SNE / UMAP embeddings | Visual cluster separation |
| Error analysis | Confused pairs, high-confidence misclassifications |
| Latency (ms) | Production viability |

## 19. Expected Deliverables

1. Multi-tier workflow recognition platform (14 classifiers, 3 tiers, all tested)
2. Comprehensive evaluation report with 8 analysis modules
3. FastAPI REST API with database persistence (9 endpoints)
4. React dashboard for video upload and workflow visualization
5. Automatic SOP generator via Claude (AWS Bedrock)
6. RAG-powered knowledge retrieval (pgvector + semantic search)
7. Agentic AI query interface (Claude tool-use orchestrator)
8. AWS deployment on ECS Fargate + SageMaker
9. Technical documentation and reference guide

## 20. Team Responsibilities

| Member | Layer | Scope |
|--------|-------|-------|
| Joshua | L1: Presentation | React dashboard, video upload, workflow visualization, UI/UX |
| Muneeswaran | L2 + L4: Backend + ML | FastAPI API, multi-tier classifier, evaluation framework, RAG, agentic AI |
| Stalin | L3: Preprocessing | Video ingestion, speech-to-text, OCR, YOLO, cursor detection, feature engineering |
| Lakshmi | L5 + L6: Infra + Data | AWS infrastructure, database, Docker, CI/CD pipelines, monitoring |

## 21. Expected Applications

- DevOps documentation automation
- IT operations knowledge capture
- Compliance audit trails
- New engineer onboarding acceleration
- Enterprise knowledge management
- Process mining from screen recordings
- Incident postmortem documentation

## 22. Future Enhancements

- Real-time screen capture and live classification
- Integration with Jira, GitHub Issues, and Jenkins
- Knowledge graph linking workflows, tools, and teams
- Predictive workflow recommendations
- Multi-language support for global teams

## 23. Timeline and Milestones

| Date | Milestone |
|------|-----------|
| Sep 15, 2026 | Project proposal submission |
| Sep 30, 2026 | First presentation — working demo with multi-tier classification + evaluation |
| Oct 15, 2026 | SOP generation + RAG pipeline integrated |
| Oct 25, 2026 | Agentic AI layer + deployment + final polish |
| Oct 31, 2026 | Final deliverables submission |
