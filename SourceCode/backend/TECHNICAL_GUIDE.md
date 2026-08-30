# Technical Guide — Video2Knowledge ML Pipeline

A detailed explanation of every component in the Multi-Tier Classifier and Evaluation Framework.
Written for team members and lecturers to understand the design decisions and implementation.

---

## Table of Contents

1. BaseClassifier Contract
2. ML Config
3. Model Registry
4. SVM Classifier (Tier 1 Pattern)
5. Synthetic Dataset
6. Evaluation Metrics
7. Confusion Matrix
8. ROC Curves
9. Report Generator
10. Multi-Tier Classifier Architecture
11. How Everything Connects

---

## 1. BaseClassifier Contract

**File:** `app/ml/base.py`

This is the contract that every classifier (all 15+ models) must follow. Think of it like an interface.

### PredictionResult

    @dataclass(frozen=True)
    class PredictionResult:
        labels: np.ndarray        # What the model predicted: [3, 1, 7, 0, ...]
        probabilities: np.ndarray # Confidence per class: [[0.1, 0.8, ...], ...]
        latency_ms: float         # How long prediction took: 12.5ms

- `frozen=True` — immutable, cannot accidentally change results after prediction
- `labels` — predicted class index for each sample (e.g., 0=git_operations, 1=docker_workflow)
- `probabilities` — needed for ROC curves, confidence scores, and ensemble voting
- `latency_ms` — needed for the comparative table (which model is fastest)

### BaseClassifier (Abstract Base Class)

    class BaseClassifier(ABC):
        name  -> "svm", "cnn", "voting_ensemble"   # identifies the model
        tier  -> "tier1", "tier2", "tier3"          # which tier it belongs to

        fit(X, y)    -> trains the model            # same interface for SVM, CNN, everything
        predict(X)   -> returns PredictionResult    # uniform output format
        save(path)   -> saves model to disk         # checkpoint for reuse
        load(path)   -> loads model from disk       # restore without retraining
        get_params() -> returns hyperparameters     # for reproducibility tracking

### Why This Design Matters

Without this contract:

    # Every model returns differently — evaluation is a mess
    svm_result = svm.predict(X)              # returns numpy array
    cnn_result = cnn(torch.tensor(X))        # returns torch tensor
    rf_result = rf.predict_proba(X)          # returns probabilities only

With this contract:

    # Every model returns the same thing — evaluation is simple
    for model in [svm, cnn, rf, lstm, voting]:
        result = model.predict(X)            # always PredictionResult
        print(result.labels)                 # always numpy array
        print(result.probabilities)          # always numpy array
        print(result.latency_ms)             # always float

### _timed_predict Helper

    def _timed_predict(self, predict_fn, X):
        start = time.perf_counter()          # start timer
        labels, probas = predict_fn(X)       # run the actual prediction
        elapsed_ms = ...                     # calculate time
        return PredictionResult(...)         # wrap in standard format

Each classifier calls this instead of manually timing. Ensures consistent latency measurement across all models.

---

## 2. ML Config

**File:** `app/ml/config.py`

### Activity Labels (Target Classes)

    ACTIVITY_LABELS = [
        "git_operations",     # 0 — git commit, push, merge, etc.
        "docker_workflow",    # 1 — docker build, run, compose
        "kubernetes_ops",     # 2 — kubectl, helm, pod management
        "terraform_iac",      # 3 — terraform plan, apply, destroy
        "aws_console",        # 4 — AWS web console operations
        "jenkins_ci_cd",      # 5 — Jenkins pipeline, builds
        "coding_editing",     # 6 — writing code in IDE
        "debugging",          # 7 — setting breakpoints, inspecting errors
        "documentation",      # 8 — writing docs, README, wiki
        "other",              # 9 — anything that doesn't fit above
    ]

These are the 10 workflow categories the classifier predicts. When the model sees a video segment, it answers: "This is a docker_workflow with 87% confidence."

Note: These describe what the VIDEO SHOWS, not our infrastructure. For example, `kubernetes_ops` means the person in the video is using kubectl — even though our project runs on ECS Fargate.

