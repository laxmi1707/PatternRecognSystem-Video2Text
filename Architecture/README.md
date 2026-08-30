# Architecture — Video2Knowledge

## Interactive Diagrams

Open in a browser to view:

| Diagram | File | Description |
|---------|------|-------------|
| AWS Architecture | aws-architecture.html | 6-layer system, multi-tier classifier, team allocation, 24 AWS services |
| Network Diagram | network-diagram.html | VPC layout, multi-AZ subnets, security groups, VPC endpoints |
| Data Flow | data-flow-diagram.html | 9-stage pipeline from video upload to RAG retrieval |

---

## 6-Layer Architecture

    +-----------------------------------------------------------+
    |  L1: Presentation Layer (Joshua)                          |
    |  React SPA -> CloudFront CDN -> Route 53                  |
    +-----------------------------------------------------------+
    |  L2: API & Backend Layer (Muneeswaran)                    |
    |  API Gateway -> ECS Fargate (FastAPI) -> Cognito -> SQS   |
    +-----------------------------------------------------------+
    |  L3: Preprocessing & Feature Extraction (Stalin)          |
    |  Lambda -> Transcribe/Whisper -> Textract/OCR -> YOLO     |
    +-----------------------------------------------------------+
    |  L4: Multi-Tier Classifier (Muneeswaran)                  |
    |  SageMaker -> Tier1 (ML) -> Tier2 (DL) -> Tier3 (Ensemble)|
    +-----------------------------------------------------------+
    |  L5: Data & Storage (Lakshmi)                             |
    |  S3 -> RDS PostgreSQL -> pgvector -> Redis -> DynamoDB    |
    +-----------------------------------------------------------+
    |  L6: Monitoring & CI/CD (Lakshmi)                         |
    |  CloudWatch -> IAM -> GitHub Actions -> WAF               |
    +-----------------------------------------------------------+

---

## Why ECS Fargate (Not EKS)

| Factor | ECS Fargate (Chosen) | EKS (Kubernetes) |
|--------|---------------------|-------------------|
| Complexity | Low | High (K8s manifests, helm, RBAC) |
| Setup time | ~1 hour | ~4-8 hours |
| Monthly cost (dev) | ~$15-30 | ~$75+ ($72 cluster fee alone) |
| Scaling | Auto-scaling built in | Needs HPA, cluster autoscaler |
| Learning curve | Minimal | Significant |
| Academic project fit | Ideal | Overkill |

Decision: ECS Fargate lets the team focus on pattern recognition (core deliverable) instead of infrastructure.

---

## AWS Services (24 Components)

### Compute and Networking

| Service | Purpose |
|---------|---------|
| ECS Fargate | Containerized FastAPI backend (serverless) |
| Lambda | Preprocessing workers (event-driven, no idle cost) |
| API Gateway | REST API routing, rate limiting, auth |
| CloudFront | CDN for React SPA, HTTPS termination |
| Route 53 | DNS management |
| ALB | Application load balancer (multi-AZ) |

### AI / ML

| Service | Purpose |
|---------|---------|
| SageMaker Training | Model training jobs (GPU support) |
| SageMaker Endpoints | Real-time inference (multi-tier classifier) |
| SageMaker Model Monitor | Model drift detection |
| AWS Transcribe | Speech-to-text (ASR) |
| AWS Textract | OCR for screen text extraction |
| AWS Rekognition | Image analysis, UI element detection |
| AWS Bedrock (Claude) | LLM for SOP generation + RAG |

### Data and Storage

| Service | Purpose |
|---------|---------|
| S3 | Videos, frames, artifacts, frontend hosting |
| RDS PostgreSQL | Metadata, analysis results, workflow history |
| pgvector (RDS extension) | Vector embeddings for RAG retrieval |
| OpenSearch | Full-text + vector search at scale |
| ElastiCache (Redis) | Session cache, query cache |
| DynamoDB | Generated SOP metadata index |

### Security and Operations

| Service | Purpose |
|---------|---------|
| Cognito | OAuth2/JWT user authentication |
| IAM | Roles, least-privilege policies |
| Secrets Manager | API keys, DB credentials |
| WAF | Web application firewall (DDoS protection) |
| CloudWatch | Logs, metrics, alarms |

### Orchestration and CI/CD

| Service | Purpose |
|---------|---------|
| Step Functions | ML pipeline orchestration (parallel branches) |
| SQS | Async job queue between layers |
| ECR | Docker image registry |
| GitHub Actions | Build, test, deploy automation |

---

