# Model Reference — Video2Knowledge Classifiers

All 16 classifiers are trained on 151-dimensional multimodal features extracted from
screen-recording videos (OCR text 50d + UI elements 30d + visual 40d + interaction 30d +
has_action_log flag 1d). They are evaluated on 13 activity classes:
`git_operations`, `docker_workflow`, `kubernetes_ops`, `terraform_iac`, `aws_console`,
`jenkins_ci_cd`, `coding_editing`, `debugging`, `documentation`, `terminal_ops`,
`system_config`, `web_browsing`, `other`.

---

## Tier 1 — Classical ML

Fast to train, fast at inference, no GPU required. Serve as baselines for RQ1
(classical vs deep learning comparison).

| Model | What it is | Strength | Weakness | Where to use | Good for |
|-------|-----------|----------|----------|--------------|----------|
| **SVM** | Finds the optimal decision boundary (hyperplane) between classes using an RBF kernel trick | Strong on small-to-medium datasets; works well with high-dimensional features; good generalisation via margin maximisation | Slow to train on large data; black box with RBF kernel; does not scale to millions of samples | When data is clean and features are well-scaled | Our 151-dim multimodal features — SVM handles high-dimensional spaces well |
| **Random Forest** | Builds 100 decision trees on random feature subsets; majority vote decides the class | Handles noisy features; robust to outliers; provides feature importance scores | Slower than a single tree; large memory footprint; can overfit on very noisy data | Medium-sized datasets with mixed feature types | General-purpose baseline; hard to go wrong |
| **Decision Tree** | Splits data on one feature at a time creating a tree of if/else rules | Fully interpretable — the tree can be visualised and explained; very fast at inference | Overfits easily; unstable (a small data change produces a very different tree) | When predictions must be explained to non-technical stakeholders | Debugging why a video was misclassified |
| **KNN** | Finds the K=5 nearest training samples and takes a majority vote | No training time; naturally handles multi-class; non-parametric | Slow at inference on large datasets; sensitive to irrelevant or redundant features | Small datasets or as a sanity-check model | Verifying whether the feature space has natural class clusters |
| **XGBoost** | Gradient boosting — builds trees sequentially, each correcting the errors of the previous | Best classical model on tabular data; handles missing values; GPU-accelerated | Many hyperparameters to tune; can overfit without regularisation | Structured/tabular data; industry standard for ML competitions | When you want the best classical accuracy |
| **LightGBM** | Faster variant of XGBoost using histogram-based leaf splits | Much faster than XGBoost on large data; lower memory; leaf-wise growth | Less mature ecosystem; slightly less accurate than XGBoost on very small datasets | Large datasets where training speed matters | Our 9,609-task dataset — faster than XGBoost without significant accuracy loss |
| **Naive Bayes** | Assumes features are conditionally independent; computes class probability via Bayes' theorem | Extremely fast to train and predict; works well with small data; naturally probabilistic | Feature independence assumption almost never holds in practice; poor on correlated features | Text classification baselines; very fast first-pass model | OCR text features — Gaussian NB suits continuous feature inputs |

---

## Tier 2 — Deep Learning

Learns complex non-linear patterns. Trained on GPU (CUDA). All use
`CrossEntropyLoss` with inverse-frequency class weights to handle imbalance.
Answers RQ1: do deep learning models outperform classical ML on this task?

| Model | What it is | Strength | Weakness | Where to use | Good for |
|-------|-----------|----------|----------|--------------|----------|
| **MLP** | Multi-layer feedforward neural network (2 hidden layers, 128 units, ReLU, dropout=0.3) | Learns non-linear feature interactions; simple architecture; fast to train | Does not capture sequential or temporal patterns; needs more data than classical models | When features have non-linear relationships | Fusing all 4 modalities into a single prediction |
| **CNN1D** | 1D convolutions over the feature vector treated as a sequence | Captures local feature co-occurrence patterns (e.g. OCR features adjacent to UI features); fast inference | Treats a fixed-length vector as a sequence — somewhat artificial for tabular features | Signal and time-series data; NLP with embeddings | Detecting spatially co-occurring features in the concatenated vector |
| **LSTM** | Recurrent network with input/forget/output gates; processes the feature vector as a 10-step sequence | Captures temporal dependencies between steps; handles variable-length sequences | Slow to train; vanishing gradient on long sequences; cannot parallelise across time steps | True sequential data — time series, speech, text | Workflow step sequences; what happened across segments |
| **Transformer** | Self-attention encoder over a 10-token sequence with sinusoidal positional encoding | Captures global dependencies across all tokens simultaneously; fully parallelisable; state-of-the-art on sequence tasks | Needs more data than LSTM; heavy for very short sequences | Long sequences, NLP, state-of-the-art classification | Currently our best Tier 2 model — attention learns which features matter most |
| **WorkflowLSTM** | LSTM operating on the **sequence of activity-level predictions** across segments (not raw features) | Recognises multi-step workflows (e.g. edit → commit → push = git workflow); captures temporal activity patterns | Requires multiple segments to be meaningful; useless on single-segment videos | Workflow recognition (Level 3 of the architecture) | Identifying higher-order patterns across a full recording session |
| **WorkflowTransformer** | Transformer operating on the **sequence of activity predictions** across segments | Same as WorkflowLSTM with the added benefit of self-attention over non-adjacent steps | Same limitations as WorkflowLSTM; heavier architecture | Workflow recognition (Level 3) | Complex workflows with non-sequential or long-range dependencies |