### MLConfig

    @dataclass(frozen=True)
    class MLConfig:
        seed: int = 42           # Random seed — same seed = same results every time
        test_size: float = 0.2   # 80% train, 20% test split
        cv_folds: int = 5        # 5-fold cross-validation
        model_dir: str = "./models"  # Where to save trained models
        num_classes: int = 10    # Number of target classes
        labels: tuple[str, ...]  # The class names

| Field | Purpose | Why It Matters |
|-------|---------|----------------|
| seed = 42 | Reproducibility — examiner runs your code, gets same results | Required for academic work |
| test_size = 0.2 | Standard 80/20 split | Standard practice |
| cv_folds = 5 | 5-fold cross-validation for robust evaluation | High marks |
| model_dir | Save/load trained models without retraining | Production readiness |

`frozen=True` means the config cannot be accidentally modified during a run.

---

## 3. Model Registry

**File:** `app/ml/registry.py`

Think of it like a phone book for classifiers. You register models, then look them up by name or tier.

### How It Works

    registry = ModelRegistry()

    # Register models
    registry.register(svm_model)       # name="svm", tier="tier1"
    registry.register(cnn_model)       # name="cnn", tier="tier2"
    registry.register(voting_model)    # name="voting", tier="tier3"

    # Look up by name
    model = registry.get("svm")

    # Get all Tier 1 models
    tier1 = registry.list_by_tier("tier1")  # [svm, naive_bayes, rf, ...]

    # Get everything
    all_models = registry.all()

### Methods

| Method | What It Does | Used By |
|--------|-------------|---------|
| register(model) | Adds a classifier to the registry | App startup |
| get(name) | Fetch one model by name | API: "classify with SVM" |
| list_by_tier(tier) | Get all models in a tier | Evaluation: "compare all Tier 1" |
| all() | Get every registered model | Evaluation: "run all 15+ models" |
| names() | List all model names | API: "what models are available?" |

### Why We Need This

Without registry — hardcoded everywhere, painful to add new models.
With registry — add a model once, evaluation picks it up automatically.

---

## 4. SVM Classifier (Tier 1 Pattern)

**File:** `app/ml/classifiers/tier1/svm.py`

### What is SVM?

Support Vector Machine — a classical ML algorithm that finds the best boundary (hyperplane) to separate classes.

    Imagine 2D space with dots of different colors:

        o o o          x x x
          o o    |    x x
        o o      |      x x x
                 |
             boundary (SVM finds this line)

For 10 classes, SVM creates multiple boundaries to separate all classes.

### Key Parameters

| Parameter | What It Does | Why This Value |
|-----------|-------------|----------------|
| kernel="rbf" | Shape of the decision boundary | RBF handles non-linear data well |
| C=1.0 | How strictly to classify | Standard default |
| probability=True | Enables confidence scores per class | Needed for ROC curves + ensemble voting |
| random_state=42 | Same results every run | Academic reproducibility |

### Predict Output Example

    PredictionResult(
        labels = [3, 1, 7],           # terraform, docker, debugging
        probabilities = [
            [0.02, 0.05, 0.03, 0.80, ...],  # 80% confident it's terraform
            [0.01, 0.85, 0.02, 0.01, ...],  # 85% confident it's docker
            [0.01, 0.02, 0.01, 0.01, ...],  # debugging
        ],
        latency_ms = 12.5             # took 12.5ms
    )

### All Tier 1 Classifiers Follow This Pattern

| Classifier | sklearn Model | Key Difference |
|------------|--------------|----------------|
| SVM | SVC(probability=True) | Finds optimal boundary |
| Naive Bayes | GaussianNB() | Assumes feature independence |
| Decision Tree | DecisionTreeClassifier | Series of if/else splits |
| Random Forest | RandomForestClassifier | 100 decision trees voting |
| KNN | KNeighborsClassifier | Finds 5 nearest neighbors |
| XGBoost | XGBClassifier | Gradient-boosted trees |
| LightGBM | LGBMClassifier | Fast gradient boosting |

Each wraps a different sklearn/library model inside the same BaseClassifier interface.

---

## 5. Synthetic Dataset

**File:** `app/ml/dataset.py`

### Purpose

Generates fake but realistic data so we can develop and test without waiting for real preprocessing data from Stalin's pipeline.

