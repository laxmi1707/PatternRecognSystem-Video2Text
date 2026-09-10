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

---

## Git Branching Strategy

### Branch Flow

    Joshua:  feat/frontend-dashboard --+
                                       |
    Muneeswaran: feat/pattern-recognition --+---> develop ---> release/* ---> main
                                       |      (dev env)    (uat env)     (prd env)
    Stalin:  feat/preprocessing -------+
                                       |
    Lakshmi: feat/infra-data ----------+

### Branch Purposes

| Branch | Purpose | Deploys To | Approvers |
|--------|---------|------------|-----------|
| feat/* | Individual feature work. Each member works here daily. | Local only | None |
| develop | Integration branch. All members merge here to test together. | dev environment | 1 approver |
| release/* | Release candidate. Frozen for UAT testing before presentations. | uat environment | 2 approvers |
| main | Production-ready. Only verified, tested code lives here. | stg, prd environments | 2 approvers |

### Why We Use a develop Branch

Without develop:

    feat/* --> main (RISKY: untested integration, could break production)

With develop:

    feat/* --> develop (test together, catch conflicts) --> main (safe, verified)

### How Each Member Works

    # 1. Start new work
    git checkout develop
    git pull origin develop
    git checkout -b feat/my-feature

    # 2. Work on your feature
    git add .
    git commit -m "feat(ml): add SVM classifier"
    git push origin feat/my-feature

    # 3. Create Pull Request to develop (on GitHub)
    #    1 team member reviews and approves
    #    Merge to develop -> auto-deploys to dev

    # 4. For release (before presentations)
    #    PR from develop to release/v0.2.0
    #    Auto-deploys to uat, team tests

    # 5. Promote to production
    #    PR from release/* to main
    #    2 approvers required
    #    Auto-deploys to stg, manual promote to prd

### Commit Message Convention

    feat(ml): add SVM classifier with probability support
    feat(api): add video upload endpoint
    feat(frontend): add video dropzone component
    fix(ml): correct confusion matrix label ordering
    test(ml): add cross-validation tests for Tier 1
    docs: update architecture README
    chore: update pyproject.toml dependencies

    Format: type(scope): description
    Types: feat, fix, test, docs, chore, refactor, ci
    Scopes: ml, api, frontend, infra, db

---

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
