# Video2Knowledge

**A Multi-Tier Ensemble Approach for Multimodal Workflow Recognition and Automated Documentation from Software Engineering Screen Recordings**

NUS M.Tech AIS — Pattern Recognition Systems | Semester 2 | 2026

---

## Problem Statement

Recorded engineering sessions (screen recordings of cloud deployments, CI/CD execution, troubleshooting) are difficult to search and reuse. Manual SOP creation is expensive, onboarding is slow, and operational knowledge remains locked inside videos.

## Solution

An AI-powered workflow understanding system that:
1. Processes recorded screen recordings
2. Extracts speech, OCR text, terminal commands, and UI context
3. Recognizes DevOps activities using a multi-tier classifier
4. Generates SOPs, timelines, and knowledge articles automatically
5. Provides searchable knowledge retrieval via RAG

## Architecture (6 Layers)

| Layer | Name | Owner | Directory |
|-------|------|-------|-----------|
| L1 | Presentation | Joshua | SourceCode/frontend/ |
| L2 | API & Backend | Muneeswaran | SourceCode/backend/app/ |
| L3 | Preprocessing & Feature Extraction | Stalin | SourceCode/backend/app/ml/feature_engineering.py |
| L4 | Multi-Tier Classifier | Muneeswaran | SourceCode/backend/app/ml/ |
| L5 | Data & Storage | Lakshmi | SourceCode/backend/app/models/ |
| L6 | Monitoring & CI/CD | Lakshmi | .github/workflows/ |

## Multi-Tier Classifier

| Tier | Type | Algorithms |
|------|------|------------|
| Tier 1 | Classical ML | SVM, Naive Bayes, Decision Tree, Random Forest, KNN, XGBoost, LightGBM |
| Tier 2 | Deep Learning | CNN, LSTM, Transformer, ViT, MLP |
| Tier 3 | Ensemble + Fusion | Voting Classifier, Stacking Classifier, Multimodal Late Fusion |

Target Classes (10): git_operations, docker_workflow, kubernetes_ops, terraform_iac, aws_console, jenkins_ci_cd, coding_editing, debugging, documentation, other

## Team

| Member | Role | Scope |
|--------|------|-------|
| Joshua | Frontend + UI/UX | React dashboard, video upload, workflow visualization |
| Muneeswaran | Backend + Pattern Recognition | FastAPI API, multi-tier classifier, evaluation framework, RAG |
| Stalin | Preprocessing + Feature Extraction | Video ingestion, speech-to-text, OCR, YOLO, audio features |
| Lakshmi | Infrastructure + Data + CI/CD | AWS infra, database, Docker, CI/CD, monitoring |

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Frontend | React, TypeScript, Vite |
| Backend | Python 3.11, FastAPI, SQLAlchemy (async) |
| ML | PyTorch, scikit-learn, XGBoost, LightGBM |
| Database | PostgreSQL, pgvector, Redis |
| Cloud | AWS (ECS Fargate, SageMaker, S3, Lambda, Step Functions) |
| CI/CD | GitHub Actions |

## Quick Start

    # Backend
    cd SourceCode/backend
    python3.11 -m venv .venv
    source .venv/bin/activate
    cp .env.example .env
    pip install -e ".[ml,dev]"
    uvicorn app.main:app --reload --port 8000

    # Frontend
    cd SourceCode/frontend
    npm install
    npm run dev

## AWS Deployment

ECS Fargate + SageMaker (not EKS). See Architecture/README.md for full rationale.

## Branch Strategy

| Branch | Purpose | Deploys To | Approvers |
|--------|---------|------------|-----------|
| main | Production-ready | stg, prd | 2 required |
| develop | Integration | dev | 1 required |
| feat/* | Feature work | local | None |
| release/* | Release candidates | uat | 2 required |

## Documentation

| Document | Description |
|----------|-------------|
| Architecture/README.md | Architecture, AWS decisions, environments, network |
| SourceCode/backend/README.md | Backend setup, ML pipeline, API reference |
| SourceCode/frontend/README.md | Frontend setup, pages, components |
| CHANGELOG.md | Version history |

## Key Dates

| Date | Milestone |
|------|-----------|
| Sep 15, 2026 | Project proposal submission |
| Sep 30, 2026 | First presentation (6:30-10:30pm, Zoom) |
| Oct 31, 2026 | Final deliverables submission |