### How It Works

    generate_synthetic_dataset(n_samples=500, n_features=200)

For each of the 10 classes:
- Creates a unique center point in feature space
- Adds random noise around that center
- Each class is slightly different so classifiers can learn to distinguish them

    Class 0 (git):      center at [0.3, 0.6, ...]  + noise
    Class 1 (docker):   center at [0.6, 1.2, ...]  + noise
    Class 2 (k8s):      center at [0.9, 1.8, ...]  + noise
    ...
    Class 9 (other):    center at [3.0, 6.0, ...]  + noise

The data is shuffled and uses a fixed seed (42) so every run produces the same dataset.

### train_test_split_data

    X_train, X_test, y_train, y_test = train_test_split_data(X, y)

Splits 80% for training, 20% for testing. Same seed ensures reproducible splits.

---

## 6. Evaluation Metrics

**File:** `app/ml/evaluation/metrics.py`

Calculates all the scores shown in the comparative table.

### What Each Metric Means

    Example: Model predicts "docker_workflow" for 100 video segments

                            Predicted Docker    Predicted Other
    Actual Docker              80 (TP)             20 (FN)
    Actual Other               10 (FP)            890 (TN)

| Metric | Formula | What It Answers | Example |
|--------|---------|-----------------|---------|
| Accuracy | correct / total | "How often is the model right?" | 970/1000 = 0.97 |
| Precision | TP / (TP + FP) | "When it says docker, is it really?" | 80/90 = 0.89 |
| Recall | TP / (TP + FN) | "Did it find all docker segments?" | 80/100 = 0.80 |
| F1 | 2 * P * R / (P + R) | "Balance of precision and recall" | 0.84 |
| AUC | Area under ROC curve | "How well does it rank correct vs incorrect?" | 0.97 |
| Latency | Prediction time | "How fast is it?" | 12.5ms |

### Why "macro" Average

    macro = average the metric across all 10 classes equally

    Class 0 (git):     F1 = 0.90
    Class 1 (docker):  F1 = 0.82
    Class 2 (k8s):     F1 = 0.78
    ...
    Class 9 (other):   F1 = 0.70

    F1_macro = (0.90 + 0.82 + 0.78 + ... + 0.70) / 10 = 0.85

Every class matters equally — even rare ones. Fairer than "weighted" which favors common classes.

### Per-Class Metrics

f1_per_class and auc_per_class show which classes the model struggles with:

    F1 per class:
      git_operations:   0.92  <- easy to classify
      docker_workflow:  0.88
      kubernetes_ops:   0.75  <- often confused with docker
      debugging:        0.65  <- hardest class

This is valuable for the error analysis section in the report.

---

## 7. Confusion Matrix

**File:** `app/ml/evaluation/confusion.py`

### What Is a Confusion Matrix?

A table showing every prediction vs every actual label.

    Example with 3 classes:

                         Predicted
                     git    docker    k8s
    Actual git      [ 45      2       3  ]   <- 45 correct, 5 wrong
    Actual docker   [  1     42       7  ]   <- 42 correct, 8 wrong
    Actual k8s      [  0      5      38  ]   <- 38 correct, 5 wrong

### Reading the Matrix

    Row = what the video ACTUALLY was
    Column = what the model PREDICTED

    matrix[i][j] = "how many times actual class i was predicted as class j"

| Cell | Meaning |
|------|---------|
| matrix[0][0] = 45 | 45 git videos correctly classified as git |
| matrix[1][2] = 7 | 7 docker videos WRONGLY classified as k8s |
| matrix[2][1] = 5 | 5 k8s videos WRONGLY classified as docker |

### What It Tells You

Diagonal (top-left to bottom-right) = correct predictions. High diagonal = good model.

Off-diagonal = misclassifications. Shows which classes confuse the model.

Example finding for the report: "The classifier struggles to distinguish docker_workflow from kubernetes_ops due to shared visual patterns (terminal UI, container-related commands)."

### Why This Gets Marks

| In Your Report | What It Shows |
|----------------|---------------|
| One confusion matrix per model | Thoroughness |
| Compare SVM vs CNN matrices | Which model handles hard classes better |
| Highlight off-diagonal clusters | Shows you understand failure modes |
| "K8s confused with Docker" | Error analysis — examiners love this |

