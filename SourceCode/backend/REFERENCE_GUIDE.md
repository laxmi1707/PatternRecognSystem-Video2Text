# Reference Guide — Video2Knowledge Backend

A personal reference for Muneeswaran covering every component built so far, why each design decision was made, and how each piece fits into the NUS Pattern Recognition project.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Multi-Tier Classifier — Why 3 Tiers?](#2-multi-tier-classifier--why-3-tiers)
3. [Tier 1 — Classical ML](#3-tier-1--classical-ml)
4. [Tier 2 — Deep Learning](#4-tier-2--deep-learning)
5. [Tier 3 — Ensemble + Fusion](#5-tier-3--ensemble--fusion)
6. [Evaluation Framework](#6-evaluation-framework)
7. [Feature Importance](#7-feature-importance)
8. [Ablation Study](#8-ablation-study)
9. [Embedding Visualization (t-SNE / UMAP)](#9-embedding-visualization-t-sne--umap)
10. [Error Analysis](#10-error-analysis)
11. [Cross-Validation](#11-cross-validation)
12. [API Layer](#12-api-layer)
13. [ORM Models (Database Layer)](#13-orm-models-database-layer)
14. [RAG (Retrieval-Augmented Generation)](#14-rag-retrieval-augmented-generation)
15. [Agentic AI](#15-agentic-ai)
16. [How Everything Connects](#16-how-everything-connects)
17. [NUS Module Coverage Map](#17-nus-module-coverage-map)

---

## 1. Project Overview

### What We're Building

An AI system that watches screen recordings of software engineers and:
1. **Recognizes** what activity they're doing (git, docker, debugging, etc.)
2. **Generates** Standard Operating Procedures (SOPs) from recognized activities
3. **Allows searching** the knowledge base via natural language queries (RAG)

### Why This Matters

- Onboarding new engineers is slow — they watch hours of recordings with no structure
- Operational knowledge is locked inside videos — not searchable or reusable
- Manual SOP creation is expensive and quickly becomes outdated

### The Full Pipeline

    User uploads screen recording
        ↓
    Preprocessing (Stalin): Extract OCR text, UI labels, cursor events, scene data
        ↓
    Feature Engineering: Convert raw features into model-ready vectors
        ↓
    Multi-Tier Classification (You): Recognize which activity each segment shows
        ↓
    SOP Generation (LLM): Convert classified segments into structured documentation
        ↓
    RAG Retrieval: User asks questions → semantic search → LLM-augmented answers
        ↓
    Agentic AI: Orchestrator that reasons, plans, and calls tools to answer complex queries

---

## 2. Multi-Tier Classifier — Why 3 Tiers?

### The Problem with Using One Model

No single model is best at everything:

    SVM:         Fast (12ms), interpretable, but misses complex patterns
    Transformer: Captures long-range patterns, but slow (68ms) and needs lots of data
    Ensemble:    Best accuracy, but slowest and most complex

### The Solution: Tiers

    Tier 1 (Classical ML)     → Fast baseline, interpretable
    Tier 2 (Deep Learning)    → Captures complex patterns classical ML misses
    Tier 3 (Ensemble)         → Combines Tier 1 + 2 for maximum accuracy

### Why This Structure Gets Marks

The NUS module requires demonstrating:

| NUS Requirement | Which Tier Covers It |
|----------------|---------------------|
| Supervised learning | All tiers (all use labeled data) |
| Machine Learning | Tier 1 (classical ML algorithms) |
| Deep Learning | Tier 2 (neural networks — CNN, LSTM, Transformer) |
| Hybrid / Ensemble | Tier 3 (combines Tier 1 + Tier 2) |
| Intelligent sensing | Tier 3 Late Fusion (multimodal feature fusion) |

We cover ALL requirements — this is a strong differentiator for the project.

---

## 3. Tier 1 — Classical ML

**7 classifiers, all using scikit-learn**

| Classifier | Algorithm | How It Works (Simple) | When It's Best |
|------------|-----------|----------------------|----------------|
| SVM | Support Vector Machine | Finds the best boundary line between classes | Small-medium data, clear boundaries |
| Naive Bayes | Gaussian NB | Assumes each feature independently contributes to the class | Very fast, good baseline |
| Decision Tree | Single tree | Series of if/else questions about features | Interpretable, good for explaining |
| Random Forest | 100 decision trees | Each tree votes, majority wins | Robust, handles noise well |
| KNN | K-Nearest Neighbors | Looks at 5 most similar training samples | Simple, no training needed |
| XGBoost | Gradient-boosted trees | Builds trees one at a time, each fixing previous errors | Often wins competitions |
| LightGBM | Fast gradient boosting | Like XGBoost but faster on large data | Production speed |

### Why These Specific 7?

They cover the major families of classical ML:

    Linear boundary  → SVM
    Probabilistic    → Naive Bayes
    Tree-based       → Decision Tree, Random Forest, XGBoost, LightGBM
    Instance-based   → KNN

This breadth shows the examiners you understand the landscape, not just one algorithm.

### BaseClassifier Contract

Every model implements the same interface:

    name       → "svm", "random_forest", etc.
    tier       → "tier1"
    fit(X, y)  → train the model
    predict(X) → PredictionResult(labels, probabilities, latency_ms)
    save/load  → checkpoint to/from disk

This means evaluation code works identically for all 14+ models:

    for model in registry.all():
        result = model.predict(X_test)  # always the same format

---

## 4. Tier 2 — Deep Learning

**4 classifiers, all using PyTorch**

### TorchBaseClassifier — Shared Base

All Tier 2 models share 60% of their code (training loop, prediction, save/load). Each model only defines:
- `_build_model()` → its unique neural network architecture
- `_reshape_input()` → how it reshapes the flat feature vector

### The 4 Models

#### MLP (Multi-Layer Perceptron)

The simplest neural network — stacked fully-connected layers.

    Input: [50 features] → no reshape needed

    50 features → 128 neurons → ReLU → Dropout(30%)
                → 128 neurons → ReLU → Dropout(30%)
                → 10 outputs (one per class)

    Think of it as:
        A more powerful version of Logistic Regression
        Each layer learns increasingly abstract representations
        Dropout prevents memorizing the training data (overfitting)

    When to use: Good default, works on any tabular data

#### CNN1D (1D Convolutional Neural Network)

Treats the feature vector as a signal and slides filters across it.

    Input: [50 features] → reshape to [1 channel × 50 length]

    Sliding window (size 3) scans across features:
        [f1, f2, f3] → pattern detected?
              [f2, f3, f4] → pattern detected?
                    [f3, f4, f5] → pattern detected?

    64 different filters look for 64 different local patterns.
    Pooling summarizes: "Was this pattern present anywhere?"

    When to use: When adjacent features are related (spatial patterns)

    Why 1D not 2D?
        2D = images (height × width)
        1D = our data is a flat feature vector

#### LSTM (Long Short-Term Memory)

Processes features as a sequence, maintaining memory.

    Input: [50 features] → reshape to [10 steps × 5 features per step]

    Reads step-by-step like reading a sentence:
        Step 1: "I see features 1-5"  → update memory
        Step 2: "I see features 6-10" → update memory (remembering step 1)
        ...
        Step 10: "I see features 46-50" → final memory captures everything

    The final memory state is used to predict the class.

    When to use: Temporal/sequential data
    Why it matters for this project:
        Screen recordings ARE temporal — actions happen in order
        "First opened terminal, THEN typed git commit, THEN pushed"
        LSTM can capture this sequential dependency

#### Transformer

Uses self-attention — every part of the input can attend to every other part.

    Input: [50 features] → reshape to [10 tokens × 5 features per token]

    Self-attention asks: "Which tokens matter to each other?"
        Token 3 (features 11-15) might attend to Token 7 (features 31-35)
        Token 1 (features 1-5) might attend to Token 10 (features 46-50)

    This captures LONG-RANGE dependencies that CNN (local window) and
    LSTM (sequential) might miss.

    Same mechanism behind GPT and BERT.

    When to use: When distant features interact
    Why it matters: A user might do something at the start of a recording
        that only makes sense in context of what they do at the end.

### LSTM vs Transformer — Key Difference

    LSTM:        reads left → right (sequential)
    Transformer: sees everything at once (parallel attention)

    LSTM is better with less data (stronger inductive bias)
    Transformer is better with more data (learns its own patterns)

---

## 5. Tier 3 — Ensemble + Fusion

**3 classifiers that combine Tier 1 + Tier 2**

### Why Ensembles Work

Different models make different mistakes:

    SVM wrong on samples:  {12, 45, 78}
    RF wrong on samples:   {23, 45, 91}
    MLP wrong on samples:  {12, 67, 91}

    Only sample 45 fools all three → ensemble gets 99%+ right

### Voting Classifier

Simplest ensemble — average the predictions.

    Soft voting (default): average probability distributions
        SVM:  docker=0.80, git=0.15, k8s=0.05
        RF:   docker=0.70, git=0.20, k8s=0.10
        MLP:  docker=0.90, git=0.05, k8s=0.05
        Avg:  docker=0.80 → predict docker

    Hard voting: majority vote on labels
        SVM → docker, RF → docker, MLP → git
        Majority → docker (2 vs 1)

    Soft voting is better because it uses confidence, not just labels.
    A model that's 99% confident should count more than one at 51%.

### Stacking Classifier

Instead of averaging, train a **meta-learner** on top.

    Step 1: Train SVM, RF, MLP on training data
    Step 2: Get their probability outputs → stack into a new feature matrix
        [SVM_10_probas | RF_10_probas | MLP_10_probas] = 30 meta-features
    Step 3: Train a Logistic Regression on these 30 meta-features

    Why better than voting?
        The meta-learner discovers: "SVM is great at docker but weak at k8s"
        It learns WHICH model to trust for WHICH class
        Voting treats all models equally — stacking doesn't

### Late Fusion (Multimodal)

Each "branch" receives a **different subset of features** (simulating different data modalities), and a meta-learner fuses their outputs.

    In production (with real preprocessing):
        Branch 1 (SVM):    OCR text features
        Branch 2 (RF):     UI detection features
        Branch 3 (LSTM):   Cursor/click features

    During development (with synthetic data):
        Branch 1 (SVM):    features[0:25]   (simulates modality A)
        Branch 2 (RF):     features[25:50]  (simulates modality B)

    Each branch only sees its own modality → specializes
    Meta-learner learns how to combine modality-specific predictions

    Why this is important for NUS:
        This is "intelligent sensing" — the system fuses multiple sensor types
        It proves the architecture handles multimodal data
        Different modalities (visual, text) capture different information

---

## 6. Evaluation Framework

### What We Measure and Why

| Metric | Formula | What It Answers | Why Examiners Care |
|--------|---------|-----------------|-------------------|
| Accuracy | correct / total | "How often is the model right?" | Basic sanity check |
| Precision | TP / (TP+FP) | "When it says docker, is it really?" | False alarms matter |
| Recall | TP / (TP+FN) | "Did it find all docker segments?" | Missing real cases matters |
| F1 | 2×P×R / (P+R) | "Balance of precision and recall" | The go-to single metric |
| AUC | Area under ROC | "How well does it rank predictions?" | Robust to class imbalance |
| Latency | Prediction time | "How fast is it?" | Production viability |

### Why "macro" Average?

    macro = average metric across ALL classes equally

    Class 0 (git):     F1 = 0.92
    Class 1 (docker):  F1 = 0.88
    ...
    Class 9 (other):   F1 = 0.70

    F1_macro = average of all = 0.85

    Every class matters equally — even rare ones.
    "Weighted" average would favor common classes and hide poor performance on rare ones.

### Confusion Matrix

A table showing every prediction vs every actual label:

                     Predicted
                 git    docker    k8s
    Actual git  [ 45      2       3  ]   ← 45 correct, 5 wrong
    Actual docker[  1     42       7  ]   ← 42 correct, 8 wrong
    Actual k8s  [  0      5      38  ]   ← 38 correct, 5 wrong

    Diagonal = correct (high = good)
    Off-diagonal = errors (shows WHICH classes confuse the model)

    Key insight: "docker and k8s are often confused because both show terminal commands"

### ROC Curves

Plot showing the trade-off between catching real positives vs false alarms:

    AUC = 1.00 → perfect classifier
    AUC = 0.95 → excellent
    AUC = 0.80 → good
    AUC = 0.50 → random guess (useless)

    AUC is more robust than accuracy because it's not affected by class imbalance.

---

## 7. Feature Importance

**File:** `app/ml/evaluation/feature_importance.py`

### What It Does

Answers: **"Which features does the model actually rely on to make predictions?"**

### How Permutation Importance Works

    1. Measure baseline accuracy (e.g., 95%)
    2. For each feature:
       a. Shuffle (permute) that feature's values randomly
       b. Measure accuracy again (e.g., 82%)
       c. Importance = drop in accuracy (95% - 82% = 13%)
    3. Repeat n_repeats times for statistical stability
    4. Rank features by average importance

    If shuffling feature X drops accuracy a lot → the model depends on it
    If shuffling feature X barely changes accuracy → the model ignores it

### Why This Matters

    For the report:
        "Features 3, 7, and 12 (corresponding to terminal command frequency,
        window switch rate, and mouse click density) are the most important
        for distinguishing docker_workflow from kubernetes_ops."

    For the project:
        Tells Stalin which preprocessing features are actually useful
        Features with zero importance can be removed → faster, simpler model

### Example Output

    Top 10 features for svm (permutation):
    Rank   Feature      Importance     Std
    1      feature_42   0.1200         0.0080
    2      feature_7    0.0950         0.0120
    3      feature_31   0.0800         0.0060
    ...

### Why Examiners Love This

| What They See | What It Proves |
|--------------|----------------|
| Ranked feature list | You understand what drives predictions |
| Importance scores | Quantitative, not hand-wavy |
| Multiple repeats with std | Statistical rigor |
| "Feature X maps to OCR frequency" | You connect ML to domain knowledge |

---

## 8. Ablation Study

**File:** `app/ml/evaluation/ablation.py`

### What It Does

Answers: **"What happens if we remove an entire modality (feature group)?"**

### How It Works

    1. Train model with ALL features → baseline F1 = 0.95
    2. Zero out OCR features → retrain → F1 = 0.82 (drop = 0.13 = 13.7%)
    3. Zero out UI features → retrain → F1 = 0.90 (drop = 0.05 = 5.3%)
    4. Zero out cursor features → retrain → F1 = 0.75 (drop = 0.20 = 21.1%)
    5. Rank modalities by impact

    Biggest drop = most important modality

### Difference from Feature Importance

    Feature importance: "Which individual features matter?"
        → fine-grained, per-feature

    Ablation study: "Which entire modality matters?"
        → coarse-grained, per-group (OCR, UI, cursor, scene)
        → directly maps to preprocessing pipeline components

### Example Output

    Ablation Study for random_forest (baseline F1: 0.950):
    Modality        F1 without   F1 drop    Drop %
    cursor          0.750        0.200      21.1%    ← most important
    ocr_text        0.820        0.130      13.7%
    ui_labels       0.900        0.050      5.3%
    scene           0.920        0.030      3.2%     ← least important

### Why This Gets Marks

| What They See | What It Proves |
|--------------|----------------|
| Modality removal study | Systematic analysis, not guessing |
| Ranked by impact | Clear understanding of data contribution |
| "Cursor events are critical" | Actionable insight for the pipeline |
| F1 drop percentages | Quantitative evidence |

---

## 9. Embedding Visualization (t-SNE / UMAP)

**File:** `app/ml/evaluation/embeddings.py`

### What It Does

Answers: **"Do our features actually separate the 10 classes into distinct clusters?"**

### How t-SNE Works (Simplified)

    Your data: 50 features per sample (50-dimensional — can't visualize)

    t-SNE compresses 50 dimensions → 2 dimensions while preserving
    which samples are "close" to each other.

    Result: a 2D scatter plot where:
        - Samples of the same class cluster together (good!)
        - Different classes are separated (good!)
        - If classes overlap → the classifier will struggle there

### What the Output Looks Like

    Imagine a 2D plot:

        ●●●           ▲▲▲
       ●●●●●        ▲▲▲▲▲          ■■■
        ●●●           ▲▲             ■■■■
                                      ■■
      (git_ops)    (docker)        (k8s)

    Clear clusters = features separate classes well
    Overlapping clusters = classifier will confuse those classes

### t-SNE vs UMAP

    t-SNE: Better at showing local structure (nearby clusters)
    UMAP: Better at preserving global structure (distances between clusters)
           Also much faster on large datasets

    We provide both. t-SNE is always available (sklearn).
    UMAP requires installing umap-learn (optional).

### Why This Gets Marks

| What They See | What It Proves |
|--------------|----------------|
| 2D cluster visualization | Visual proof the features work |
| Color-coded by class | Clear presentation |
| "docker and k8s overlap" | Explains confusion matrix findings |
| Both t-SNE and UMAP | Thorough analysis |

---

## 10. Error Analysis

**File:** `app/ml/evaluation/error_analysis.py`

### What It Does

Answers: **"WHERE does the model fail, and WHY?"**

Goes beyond accuracy to dissect every misclassification.

### Three Types of Analysis

#### 1. Most Confused Class Pairs

    "Which two classes does the model confuse most often?"

    docker_workflow ↔ kubernetes_ops:  15 errors (8 + 7)
    coding_editing ↔ debugging:        9 errors (5 + 4)
    terraform_iac ↔ aws_console:       6 errors (4 + 2)

    WHY: Docker and K8s both show terminal commands, container-related text.
    This finding directly guides feature engineering improvements.

#### 2. Highest-Confidence Misclassifications

    "Which errors was the model MOST confident about?"

    Sample 42: debugging → coding_editing (confidence: 0.91!)
        The model was 91% sure it was coding, but it was actually debugging.
        These are the WORST errors — the model is confidently wrong.

    This reveals blind spots in the feature representation.

#### 3. Per-Class Error Rate

    "Which classes are hardest?"

    debugging          15.0% ################
    kubernetes_ops     12.0% ############
    terraform_iac       8.0% ########
    docker_workflow     5.0% #####
    git_operations      2.0% ##
    ...

    Tells you exactly which classes need more training data or better features.

### Why This Gets Marks

| What They See | What It Proves |
|--------------|----------------|
| Confused pairs | Deep understanding of model weaknesses |
| High-confidence errors | Critical failure mode analysis |
| Per-class breakdown | Systematic, not just top-line metrics |
| "Debugging confused with coding because..." | Domain insight |

---

## 11. Cross-Validation

**File:** `app/ml/evaluation/cross_validation.py`

### What Is Cross-Validation?

A single train/test split is like flipping a coin once — the result depends on luck (which samples landed where). Cross-validation flips the coin 5 times.

    5-Fold CV:

    Fold 1: [TEST][train][train][train][train] → accuracy = 0.95
    Fold 2: [train][TEST][train][train][train] → accuracy = 0.93
    Fold 3: [train][train][TEST][train][train] → accuracy = 0.96
    Fold 4: [train][train][train][TEST][train] → accuracy = 0.94
    Fold 5: [train][train][train][train][TEST] → accuracy = 0.95

    Mean = 0.946, Std = 0.010

    Every sample appears in the test set exactly once.

### Why Stratified?

    Regular split might accidentally put all docker samples in training
    and none in testing → misleading results.

    Stratified split keeps class proportions the same in every fold:
        Each fold has ~20% git, ~20% docker, ~20% k8s, etc.

### Reading CV Results

    Model          Acc (mean±std)    F1 (mean±std)
    SVM            0.980 ± 0.012     0.978 ± 0.015
    Random Forest  0.975 ± 0.018     0.970 ± 0.020

    Low std (0.012) → model is consistent (good!)
    High std (0.050) → model is unstable, depends on which data it sees (bad!)

---

## 12. API Layer

**Files:** `app/routers/`, `app/schemas/`, `app/services/`

### Why an API?

The classifiers are Python objects. The React frontend is JavaScript. They can't talk directly. The API is the bridge:

    React (JavaScript)  →  HTTP request  →  FastAPI (Python)  →  ML Pipeline
                        ←  JSON response  ←

### Architecture (3 Layers)

    Router (thin)     → validates input, returns response
    Service (logic)   → MLService orchestrates classifiers
    ML Pipeline       → registry, classifiers, evaluation

    Why separate layers?
        Router shouldn't know about PyTorch
        ML Pipeline shouldn't know about HTTP
        Service layer bridges them

### Endpoints

| Method | Endpoint | What It Does |
|--------|----------|-------------|
| GET | `/health` | Health check (is the server running?) |
| GET | `/api/v1/evaluation/models` | List all 14 models grouped by tier |
| POST | `/api/v1/classification/predict` | Classify one feature vector |
| POST | `/api/v1/classification/predict/batch` | Classify multiple at once |
| POST | `/api/v1/evaluation/run` | Run full comparative evaluation |
| POST | `/api/v1/evaluation/cross-validation` | Run 5-fold CV |

### Lazy Training

    Problem: Training all 14 models takes ~60 seconds
    Solution: Only train the requested model on first use

    First request for SVM:  trains SVM (~1s), caches it
    Second request for SVM: uses cached model (~12ms)
    First request for LSTM: trains LSTM (~3s), caches it

### Schemas (Pydantic v2)

Type-safe request/response models:

    ClassifyRequest:
        features: list[float]       # [0.5, 0.3, 0.8, ...]
        model_name: str | None      # "svm" (optional, defaults to "svm")

    ClassificationResult:
        label: "docker_workflow"     # predicted activity
        confidence: 0.87            # how sure the model is
        probabilities: {...}        # confidence for all 10 classes
        model_name: "svm"           # which model was used
        latency_ms: 12.5            # how fast

    These auto-generate OpenAPI docs at /docs (Swagger UI).

---

## 13. ORM Models (Database Layer)

### What is ORM?

**ORM (Object-Relational Mapping)** = interact with the database using Python classes instead of raw SQL.

    Without ORM (raw SQL):
        cursor.execute("INSERT INTO videos (filename, status) VALUES ('demo.mp4', 'uploaded')")
        cursor.execute("SELECT * FROM videos WHERE id = 1")
        row = cursor.fetchone()
        filename = row[0]   # which column is this? easy to mess up

    With ORM (SQLAlchemy):
        video = Video(filename="demo.mp4", status="uploaded")
        db.add(video)

        video = db.get(Video, 1)
        print(video.filename)   # clear, type-safe, IDE autocomplete

### How ORM Maps Python to SQL

    Python class Video          ←→    PostgreSQL table "videos"
    ├── id: int                        id SERIAL PRIMARY KEY
    ├── filename: str                  filename VARCHAR(255)
    ├── status: str                    status VARCHAR(50)
    ├── uploaded_at: datetime          uploaded_at TIMESTAMP
    └── results: list[Result]          (foreign key from results table)

### Why We Need a Database

Right now everything is **in-memory** — when the server restarts, all data is lost.

For the project to work end-to-end:

    1. User uploads video         → Video record created in DB
    2. Preprocessing starts       → Job record: status="processing"
    3. Features extracted          → Features stored in DB
    4. Classification runs         → ClassificationResult records written
    5. Evaluation completed        → Job status → "completed"
    6. Frontend fetches results    → Reads from DB → displays in dashboard
    7. User asks a question (RAG)  → Searches DB + vector store

### What Models We Need

| Model | Table | Purpose |
|-------|-------|---------|
| Video | videos | Track uploaded screen recordings |
| AnalysisJob | analysis_jobs | Track processing status (queued → processing → completed) |
| ClassificationResult | classification_results | Store per-segment predictions |
| EvaluationRun | evaluation_runs | Store comparative evaluation reports |

### Why SQLAlchemy (Not Raw SQL)?

| Reason | Detail |
|--------|--------|
| **Safety** | Auto-escapes parameters → prevents SQL injection |
| **Portability** | Same code works on SQLite (local) and PostgreSQL (AWS) |
| **Relationships** | `video.results` automatically joins tables |
| **Migrations** | Schema changes tracked in version control (via Alembic) |
| **Async** | SQLAlchemy 2.0 supports `async/await` → matches FastAPI |
| **Industry standard** | Most Python backends use SQLAlchemy |

### How It Fits Our Architecture

    React Frontend
        ↓ (HTTP)
    FastAPI Router
        ↓
    Service Layer (MLService, VideoService, JobService)
        ↓                    ↓
    ML Pipeline          SQLAlchemy ORM
    (classifiers)        (database)
                             ↓
                    SQLite (local) / PostgreSQL (AWS)

### The Data Flow That Needs a Database

    1. Joshua's frontend:     POST /api/v1/videos/upload
                              → creates Video + Job records

    2. Stalin's preprocessing: GET /api/v1/jobs/{id} (polls status)
                              → updates Job status, writes features

    3. Your classifier:       reads features from DB
                              → runs Tier 1+2+3
                              → writes ClassificationResult records
                              → updates Job → "completed"

    4. Joshua's frontend:     GET /api/v1/jobs/{id}/results
                              → reads ClassificationResult from DB
                              → displays timeline, labels, confidence

    Without a database: None of this works.

---

## 14. RAG (Retrieval-Augmented Generation)

### What is RAG?

RAG = let an LLM answer questions using YOUR data, not just its training data.

    Without RAG:
        User: "How did the team deploy with Docker last week?"
        LLM: "Docker deployment typically involves..." (generic, not your data)

    With RAG:
        User: "How did the team deploy with Docker last week?"
        System: searches your processed video SOPs → finds relevant segments
        LLM: "In the recording from Sep 2, the engineer ran docker-compose up
              with a custom network, then verified with docker ps..." (specific!)

### How RAG Works

    Step 1: INDEXING (done once, when SOPs are generated)
        SOP text → split into chunks (200-500 words each)
        Each chunk → embedding model → 768-dimensional vector
        Vectors stored in pgvector (PostgreSQL extension)

    Step 2: RETRIEVAL (done per query)
        User query → embedding model → query vector
        Query vector → pgvector similarity search → top 5 most similar chunks

    Step 3: GENERATION (done per query)
        Retrieved chunks + user query → Claude (via AWS Bedrock) → answer

    The key insight: the LLM answers FROM your data, not from memory.

### Our Stack for RAG

    Embedding model:    sentence-transformers (local) or Bedrock Titan Embeddings
    Vector store:       pgvector (PostgreSQL extension — already in our stack)
    LLM:                Claude via AWS Bedrock (already in our architecture)

    Why pgvector (not a dedicated vector DB like Pinecone)?
        - Already using PostgreSQL for everything else
        - No extra service to manage
        - Good enough for our scale (thousands of SOPs, not millions)
        - One fewer cloud service = simpler architecture + lower cost

---

## 15. Agentic AI

### What Makes It "Agentic"?

A regular pipeline is like a conveyor belt — fixed steps in fixed order:

    video → preprocess → classify → generate SOP → done

An agentic system is like a smart assistant — it THINKS about what to do:

    User: "Compare the Docker workflows from Monday and Wednesday recordings"

    Agent thinks:
        1. I need to find recordings from Monday → search_videos(date="Monday")
        2. I need to find recordings from Wednesday → search_videos(date="Wednesday")
        3. I need Docker segments from both → classify + filter(label="docker_workflow")
        4. I need to compare them → compare_workflows(video_a, video_b)
        5. Let me synthesize the comparison → generate answer

    The agent DECIDES which tools to call and in what order.
    A fixed pipeline can't handle this — it doesn't reason.

### How It Works (Claude Tool Use)

    You define TOOLS the agent can use:

    tools = [
        {
            "name": "search_knowledge_base",
            "description": "Search SOPs and video knowledge base",
            "parameters": {"query": "string"}
        },
        {
            "name": "classify_segment",
            "description": "Run classifier on feature vector",
            "parameters": {"features": "array", "model": "string"}
        },
        {
            "name": "get_video_timeline",
            "description": "Get classified timeline for a video",
            "parameters": {"video_id": "string"}
        },
    ]

    You send the user's question + tools to Claude (via Bedrock).
    Claude decides which tools to call, you execute them, return results.
    Claude reasons over results and either calls more tools or gives the answer.

### Why Agentic (Not Just RAG)?

    RAG alone: "Find me Docker info" → search → answer
        Simple question → simple retrieval

    Agentic: "What changed in our Docker deployment between v1 and v2?"
        → search for v1 recordings → classify → extract Docker segments
        → search for v2 recordings → classify → extract Docker segments
        → compare the two → synthesize differences
        Multi-step reasoning that RAG alone can't do

### How It Fits Our Architecture

    User Query
        ↓
    AI Agent (Claude via Bedrock)
        ↓ (reasons, plans)
    Tool Calls:
        ├── classify_segment()        → ML Pipeline
        ├── search_knowledge_base()   → RAG (pgvector)
        ├── get_video_timeline()      → Database
        ├── generate_sop()            → LLM
        └── compare_workflows()       → Custom logic
        ↓
    Synthesized Answer

---

## 16. How Everything Connects

### Full System Map

    app/
    ├── main.py                  ← FastAPI app, router registration
    ├── config.py                ← Settings (DB URL, CORS, etc.)
    ├── schemas/                 ← Pydantic request/response models
    │   ├── classification.py    ← ClassifyRequest, ClassificationResult
    │   └── evaluation.py        ← EvalReport, CVReport
    ├── services/                ← Business logic
    │   └── ml_service.py        ← MLService (lazy training, classify, evaluate)
    ├── routers/                 ← API endpoints
    │   ├── classification.py    ← /predict, /predict/batch
    │   └── evaluation.py        ← /models, /run, /cross-validation
    ├── models/                  ← ORM models (TODO)
    └── ml/
        ├── base.py              ← BaseClassifier contract
        ├── config.py            ← MLConfig (seed, labels, classes)
        ├── registry.py          ← Model registry
        ├── dataset.py           ← Synthetic data generator
        ├── classifiers/
        │   ├── tier1/           ← 7 classical ML (DONE)
        │   ├── tier2/           ← 4 deep learning (DONE)
        │   └── tier3/           ← 3 ensemble (DONE)
        └── evaluation/
            ├── metrics.py           ← Accuracy, F1, AUC (DONE)
            ├── confusion.py         ← Confusion matrices (DONE)
            ├── roc_curves.py        ← ROC/AUC curves (DONE)
            ├── report.py            ← Comparative report (DONE)
            ├── cross_validation.py  ← 5-fold CV (DONE)
            ├── feature_importance.py← Permutation importance (DONE)
            ├── ablation.py          ← Modality removal (DONE)
            ├── embeddings.py        ← t-SNE / UMAP (DONE)
            └── error_analysis.py    ← Misclassification analysis (DONE)

### Current Status

    ✅ 14 classifiers (7 Tier 1 + 4 Tier 2 + 3 Tier 3)
    ✅ 8 evaluation modules
    ✅ REST API (5 endpoints)
    ✅ Lazy-training service
    ⬜ ORM models (database persistence)
    ⬜ SOP generation (LLM integration)
    ⬜ RAG pipeline (embedding + retrieval)
    ⬜ Agentic layer (tool-use orchestrator)

---

## 17. NUS Module Coverage Map

| NUS Requirement | How We Cover It | Component |
|----------------|-----------------|-----------|
| Supervised learning | All classifiers use labeled training data | Tier 1, 2, 3 |
| Machine Learning | 7 classical ML algorithms | Tier 1 |
| Deep Learning | 4 neural networks (MLP, CNN, LSTM, Transformer) | Tier 2 |
| Hybrid / Ensemble | 3 ensemble methods (Voting, Stacking, Late Fusion) | Tier 3 |
| Intelligent sensing | Multimodal late fusion (fuses OCR + UI + cursor + scene) | Tier 3 Late Fusion |
| Comparative evaluation | 14 models compared on 6 metrics with 5-fold CV | Evaluation Framework |
| Interpretability | Feature importance, ablation study, error analysis | Evaluation Framework |
| Visualization | t-SNE/UMAP embeddings, confusion matrices, ROC curves | Evaluation Framework |
| Practical application | REST API, database persistence, SOP generation, RAG | API + Pipeline |
| Advanced AI | Agentic AI with tool-use reasoning over the knowledge base | Agentic Layer |