---

## Tier 3 — Ensembles / Multimodal Fusion

Combines outputs of multiple models. Answers RQ2: does fusion outperform individual models?
These are the highest-accuracy models and are preferred for production inference.

| Model | What it is | Strength | Weakness | Where to use | Good for |
|-------|-----------|----------|----------|--------------|----------|
| **Voting** | Averages probability outputs from SVM + RF + MLP (soft vote); argmax gives the final class | Simple; reduces variance; one wrong model is corrected by the others; no extra training data needed | Slow — runs 3 full models per inference; all models must agree to produce high confidence | When individual models have complementary error patterns | General robustness; currently the default BEST model in the UI |
| **Stacking** | SVM + RF + MLP as base models; their probability outputs are concatenated and fed to a Logistic Regression meta-learner | The meta-learner learns *which base model to trust* per situation; higher accuracy ceiling than voting | Complex pipeline; risk of overfitting if meta-learner is trained on the same data as base models | When base models have meaningfully different strengths | Highest accuracy potential when the base models are diverse and calibrated |
| **Late Fusion** | Feature vector is split into two halves (simulating two modalities) — SVM on the first half, RF on the second — outputs fused by a Logistic Regression meta-learner | Simulates true multimodal fusion where each sensor/modality has its own classifier; proves fusion benefit | Currently uses an artificial feature split rather than true modality boundaries (OCR vs UI vs visual) | True multimodal systems where different inputs come from different sensors or pipelines | Research value: directly demonstrates that fusion outperforms individual modalities (RQ2) |

---

## Quick Reference

| Goal | Best model |
|------|-----------|
| Highest accuracy | Late Fusion / Stacking (Tier 3) |
| Fastest inference | Naive Bayes, Decision Tree (<2 ms) |
| Most interpretable | Decision Tree |
| Best classical baseline | XGBoost / LightGBM |
| Best deep learning | Transformer |
| Research: classical vs deep (RQ1) | All Tier 1 vs all Tier 2 |
| Research: fusion benefit (RQ2) | Late Fusion vs individual models |
| Production deployment | Late Fusion (best macro-F1) |

---

## Architecture Summary

```
Input: video.mp4 (+ optional action_log.json)
         │
         ▼
   Feature Extraction  ──────────────────────────────────────────────┐
   ├── EasyOCR          → 50-dim TF-IDF text features                │
   ├── YOLOv8           → 30-dim UI element detection features        │
   ├── OpenCV           → 40-dim visual features (colour, edges)      │
   ├── Interaction log  → 30-dim click/keyboard/drag encoding         │
   └── has_action_log   →  1-dim presence flag                        │
                                           Total: 151-dim per segment │
         │                                                            │
         ▼                                                            │
   ┌─────────────────────────────────────────────────────────────┐   │
   │                  Classifier Tiers                           │   │
   │  Tier 1 (Classical):  SVM  RF  DT  KNN  XGB  LGBM  NB      │   │
   │  Tier 2 (Deep):       MLP  CNN1D  LSTM  Transformer         │   │
   │                       WorkflowLSTM  WorkflowTransformer     │   │
   │  Tier 3 (Ensemble):   Voting  Stacking  LateFusion          │   │
   └─────────────────────────────────────────────────────────────┘   │
         │                                                            │
         ▼                                                            │
   Activity label + confidence per model                             │
   Best model selected by tier (Tier3 > Tier2 > Tier1)              │
                                                                     │
Training (offline, EC2, ~15 h): ─────────────────────────────────────┘
  python -m app.train --dataset-root ./dataset --model-dir ./models
  → saves 16 .pkl files

Fast retrain after label/model changes (~10 min):
  python -m app.train ... --load-features
  → loads cached X_train.npy, skips extraction
```