---

## 8. ROC Curves

**File:** `app/ml/evaluation/roc_curves.py`

### What is ROC?

Receiver Operating Characteristic — a plot showing the trade-off between catching real positives and falsely flagging negatives.

For each class, the model gives a confidence score (0.0 to 1.0). ROC asks: "If we change the threshold for calling something docker, how does performance change?"

### Example

    Video segments with model's confidence for "docker_workflow":

    Segment  | Actual  | Confidence
    ---------|---------|----------
    A        | docker  | 0.95  <- high confidence, correct
    B        | docker  | 0.82  <- correct
    C        | git     | 0.70  <- WRONG (false positive)
    D        | docker  | 0.45  <- correct
    E        | k8s     | 0.30  <- correctly low
    F        | docker  | 0.20  <- missed (false negative)

    If threshold = 0.80: catches A, B (2/4) but no false positives
    If threshold = 0.40: catches A, B, D (3/4) but C is false positive
    If threshold = 0.10: catches all 4 but also C and E are false positives

### The ROC Plot

    TPR (how many real dockers we catch)
      1.0 |            ___------    <- perfect classifier
          |          /
          |        /
          |      /         <- our model (AUC = 0.95)
      0.5 |    /
          |  /       /
          | /      /       <- random guess (AUC = 0.50)
      0.0 +---------------
          0.0    0.5    1.0
          FPR (how many non-dockers we wrongly flag)

### AUC (Area Under Curve)

    AUC = 1.00 -> perfect classifier
    AUC = 0.95 -> excellent
    AUC = 0.80 -> good
    AUC = 0.50 -> random guess (useless)

### The Two Axes

| Axis | Name | Meaning |
|------|------|---------|
| Y-axis | TPR (True Positive Rate) | "Of all real dockers, how many did we catch?" |
| X-axis | FPR (False Positive Rate) | "Of all non-dockers, how many did we wrongly flag?" |

### Why This Gets Marks

| What Examiners See | What It Proves |
|-------------------|----------------|
| ROC curve per model | Thorough evaluation, not just accuracy |
| AUC per class | You know WHICH classes are hard |
| Compare SVM ROC vs CNN ROC | Visual proof of performance difference |
| AUC > 0.90 | Your classifier actually works |

AUC is considered more robust than accuracy because it is not affected by class imbalance.

---

## 9. Report Generator

**File:** `app/ml/evaluation/report.py`

### What It Does

The brain of the evaluation framework. Takes all classifiers, trains them, tests them, and produces the full comparative report.

### The Process

    For EACH classifier (SVM, RF, CNN, LSTM, Voting, ...):

    Step 1: Train it
        clf.fit(X_train, y_train)

    Step 2: Predict on test data
        result = clf.predict(X_test)

    Step 3: Compute metrics (accuracy, F1, AUC, etc.)
        metrics = compute_metrics(...)

    Step 4: Compute confusion matrix
        cm = compute_confusion_matrix(...)

    Step 5: Compute ROC curves
        roc = compute_roc_curves(...)

    Step 6: Store in report
        report.comparison_table.append(metrics)

    After all models: sort by F1 score (best first)

### Output

    Model                Tier       Acc   Prec    Rec     F1    AUC       ms
    -----------------------------------------------------------------------
    voting_ensemble      tier3    0.940  0.930  0.950  0.940  0.990    85.00
    transformer          tier2    0.910  0.900  0.920  0.910  0.985    68.00
    xgboost              tier1    0.870  0.860  0.880  0.870  0.975    22.00
    svm                  tier1    0.820  0.810  0.830  0.820  0.960    12.00
    naive_bayes          tier1    0.710  0.680  0.740  0.710  0.920     5.00

### How It All Connects

    registry.all()
        |
        v
    ReportGenerator(classifiers=registry.all())
        |
        v
    report = generator.run(X_train, y_train, X_test, y_test)
        |
        +--- comparison_table   (15 rows, one per model)
        +--- confusion_matrices (15 matrices)
        +--- roc_curves         (15 curve sets)

Add a new model to the registry -> it automatically appears in the report.

---

