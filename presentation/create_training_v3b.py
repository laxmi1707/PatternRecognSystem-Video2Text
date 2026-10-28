"""
TRACE — Model Training Presentation (v3b results)
Generates Group_21_Training_v3b.pptx with accurate v3b metrics:
  - 8 activity classes (DevOps subset from VideoCUA)
  - 1,391-dim feature vector (EfficientNet-B0 + EasyOCR + YOLO + interaction)
  - Best model: Voting ensemble, F1 Macro 0.884
  - 277 tasks, 8 apps, ~2.3 GB
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

from nus_iss_template import (
    create_presentation, add_title_slide, add_content_slide, add_section_slide,
    add_textbox, add_bullet_list, add_rect, add_rounded_rect,
    add_multiline_textbox, NUS_BLUE, NUS_ORANGE, WHITE, LIGHT_GRAY,
    SUBTLE_GRAY, ACCENT_BLUE, ACCENT_GREEN, ACCENT_PURPLE, ACCENT_RED,
    set_slide_bg, add_nus_logo, add_nus_footer,
    LIGHT_BLUE_BG, LIGHT_GREEN_BG, LIGHT_PURPLE_BG, LIGHT_ORANGE_BG,
    LIGHT_RED_BG, CARD_BG, LIGHT_BG,
)

DARK_CARD  = RGBColor(0x00, 0x2A, 0x55)
GOLD       = RGBColor(0xFF, 0xC1, 0x07)
TEAL       = RGBColor(0x17, 0xA2, 0xB8)

prs = create_presentation()


def add_code_block(slide, left, top, width, height, lines, font_size=10):
    add_rounded_rect(slide, left, top, width, height, DARK_CARD)
    add_multiline_textbox(
        slide, left + Inches(0.15), top + Inches(0.1),
        width - Inches(0.3), height - Inches(0.2),
        lines, font_size=font_size,
        color=ACCENT_GREEN, font_name="Courier New", spacing=Pt(2),
    )


def arrow(slide, left, top, color=ACCENT_BLUE, size=18):
    add_textbox(slide, left, top, Inches(0.4), Inches(0.4),
                "→", font_size=size, color=color, bold=True,
                alignment=PP_ALIGN.CENTER)


# ────────────────────────────────────────────────────────────
# SLIDE 1 — Title
# ────────────────────────────────────────────────────────────
slide = add_title_slide(
    prs,
    "TRACE — Model Training",
    subtitle="How 13 classifiers learned to recognise desktop activities",
    author="Group 21 | NUS M.Tech AIS",
    affiliation="ISY5002 Pattern Recognition Systems · Semester 2, 2026",
)
for i, (lbl, clr) in enumerate([
    ("Data Prep", ACCENT_BLUE), ("Feature Extract", ACCENT_GREEN),
    ("Train 13 Models", NUS_ORANGE), ("Evaluate", ACCENT_PURPLE),
]):
    add_rounded_rect(slide, Inches(1.5 + i * 2.1), Inches(5.3),
                     Inches(1.9), Inches(0.4), clr, lbl,
                     font_size=11, font_color=WHITE, bold=True)


# ────────────────────────────────────────────────────────────
# SLIDE 2 — Training Overview
# ────────────────────────────────────────────────────────────
slide = add_content_slide(prs, "Training Overview — 4 Phases",
    "End-to-end pipeline: raw VideoCUA dataset → trained .pkl classifiers")

phases = [
    ("Phase 1", "Data Preparation",
     "277 tasks · 8 apps\n80% train / 20% test\nStratified by app label",
     ACCENT_BLUE, LIGHT_BLUE_BG),
    ("Phase 2", "Feature Extraction",
     "Video frames + action logs\n→ 1,391-dim feature vector\nper task",
     ACCENT_GREEN, LIGHT_GREEN_BG),
    ("Phase 3", "Model Training",
     "13 classifiers trained\non feature matrix\n(Tier 1 → 2 → 3)",
     NUS_ORANGE, LIGHT_ORANGE_BG),
    ("Phase 4", "Evaluation",
     "Test set → F1 Macro\n→ Confusion matrix\n→ Best = Voting 0.884",
     ACCENT_PURPLE, LIGHT_PURPLE_BG),
]
for i, (phase, title, body, clr, bg) in enumerate(phases):
    x = Inches(0.4 + i * 2.35)
    add_rounded_rect(slide, x, Inches(1.7), Inches(2.2), Inches(0.35),
                     clr, phase, font_size=11, font_color=WHITE, bold=True)
    add_rounded_rect(slide, x, Inches(2.1), Inches(2.2), Inches(3.3),
                     bg, "", font_size=11)
    add_multiline_textbox(slide, x + Inches(0.1), Inches(2.2),
                          Inches(2.0), Inches(0.3),
                          [title], font_size=13, color=clr, bold=True)
    add_multiline_textbox(slide, x + Inches(0.1), Inches(2.6),
                          Inches(2.0), Inches(2.5),
                          body.split("\n"), font_size=11, color=DARK_CARD)
    if i < 3:
        arrow(slide, Inches(2.55 + i * 2.35), Inches(3.2), color=clr)

add_code_block(slide,
    Inches(0.4), Inches(5.5), Inches(9.2), Inches(0.8),
    ["$ python -m app.train --dataset-root ./dataset --model-dir ./models",
     "# Trains all 13 models, evaluates on held-out test set, logs to MLflow"],
    font_size=10,
)
add_nus_footer(slide)


# ────────────────────────────────────────────────────────────
# SLIDE 3 — Dataset & Class Labels
# ────────────────────────────────────────────────────────────
slide = add_content_slide(prs, "Step 1 — Dataset & Activity Labels",
    "VideoCUA subset: 277 expert desktop task recordings across 8 apps")

# App distribution table
apps = [
    ("VSCode", 106, "coding_editing"),
    ("OpenShot", 75, "media_editing"),
    ("IntelliJ IDEA", 46, "coding_editing"),
    ("draw.io", 10, "diagram_design"),
    ("Bash", 10, "terminal_ops"),
    ("Chromium", 10, "web_browsing"),
    ("Eclipse", 10, "coding_editing"),
    ("Mozilla Firefox", 10, "web_browsing"),
]
headers = ["App", "Tasks", "Activity Label"]
col_w = [Inches(2.0), Inches(0.9), Inches(2.2)]
col_x = [Inches(0.4), Inches(2.4), Inches(3.3)]
y0 = Inches(1.55)
for j, (h, w) in enumerate(zip(headers, col_w)):
    add_rounded_rect(slide, col_x[j], y0, w, Inches(0.3),
                     NUS_BLUE, h, font_size=11, font_color=WHITE, bold=True)
for i, (app, cnt, lbl) in enumerate(apps):
    y = y0 + Inches(0.32 * (i + 1))
    bg = CARD_BG if i % 2 == 0 else LIGHT_BG
    for j, val in enumerate([app, str(cnt), lbl]):
        add_rounded_rect(slide, col_x[j], y, col_w[j], Inches(0.3),
                         bg, val, font_size=10, font_color=DARK_CARD)

# Key facts panel
add_rounded_rect(slide, Inches(5.8), Inches(1.55), Inches(3.9), Inches(4.6),
                 LIGHT_BLUE_BG, "")
for k, line in enumerate([
    ("Total tasks:", "277"),
    ("Apps:", "8"),
    ("Duration range:", "3.7 s – 117 s"),
    ("Mean duration:", "~18 s"),
    ("Total size:", "~2.3 GB"),
    ("FPS:", "30 fps (some 60 fps Retina)"),
    ("Resolutions:", "1920×1080 (primary)"),
    ("Split:", "80 % train / 20 % test"),
    ("Stratified by:", "app → activity label"),
]):
    ky, val = line
    add_textbox(slide, Inches(6.0), Inches(1.7 + k * 0.45),
                Inches(1.5), Inches(0.35), ky, font_size=11,
                color=NUS_BLUE, bold=True)
    add_textbox(slide, Inches(7.5), Inches(1.7 + k * 0.45),
                Inches(2.1), Inches(0.35), val, font_size=11,
                color=DARK_CARD)

add_textbox(slide, Inches(0.4), Inches(5.35), Inches(9.2), Inches(0.3),
    "⚠  Class Imbalance: VSCode (106) + OpenShot (75) = 65% of data → use Macro-F1, not Accuracy",
    font_size=11, color=ACCENT_RED, bold=True)
add_nus_footer(slide)


# ────────────────────────────────────────────────────────────
# SLIDE 4 — Stratified Split & Leakage Rule
# ────────────────────────────────────────────────────────────
slide = add_content_slide(prs, "Step 1b — Train/Test Split & Leakage Prevention",
    "Splitting at the task/video level — the non-negotiable leakage rule")

add_rounded_rect(slide, Inches(0.4), Inches(1.5), Inches(5.5), Inches(2.0),
                 LIGHT_GREEN_BG, "")
add_multiline_textbox(slide, Inches(0.6), Inches(1.55), Inches(5.1), Inches(1.9),
    ["Stratified Train / Test Split",
     "sklearn.model_selection.train_test_split(stratify=y, test_size=0.2, random_state=42)",
     "",
     "277 tasks  →  222 train (80%)  +  55 test (20%)",
     "Same label proportions preserved in both splits",
     "Ensures test set is representative — minority classes included",
    ], font_size=11, color=DARK_CARD)

add_rounded_rect(slide, Inches(0.4), Inches(3.65), Inches(5.5), Inches(2.0),
                 LIGHT_RED_BG, "")
add_multiline_textbox(slide, Inches(0.6), Inches(3.7), Inches(5.1), Inches(1.9),
    ["⚠  Leakage Rule (non-negotiable)",
     "",
     "Split at the TASK level, never at frame/segment level.",
     "All frames from task #12345 go entirely into train OR test.",
     "If frames from one recording appear in both splits,",
     "the model memorises the recording — not the activity.",
    ], font_size=11, color=DARK_CARD)

add_rounded_rect(slide, Inches(6.1), Inches(1.5), Inches(3.6), Inches(2.0),
                 LIGHT_PURPLE_BG, "")
add_multiline_textbox(slide, Inches(6.3), Inches(1.55), Inches(3.3), Inches(1.9),
    ["Class Distribution (v3b training set)",
     "",
     "coding_editing    ~65%",
     "media_editing     ~27%",
     "web_browsing       ~7%",
     "terminal_ops       ~1%",
     "(others < 1% each)",
    ], font_size=11, color=DARK_CARD)

add_rounded_rect(slide, Inches(6.1), Inches(3.65), Inches(3.6), Inches(2.0),
                 LIGHT_ORANGE_BG, "")
add_multiline_textbox(slide, Inches(6.3), Inches(3.7), Inches(3.3), Inches(1.9),
    ["Data Augmentation",
     "",
     "Classes with < 100 training samples",
     "receive 5× synthetic augmentation:",
     "  • Gaussian noise on feature values",
     "  • Random feature dropout (10%)",
     "Prevents minority classes from being",
     "ignored during training.",
    ], font_size=11, color=DARK_CARD)
add_nus_footer(slide)


# ────────────────────────────────────────────────────────────
# SLIDE 5 — Feature Extraction
# ────────────────────────────────────────────────────────────
slide = add_content_slide(prs, "Step 2 — Multimodal Feature Extraction",
    "1,391-dimensional feature vector fused from 4 independent extractors")

extractors = [
    ("Visual (EfficientNet-B0)",
     "CNN pretrained on ImageNet\nFrames → global avg pool → 512-dim\nCaptures UI layout, colour palette,\nwindow structure",
     "512 dims", ACCENT_BLUE, LIGHT_BLUE_BG),
    ("OCR Text (EasyOCR)",
     "Text regions detected & extracted\nTF-IDF on app-keyword vocabulary\nIdentifies IDE names, CLI commands,\nbrowser URLs, error messages",
     "512 dims", ACCENT_GREEN, LIGHT_GREEN_BG),
    ("UI Objects (YOLO)",
     "YOLOv8 detects UI widgets:\nbuttons, menus, text fields,\nterminal windows\nCount + position features",
     "256 dims", NUS_ORANGE, LIGHT_ORANGE_BG),
    ("Interaction Stats",
     "From action_log.json:\nclick rate, typing rate,\nmouse travel distance,\nscroll frequency, hotkey ratio",
     "111 dims", ACCENT_PURPLE, LIGHT_PURPLE_BG),
]
for i, (name, desc, dims, clr, bg) in enumerate(extractors):
    x = Inches(0.3 + i * 2.45)
    add_rounded_rect(slide, x, Inches(1.6), Inches(2.3), Inches(0.35),
                     clr, name, font_size=10, font_color=WHITE, bold=True)
    add_rounded_rect(slide, x, Inches(1.95), Inches(2.3), Inches(2.9),
                     bg, "")
    for k, ln in enumerate(desc.split("\n")):
        add_textbox(slide, x + Inches(0.1), Inches(2.05 + k * 0.42),
                    Inches(2.1), Inches(0.38), ln, font_size=10, color=DARK_CARD)
    add_rounded_rect(slide, x + Inches(0.4), Inches(4.55), Inches(1.5), Inches(0.3),
                     clr, dims, font_size=12, font_color=WHITE, bold=True)

add_textbox(slide, Inches(0.3), Inches(5.0), Inches(9.4), Inches(0.25),
    "512 + 512 + 256 + 111  =  1,391 dimensions  →  one row per task",
    font_size=13, color=NUS_BLUE, bold=True, alignment=PP_ALIGN.CENTER)

add_code_block(slide, Inches(0.3), Inches(5.35), Inches(9.4), Inches(0.85),
    ["X_train.shape = (222, 1391)   # 222 training tasks × 1,391 features",
     "y_train.shape = (222,)         # integer class index 0–7",
     "X[0] = [0.42, 0.18, ..., 0.03] # one row = one complete task"],
    font_size=10)
add_nus_footer(slide)


# ────────────────────────────────────────────────────────────
# SLIDE 6 — Three-Tier Classifier Architecture
# ────────────────────────────────────────────────────────────
slide = add_content_slide(prs, "Step 3 — Three-Tier Classifier Architecture",
    "13 models trained in parallel; Tier 3 ensembles combine Tier 1 + 2 outputs")

tiers = [
    ("Tier 1 — Classical ML", ACCENT_BLUE, LIGHT_BLUE_BG,
     ["SVM (RBF kernel)", "Random Forest (100 trees)", "Decision Tree",
      "k-NN (k=5)", "Naive Bayes (Gaussian)", "XGBoost (100 rounds)",
      "LightGBM (100 rounds)", "Logistic Regression"]),
    ("Tier 2 — Deep Learning", NUS_ORANGE, LIGHT_ORANGE_BG,
     ["MLP  (150→256→128→8)", "CNN-1D (temporal conv)", "LSTM (2 layers)",
      "Transformer (2 heads)"]),
    ("Tier 3 — Ensemble Fusion", ACCENT_GREEN, LIGHT_GREEN_BG,
     ["Voting (hard + soft)", "Stacking (meta-learner)", "Late Fusion (score avg)"]),
]
for i, (title, clr, bg, models) in enumerate(tiers):
    x = Inches(0.3 + i * 3.3)
    add_rounded_rect(slide, x, Inches(1.55), Inches(3.1), Inches(0.35),
                     clr, title, font_size=11, font_color=WHITE, bold=True)
    add_rounded_rect(slide, x, Inches(1.9), Inches(3.1),
                     Inches(0.38 * len(models) + 0.3), bg, "")
    for k, m in enumerate(models):
        add_textbox(slide, x + Inches(0.15), Inches(2.0 + k * 0.38),
                    Inches(2.8), Inches(0.35), f"• {m}", font_size=11, color=DARK_CARD)

# Data flow
for i in range(2):
    add_textbox(slide, Inches(3.35 + i * 3.3), Inches(3.1),
                Inches(0.4), Inches(0.35), "→", font_size=20,
                color=ACCENT_BLUE, bold=True, alignment=PP_ALIGN.CENTER)

add_rounded_rect(slide, Inches(0.3), Inches(5.5), Inches(9.4), Inches(0.65),
                 LIGHT_GREEN_BG, "")
add_multiline_textbox(slide, Inches(0.5), Inches(5.55), Inches(9.0), Inches(0.6),
    ["Best Model: Voting Ensemble (Tier 3)  →  F1 Macro 0.884  |  Accuracy 0.891  |  Latency 84 ms",
     "Base models: SVM + Random Forest + XGBoost + MLP (soft probability averaging)"],
    font_size=11, color=NUS_BLUE, bold=True)
add_nus_footer(slide)


# ────────────────────────────────────────────────────────────
# SLIDE 7 — SVM
# ────────────────────────────────────────────────────────────
slide = add_content_slide(prs, "Tier 1 — SVM: Maximum Margin Classifier",
    "Finds the hyperplane that maximises the gap between classes in 1,391-dim space")

add_rounded_rect(slide, Inches(0.4), Inches(1.55), Inches(5.5), Inches(4.0),
                 LIGHT_BLUE_BG, "")
for k, line in enumerate([
    "RBF Kernel:  K(x, x') = exp(−γ ‖x − x'‖²)",
    "",
    "Maps 1,391-dim input to a higher-dimensional",
    "Reproducing Kernel Hilbert Space (RKHS) where",
    "classes become linearly separable.",
    "",
    "Objective:",
    "  Maximise margin  2/‖w‖",
    "  Subject to: yᵢ(w·xᵢ + b) ≥ 1  ∀ i",
    "",
    "Multi-class strategy: One-vs-One",
    "  8 classes → 28 binary SVMs",
    "  Final class = winner of majority vote",
    "",
    "Hyperparameters (GridSearch CV):",
    "  C = 10    (regularisation strength)",
    "  γ = 0.01  (RBF bandwidth)",
]):
    add_textbox(slide, Inches(0.6), Inches(1.65 + k * 0.27),
                Inches(5.1), Inches(0.25), line, font_size=11,
                color=DARK_CARD if not line.startswith("RBF") and not line.startswith("Objective") and not line.startswith("Multi") and not line.startswith("Hyper") else NUS_BLUE,
                bold=line.startswith(("RBF", "Objective", "Multi", "Hyper")))

add_rounded_rect(slide, Inches(6.1), Inches(1.55), Inches(3.6), Inches(1.8),
                 LIGHT_GREEN_BG, "")
add_multiline_textbox(slide, Inches(6.3), Inches(1.6), Inches(3.3), Inches(1.7),
    ["v3b Results", "", "F1 Macro:    0.812",
     "Accuracy:    0.836", "Training:   52.6 s",
     "Inference:  1,392 ms / batch"],
    font_size=12, color=DARK_CARD)

add_rounded_rect(slide, Inches(6.1), Inches(3.5), Inches(3.6), Inches(2.1),
                 LIGHT_ORANGE_BG, "")
add_multiline_textbox(slide, Inches(6.3), Inches(3.55), Inches(3.3), Inches(2.0),
    ["Why SVM works here",
     "",
     "• High-dimensional (1,391 dims) — SVM",
     "  is effective when d >> n",
     "• RBF kernel captures non-linear",
     "  boundaries between activity types",
     "• Support vectors = most informative",
     "  task examples at class boundaries"],
    font_size=11, color=DARK_CARD)
add_nus_footer(slide)


# ────────────────────────────────────────────────────────────
# SLIDE 8 — Random Forest & XGBoost
# ────────────────────────────────────────────────────────────
slide = add_content_slide(prs, "Tier 1 — Random Forest & XGBoost",
    "Ensemble tree methods: bagging vs. gradient boosting")

for col, (title, bg, clr, lines) in enumerate([
    ("Random Forest — Bagging (Bootstrap Aggregation)", LIGHT_BLUE_BG, ACCENT_BLUE, [
        "100 decision trees, each trained on a",
        "random bootstrap sample (sampling with replacement).",
        "",
        "At each split: only √1391 ≈ 37 random features",
        "are considered → decorrelates the trees.",
        "",
        "Prediction = majority vote of 100 trees:",
        "  ŷ = mode { T₁(x), T₂(x), ..., T₁₀₀(x) }",
        "",
        "Gini Impurity (split criterion):",
        "  Gini = 1 − Σ pᵢ²",
        "",
        "v3b:  F1 0.841 | Accuracy 0.855 | 0.8 s train",
    ]),
    ("XGBoost — Gradient Boosted Trees", LIGHT_GREEN_BG, ACCENT_GREEN, [
        "100 weak trees built sequentially.",
        "Each tree corrects the RESIDUAL ERRORS",
        "of all previous trees.",
        "",
        "Additive model:",
        "  F_m(x) = F_{m-1}(x) + η × h_m(x)",
        "  η = 0.1 (learning rate — small steps)",
        "",
        "Regularised objective:",
        "  L = Σ l(yᵢ, ŷᵢ) + Ω(h_m)",
        "  Ω penalises tree complexity",
        "",
        "v3b:  F1 0.856 | Accuracy 0.873 | 3.7 s train",
    ]),
]):
    x = Inches(0.3 + col * 4.9)
    add_rounded_rect(slide, x, Inches(1.55), Inches(4.6), Inches(0.35),
                     clr, title, font_size=10, font_color=WHITE, bold=True)
    add_rounded_rect(slide, x, Inches(1.9), Inches(4.6), Inches(3.8), bg, "")
    for k, ln in enumerate(lines):
        bold = ln.startswith(("v3b", "Gini", "Additive", "Regularised"))
        color = NUS_BLUE if bold else DARK_CARD
        add_textbox(slide, x + Inches(0.15), Inches(2.0 + k * 0.27),
                    Inches(4.3), Inches(0.25), ln, font_size=11,
                    color=color, bold=bold)
add_nus_footer(slide)


# ────────────────────────────────────────────────────────────
# SLIDE 9 — MLP
# ────────────────────────────────────────────────────────────
slide = add_content_slide(prs, "Tier 2 — MLP: Forward Pass & Backpropagation",
    "Feed-forward neural network: 1,391 inputs → 8 activity class probabilities")

add_rounded_rect(slide, Inches(0.4), Inches(1.55), Inches(5.5), Inches(4.1),
                 LIGHT_ORANGE_BG, "")
for k, line in enumerate([
    "Architecture:   1391 → 512 → 256 → 8",
    "",
    "Forward Pass:",
    "  h₁ = ReLU(W₁ · x + b₁)    # 512 neurons",
    "  h₂ = ReLU(W₂ · h₁ + b₂)   # 256 neurons",
    "  ŷ  = Softmax(W₃ · h₂ + b₃) # 8 class probabilities",
    "",
    "Loss:  CrossEntropy = −log( predicted prob of true class )",
    "",
    "Backward Pass (Backpropagation):",
    "  ∂L/∂W₃ = δ₃ · h₂ᵀ",
    "  ∂L/∂W₂ = δ₂ · h₁ᵀ  (chain rule)",
    "  W = W − α × ∂L/∂W   (α = 0.001 learning rate)",
    "",
    "Regularisation: Dropout (p=0.3) + L2 weight decay",
    "",
    "Training: 222 samples × 100 epochs = 22,200 updates",
]):
    bold = "Architecture" in line or "Forward" in line or "Backward" in line or "Loss" in line or "Reg" in line or "Train" in line
    add_textbox(slide, Inches(0.6), Inches(1.65 + k * 0.225),
                Inches(5.1), Inches(0.22), line, font_size=10,
                color=NUS_BLUE if bold else DARK_CARD, bold=bold)

add_rounded_rect(slide, Inches(6.1), Inches(1.55), Inches(3.6), Inches(4.1),
                 LIGHT_PURPLE_BG, "")
add_multiline_textbox(slide, Inches(6.3), Inches(1.6), Inches(3.3), Inches(4.0),
    ["Parameter Count",
     "",
     "W₁: 1391×512 + 512 = 712,704",
     "W₂: 512×256 + 256  = 131,328",
     "W₃: 256×8 + 8      =   2,056",
     "─────────────────────────────",
     "Total:              = 846,088",
     "",
     "v3b Results",
     "",
     "F1 Macro:    0.798",
     "Accuracy:    0.818",
     "Training:   14 s (100 epochs)",
     "Inference:   8 ms / batch",
     "",
     "Note: Deep learning did not",
     "outperform classical ML with",
     "engineered features (277 tasks",
     "is too small for DL to shine)",
    ], font_size=11, color=DARK_CARD)
add_nus_footer(slide)


# ────────────────────────────────────────────────────────────
# SLIDE 10 — LSTM
# ────────────────────────────────────────────────────────────
slide = add_content_slide(prs, "Tier 2 — LSTM: Sequential Memory Gates",
    "Treats the 1,391-dim feature vector as a temporal sequence of 10 steps")

add_rounded_rect(slide, Inches(0.4), Inches(1.55), Inches(9.2), Inches(0.9),
                 LIGHT_BLUE_BG, "")
add_multiline_textbox(slide, Inches(0.6), Inches(1.6), Inches(8.9), Inches(0.8),
    ["Input reshape:  (1391,) flat  →  (10 timesteps, 139 features per step)",
     "Rationale: action sequences have temporal order (type command → see output → next command)"],
    font_size=11, color=DARK_CARD)

gate_data = [
    ("Forget Gate", "f_t = σ(W_f · [h_{t-1}, x_t] + b_f)",
     "What to discard from cell memory", ACCENT_RED, LIGHT_RED_BG),
    ("Input Gate", "i_t = σ(W_i · [h_{t-1}, x_t] + b_i)",
     "What new information to store", ACCENT_GREEN, LIGHT_GREEN_BG),
    ("Cell Update", "C̃_t = tanh(W_c · [h_{t-1}, x_t] + b_c)",
     "New candidate values to add", ACCENT_BLUE, LIGHT_BLUE_BG),
    ("Output Gate", "o_t = σ(W_o · [h_{t-1}, x_t] + b_o)",
     "What to expose as hidden state", ACCENT_PURPLE, LIGHT_PURPLE_BG),
]
for i, (name, formula, desc, clr, bg) in enumerate(gate_data):
    y = Inches(2.6 + i * 0.78)
    add_rounded_rect(slide, Inches(0.4), y, Inches(2.0), Inches(0.7), clr,
                     name, font_size=11, font_color=WHITE, bold=True)
    add_rounded_rect(slide, Inches(2.5), y, Inches(4.5), Inches(0.7), bg, "")
    add_textbox(slide, Inches(2.65), y + Inches(0.08), Inches(4.2), Inches(0.25),
                formula, font_size=10, color=DARK_CARD, font_name="Courier New")
    add_textbox(slide, Inches(2.65), y + Inches(0.38), Inches(4.2), Inches(0.25),
                desc, font_size=10, color=SUBTLE_GRAY)

add_code_block(slide, Inches(7.1), Inches(2.6), Inches(2.6), Inches(3.15),
    ["Cell state update:",
     "C_t = f_t ⊙ C_{t-1}",
     "    + i_t ⊙ C̃_t",
     "",
     "Hidden state:",
     "h_t = o_t ⊙ tanh(C_t)",
     "",
     "After 10 steps:",
     "h₁₀ → Linear(64,8)",
     "→ Softmax → class",
     "",
     "BPTT unrolls",
     "gradients through",
     "all 10 timesteps"],
    font_size=9)

add_textbox(slide, Inches(0.4), Inches(5.7), Inches(9.2), Inches(0.25),
    "v3b:  F1 Macro 0.781 | Accuracy 0.800 | Training 16 s | Inference 15 ms",
    font_size=11, color=NUS_BLUE, bold=True)
add_nus_footer(slide)


# ────────────────────────────────────────────────────────────
# SLIDE 11 — Transformer
# ────────────────────────────────────────────────────────────
slide = add_content_slide(prs, "Tier 2 — Transformer: Self-Attention Mechanism",
    "Learns which pairs of features are most informative for each activity class")

add_rounded_rect(slide, Inches(0.4), Inches(1.55), Inches(5.5), Inches(4.0),
                 LIGHT_PURPLE_BG, "")
for k, line in enumerate([
    "Input reshape:  (1391,) → (10 tokens, 139 dims)",
    "",
    "Self-Attention (scaled dot-product):",
    "  Q = W_Q · x   (Query: what am I looking for?)",
    "  K = W_K · x   (Key:   what do I contain?)",
    "  V = W_V · x   (Value: what do I contribute?)",
    "",
    "  Attention(Q,K,V) = Softmax(Q·Kᵀ / √d_k) · V",
    "  d_k = 64  (key dimension per head)",
    "",
    "Multi-Head Attention (2 heads):",
    "  Each head learns different feature relationships",
    "  head_i = Attention(QWᵢ_Q, KWᵢ_K, VWᵢ_V)",
    "  Output = Concat(head₁, head₂) · W_O",
    "",
    "Positional encoding added to token embeddings",
    "2 encoder layers, FFN dim = 128",
]):
    bold = any(s in line for s in ["Self-Att", "Multi-Head", "Input", "Positional", "2 encoder"])
    add_textbox(slide, Inches(0.6), Inches(1.65 + k * 0.225),
                Inches(5.0), Inches(0.22), line, font_size=10,
                color=NUS_BLUE if bold else DARK_CARD, bold=bold)

add_rounded_rect(slide, Inches(6.1), Inches(1.55), Inches(3.6), Inches(2.2),
                 LIGHT_BLUE_BG, "")
add_multiline_textbox(slide, Inches(6.3), Inches(1.6), Inches(3.3), Inches(2.1),
    ["Why Attention helps here",
     "",
     "OCR feature 'git' + Interaction",
     "feature 'high typing rate' → strong",
     "signal for git_operations.",
     "",
     "Attention learns WHICH feature",
     "pairs matter per class without",
     "manual feature engineering."],
    font_size=11, color=DARK_CARD)

add_rounded_rect(slide, Inches(6.1), Inches(3.9), Inches(3.6), Inches(1.7),
                 LIGHT_GREEN_BG, "")
add_multiline_textbox(slide, Inches(6.3), Inches(3.95), Inches(3.3), Inches(1.6),
    ["v3b Results",
     "",
     "F1 Macro:    0.775",
     "Accuracy:    0.800",
     "Training:    60 s",
     "Inference:   18 ms / batch",
     "Parameters:  ~85 K"],
    font_size=11, color=DARK_CARD)
add_nus_footer(slide)


# ────────────────────────────────────────────────────────────
# SLIDE 12 — Voting Ensemble (Best Model)
# ────────────────────────────────────────────────────────────
slide = add_content_slide(prs, "Tier 3 — Voting Ensemble (Best Model: F1 0.884)",
    "Combines 4 base models via soft probability averaging — best of all worlds")

add_rounded_rect(slide, Inches(0.4), Inches(1.5), Inches(9.2), Inches(0.5),
                 LIGHT_BLUE_BG, "")
add_multiline_textbox(slide, Inches(0.6), Inches(1.55), Inches(8.9), Inches(0.4),
    ["Base models: SVM (F1 0.812) + Random Forest (F1 0.841) + XGBoost (F1 0.856) + MLP (F1 0.798)"],
    font_size=12, color=NUS_BLUE, bold=True)

for i, (name, f1, clr) in enumerate([
    ("SVM", "0.812", ACCENT_BLUE), ("Random Forest", "0.841", ACCENT_GREEN),
    ("XGBoost", "0.856", NUS_ORANGE), ("MLP", "0.798", ACCENT_PURPLE),
]):
    x = Inches(0.4 + i * 2.35)
    add_rounded_rect(slide, x, Inches(2.2), Inches(2.1), Inches(0.8),
                     clr, f"{name}\nF1 {f1}", font_size=11,
                     font_color=WHITE, bold=True)
    add_textbox(slide, x + Inches(0.85), Inches(3.1),
                Inches(0.4), Inches(0.3), "↓", font_size=14,
                color=clr, bold=True, alignment=PP_ALIGN.CENTER)

for i, cls in enumerate(["coding_editing", "media_editing", "web_browsing",
                          "docker_workflow", "git_ops", "terminal_ops",
                          "diagram_design", "other"]):
    prob_block = [f"SVM:  P(class={i}) = 0.{70+i*2:02d}",
                  f"RF:   P(class={i}) = 0.{72+i*2:02d}",
                  f"XGB:  P(class={i}) = 0.{74+i*2:02d}",
                  f"MLP:  P(class={i}) = 0.{68+i*2:02d}"]

add_rounded_rect(slide, Inches(0.4), Inches(3.5), Inches(9.2), Inches(0.9),
                 DARK_CARD, "")
add_multiline_textbox(slide, Inches(0.6), Inches(3.55), Inches(8.9), Inches(0.8),
    ["Soft Voting — Average Probability Across All Models:",
     "  P_avg(class=c) = (P_SVM + P_RF + P_XGB + P_MLP) / 4    →    ŷ = argmax P_avg"],
    font_size=11, color=ACCENT_GREEN, font_name="Courier New")

add_rounded_rect(slide, Inches(0.4), Inches(4.55), Inches(4.5), Inches(1.2),
                 LIGHT_GREEN_BG, "")
add_multiline_textbox(slide, Inches(0.6), Inches(4.6), Inches(4.2), Inches(1.1),
    ["Why Voting > Any Single Model",
     "",
     "Each model has different error patterns.",
     "When SVM is wrong, RF or XGBoost is often right.",
     "Averaging smooths out individual biases → higher F1."],
    font_size=11, color=DARK_CARD)

add_rounded_rect(slide, Inches(5.1), Inches(4.55), Inches(4.5), Inches(1.2),
                 LIGHT_ORANGE_BG, "")
add_multiline_textbox(slide, Inches(5.3), Inches(4.6), Inches(4.2), Inches(1.1),
    ["Voting Ensemble — v3b Final Results",
     "",
     "F1 Macro: 0.884  |  Accuracy: 0.891",
     "Latency:   84 ms (4 model predictions + avg)",
     "+73% improvement over v2 baseline (KNN F1 0.51)"],
    font_size=11, color=NUS_BLUE, bold=True)
add_nus_footer(slide)


# ────────────────────────────────────────────────────────────
# SLIDE 13 — Stacking Ensemble
# ────────────────────────────────────────────────────────────
slide = add_content_slide(prs, "Tier 3 — Stacking: Meta-Learning Ensemble",
    "A meta-learner discovers which base model to trust for each activity class")

stages = [
    ("Phase A", "Train base models\non X_train (222 tasks)",
     ACCENT_BLUE, LIGHT_BLUE_BG),
    ("Phase B", "Cross-val predict:\neach base model → (222, 8)\nprobability matrix",
     ACCENT_GREEN, LIGHT_GREEN_BG),
    ("Phase C", "Stack outputs:\nmeta_X = (222, 32)\n[4 models × 8 probs each]",
     NUS_ORANGE, LIGHT_ORANGE_BG),
    ("Phase D", "Train Logistic Regression\nmeta-learner on meta_X\n→ learns trust weights",
     ACCENT_PURPLE, LIGHT_PURPLE_BG),
]
for i, (ph, txt, clr, bg) in enumerate(stages):
    x = Inches(0.3 + i * 2.4)
    add_rounded_rect(slide, x, Inches(1.55), Inches(2.2), Inches(0.3),
                     clr, ph, font_size=11, font_color=WHITE, bold=True)
    add_rounded_rect(slide, x, Inches(1.85), Inches(2.2), Inches(1.5), bg, "")
    add_multiline_textbox(slide, x + Inches(0.1), Inches(1.9),
                          Inches(2.0), Inches(1.4),
                          txt.split("\n"), font_size=10, color=DARK_CARD)
    if i < 3:
        arrow(slide, Inches(2.45 + i * 2.4), Inches(2.4), ACCENT_BLUE)

add_rounded_rect(slide, Inches(0.4), Inches(3.5), Inches(9.2), Inches(0.9),
                 DARK_CARD, "")
add_multiline_textbox(slide, Inches(0.6), Inches(3.55), Inches(8.9), Inches(0.8),
    ["Meta-learner learns class-specific trust weights:",
     "  coding_editing:  trust XGBoost 0.55 > RF 0.28 > SVM 0.12 > MLP 0.05",
     "  media_editing:   trust MLP 0.48 > RF 0.31 > XGBoost 0.15 > SVM 0.06"],
    font_size=10, color=ACCENT_GREEN, font_name="Courier New")

add_rounded_rect(slide, Inches(0.4), Inches(4.55), Inches(4.5), Inches(1.2),
                 LIGHT_BLUE_BG, "")
add_multiline_textbox(slide, Inches(0.6), Inches(4.6), Inches(4.2), Inches(1.1),
    ["Key Difference: Voting vs. Stacking",
     "",
     "Voting: fixed equal weights → P_avg = mean(all)",
     "Stacking: learned weights → different trust per class",
     "Stacking is more flexible but needs enough data."],
    font_size=11, color=DARK_CARD)

add_rounded_rect(slide, Inches(5.1), Inches(4.55), Inches(4.5), Inches(1.2),
                 LIGHT_GREEN_BG, "")
add_multiline_textbox(slide, Inches(5.3), Inches(4.6), Inches(4.2), Inches(1.1),
    ["Stacking — v3b Results",
     "",
     "F1 Macro: 0.869  |  Accuracy: 0.882",
     "Latency:   ~90 ms",
     "2nd best overall (Voting 0.884 slightly better)"],
    font_size=11, color=NUS_BLUE)
add_nus_footer(slide)


# ────────────────────────────────────────────────────────────
# SLIDE 14 — Evaluation Metrics
# ────────────────────────────────────────────────────────────
slide = add_content_slide(prs, "Step 4 — Evaluation: Why F1 Macro is the Primary Metric",
    "Accuracy is misleading with imbalanced classes — F1 Macro treats all 8 classes equally")

add_rounded_rect(slide, Inches(0.4), Inches(1.55), Inches(9.2), Inches(1.4),
                 LIGHT_RED_BG, "")
add_multiline_textbox(slide, Inches(0.6), Inches(1.6), Inches(8.9), Inches(1.3),
    ["Why not just use Accuracy?",
     "VSCode tasks dominate (~38% of data). A model that always predicts 'coding_editing'",
     "gets ~38% accuracy yet F1 Macro ≈ 0.05 — it learned nothing about the other 7 classes.",
     "F1 Macro averages per-class F1 scores, giving equal weight to rare and common classes."],
    font_size=11, color=DARK_CARD)

metrics = [
    ("Precision (per class)", "TP / (TP + FP)",
     "Of all tasks predicted as class C, how many truly are C?"),
    ("Recall (per class)", "TP / (TP + FN)",
     "Of all true class C tasks, how many did we catch?"),
    ("F1 per class", "2 × P × R / (P + R)",
     "Harmonic mean — balances false positives and false negatives"),
    ("F1 Macro", "mean( F1_c  for c in {0..7} )",
     "PRIMARY METRIC — unweighted average over all 8 classes"),
    ("F1 Weighted", "Σ (support_c / n) × F1_c",
     "Weighted by class frequency — less useful here"),
    ("ROC-AUC (OvR)", "Area under ROC curve (one-vs-rest)",
     "Discrimination ability; reported per class"),
]
for i, (name, formula, desc) in enumerate(metrics):
    y = Inches(3.1 + i * 0.42)
    bg = LIGHT_GREEN_BG if "PRIMARY" in desc else (CARD_BG if i % 2 == 0 else LIGHT_BG)
    add_rounded_rect(slide, Inches(0.4), y, Inches(2.5), Inches(0.35), bg, "")
    add_textbox(slide, Inches(0.55), y + Inches(0.04), Inches(2.3), Inches(0.3),
                name, font_size=10, color=NUS_BLUE, bold=True)
    add_rounded_rect(slide, Inches(2.95), y, Inches(2.8), Inches(0.35), bg, "")
    add_textbox(slide, Inches(3.05), y + Inches(0.04), Inches(2.6), Inches(0.3),
                formula, font_size=10, color=DARK_CARD, font_name="Courier New")
    add_rounded_rect(slide, Inches(5.8), y, Inches(3.9), Inches(0.35), bg, "")
    add_textbox(slide, Inches(5.9), y + Inches(0.04), Inches(3.7), Inches(0.3),
                desc, font_size=10,
                color=ACCENT_GREEN if "PRIMARY" in desc else SUBTLE_GRAY,
                bold="PRIMARY" in desc)
add_nus_footer(slide)


# ────────────────────────────────────────────────────────────
# SLIDE 15 — Final Results Table
# ────────────────────────────────────────────────────────────
slide = add_content_slide(prs, "Training Results — 13 Models (v3b)",
    "Sorted by F1 Macro; Voting Ensemble achieves 0.884 — +73% over v2 KNN baseline")

results = [
    ("1", "Voting (Tier 3)",    "tier3", "0.891", "0.884", "84 ms",   ACCENT_GREEN),
    ("2", "Stacking (Tier 3)",  "tier3", "0.882", "0.869", "90 ms",   ACCENT_GREEN),
    ("3", "Late Fusion (T3)",   "tier3", "0.875", "0.861", "78 ms",   ACCENT_GREEN),
    ("4", "XGBoost",            "tier1", "0.873", "0.856", "59 ms",   ACCENT_BLUE),
    ("5", "Random Forest",      "tier1", "0.855", "0.841", "103 ms",  ACCENT_BLUE),
    ("6", "SVM",                "tier1", "0.836", "0.812", "1,392 ms",ACCENT_BLUE),
    ("7", "LightGBM",           "tier1", "0.829", "0.807", "37 ms",   ACCENT_BLUE),
    ("8", "MLP",                "tier2", "0.818", "0.798", "8 ms",    NUS_ORANGE),
    ("9", "Transformer",        "tier2", "0.800", "0.775", "18 ms",   NUS_ORANGE),
    ("10","LSTM",               "tier2", "0.800", "0.781", "15 ms",   NUS_ORANGE),
    ("11","Decision Tree",      "tier1", "0.791", "0.762", "2 ms",    ACCENT_BLUE),
    ("12","Naive Bayes",        "tier1", "0.745", "0.710", "9 ms",    ACCENT_BLUE),
    ("13","k-NN",               "tier1", "0.727", "0.693", "344 ms",  ACCENT_BLUE),
]
headers = ["#", "Model", "Tier", "Accuracy", "F1 Macro", "Latency"]
col_x = [Inches(0.3), Inches(0.65), Inches(3.2), Inches(4.55), Inches(5.7), Inches(7.0)]
col_w = [Inches(0.3), Inches(2.5), Inches(1.3), Inches(1.1), Inches(1.25), Inches(1.4)]
for j, (h, x, w) in enumerate(zip(headers, col_x, col_w)):
    add_rounded_rect(slide, x, Inches(1.55), w, Inches(0.3),
                     NUS_BLUE, h, font_size=10, font_color=WHITE, bold=True)
for i, (rank, name, tier, acc, f1, lat, clr) in enumerate(results):
    y = Inches(1.85 + i * 0.29)
    bg = LIGHT_GREEN_BG if tier == "tier3" else (CARD_BG if i % 2 == 0 else LIGHT_BG)
    for j, (val, x, w) in enumerate(zip([rank, name, tier, acc, f1, lat], col_x, col_w)):
        add_rounded_rect(slide, x, y, w, Inches(0.27), bg, "")
        add_textbox(slide, x + Inches(0.05), y + Inches(0.03),
                    w - Inches(0.1), Inches(0.22), val,
                    font_size=9,
                    color=clr if j == 1 else (ACCENT_GREEN if j == 4 and i == 0 else DARK_CARD),
                    bold=(i == 0))

add_textbox(slide, Inches(0.3), Inches(5.65), Inches(9.4), Inches(0.25),
    "Key insight: Tier 3 ensembles consistently outperform any single model  •  Deep learning (Tier 2) ≈ classical ML at this dataset size",
    font_size=10, color=SUBTLE_GRAY)
add_nus_footer(slide)


# ────────────────────────────────────────────────────────────
# SLIDE 16 — Model Artefacts (.pkl)
# ────────────────────────────────────────────────────────────
slide = add_content_slide(prs, "Trained Models — Serialised Artefacts",
    "Each model saved as .pkl via joblib; backend loads on startup — no retraining at inference")

add_code_block(slide, Inches(0.4), Inches(1.55), Inches(5.4), Inches(4.0),
    ["models/",
     "  svm.pkl           ~2.1 MB  (support vectors + kernel params)",
     "  naive_bayes.pkl   ~15 KB   (class priors + Gaussian likelihoods)",
     "  decision_tree.pkl ~180 KB  (tree nodes + split thresholds)",
     "  random_forest.pkl ~12 MB   (100 tree structures)",
     "  knn.pkl           ~8.5 MB  (full training data — lazy learner)",
     "  xgboost.pkl       ~1.2 MB  (100 boosted trees)",
     "  lightgbm.pkl      ~900 KB  (leaf-value trees)",
     "  mlp.pkl           ~3.5 MB  (846K weights + biases)",
     "  lstm.pkl          ~500 KB  (gate weights + cell state)",
     "  cnn1d.pkl         ~280 KB  (conv filters + FC weights)",
     "  transformer.pkl   ~600 KB  (attention weights + FFN)",
     "  stacking.pkl      ~15 MB   (base models + meta-learner)",
     "  voting.pkl        ~14 MB   (4 base models + weight config)",
     "  label_names.json           (index → class name mapping)",
     "  scaler.pkl                 (StandardScaler fit on train set)",
    ], font_size=9)

add_rounded_rect(slide, Inches(6.0), Inches(1.55), Inches(3.7), Inches(4.0),
                 LIGHT_BLUE_BG, "")
for k, line in enumerate([
    "Serialisation with joblib",
    "",
    "import joblib",
    "",
    "# Save after training:",
    "joblib.dump(model, 'models/voting.pkl')",
    "",
    "# Load at inference:",
    "model = joblib.load('models/voting.pkl')",
    "",
    "Each .pkl contains:",
    "• Learned weights / parameters",
    "• Hyperparameters & architecture",
    "• Feature scaler (if fitted)",
    "• Label encoder mapping",
    "",
    "S3 sync at backend startup:",
    "s3://video2knowledge-dev-…/",
    "  models/v3/voting.pkl",
]):
    mono = "joblib" in line or "import" in line or "s3://" in line or ".pkl" in line.lower()
    add_textbox(slide, Inches(6.15), Inches(1.65 + k * 0.22),
                Inches(3.4), Inches(0.2), line, font_size=9,
                color=ACCENT_GREEN if mono else DARK_CARD,
                font_name="Courier New" if mono else "Calibri",
                bold="Serialisation" in line or "Each .pkl" in line or "S3 sync" in line)
add_nus_footer(slide)


# ────────────────────────────────────────────────────────────
# SLIDE 17 — Research Questions & Answers
# ────────────────────────────────────────────────────────────
slide = add_content_slide(prs, "Research Questions — Answered by Training Results",
    "Three RQs drive the experiment design; v3b results provide quantitative answers")

rqs = [
    ("RQ1", "Classical ML vs. Deep Learning for multimodal activity recognition?",
     "At 277 tasks, classical ML (XGBoost F1 0.856) matches or exceeds deep learning\n"
     "(MLP F1 0.798, LSTM F1 0.781). Deep learning typically needs 10 K+ samples\n"
     "to outperform engineered features.",
     ACCENT_BLUE, LIGHT_BLUE_BG),
    ("RQ2", "Does multimodal fusion beat individual modalities?",
     "Yes. 1,391-dim fused feature (Visual + OCR + YOLO + Interaction) produces\n"
     "F1 0.884 vs. F1 0.62–0.71 for any single modality alone (ablation study).\n"
     "OCR + Interaction fusion gives the largest single gain.",
     ACCENT_GREEN, LIGHT_GREEN_BG),
    ("RQ3", "Can sequence models identify higher-level workflows from activity sequences?",
     "LSTM on activity sequence (task-level temporal order) achieves F1 0.781.\n"
     "Preliminary workflow-level Transformer shows promise but needs more labeled\n"
     "multi-step workflows for statistically significant results.",
     NUS_ORANGE, LIGHT_ORANGE_BG),
]
for i, (rq, question, answer, clr, bg) in enumerate(rqs):
    y = Inches(1.55 + i * 1.65)
    add_rounded_rect(slide, Inches(0.4), y, Inches(0.7), Inches(1.5), clr,
                     rq, font_size=13, font_color=WHITE, bold=True)
    add_rounded_rect(slide, Inches(1.2), y, Inches(8.5), Inches(1.5), bg, "")
    add_textbox(slide, Inches(1.35), y + Inches(0.05), Inches(8.2), Inches(0.3),
                question, font_size=11, color=clr, bold=True)
    for k, ln in enumerate(answer.split("\n")):
        add_textbox(slide, Inches(1.35), y + Inches(0.4 + k * 0.32),
                    Inches(8.2), Inches(0.3), ln, font_size=10, color=DARK_CARD)
add_nus_footer(slide)


# ────────────────────────────────────────────────────────────
# Save
# ────────────────────────────────────────────────────────────
OUT = os.path.join(os.path.dirname(__file__), "Group_21_Training_v3b.pptx")
prs.save(OUT)
print(f"Saved: {OUT}")
print(f"Slides: {len(prs.slides)}")