## Data Flow Through AWS

    User Browser
        |
        v
    CloudFront (CDN) --> S3 (React SPA)
        |
        v
    API Gateway --> Cognito (Auth)
        |
        v
    ECS Fargate (FastAPI)
        |
        +---> S3 (video upload via presigned URL)
        |       |
        |       v
        |    Lambda (S3 event trigger)
        |       |
        |       v
        |    Step Functions (orchestrate pipeline)
        |       |
        |       +---> Lambda: Frame extraction (OpenCV + FFmpeg)
        |       +---> AWS Transcribe: Speech -> text
        |       +---> AWS Textract: Screen -> OCR text
        |       +---> Lambda: Audio features (librosa)
        |               |
        |               v (all features collected)
        |
        |    SageMaker Endpoint (Multi-Tier Classifier)
        |       |
        |       +---> Tier 1: SVM, RF, XGBoost (scikit-learn)
        |       +---> Tier 2: CNN, LSTM, Transformer (PyTorch)
        |       +---> Tier 3: Voting, Stacking, Fusion (ensemble)
        |               |
        |               v
        |    AWS Bedrock (LLM -> generate SOP)
        |       |
        |       v
        +---> RDS PostgreSQL (metadata + results)
        +---> pgvector (embeddings for RAG)
        +---> S3 (generated documents)
        +---> ElastiCache (cache)

---

## Environment Strategy

### Four Environments

| Env | Purpose | When Active | Cost/Day |
|-----|---------|-------------|----------|
| dev | Daily development | Always (sprint hours) | ~$3-5 |
| uat | User acceptance testing | Week 5+ | ~$3-5 |
| stg | Pre-production mirror | Week 7+ | ~$8-10 |
| prd | Final demo + submission | Week 8 only (Oct 25-31) | ~$10-15 |

### Activation Timeline

    Week 1-4 (Sep 1-27):      Local + dev
    Week 5-6 (Sep 28-Oct 11): Local + dev + uat
    Week 7   (Oct 12-18):     Local + dev + uat + stg
    Week 8   (Oct 19-31):     Local + dev(scaled down) + stg + prd

### Estimated Total Cost: ~$450 (use NUS AWS Academy credits)

---

## Network Architecture (VPC)

    VPC: 10.0.0.0/16
    |
    +-- Public Subnets (internet-facing)
    |   +-- 10.0.1.0/24 (AZ-a) -- ALB, NAT Gateway
    |   +-- 10.0.2.0/24 (AZ-b) -- ALB standby
    |
    +-- Private App Subnets
    |   +-- 10.0.10.0/24 (AZ-a) -- ECS Fargate, Lambda
    |   +-- 10.0.11.0/24 (AZ-b) -- ECS Fargate replica
    |
    +-- Private ML Subnets
    |   +-- 10.0.20.0/24 (AZ-a) -- SageMaker endpoints
    |   +-- 10.0.21.0/24 (AZ-b) -- SageMaker replica
    |
    +-- Private Data Subnets (isolated)
        +-- 10.0.30.0/24 (AZ-a) -- RDS primary, Redis
        +-- 10.0.31.0/24 (AZ-b) -- RDS standby, OpenSearch

### Security Groups

| SG | Inbound | Outbound | Purpose |
|----|---------|----------|---------|
| sg-alb | :443 from 0.0.0.0/0 | :8000 to sg-ecs | Load balancer |
| sg-ecs | :8000 from sg-alb | :5432, :6379, :9200, :443 | FastAPI |
| sg-lambda | None | :5432, :443 | Preprocessing |
| sg-sagemaker | :8501 from sg-ecs | :443 (S3, ECR) | ML inference |
| sg-rds | :5432 from sg-ecs, sg-lambda | None | Database |
| sg-redis | :6379 from sg-ecs | None | Cache |
| sg-opensearch | :9200 from sg-ecs | None | Vector search |

---

## Branch Protection and Merge Rules

| Branch | Min Approvers | Direct Push | Who Merges |
|--------|--------------|-------------|------------|
| main | 2 required | Blocked | Team lead + 1 reviewer |
| develop | 1 required | Blocked | Any team member |
| feat/* | None | Allowed | Author |
| release/* | 2 required | Blocked | Team lead + 1 reviewer |

### Commit Convention

    feat(ml): add SVM classifier with probability support
    feat(api): add video upload endpoint
    fix(ml): correct confusion matrix label ordering
    test(ml): add cross-validation tests for Tier 1
    docs: update architecture README
    chore: update pyproject.toml dependencies