## 10. Multi-Tier Classifier Architecture

### Three Tiers

| Tier | Type | Purpose | Algorithms |
|------|------|---------|------------|
| Tier 1 | Classical ML | Fast baseline, interpretable | SVM, Naive Bayes, Decision Tree, Random Forest, KNN, XGBoost, LightGBM |
| Tier 2 | Deep Learning | Capture complex patterns | CNN, LSTM, Transformer, ViT, MLP |
| Tier 3 | Ensemble + Fusion | Maximize accuracy | Voting, Stacking, Multimodal Late Fusion |

### Why Three Tiers?

    Tier 1 alone:  Good accuracy, fast, but misses complex patterns
    Tier 2 alone:  Better accuracy, but slow and needs more data
    Tier 3 (combines 1+2): Best accuracy — uses strengths of both

### Module Requirements Coverage

| NUS Requirement | How We Cover It |
|----------------|-----------------|
| Supervised learning | All classifiers use labeled data |
| ML + Deep Learning | Tier 1 (classical ML) + Tier 2 (deep learning) |
| Hybrid / Ensemble | Tier 3 combines Tier 1 and Tier 2 predictions |
| Intelligent sensing | Multimodal fusion (video + audio + text + UI) |

We cover ALL FOUR requirements — this is a strong differentiator.

---

## 11. How Everything Connects

### Full Pipeline

    1. Video uploaded by user
       |
    2. Preprocessing (Stalin's pipeline)
       |  Extracts: transcript, OCR text, UI labels, audio MFCC, scene labels
       |
    3. Feature Engineering
       |  Converts raw features into model-ready vectors
       |
    4. Multi-Tier Classification
       |  Tier 1: SVM, RF, XGBoost, etc. (fast, interpretable)
       |  Tier 2: CNN, LSTM, Transformer (complex patterns)
       |  Tier 3: Ensemble (combines Tier 1 + Tier 2)
       |
    5. Evaluation Framework
       |  Metrics, confusion matrix, ROC curves
       |  Comparative table across all models
       |
    6. Report Generation
       |  Full evaluation report for the project submission
       |
    7. SOP Generation (via LLM)
       |  Classified workflow steps -> structured documentation
       |
    8. RAG Retrieval
          User queries -> semantic search -> LLM-augmented answers

### File Map

    app/ml/
    +-- base.py              <- BaseClassifier contract (all models implement this)
    +-- config.py            <- MLConfig (seed, labels, classes)
    +-- registry.py          <- Model phone book (register, get, list)
    +-- dataset.py           <- Synthetic data generator
    +-- pipeline.py          <- Orchestrates classification (TODO)
    +-- feature_engineering.py <- Feature transforms (TODO)
    +-- classifiers/
    |   +-- tier1/           <- 7 classical ML models (DONE)
    |   +-- tier2/           <- 5 deep learning models (TODO)
    |   +-- tier3/           <- 3 ensemble models (TODO)
    +-- evaluation/
        +-- metrics.py       <- Accuracy, F1, AUC per model (DONE)
        +-- confusion.py     <- Confusion matrices (DONE)
        +-- roc_curves.py    <- ROC/AUC curves (DONE)
        +-- report.py        <- Full comparative report (DONE)
        +-- cross_validation.py <- 5-fold CV (TODO)
        +-- ablation.py      <- Modality removal study (TODO)
        +-- feature_importance.py <- (TODO)
        +-- embeddings.py    <- t-SNE / UMAP (TODO)
        +-- error_analysis.py <- (TODO)

### Current Tier 1 Results (Synthetic Data)

    Model                Tier        Acc     F1    AUC       ms
    SVM                  tier1     1.000  1.000  1.000     1.72
    KNN                  tier1     1.000  1.000  1.000    27.99
    Naive Bayes          tier1     0.983  0.978  1.000     0.43
    Random Forest        tier1     0.983  0.978  1.000    25.80
    XGBoost              tier1     0.983  0.978  0.998     1.15
    LightGBM             tier1     0.967  0.960  0.999     1.36
    Decision Tree        tier1     0.900  0.917  0.961     0.11

Note: High scores are expected on synthetic data. Real data from the preprocessing pipeline will show more realistic differences between models.
