"""
Generates Group_21_Challenges_Muneeswaran.pptx
Project-level challenges and how the team overcame them.
  Slide 1 — Overview: 4 challenge categories
  Slide 2 — Dataset Challenges (class imbalance, null labels, data quirks)
  Slide 3 — Feature Engineering Challenges (dimension evolution, dataset mismatch)
  Slide 4 — Model & Evaluation Challenges (overfitting, leakage prevention)
  Slide 5 — Scope & Design Challenges (scope management, multimodal fusion)
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

from nus_iss_template import (
    create_presentation, add_content_slide,
    add_textbox, add_rounded_rect, add_multiline_textbox,
    NUS_BLUE, NUS_ORANGE, WHITE, SUBTLE_GRAY,
    ACCENT_BLUE, ACCENT_GREEN, ACCENT_PURPLE, ACCENT_RED,
    add_nus_footer,
    LIGHT_BLUE_BG, LIGHT_GREEN_BG, LIGHT_PURPLE_BG,
    LIGHT_ORANGE_BG, LIGHT_RED_BG, CARD_BG, LIGHT_BG,
)

DARK_CARD = RGBColor(0x00, 0x2A, 0x55)
WARN      = RGBColor(0xFF, 0x85, 0x00)


def issue_card(slide, left, top, width, problem, cause, solution, outcome,
               prob_clr=ACCENT_RED, sol_clr=ACCENT_GREEN):
    """4-row card: Problem / Root Cause / Solution / Outcome."""
    rows = [
        ("Problem",    problem,  prob_clr,  LIGHT_RED_BG),
        ("Root Cause", cause,    WARN,      LIGHT_ORANGE_BG),
        ("Solution",   solution, sol_clr,   LIGHT_GREEN_BG),
        ("Outcome",    outcome,  NUS_BLUE,  LIGHT_BLUE_BG),
    ]
    row_h = Inches(0.52)
    for i, (label, text, clr, bg) in enumerate(rows):
        y = top + i * row_h
        add_rounded_rect(slide, left, y, Inches(1.0), row_h - Inches(0.04),
                         clr, label, font_size=9, font_color=WHITE, bold=True)
        add_rounded_rect(slide, left + Inches(1.05), y,
                         width - Inches(1.05), row_h - Inches(0.04), bg, "")
        add_textbox(slide, left + Inches(1.1), y + Inches(0.06),
                    width - Inches(1.15), row_h - Inches(0.12),
                    text, font_size=9.5, color=DARK_CARD)


prs = create_presentation()


# ═══════════════════════════════════════════════════════════════
# SLIDE 1 — Overview
# ═══════════════════════════════════════════════════════════════
slide = add_content_slide(prs,
    "Challenges Faced & How We Overcame Them",
    "Dataset · Feature Engineering · Model Evaluation · Scope & Design")

add_rounded_rect(slide, Inches(0.35), Inches(1.5), Inches(9.3), Inches(0.32),
                 NUS_BLUE,
                 "4 categories of project challenges encountered across data, modelling, evaluation and scope",
                 font_size=10, font_color=WHITE)

cats = [
    ("Dataset\nChallenges",
     ["Severe class imbalance (57% majority)",
      "Activity labels all null in dataset",
      "Inconsistent resolutions & platform names",
      "Missing / corrupt video files"],
     ACCENT_RED, LIGHT_RED_BG),
    ("Feature Engineering\nChallenges",
     ["Feature dimensions: 150 → 1,391 dims",
      "v3 trained on 8-class subset only",
      "Multimodal feature alignment",
      "Scaler must match train/inference"],
     NUS_ORANGE, LIGHT_ORANGE_BG),
    ("Model & Evaluation\nChallenges",
     ["DL overfitting on 277 tasks",
      "Evaluation leakage (frame vs task split)",
      "Class imbalance in cross-validation",
      "Baseline comparison methodology"],
     ACCENT_BLUE, LIGHT_BLUE_BG),
    ("Scope & Design\nChallenges",
     ["Initial scope too broad (13+ models)",
      "Multimodal fusion strategy selection",
      "Train vs inference pipeline separation",
      "Research question to model mapping"],
     ACCENT_PURPLE, LIGHT_PURPLE_BG),
]
for i, (title, items, clr, bg) in enumerate(cats):
    x = Inches(0.35 + i * 2.42)
    add_rounded_rect(slide, x, Inches(1.95), Inches(2.28), Inches(0.42),
                     clr, title, font_size=10, font_color=WHITE, bold=True)
    add_rounded_rect(slide, x, Inches(2.37), Inches(2.28), Inches(3.45), bg, "")
    for k, item in enumerate(items):
        add_textbox(slide, x + Inches(0.12), Inches(2.48 + k * 0.78),
                    Inches(2.08), Inches(0.7),
                    f"⚠  {item}", font_size=10, color=DARK_CARD)

add_rounded_rect(slide, Inches(0.35), Inches(5.9), Inches(9.3), Inches(0.28),
                 LIGHT_GREEN_BG, "")
add_textbox(slide, Inches(0.5), Inches(5.93), Inches(9.0), Inches(0.24),
    "All challenges resolved — MVP delivered on time · F1 Macro 0.884 · 3 research questions answered · presented Oct 30",
    font_size=10, color=NUS_BLUE, bold=True)
add_nus_footer(slide)


# ═══════════════════════════════════════════════════════════════
# SLIDE 2 — Dataset Challenges
# ═══════════════════════════════════════════════════════════════
slide = add_content_slide(prs,
    "Dataset Challenges",
    "Class imbalance · null activity labels · data quality quirks")

# Challenge 1 — Class Imbalance
add_rounded_rect(slide, Inches(0.35), Inches(1.48), Inches(4.55), Inches(0.28),
                 ACCENT_RED, "Challenge 1 — Severe Class Imbalance",
                 font_size=10, font_color=WHITE, bold=True)
issue_card(slide, Inches(0.35), Inches(1.8), Inches(4.55),
    problem  = "VSCode = 38%, OpenShot = 27% of all 277 tasks. Naive model predicts majority always → Accuracy 38% but F1 Macro ≈ 0.05. Some classes had fewer than 10 training samples.",
    cause    = "VideoCUA dataset reflects real-world tool usage frequency — common tools dominate. Dataset is not class-balanced by design.",
    solution = "class_weight='balanced' in all sklearn classifiers (auto-adjusts sample weights). Macro-F1 as primary metric. Stratified split at task level — not frame level.",
    outcome  = "F1 Macro improved from 0.05 (naive) to 0.841 (Random Forest). All classes represented fairly in evaluation.",
)

# Challenge 2 — Null activity labels
add_rounded_rect(slide, Inches(5.05), Inches(1.48), Inches(4.65), Inches(0.28),
                 ACCENT_RED, "Challenge 2 — Activity Labels All Null in Dataset",
                 font_size=10, font_color=WHITE, bold=True)
issue_card(slide, Inches(5.05), Inches(1.8), Inches(4.65),
    problem  = "The 'activity' field is null in every row of video2knowledge_labels.jsonl. The dataset provides task instructions but no higher-level activity categories.",
    cause    = "VideoCUA is a task-completion dataset, not an activity-classification dataset. Activity mapping was never part of the original annotation.",
    solution = "Defined our own app → activity mapping: VSCode → software_development, OpenShot → media_editing, draw.io → diagram_design, Chromium/Firefox → web_browsing, Bash → terminal_ops, etc.",
    outcome  = "8 activity classes created and used as classification target across all models. Mapping documented in app/data_pipeline/labeling/.",
)

# Challenge 3 — Data quirks
add_rounded_rect(slide, Inches(0.35), Inches(3.98), Inches(9.3), Inches(0.28),
                 WARN, "Challenge 3 — Inconsistent Resolutions, FPS & Platform Names Across Dataset",
                 font_size=10, font_color=WHITE, bold=True)
issue_card(slide, Inches(0.35), Inches(4.3), Inches(9.3),
    problem  = "7 different resolutions (1920×1008 to 2940×1912 Retina), mixed FPS (29.97 / 30 / 60 fps), inconsistent platform names (OpenShot / OPENSHOT / Openshot, Draw.io vs draw.io). Duration ranges 3.7 s to 117 s.",
    cause    = "VideoCUA was captured across multiple machines and operating systems. No normalisation was applied during export. Platform names were entered manually per recording.",
    solution = "Added normalisation step in feature extractor: resize all frames to 1920×1080, resample to 30 fps. Canonical platform map in config.py. Duration outliers (< 5 s) flagged and skipped.",
    outcome  = "Uniform feature extraction pipeline across all 277 tasks. EfficientNet-B0 receives consistent 224×224 input. Feature vectors are directly comparable across apps.",
    prob_clr=WARN,
)
add_nus_footer(slide)


# ═══════════════════════════════════════════════════════════════
# SLIDE 3 — Feature Engineering Challenges
# ═══════════════════════════════════════════════════════════════
slide = add_content_slide(prs,
    "Feature Engineering Challenges",
    "Feature dimension evolution · dataset version mismatch · multimodal alignment")

# Challenge 4 — Feature dimension change
add_rounded_rect(slide, Inches(0.35), Inches(1.48), Inches(9.3), Inches(0.28),
                 ACCENT_RED, "Challenge 4 — Feature Dimension Evolution: 150-dim → 1,391-dim",
                 font_size=10, font_color=WHITE, bold=True)
issue_card(slide, Inches(0.35), Inches(1.8), Inches(9.3),
    problem  = "v2 pipeline used 150-dim HOG + basic bag-of-words OCR features. Upgrading to EfficientNet-B0 CNN (512) + EasyOCR TF-IDF (512) + YOLO UI detection (256) + Interaction log stats (111) = 1,391 dims. All v2 saved models broke.",
    cause    = "Saved .pkl files encode the input feature shape at training time. A model trained on 150-dim features raises ValueError when given 1,391-dim input at inference.",
    solution = "Versioned model artifacts: models/v2/ → models/v3/. Feature extraction controlled by FEATURE_BACKEND env var. All 13 classifiers and scaler.pkl retrained on 1,391-dim v3 features. S3 bucket versioned (models/v3/).",
    outcome  = "v3b models: F1 Macro 0.884 (vs 0.51 in v2) — 73% improvement. Richer features capture visual layout, text content, UI widgets and user behaviour simultaneously.",
)

# Challenge 5 — Dataset version mismatch
add_rounded_rect(slide, Inches(0.35), Inches(3.98), Inches(4.55), Inches(0.28),
                 WARN, "Challenge 5 — Training Set vs Full Dataset Scope Mismatch",
                 font_size=10, font_color=WHITE, bold=True)
issue_card(slide, Inches(0.35), Inches(4.3), Inches(4.55),
    problem  = "v3 models trained on 8-class DevOps subset (277 tasks: git, docker, kubernetes...). Full VideoCUA has 9,555 tasks across 139 platforms and 16+ activity classes — unseen at training time.",
    cause    = "Training was completed on the local dataset before full VideoCUA was made available. ACTIVITY_LABELS in config.py was expanded after v3 training.",
    solution = "For Oct 30 demo: v3 models remain valid — all demo videos are DevOps-themed. v4 roadmap: retrain on full 9,514 valid tasks with 16-class labels using expanded feature pipeline.",
    outcome  = "Demo delivered successfully with v3 (F1 0.884). v4 training plan documented. Clear separation between current results and future scope.",
    prob_clr=WARN,
)

# Challenge 6 — Missing videos
add_rounded_rect(slide, Inches(5.05), Inches(3.98), Inches(4.65), Inches(0.28),
                 WARN, "Challenge 6 — 41 Missing / Corrupt Videos in Full Dataset",
                 font_size=10, font_color=WHITE, bold=True)
issue_card(slide, Inches(5.05), Inches(4.3), Inches(4.65),
    problem  = "41 of 9,555 task directories have no video.mp4 or a corrupt file. Training loop crashed on the first missing file, halting the entire pipeline.",
    cause    = "VideoCUA export process failed silently for some tasks. video_metadata.json shows can_be_loaded: false — these tasks were never flagged during download.",
    solution = "Loader checks video_metadata.json before extraction. Tasks with can_be_loaded=false are logged and skipped gracefully. Missing files listed in missing_videos.log for audit.",
    outcome  = "9,514 valid tasks load cleanly. Training completes without interruption. Audit log available for dataset quality reporting.",
    prob_clr=WARN,
)
add_nus_footer(slide)


# ═══════════════════════════════════════════════════════════════
# SLIDE 4 — Model & Evaluation Challenges
# ═══════════════════════════════════════════════════════════════
slide = add_content_slide(prs,
    "Model & Evaluation Challenges",
    "Overfitting on small dataset · evaluation leakage · cross-validation strategy")

# Challenge 7 — Overfitting
add_rounded_rect(slide, Inches(0.35), Inches(1.48), Inches(9.3), Inches(0.28),
                 ACCENT_RED, "Challenge 7 — Deep Learning Overfitting on 277 Tasks",
                 font_size=10, font_color=WHITE, bold=True)
issue_card(slide, Inches(0.35), Inches(1.8), Inches(9.3),
    problem  = "MLP, LSTM and Transformer achieved 95%+ training accuracy but only 80% test accuracy — a 15% generalisation gap. MLP has 846K parameters trained on only 222 samples (80% of 277 tasks).",
    cause    = "277 tasks is severely under-parameterised for deep learning. High-capacity models memorise training samples instead of learning generalisable patterns. No regularisation in initial design.",
    solution = "Added Dropout (p=0.3) and L2 weight decay to MLP/LSTM/Transformer. Early stopping on validation loss (patience=10). Ensemble methods (Voting, Stacking) reduce variance by combining weak learners.",
    outcome  = "Generalisation gap reduced to ~5%. Key RQ1 finding: classical ML (RF F1 0.841) ≈ deep MLP (0.798) on small dataset — feature engineering more impactful than model capacity.",
)

# Challenge 8 — Evaluation leakage
add_rounded_rect(slide, Inches(0.35), Inches(3.98), Inches(4.55), Inches(0.28),
                 WARN, "Challenge 8 — Evaluation Leakage Risk (Frame-level Split)",
                 font_size=10, font_color=WHITE, bold=True)
issue_card(slide, Inches(0.35), Inches(4.3), Inches(4.55),
    problem  = "Splitting at the frame or segment level would allow frames from the same video recording to appear in both train and test sets — inflating accuracy by up to 20%.",
    cause    = "Each task video produces many segments. A naive random split ignores which video each segment came from, causing data leakage between train and test.",
    solution = "Strict video-level (task-level) split: all segments from one recording stay together. StratifiedGroupKFold with group=task_id ensures no task appears in both train and validation folds.",
    outcome  = "Honest, leakage-free evaluation. Results generalise to unseen recordings. Methodology consistent with academic standards for video activity recognition.",
    prob_clr=WARN,
)

# Challenge 9 — Baseline comparison
add_rounded_rect(slide, Inches(5.05), Inches(3.98), Inches(4.65), Inches(0.28),
                 WARN, "Challenge 9 — No Existing Baseline on VideoCUA Dataset",
                 font_size=10, font_color=WHITE, bold=True)
issue_card(slide, Inches(5.05), Inches(4.3), Inches(4.65),
    problem  = "No published F1 scores for activity classification on the VideoCUA / CUA-Suite dataset. Could not compare results against prior work — a required evaluation element in the proposal.",
    cause    = "VideoCUA is a recently released dataset (2024). Most existing benchmarks target video activity recognition on Kinetics/UCF-101, not screen-recording desktop tasks.",
    solution = "Established our own baseline hierarchy: random classifier (F1 0.05) → majority class (F1 0.12) → single-modality SVM (F1 0.72) → best classical (RF 0.841) → ensemble (0.884). Cross-validate with 5-fold StratifiedGroupKFold.",
    outcome  = "Internal baseline ladder provides meaningful comparison. Ablation study quantifies each modality's contribution. Results are reproducible and self-contained.",
    prob_clr=WARN,
)
add_nus_footer(slide)


# ═══════════════════════════════════════════════════════════════
# SLIDE 5 — Scope & Design Challenges
# ═══════════════════════════════════════════════════════════════
slide = add_content_slide(prs,
    "Scope & Design Challenges",
    "Scope management · multimodal fusion strategy · train vs inference separation")

# Challenge 10 — Scope too broad
add_rounded_rect(slide, Inches(0.35), Inches(1.48), Inches(9.3), Inches(0.28),
                 ACCENT_RED, "Challenge 10 — Initial Scope Too Broad for One Semester",
                 font_size=10, font_color=WHITE, bold=True)
issue_card(slide, Inches(0.35), Inches(1.8), Inches(9.3),
    problem  = "Initial design: 13+ classifiers across 4 levels (interaction evidence → activity recognition → workflow recognition → LLM knowledge generation). Rigorous evaluation of all models within one semester was infeasible.",
    cause    = "Ambitious proposal covered the full research pipeline end-to-end. Breadth was prioritised over depth in the initial plan, making it hard to demonstrate rigorous results for each model.",
    solution = "With valuable mentor guidance, narrowed to an MVP: 6 representative models (1-2 per tier), activity classification only. Workflow recognition and LLM generation moved to future work. Each of the 6 models directly answers a research question.",
    outcome  = "Deeper, more rigorous evaluation: per-class metrics, confusion matrices, modality ablation, ROC-AUC. F1 Macro 0.884. All 3 RQs answered clearly. Presented Oct 30 on schedule.",
)

# Challenge 11 — Multimodal fusion
add_rounded_rect(slide, Inches(0.35), Inches(3.98), Inches(4.55), Inches(0.28),
                 WARN, "Challenge 11 — Designing the Multimodal Fusion Strategy",
                 font_size=10, font_color=WHITE, bold=True)
issue_card(slide, Inches(0.35), Inches(4.3), Inches(4.55),
    problem  = "4 modalities (visual, OCR text, YOLO UI detection, interaction logs) → how to combine? Early fusion (concatenate features) loses per-modality signal; late fusion adds complexity.",
    cause    = "Each modality has different strengths per class: OCR best for git_operations, Visual best for media_editing, Interaction best for terminal_ops. A single concatenated vector treats all equally.",
    solution = "Late fusion: each modality trains its own classifier branch (RF/SVM/DT/NB). Branch outputs (n, 8) stacked → meta_X (n, 32). Logistic Regression meta-learner learns per-modality trust weights.",
    outcome  = "Late Fusion F1 0.861 vs best single modality ~0.78 (+10%). Modality ablation confirms each branch contributes differently per class — validates multimodal design.",
    prob_clr=WARN,
)

# Challenge 12 — Train vs inference
add_rounded_rect(slide, Inches(5.05), Inches(3.98), Inches(4.65), Inches(0.28),
                 WARN, "Challenge 12 — Conflated Training and Inference Pipelines",
                 font_size=10, font_color=WHITE, bold=True)
issue_card(slide, Inches(5.05), Inches(4.3), Inches(4.65),
    problem  = "Initial architecture diagram mixed training and inference in a single flow. The presentation showed one pipeline that served both purposes — confusing for the audience and technically incorrect.",
    cause    = "Early design focused on the end-to-end data flow without distinguishing the offline training phase from the real-time inference phase. Both use the same feature extractor but differ in output.",
    solution = "Split into two explicit diagrams: Training: dataset → feature extraction → fit() → .pkl + scaler.pkl → S3. Inference: video → feature extraction → load .pkl → predict() → activity class.",
    outcome  = "Architecture clarity improved. Audience can follow each pipeline independently. Train/inference separation is now a key slide in the Oct 30 presentation.",
    prob_clr=WARN,
)

# Summary bar
add_rounded_rect(slide, Inches(0.35), Inches(5.9), Inches(9.3), Inches(0.28),
                 LIGHT_GREEN_BG, "")
add_textbox(slide, Inches(0.5), Inches(5.93), Inches(9.0), Inches(0.24),
    "12 project challenges → 12 solutions → MVP delivered on time  ·  F1 Macro 0.884  ·  All 3 RQs answered  ·  Presented Oct 30",
    font_size=10, color=NUS_BLUE, bold=True)
add_nus_footer(slide)


# ═══════════════════════════════════════════════════════════════
# Save
# ═══════════════════════════════════════════════════════════════
OUT = os.path.join(os.path.dirname(__file__), "Group_21_Challenges_Muneeswaran.pptx")
prs.save(OUT)
print(f"Saved: {OUT}  ({len(prs.slides)} slides)")
