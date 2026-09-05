# Proposal Template Content

Content ready to paste into the official NUS ISS Project_Proposal_Template.docx

---

## Date of proposal

15 September 2026

## Project Title

Video2Knowledge: A Multi-Tier Ensemble Approach for Multimodal Workflow Recognition and Automated Documentation from Software Engineering Screen Recordings

## Group ID

[Your Canvas Group ID]

## Group Members

| Name | Student ID |
|------|-----------|
| Joshua | [Student ID] |
| Muneeswaran | [Student ID] |
| Stalin | [Student ID] |
| Lakshmi Barthwal Chamoli | [Student ID] |

## Sponsor/Client

Academic Project — NUS M.Tech in Artificial Intelligence Systems, Pattern Recognition Systems Module (Semester 2, 2026)

## Background/Aims/Objectives

### Background

Organizations record software engineering activities such as cloud deployments, CI/CD execution, and troubleshooting sessions. These recordings contain valuable operational knowledge but remain difficult to search and reuse. Existing transcription tools convert speech to text but cannot understand engineering workflows, terminal commands, or deployment intent. Manual SOP creation is expensive, onboarding is slow, and knowledge remains locked inside hours of video.

### Aim

Develop an AI-powered workflow understanding system that recognizes software engineering activities from screen recordings and automatically generates structured documentation, searchable via natural language queries.

### Objectives

1. Process screen recordings to extract multimodal features — speech transcription, OCR text, terminal commands, UI context, and cursor/click events.
2. Build a multi-tier classifier (14 models across Classical ML, Deep Learning, and Ensemble tiers) to recognize 10 DevOps activity categories.
3. Compare and evaluate all classifiers using 5-fold cross-validation, confusion matrices, ROC/AUC curves, feature importance, ablation studies, and error analysis.
4. Generate SOPs, timelines, and knowledge articles from classified workflow segments using an LLM (Claude via AWS Bedrock).
5. Provide searchable knowledge retrieval via RAG (Retrieval-Augmented Generation) and an agentic AI orchestrator that reasons over the knowledge base.

## Project Description

### 1. Problem Statement

Recorded engineering sessions are difficult to search and reuse. Manual SOP creation is expensive, onboarding is slow, and operational knowledge remains locked inside videos. Existing tools transcribe speech but do not understand what the engineer is doing — they cannot distinguish a Docker deployment from a Kubernetes troubleshooting session.

### 2. Proposed Solution

An AI-powered pipeline that processes screen recordings through 6 architectural layers:

- Layer 1 — Presentation: React SPA via CloudFront CDN
- Layer 2 — API & Backend: FastAPI on ECS Fargate
- Layer 3 — Preprocessing & Feature Extraction: Lambda + Textract + YOLO
- Layer 4 — Multi-Tier Classifier: SageMaker with 14 models
- Layer 5 — Data & Storage: RDS PostgreSQL + pgvector + Redis
- Layer 6 — Monitoring & CI/CD: CloudWatch + GitHub Actions

### 3. Multi-Tier Classifier Architecture

**Tier 1 — Classical ML (7 models):** SVM, Naive Bayes, Decision Tree, Random Forest, KNN, XGBoost, LightGBM. Fast baseline classifiers using scikit-learn. All implement a shared BaseClassifier contract for uniform training, prediction, and evaluation.

**Tier 2 — Deep Learning (4 models):** MLP, CNN1D, LSTM, Transformer. PyTorch-based models that capture complex patterns — local, sequential, and long-range dependencies. All share a TorchBaseClassifier providing the training loop, prediction, and serialization.

**Tier 3 — Ensemble + Fusion (3 models):** Voting Classifier (soft/hard), Stacking Classifier (meta-learner over base model probabilities), Multimodal Late Fusion (modality-specific branches with meta-learner fusion). Combines Tier 1 + Tier 2 outputs to maximize accuracy.

**Target Classes (10):** git_operations, docker_workflow, kubernetes_ops, terraform_iac, aws_console, jenkins_ci_cd, coding_editing, debugging, documentation, other.

### 4. Evaluation Framework (8 modules)

- Metrics: Accuracy, Precision, Recall, F1-score (macro), AUC-ROC
- Confusion matrices per model
- ROC curves with per-class AUC
- 5-fold stratified cross-validation (mean ± std)
- Permutation-based feature importance
- Ablation study (modality removal impact analysis)
- t-SNE / UMAP embedding visualization
- Error analysis (confused-pair detection, per-class error rates)

### 5. RAG & Agentic AI

**RAG Pipeline:** Classified workflow segments are converted into SOPs, chunked, and embedded into pgvector. Users query via natural language — semantic search retrieves relevant chunks, and Claude (via Bedrock) generates answers grounded in the actual recordings.

**Agentic AI:** An LLM orchestrator (Claude tool-use API) that reasons, plans, and calls tools (classify, search, compare, generate SOP) to answer complex multi-step queries — e.g., "Compare Docker deployment workflows from this week's recordings."

### 6. Technology Stack

| Component | Technology |
|-----------|-----------|
| Frontend | React, TypeScript, Vite |
| Backend | Python 3.11, FastAPI, SQLAlchemy (async) |
| ML | PyTorch, scikit-learn, XGBoost, LightGBM |
| Database | PostgreSQL, pgvector, Redis |
| LLM | Claude via AWS Bedrock |
| Cloud | AWS (ECS Fargate, SageMaker, S3, Lambda, Step Functions) |
| CI/CD | GitHub Actions |

### 7. Team Responsibilities

| Member | Role | Scope |
|--------|------|-------|
| Joshua | Frontend + UI/UX | React dashboard, video upload, workflow visualization |
| Muneeswaran | Backend + Pattern Recognition | FastAPI API, multi-tier classifier, evaluation, RAG, agentic AI |
| Stalin | Preprocessing + Feature Extraction | Video ingestion, speech-to-text, OCR, YOLO, audio features |
| Lakshmi | Infrastructure + Data + CI/CD | AWS infra, database, Docker, CI/CD, monitoring |

### 8. Pattern Recognition Techniques Coverage

| NUS Requirement | How Covered |
|----------------|------------|
| Supervised learning | All 14 classifiers use labeled training data |
| Machine Learning | 7 classical ML algorithms (Tier 1) |
| Deep Learning | 4 neural networks — MLP, CNN, LSTM, Transformer (Tier 2) |
| Hybrid / Ensemble | 3 ensemble methods — Voting, Stacking, Late Fusion (Tier 3) |
| Intelligent sensing | Multimodal late fusion (OCR + UI + cursor + scene modalities) |
| Comparative evaluation | 14 models compared across 6 metrics with 5-fold CV |

### 9. Timeline

| Date | Milestone |
|------|-----------|
| Sep 15, 2026 | Project proposal submission |
| Sep 30, 2026 | First presentation — working demo with multi-tier classification |
| Oct 15, 2026 | SOP generation + RAG pipeline integrated |
| Oct 25, 2026 | Agentic AI layer + deployment + final polish |
| Oct 31, 2026 | Final deliverables submission |

### 10. Expected Deliverables

1. Multi-tier workflow recognition platform (14 classifiers, 3 tiers)
2. Comprehensive evaluation report (8 evaluation modules, comparative analysis)
3. FastAPI REST API backend with database persistence
4. React dashboard for video upload and workflow visualization
5. Automatic SOP generator via LLM
6. RAG-powered knowledge retrieval system
7. Agentic AI query interface
8. Project documentation and technical guide
