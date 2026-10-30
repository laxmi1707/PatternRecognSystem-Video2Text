<div align="center">
  <img src="Miscellaneous/images/banner.svg" alt="TRACE — Task Recognition & Activity Capture Engine" width="100%"/>
</div>

# TRACE — Task Recognition & Activity Capture Engine

**A Multi-Tier Ensemble Approach for Multimodal Activity Recognition and Automated SOP Generation from Desktop Screen Recordings**

NUS M.Tech AIS — ISY5002 Pattern Recognition Systems | Group 21 | Semester 2, 2026

* * *

## Executive Summary

Desktop screen recordings contain expert knowledge that is impossible to search or reuse. **TRACE** automatically converts these recordings into structured SOPs and runbooks by fusing six modalities — visual frames, OCR text, UI context, command/log signals, interaction events, and temporal patterns — through a three-tier classifier.

| Metric | Value |
|--------|-------|
| Dataset | 277 tasks · 8 apps · ~2.3 GB (VideoCUA subset) |
| Activity classes | 5 classes from 8 apps: `coding_editing`, `media_editing`, `web_browsing`, `diagram_design`, `terminal_ops` |
| Best model (v3b) | Voting ensemble — F1 **0.884** |
| 2nd best (v3b) | Stacking ensemble — F1 **0.869** |
| vs. v2 baseline | +73% macro-F1 improvement (KNN 0.51 → Voting 0.884) |
| Feature vector | 1,391 dims (OCR + UI + CNN-visual + interaction) |
| Models trained | 13 — SVM, KNN, Decision Tree, Random Forest, Naive Bayes, XGBoost, LightGBM (Tier 1) · MLP, CNN1D, LSTM, Transformer (Tier 2) · Voting, Stacking (Tier 3) |

**System components:**

- **Ingestion** — video upload, frame extraction, action log parsing
- **Feature extraction** — EfficientNet-B0 CNN visual features, EasyOCR, YOLO UI detection, interaction statistics
- **Multi-tier classifier** — classical ML → deep learning → ensemble fusion
- **Anomaly detection** — OCR-based rule engine flags destructive commands, privilege escalation, and risky SQL in recorded sessions
- **Knowledge generation** — Rule-based SOP, runbook, and timeline generation from pattern recognition output
- **Dashboard** — React frontend for upload, activity timeline, anomaly alerts, and knowledge retrieval

* * *

## Project Contribution

| Member | Student ID | Scope | Email |
|--------|-----------|-------|-------|
| Lakshmi Barthwal Chamoli | A0340664E | AWS infrastructure, video upload, OCR pipeline, SVM, Naive Bayes, temporal sequence analysis, CI/CD | *(email)* |
| Yuan Zilin | A0283899Y | React dashboard, workflow visualization, ground-truth collection, evaluation framework, MLP, CNN1D, Voting ensemble | *(email)* |
| Stalin Sagayaraj | A0340115X | Docker, video ingestion, YOLO UI detection, LSTM, Transformer | *(email)* |
| Muthaiah Muneeswaran | A0019650J | FastAPI backend, multi-tier classifier, Decision Tree, Random Forest, multimodal late fusion, CI/CD, monitoring | *(email)* |

* * *

## Video Demo

| Video | Link |
|-------|------|
| Promotional overview | *(link to be added)* |
| Technical walkthrough | *(link to be added)* |

Region ap-southeast-1 (Singapore)
Account 984263476980
API https://d3aev25xtfpx7z.cloudfront.net/api/v1
App https://main.d2tjfo3h4t5uox.amplifyapp.com
* * *

## User Guide

The full setup and run guide is in [SourceCode/backend/README.md](SourceCode/backend/README.md).

**Quick start (Docker):**

```bash
# Clone
git clone https://github.com/laxmi1707/PatternRecognSystem-Video2Text.git
cd PatternRecognSystem-Video2Text

# Start backend + frontend + DB
docker compose up -d

# Access
# Frontend:  https://main.d2tjfo3h4t5uox.amplifyapp.com/
# API docs:  http://localhost:8000/docs
```

* * *

## Research Questions

| RQ | Question | Experiment |
|----|----------|------------|
| RQ1 | Classical ML vs. deep learning for multimodal activity recognition? | Tier 1 vs. Tier 2 |
| RQ2 | Does multimodal fusion beat individual modalities? | Tier 3 ensemble + modality ablation |
| RQ3 | Can sequence models identify higher-level workflows from activity sequences? | LSTM/Transformer on activity sequences |

* * *

## Architecture

See [architecture.pdf](Miscellaneous/images/architecture.pdf) for the full pipeline diagram.

| Layer | Technologies |
|-------|-------------|
| Frontend | React 18, TypeScript, Vite |
| Backend | Python 3.11, FastAPI, SQLAlchemy (async) |
| ML | PyTorch, scikit-learn, XGBoost, LightGBM, EfficientNet-B0 |
| OCR / Vision | EasyOCR, YOLO, OpenCV, Albumentations |
| Database | PostgreSQL + pgvector |
| Knowledge Generation | Rule-based SOP and runbook from pattern recognition output |
| Cloud | AWS ECS Fargate, S3 |
| CI/CD | GitHub Actions, Docker, MLflow |

* * *

## Project Report

Full report: [ProjectReport/](ProjectReport/) *(final PDF to be linked after Oct 31)*

* * *

## Key Dates

| Date | Milestone |
|------|-----------|
| Sep 15, 2026 | Project proposal submitted |
| Sep 30, 2026 | First presentation (Zoom, 6:30–10:30 pm) |
| Oct 31, 2026 | Final deliverables — code, report, demo video |

* * *

## Miscellaneous

Screenshots and assets: [Miscellaneous/images/](Miscellaneous/images/)

---

*NUS-ISS M.Tech in Artificial Intelligence Systems — ISY5002 Pattern Recognition Systems*
