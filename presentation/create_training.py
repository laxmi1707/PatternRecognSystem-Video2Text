"""Generate 'How Model Training Works' presentation for Video2Knowledge."""
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

DARK_CARD = RGBColor(0x00, 0x2A, 0x55)

prs = create_presentation()


# ── Local helpers (not in template) ────────────────────────────────────────

def add_code_block(slide, left, top, width, height, lines, font_size=10):
    """Dark code block with monospaced text."""
    add_rounded_rect(slide, left, top, width, height, DARK_CARD)
    add_multiline_textbox(
        slide, left + Inches(0.15), top + Inches(0.1),
        width - Inches(0.3), height - Inches(0.2),
        lines, font_size=font_size,
        color=ACCENT_GREEN, font_name="Courier New",
        spacing=Pt(2),
    )


def add_arrow_right(slide, left, top, color=ACCENT_BLUE, size=18):
    """Right-arrow character."""
    add_textbox(slide, left, top, Inches(0.4), Inches(0.4),
                "→", font_size=size, color=color, bold=True,
                alignment=PP_ALIGN.CENTER)


# ============================================================
# SLIDE 1: Title
# ============================================================
slide = add_title_slide(
    prs,
    "How Model Training Works",
    subtitle="From raw data to trained classifiers",
)

# Phase indicators at bottom
phases = [
    ("Data Prep", ACCENT_BLUE),
    ("Features", ACCENT_GREEN),
    ("Training", NUS_ORANGE),
    ("Evaluation", ACCENT_PURPLE),
]
x = Inches(3.5)
for label, clr in phases:
    add_rounded_rect(slide, x, Inches(5.3), Inches(1.5), Inches(0.4),
                     clr, label, font_size=12, font_color=WHITE, bold=True)
    x += Inches(1.7)


# ============================================================
# SLIDE 2: Training Overview -- 4 Phases
# ============================================================
slide = add_content_slide(prs, "Training Overview — 4 Phases",
                          "End-to-end pipeline from raw dataset to evaluated classifiers")

phase_data = [
    ("Phase 1", "Data Preparation", "Split 9,609 tasks\n80% train / 20% test",
     ACCENT_BLUE, LIGHT_BLUE_BG),
    ("Phase 2", "Feature Extraction", "Video + actions\n→ 150-dim vectors",
     ACCENT_GREEN, LIGHT_GREEN_BG),
    ("Phase 3", "Model Training", "14 models learn\nfrom feature vectors",
     NUS_ORANGE, LIGHT_ORANGE_BG),
    ("Phase 4", "Evaluation", "Test set → metrics\n→ model comparison",
     ACCENT_PURPLE, LIGHT_PURPLE_BG),
]

x = Inches(1.3)
for i, (phase, title, desc, accent, bg) in enumerate(phase_data):
    add_rounded_rect(slide, x, Inches(1.3), Inches(2.5), Inches(2.4), bg)
    add_rounded_rect(slide, x + Inches(0.5), Inches(1.4), Inches(1.5),
                     Inches(0.35), accent, phase, font_size=12,
                     font_color=WHITE, bold=True)
    add_textbox(slide, x + Inches(0.1), Inches(1.9), Inches(2.3), Inches(0.4),
                title, font_size=18, color=accent, bold=True,
                alignment=PP_ALIGN.CENTER)
    add_textbox(slide, x + Inches(0.1), Inches(2.4), Inches(2.3), Inches(0.9),
                desc, font_size=13, color=NUS_ORANGE, alignment=PP_ALIGN.CENTER)
    if i < 3:
        add_arrow_right(slide, x + Inches(2.55), Inches(2.2), color=accent,
                        size=24)
    x += Inches(2.85)

# Training command
add_code_block(slide, Inches(1.5), Inches(4.2), Inches(10.3), Inches(0.6),
               ["$ python -m app.train --dataset-root ./dataset --model-dir ./models"],
               font_size=13)

# Summary note
add_textbox(slide, Inches(1.3), Inches(5.1), Inches(11), Inches(0.6),
            "One command trains all 14 models, evaluates on held-out test set, "
            "and logs results to MLflow",
            font_size=14, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)


# ============================================================
# SLIDE 3: Phase 1 -- Data Preparation
# ============================================================
slide = add_content_slide(prs, "Phase 1 — Data Preparation",
                          "Stratified Train/Test Split")

# Split diagram
add_rounded_rect(slide, Inches(1.3), Inches(1.3), Inches(2.2), Inches(0.6),
                 ACCENT_BLUE, "9,609 Tasks", font_size=16,
                 font_color=WHITE, bold=True)

add_arrow_right(slide, Inches(3.6), Inches(1.35), color=ACCENT_BLUE, size=22)

add_rounded_rect(slide, Inches(4.1), Inches(1.2), Inches(2.5), Inches(0.45),
                 ACCENT_GREEN, "7,685 train (80%)", font_size=13,
                 font_color=WHITE, bold=True)
add_rounded_rect(slide, Inches(4.1), Inches(1.7), Inches(2.5), Inches(0.45),
                 NUS_ORANGE, "1,924 test (20%)", font_size=13,
                 font_color=WHITE, bold=True)

# Label distribution table
add_textbox(slide, Inches(1.3), Inches(2.4), Inches(5), Inches(0.35),
            "Label Distribution", font_size=16, color=WHITE, bold=True)

labels = [
    ("other", "5,441", "57%", ACCENT_BLUE),
    ("coding_editing", "3,240", "34%", ACCENT_GREEN),
    ("documentation", "449", "4.7%", ACCENT_PURPLE),
    ("docker_workflow", "299", "3.1%", NUS_ORANGE),
    ("git_operations", "87", "0.9%", ACCENT_BLUE),
    ("aws_console", "45", "0.5%", ACCENT_GREEN),
    ("debugging", "38", "0.4%", ACCENT_RED),
    ("kubernetes_ops", "9", "0.1%", ACCENT_PURPLE),
    ("jenkins_ci_cd", "1", "0.01%", NUS_ORANGE),
]

# Table header
y = Inches(2.8)
add_rect(slide, Inches(1.3), y, Inches(5.5), Inches(0.35), DARK_CARD)
add_textbox(slide, Inches(1.4), y, Inches(2), Inches(0.35),
            "Label", font_size=11, color=WHITE, bold=True)
add_textbox(slide, Inches(3.5), y, Inches(1.2), Inches(0.35),
            "Count", font_size=11, color=WHITE, bold=True,
            alignment=PP_ALIGN.RIGHT)
add_textbox(slide, Inches(4.9), y, Inches(1), Inches(0.35),
            "Pct", font_size=11, color=WHITE, bold=True,
            alignment=PP_ALIGN.RIGHT)
add_textbox(slide, Inches(6.0), y, Inches(0.8), Inches(0.35),
            "", font_size=11, color=WHITE, bold=True)

y += Inches(0.35)
max_count = 5441
for idx, (label, count, pct, clr) in enumerate(labels):
    row_bg = CARD_BG if idx % 2 == 0 else LIGHT_BG
    add_rect(slide, Inches(1.3), y, Inches(5.5), Inches(0.3), row_bg)
    add_textbox(slide, Inches(1.4), y, Inches(2), Inches(0.3),
                label, font_size=10, color=NUS_ORANGE, font_name="Courier New")
    add_textbox(slide, Inches(3.5), y, Inches(1.2), Inches(0.3),
                count, font_size=10, color=NUS_ORANGE,
                alignment=PP_ALIGN.RIGHT)
    add_textbox(slide, Inches(4.9), y, Inches(1), Inches(0.3),
                pct, font_size=10, color=LIGHT_GRAY,
                alignment=PP_ALIGN.RIGHT)
    bar_w = float(count.replace(",", "")) / max_count * 1.2
    if bar_w > 0.02:
        add_rect(slide, Inches(6.0), y + Inches(0.07),
                 Inches(bar_w), Inches(0.16), clr)
    y += Inches(0.3)

# Right side notes
add_rounded_rect(slide, Inches(7.5), Inches(1.3), Inches(5.3), Inches(1.5),
                 LIGHT_BLUE_BG)
add_textbox(slide, Inches(7.7), Inches(1.4), Inches(4.9), Inches(0.35),
            "Stratified Split", font_size=15, color=ACCENT_BLUE, bold=True)
add_multiline_textbox(slide, Inches(7.7), Inches(1.8), Inches(4.9), Inches(0.9),
                      ["Same label proportions in both train and test",
                       "Ensures test set is representative of real data",
                       "sklearn.model_selection.train_test_split(stratify=y)"],
                      font_size=12, color=NUS_ORANGE, spacing=Pt(6))

# Class imbalance callout
add_rounded_rect(slide, Inches(7.5), Inches(3.1), Inches(5.3), Inches(1.4),
                 LIGHT_RED_BG)
add_textbox(slide, Inches(7.7), Inches(3.2), Inches(4.9), Inches(0.35),
            "Class Imbalance Problem", font_size=15, color=ACCENT_RED,
            bold=True)
add_multiline_textbox(slide, Inches(7.7), Inches(3.6), Inches(4.9), Inches(0.8),
                      ['"other" dominates at 57% — model can just predict "other"',
                       "jenkins_ci_cd has only 1 sample",
                       "Data augmentation applied when < 100 training samples (5x)"],
                      font_size=12, color=NUS_ORANGE, spacing=Pt(6))

# Augmentation note
add_rounded_rect(slide, Inches(7.5), Inches(4.8), Inches(5.3), Inches(1.0),
                 LIGHT_GREEN_BG)
add_textbox(slide, Inches(7.7), Inches(4.9), Inches(4.9), Inches(0.35),
            "Data Augmentation", font_size=15, color=ACCENT_GREEN, bold=True)
add_multiline_textbox(slide, Inches(7.7), Inches(5.3), Inches(4.9), Inches(0.4),
                      ["Classes with < 100 samples get 5x augmentation",
                       "Adds noise to feature vectors to create synthetic samples"],
                      font_size=12, color=NUS_ORANGE, spacing=Pt(6))


# ============================================================
# SLIDE 4: Phase 2 -- Feature Extraction
# ============================================================
slide = add_content_slide(prs, "Phase 2 — Feature Extraction",
                          "Converting raw video + actions into numeric vectors")

# Pipeline: Video + action_log -> 4 extractors -> 150-dim vector
add_rounded_rect(slide, Inches(1.3), Inches(1.3), Inches(2.0), Inches(1.0),
                 ACCENT_BLUE, "Video +\naction_log", font_size=14,
                 font_color=WHITE, bold=True)

add_arrow_right(slide, Inches(3.35), Inches(1.55), color=ACCENT_BLUE, size=22)

# 4 Extractors
extractor_data = [
    ("Visual", "Frames, UI layout,\nscreen regions"),
    ("OCR", "Text on screen,\ncommand output"),
    ("Interaction", "Mouse, keyboard,\ntiming patterns"),
    ("Action Log", "CLI commands,\nfile operations"),
]

y_ext = Inches(1.1)
for name, desc in extractor_data:
    add_rounded_rect(slide, Inches(3.9), y_ext, Inches(2.5), Inches(0.55),
                     ACCENT_GREEN)
    add_textbox(slide, Inches(4.0), y_ext + Inches(0.02), Inches(1.0),
                Inches(0.25), name, font_size=11, color=WHITE, bold=True)
    add_textbox(slide, Inches(4.9), y_ext + Inches(0.02), Inches(1.4),
                Inches(0.5), desc, font_size=9, color=WHITE)
    y_ext += Inches(0.6)

add_arrow_right(slide, Inches(6.5), Inches(1.55), color=ACCENT_GREEN, size=22)

# Output vector
add_rounded_rect(slide, Inches(7.0), Inches(1.3), Inches(2.2), Inches(1.0),
                 NUS_ORANGE, "150-dim\nFeature Vector", font_size=14,
                 font_color=WHITE, bold=True)

# Matrix shapes
add_textbox(slide, Inches(1.3), Inches(3.1), Inches(11), Inches(0.35),
            "Result Matrices", font_size=18, color=WHITE, bold=True)

add_rounded_rect(slide, Inches(1.3), Inches(3.6), Inches(3.5), Inches(0.55),
                 LIGHT_BLUE_BG)
add_textbox(slide, Inches(1.4), Inches(3.65), Inches(3.3), Inches(0.45),
            "X_train shape: (7685, 150)", font_size=14, color=ACCENT_BLUE,
            bold=True, font_name="Courier New")

add_rounded_rect(slide, Inches(5.1), Inches(3.6), Inches(3.0), Inches(0.55),
                 LIGHT_BLUE_BG)
add_textbox(slide, Inches(5.2), Inches(3.65), Inches(2.8), Inches(0.45),
            "y_train shape: (7685,)", font_size=14, color=ACCENT_BLUE,
            bold=True, font_name="Courier New")

# Sample row
add_textbox(slide, Inches(1.3), Inches(4.4), Inches(11), Inches(0.35),
            "Sample Row", font_size=16, color=WHITE, bold=True)

add_code_block(slide, Inches(1.3), Inches(4.8), Inches(11.0), Inches(0.8),
               ["X[0] = [0.82, 0.75, 0.03, 0.91, ..., 0.29]   # 150 features",
                "y[0] = 0                                       # git_operations"],
               font_size=12)

# Notes
add_textbox(slide, Inches(1.3), Inches(5.9), Inches(5.5), Inches(0.3),
            "Each row is one task, each column is one feature",
            font_size=13, color=LIGHT_GRAY)
add_textbox(slide, Inches(7.0), Inches(5.9), Inches(6), Inches(0.3),
            "This matrix is what every model trains on",
            font_size=13, color=NUS_ORANGE, bold=True)

# Right-side: Extractor detail
add_rounded_rect(slide, Inches(9.5), Inches(1.1), Inches(3.5), Inches(2.3),
                 CARD_BG)
add_textbox(slide, Inches(9.7), Inches(1.2), Inches(3.1), Inches(0.35),
            "4 Extractors → 150 Dimensions", font_size=14,
            color=NUS_ORANGE, bold=True)
add_multiline_textbox(slide, Inches(9.7), Inches(1.6), Inches(3.1), Inches(1.6),
                      ["Visual extractor:    ~40 dims",
                       "OCR extractor:       ~40 dims",
                       "Interaction extractor: ~40 dims",
                       "Action log extractor: ~30 dims",
                       "---",
                       "Total:               150 dims"],
                      font_size=11, color=NUS_ORANGE, font_name="Courier New",
                      spacing=Pt(5))


# ============================================================
# SLIDE 5: Phase 3a -- SVM
# ============================================================
slide = add_content_slide(prs, "Phase 3a — SVM: Finding the Optimal Boundary",
                          "Support Vector Machine with RBF kernel")

# 2D visualization area
add_rounded_rect(slide, Inches(1.3), Inches(1.3), Inches(5.0), Inches(4.8),
                 DARK_CARD)
add_textbox(slide, Inches(1.5), Inches(1.35), Inches(4.6), Inches(0.35),
            "2D Visualization (simplified from 150D)", font_size=13,
            color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

# Class A — blue dots (left cluster)
class_a_positions = [
    (1.7, 2.2), (2.0, 2.8), (1.8, 3.4), (2.2, 2.5), (1.6, 3.0),
    (2.1, 3.7), (1.9, 3.9), (2.4, 3.1), (2.3, 4.1), (1.7, 4.3),
]
for cx, cy in class_a_positions:
    add_rounded_rect(slide, Inches(cx), Inches(cy), Inches(0.2),
                     Inches(0.2), ACCENT_BLUE)

# Class B — orange dots (right cluster)
class_b_positions = [
    (4.0, 2.1), (4.3, 2.7), (4.1, 3.3), (4.5, 2.4), (3.9, 3.0),
    (4.4, 3.6), (4.2, 3.9), (4.7, 3.2), (4.6, 4.1), (4.3, 4.4),
]
for cx, cy in class_b_positions:
    add_rounded_rect(slide, Inches(cx), Inches(cy), Inches(0.2),
                     Inches(0.2), NUS_ORANGE)

# Vertical decision boundary (between the two clusters)
add_rect(slide, Inches(3.25), Inches(1.8), Inches(0.04), Inches(4.0),
         ACCENT_RED)

# Vertical margin lines (dashed effect — parallel to boundary)
add_rect(slide, Inches(2.75), Inches(1.8), Inches(0.02), Inches(4.0),
         LIGHT_GRAY)
add_rect(slide, Inches(3.75), Inches(1.8), Inches(0.02), Inches(4.0),
         LIGHT_GRAY)

# Margin annotation
add_textbox(slide, Inches(2.6), Inches(5.0), Inches(1.4), Inches(0.3),
            "← margin →", font_size=10, color=LIGHT_GRAY,
            alignment=PP_ALIGN.CENTER)

# Labels
add_textbox(slide, Inches(1.5), Inches(5.35), Inches(1.3), Inches(0.3),
            "■ git_ops", font_size=11, color=ACCENT_BLUE, bold=True)
add_textbox(slide, Inches(2.9), Inches(5.35), Inches(1.3), Inches(0.3),
            "■ coding", font_size=11, color=NUS_ORANGE, bold=True)
add_textbox(slide, Inches(4.3), Inches(5.35), Inches(1.8), Inches(0.3),
            "— Boundary", font_size=11, color=ACCENT_RED)

# Key concepts (right side)
add_textbox(slide, Inches(6.8), Inches(1.3), Inches(6), Inches(0.4),
            "Key Concepts", font_size=18, color=WHITE, bold=True)

concepts = [
    ("Maximize Margin",
     "Finds the hyperplane that maximizes the gap between classes"),
    ("RBF Kernel",
     "K(x,x') = exp(-γ||x-x'||²) — maps to higher dimensions "
     "for non-linear boundaries"),
    ("Support Vectors",
     "The boundary points closest to the hyperplane that define the decision"),
    ("Multi-class",
     "150-dim space → find separating hyperplanes for all 9 classes "
     "(one-vs-one)"),
]

y = Inches(1.7)
for title, desc in concepts:
    add_rounded_rect(slide, Inches(6.8), y, Inches(6.0), Inches(0.9),
                     LIGHT_BLUE_BG)
    add_textbox(slide, Inches(7.0), y + Inches(0.05), Inches(5.6),
                Inches(0.3), title, font_size=13, color=ACCENT_BLUE,
                bold=True)
    add_textbox(slide, Inches(7.0), y + Inches(0.35), Inches(5.6),
                Inches(0.5), desc, font_size=11, color=NUS_ORANGE)
    y += Inches(1.0)

# Training time
add_rounded_rect(slide, Inches(6.8), Inches(5.7), Inches(3.0), Inches(0.5),
                 ACCENT_BLUE, "Training time: 52.6 seconds", font_size=13,
                 font_color=WHITE, bold=True)


# ============================================================
# SLIDE 6: Phase 3b -- Decision Tree & Random Forest
# ============================================================
slide = add_content_slide(prs, "Phase 3b — Decision Tree & Random Forest",
                          "Greedy splitting and ensemble aggregation")

# LEFT: Decision Tree
add_rounded_rect(slide, Inches(1.3), Inches(1.2), Inches(5.5), Inches(5.2),
                 LIGHT_BLUE_BG)
add_textbox(slide, Inches(1.5), Inches(1.3), Inches(5.1), Inches(0.4),
            "Decision Tree", font_size=20, color=ACCENT_BLUE, bold=True)

add_multiline_textbox(slide, Inches(1.5), Inches(1.8), Inches(5.1), Inches(1.0),
                      ["Greedy recursive splitting",
                       "At each node: pick feature + threshold that maximizes",
                       "Information Gain"],
                      font_size=12, color=NUS_ORANGE, spacing=Pt(5))

# Formula
add_code_block(slide, Inches(1.5), Inches(2.6), Inches(5.1), Inches(0.5),
               ["IG = Entropy(parent) - Σ(weighted × Entropy(children))"],
               font_size=11)

# Tree visualization
add_rounded_rect(slide, Inches(2.5), Inches(3.3), Inches(2.8), Inches(0.45),
                 ACCENT_BLUE, "OCR[3] > 0.5 ?", font_size=12,
                 font_color=WHITE, bold=True)

add_rounded_rect(slide, Inches(1.5), Inches(4.2), Inches(2.2), Inches(0.4),
                 ACCENT_GREEN, "Mostly: git_ops", font_size=11,
                 font_color=WHITE, bold=True)

add_rounded_rect(slide, Inches(4.1), Inches(4.2), Inches(2.5), Inches(0.4),
                 NUS_ORANGE, "Mostly: coding_editing", font_size=11,
                 font_color=WHITE, bold=True)

# Connectors
add_textbox(slide, Inches(2.9), Inches(3.75), Inches(0.5), Inches(0.4),
            "↙", font_size=16, color=ACCENT_BLUE, bold=True)
add_textbox(slide, Inches(4.3), Inches(3.75), Inches(0.5), Inches(0.4),
            "↘", font_size=16, color=ACCENT_BLUE, bold=True)

# Yes/No labels
add_textbox(slide, Inches(2.0), Inches(3.8), Inches(0.6), Inches(0.3),
            "Yes", font_size=10, color=ACCENT_GREEN, bold=True)
add_textbox(slide, Inches(5.0), Inches(3.8), Inches(0.6), Inches(0.3),
            "No", font_size=10, color=NUS_ORANGE, bold=True)

# Training time
add_rounded_rect(slide, Inches(1.5), Inches(5.0), Inches(3.0), Inches(0.45),
                 ACCENT_BLUE, "Training: 0.2 seconds", font_size=12,
                 font_color=WHITE, bold=True)

# Strengths/weaknesses
add_multiline_textbox(slide, Inches(1.5), Inches(5.6), Inches(5.1), Inches(0.8),
                      ["+ Interpretable: you can read the rules",
                       "+ Fastest inference (2ms)",
                       "- Prone to overfitting on training data"],
                      font_size=11, color=NUS_ORANGE, spacing=Pt(4))

# RIGHT: Random Forest
add_rounded_rect(slide, Inches(7.1), Inches(1.2), Inches(5.5), Inches(5.2),
                 LIGHT_GREEN_BG)
add_textbox(slide, Inches(7.3), Inches(1.3), Inches(5.1), Inches(0.4),
            "Random Forest", font_size=20, color=ACCENT_GREEN, bold=True)

add_multiline_textbox(slide, Inches(7.3), Inches(1.8), Inches(5.1), Inches(1.2),
                      ["100 trees, each trained on random bootstrap sample",
                       "Each split considers only √150 ≈ 12 random features",
                       "Prediction = majority vote of 100 trees",
                       "Diversity + aggregation = robustness"],
                      font_size=12, color=NUS_ORANGE, spacing=Pt(6))

# Forest visualization: multiple small trees
tree_x = Inches(7.5)
for i in range(5):
    clr = ACCENT_GREEN if i % 2 == 0 else ACCENT_BLUE
    add_rounded_rect(slide, tree_x, Inches(3.1), Inches(0.8), Inches(0.35),
                     clr, f"Tree {i+1}", font_size=9, font_color=WHITE,
                     bold=True)
    add_rounded_rect(slide, tree_x - Inches(0.1), Inches(3.6), Inches(0.45),
                     Inches(0.25), CARD_BG, "L", font_size=8,
                     font_color=LIGHT_GRAY)
    add_rounded_rect(slide, tree_x + Inches(0.45), Inches(3.6), Inches(0.45),
                     Inches(0.25), CARD_BG, "R", font_size=8,
                     font_color=LIGHT_GRAY)
    tree_x += Inches(1.05)

add_textbox(slide, Inches(12.4), Inches(3.2), Inches(0.6), Inches(0.3),
            "...", font_size=18, color=LIGHT_GRAY, bold=True)

# Vote arrow
add_textbox(slide, Inches(9.5), Inches(4.0), Inches(2.0), Inches(0.35),
            "↓  Majority Vote  ↓", font_size=13,
            color=ACCENT_GREEN, bold=True, alignment=PP_ALIGN.CENTER)

add_rounded_rect(slide, Inches(8.8), Inches(4.4), Inches(3.5), Inches(0.45),
                 ACCENT_GREEN, "Final Prediction: coding_editing",
                 font_size=12, font_color=WHITE, bold=True)

# Training time
add_rounded_rect(slide, Inches(7.3), Inches(5.0), Inches(3.0), Inches(0.45),
                 ACCENT_GREEN, "Training: 0.8 seconds", font_size=12,
                 font_color=WHITE, bold=True)

# Key advantage
add_multiline_textbox(slide, Inches(7.3), Inches(5.6), Inches(5.1), Inches(0.8),
                      ["+ Reduces overfitting via bagging (bootstrap aggregation)",
                       "+ Handles high-dimensional data well",
                       "- Less interpretable than a single tree"],
                      font_size=11, color=NUS_ORANGE, spacing=Pt(4))


# ============================================================
# SLIDE 7: Phase 3c -- XGBoost
# ============================================================
slide = add_content_slide(prs, "Phase 3c — XGBoost: Sequential Error Correction",
                          "Gradient Boosted Decision Trees")

# Boosting process visualization
add_textbox(slide, Inches(1.3), Inches(1.3), Inches(11), Inches(0.4),
            "Boosting Process: Each tree corrects the previous tree's mistakes",
            font_size=15, color=WHITE, bold=True)

rounds = [
    ("Round 1", "Tree₁ predicts", "60% correct", ACCENT_BLUE),
    ("Round 2", "Tree₂ on RESIDUALS of Tree₁",
     "fixes 20% more", ACCENT_GREEN),
    ("Round 3", "Tree₃ on remaining errors",
     "fixes 10% more", NUS_ORANGE),
    ("...", "100 rounds total", "", LIGHT_GRAY),
    ("Final", "F(x) = Tree₁ + 0.1×Tree₂ + 0.1×Tree₃ + ...",
     "93% correct", ACCENT_PURPLE),
]

y = Inches(1.8)
for i, (rnd, desc, result, clr) in enumerate(rounds):
    add_rounded_rect(slide, Inches(1.3), y, Inches(1.2), Inches(0.4),
                     clr, rnd, font_size=12, font_color=WHITE, bold=True)
    add_textbox(slide, Inches(2.7), y + Inches(0.03), Inches(6.5),
                Inches(0.35), desc, font_size=13, color=NUS_ORANGE)
    if result:
        add_rounded_rect(slide, Inches(9.5), y, Inches(2.2), Inches(0.4),
                         clr if i != 4 else ACCENT_PURPLE,
                         result, font_size=11, font_color=WHITE, bold=True)
    if i < len(rounds) - 1:
        add_textbox(slide, Inches(1.7), y + Inches(0.35), Inches(0.5),
                    Inches(0.3), "↓", font_size=14, color=clr,
                    bold=True, alignment=PP_ALIGN.CENTER)
    y += Inches(0.65)

# Key formula
add_textbox(slide, Inches(1.3), Inches(5.1), Inches(11), Inches(0.35),
            "Key Formula", font_size=16, color=WHITE, bold=True)

add_code_block(slide, Inches(1.3), Inches(5.5), Inches(6.5), Inches(0.5),
               ["F_m(x) = F_{m-1}(x) + η × h_m(x)"],
               font_size=14)

# Parameters
add_rounded_rect(slide, Inches(8.3), Inches(5.1), Inches(4.5), Inches(1.5),
                 CARD_BG)
add_textbox(slide, Inches(8.5), Inches(5.2), Inches(4.1), Inches(0.35),
            "Key Parameters", font_size=14, color=NUS_ORANGE, bold=True)
add_multiline_textbox(slide, Inches(8.5), Inches(5.6), Inches(4.1), Inches(0.9),
                      ["η = 0.1 (learning rate) — small steps prevent overfitting",
                       "Regularization Ω(h) penalizes complex trees",
                       "100 boosting rounds total"],
                      font_size=11, color=NUS_ORANGE, spacing=Pt(5))

# Training time
add_rounded_rect(slide, Inches(1.3), Inches(6.3), Inches(3.0), Inches(0.45),
                 NUS_ORANGE, "Training: 3.7 seconds", font_size=13,
                 font_color=WHITE, bold=True)


# ============================================================
# SLIDE 8: Phase 3d -- MLP
# ============================================================
slide = add_content_slide(prs, "Phase 3d — MLP: Forward Pass + Backpropagation",
                          "Multi-Layer Perceptron (feed-forward neural network)")

# Architecture diagram: 150 -> 256 -> 128 -> 9
layers = [
    ("Input\n150", Inches(1.3), ACCENT_BLUE),
    ("Hidden 1\n256 neurons", Inches(4.0), ACCENT_GREEN),
    ("Hidden 2\n128 neurons", Inches(6.7), NUS_ORANGE),
    ("Output\n9 classes", Inches(9.4), ACCENT_PURPLE),
]

for label, x, clr in layers:
    add_rounded_rect(slide, x, Inches(1.3), Inches(2.0), Inches(0.8),
                     clr, label, font_size=12, font_color=WHITE, bold=True)

# Arrows between layers
for i in range(3):
    ax = layers[i][1] + Inches(2.05)
    add_arrow_right(slide, ax, Inches(1.45), color=WHITE, size=20)

# Forward pass equations
add_textbox(slide, Inches(1.3), Inches(2.4), Inches(11), Inches(0.35),
            "Forward Pass", font_size=16, color=ACCENT_GREEN, bold=True)

add_code_block(slide, Inches(1.3), Inches(2.8), Inches(5.5), Inches(1.1),
               ["h₁ = ReLU(W₁·x + b₁)    # 256 neurons",
                "h₂ = ReLU(W₂·h₁ + b₂)   # 128 neurons",
                "ŷ  = Softmax(W₃·h₂ + b₃) # 9 class probs"],
               font_size=12)

# Loss
add_textbox(slide, Inches(7.3), Inches(2.4), Inches(6), Inches(0.35),
            "Loss Function", font_size=16, color=ACCENT_RED, bold=True)

add_code_block(slide, Inches(7.3), Inches(2.8), Inches(5.5), Inches(0.5),
               ["CrossEntropy = -log(predicted prob of true class)"],
               font_size=12)

# Backward pass
add_textbox(slide, Inches(7.3), Inches(3.5), Inches(6), Inches(0.35),
            "Backward Pass (Backpropagation)", font_size=16,
            color=NUS_ORANGE, bold=True)

add_code_block(slide, Inches(7.3), Inches(3.9), Inches(5.5), Inches(0.75),
               ["1. Compute gradient ∂Loss/∂W for each layer",
                "2. Update: W = W - learning_rate × gradient"],
               font_size=12)

# Stats
add_rounded_rect(slide, Inches(1.3), Inches(4.3), Inches(5.5), Inches(1.8),
                 CARD_BG)
add_textbox(slide, Inches(1.5), Inches(4.4), Inches(5.1), Inches(0.35),
            "Network Statistics", font_size=15, color=NUS_ORANGE, bold=True)

stats = [
    ("Total parameters:", "72,448"),
    ("  Layer 1 (150→256):", "150×256 + 256 = 38,656"),
    ("  Layer 2 (256→128):", "256×128 + 128 = 32,896"),
    ("  Layer 3 (128→9):", "128×9 + 9 = 1,161"),
]

y = Inches(4.8)
for label, value in stats:
    add_textbox(slide, Inches(1.5), y, Inches(2.5), Inches(0.25),
                label, font_size=11, color=NUS_ORANGE,
                font_name="Courier New")
    add_textbox(slide, Inches(4.0), y, Inches(2.5), Inches(0.25),
                value, font_size=11, color=ACCENT_BLUE,
                font_name="Courier New", bold=True)
    y += Inches(0.25)

# Training info
add_rounded_rect(slide, Inches(7.3), Inches(5.0), Inches(5.5), Inches(1.1),
                 LIGHT_ORANGE_BG)
add_textbox(slide, Inches(7.5), Inches(5.1), Inches(5.1), Inches(0.35),
            "Training Process", font_size=15, color=NUS_ORANGE, bold=True)
add_multiline_textbox(slide, Inches(7.5), Inches(5.5), Inches(5.1), Inches(0.5),
                      ["7,685 samples × 50 epochs = 384,250 weight updates",
                       "Training time: 14 seconds"],
                      font_size=12, color=NUS_ORANGE, spacing=Pt(5))


# ============================================================
# SLIDE 9: Phase 3e -- LSTM
# ============================================================
slide = add_content_slide(prs, "Phase 3e — LSTM: Learning Sequences with Memory",
                          "Long Short-Term Memory recurrent neural network")

# Input reshape
add_textbox(slide, Inches(1.3), Inches(1.3), Inches(11), Inches(0.35),
            "Input Reshape", font_size=16, color=WHITE, bold=True)

add_rounded_rect(slide, Inches(1.3), Inches(1.7), Inches(2.5), Inches(0.5),
                 ACCENT_BLUE, "(150,) flat", font_size=13,
                 font_color=WHITE, bold=True)
add_arrow_right(slide, Inches(3.9), Inches(1.75), color=ACCENT_BLUE, size=20)
add_rounded_rect(slide, Inches(4.4), Inches(1.7), Inches(3.5), Inches(0.5),
                 ACCENT_GREEN, "(10 timesteps, 15 features)",
                 font_size=13, font_color=WHITE, bold=True)

# LSTM Cell - 4 Gates
add_textbox(slide, Inches(1.3), Inches(2.5), Inches(11), Inches(0.35),
            "LSTM Cell: 4 Gates Control Information Flow",
            font_size=16, color=WHITE, bold=True)

gates = [
    ("Forget Gate", "f_t = σ(W_f · [h_{t-1}, x_t])",
     "What to forget from memory", ACCENT_RED, LIGHT_RED_BG),
    ("Input Gate", "i_t = σ(W_i · [h_{t-1}, x_t])",
     "What new info to store", ACCENT_GREEN, LIGHT_GREEN_BG),
    ("Cell Update", "C̃_t = tanh(W_c · [h_{t-1}, x_t])",
     "New candidate information", ACCENT_BLUE, LIGHT_BLUE_BG),
    ("Output Gate", "o_t = σ(W_o · [h_{t-1}, x_t])",
     "What to output", ACCENT_PURPLE, LIGHT_PURPLE_BG),
]

x = Inches(1.3)
for name, formula, desc, accent, bg in gates:
    add_rounded_rect(slide, x, Inches(3.0), Inches(2.8), Inches(1.5), bg)
    add_rounded_rect(slide, x + Inches(0.2), Inches(3.1), Inches(2.4),
                     Inches(0.35), accent, name, font_size=12,
                     font_color=WHITE, bold=True)
    add_textbox(slide, x + Inches(0.1), Inches(3.6), Inches(2.6),
                Inches(0.35), formula, font_size=10, color=NUS_ORANGE,
                font_name="Courier New")
    add_textbox(slide, x + Inches(0.1), Inches(4.0), Inches(2.6),
                Inches(0.35), desc, font_size=10, color=LIGHT_GRAY)
    x += Inches(3.0)

# Cell state equation
add_textbox(slide, Inches(1.3), Inches(4.8), Inches(11), Inches(0.35),
            "Cell State Update", font_size=15, color=WHITE, bold=True)

add_code_block(slide, Inches(1.3), Inches(5.2), Inches(8.0), Inches(0.5),
               ["C_t = f_t ⊙ C_{t-1} + i_t ⊙ C̃_t    "
                "# forget old + add new"],
               font_size=12)

# Output flow
add_textbox(slide, Inches(1.3), Inches(5.9), Inches(11), Inches(0.4),
            "After 10 steps: final hidden state → Linear(64, 9) "
            "→ prediction", font_size=13, color=NUS_ORANGE)

add_textbox(slide, Inches(1.3), Inches(6.3), Inches(8), Inches(0.3),
            "Backpropagation Through Time (BPTT) — gradients flow back "
            "through all 10 timesteps", font_size=12, color=LIGHT_GRAY)

# Training time
add_rounded_rect(slide, Inches(9.8), Inches(6.0), Inches(3.0), Inches(0.5),
                 ACCENT_GREEN, "Training: 16 seconds", font_size=13,
                 font_color=WHITE, bold=True)


# ============================================================
# SLIDE 10: Phase 3f -- Transformer
# ============================================================
slide = add_content_slide(prs, "Phase 3f — Transformer: Self-Attention",
                          "Learning which feature pairs matter for each class")

# Attention mechanism
add_textbox(slide, Inches(1.3), Inches(1.3), Inches(11), Inches(0.35),
            "Self-Attention Mechanism", font_size=18, color=WHITE,
            bold=True)

# Q, K, V explanations
qkv = [
    ("Query", "Q_i = W_Q · x_i", "What am I looking for?",
     ACCENT_BLUE, LIGHT_BLUE_BG),
    ("Key", "K_j = W_K · x_j", "What do I contain?",
     ACCENT_GREEN, LIGHT_GREEN_BG),
    ("Value", "V_j = W_V · x_j", "What do I offer?",
     NUS_ORANGE, LIGHT_ORANGE_BG),
]

x = Inches(1.3)
for name, formula, question, accent, bg in qkv:
    add_rounded_rect(slide, x, Inches(1.8), Inches(3.6), Inches(1.2), bg)
    add_rounded_rect(slide, x + Inches(0.8), Inches(1.9), Inches(2.0),
                     Inches(0.35), accent, name, font_size=13,
                     font_color=WHITE, bold=True)
    add_textbox(slide, x + Inches(0.15), Inches(2.35), Inches(3.3),
                Inches(0.3), formula, font_size=12, color=NUS_ORANGE,
                bold=True, font_name="Courier New")
    add_textbox(slide, x + Inches(0.15), Inches(2.65), Inches(3.3),
                Inches(0.3), f'"{question}"', font_size=11,
                color=LIGHT_GRAY)
    x += Inches(3.85)

# Attention formula
add_textbox(slide, Inches(1.3), Inches(3.3), Inches(11), Inches(0.35),
            "Attention Computation", font_size=16, color=WHITE, bold=True)

add_code_block(slide, Inches(1.3), Inches(3.7), Inches(7.0), Inches(0.8),
               ["Attention weights: α = softmax(Q·Kᵀ / √d_k)",
                "Output:           z = α · V   # weighted combination"],
               font_size=13)

# Example
add_rounded_rect(slide, Inches(1.3), Inches(4.8), Inches(11.5), Inches(1.2),
                 CARD_BG)
add_textbox(slide, Inches(1.5), Inches(4.9), Inches(11), Inches(0.35),
            "Example: How Attention Helps Classification",
            font_size=15, color=NUS_ORANGE, bold=True)

add_textbox(slide, Inches(1.5), Inches(5.3), Inches(11), Inches(0.3),
            'OCR feature "git" attends to Interaction feature '
            '"typing commands" → strong signal for git_operations',
            font_size=13, color=ACCENT_BLUE)

add_textbox(slide, Inches(1.5), Inches(5.7), Inches(11), Inches(0.3),
            "Learns WHICH feature pairs matter for each class — "
            "no manual feature engineering needed",
            font_size=13, color=NUS_ORANGE)

# Training time
add_rounded_rect(slide, Inches(8.8), Inches(3.7), Inches(3.8), Inches(0.5),
                 ACCENT_PURPLE, "Training: 60 seconds", font_size=13,
                 font_color=WHITE, bold=True)

# Architecture note
add_rounded_rect(slide, Inches(8.8), Inches(4.3), Inches(3.8), Inches(0.3),
                 LIGHT_PURPLE_BG)
add_textbox(slide, Inches(8.9), Inches(4.3), Inches(3.6), Inches(0.3),
            "2 attention heads, 2 encoder layers",
            font_size=11, color=ACCENT_PURPLE, bold=True,
            alignment=PP_ALIGN.CENTER)


# ============================================================
# SLIDE 11: Phase 3g -- Stacking Ensemble
# ============================================================
slide = add_content_slide(prs, "Phase 3g — Stacking: Learning Which Model to Trust",
                          "Two-phase meta-learning ensemble")

# Phase A
add_textbox(slide, Inches(1.3), Inches(1.3), Inches(11), Inches(0.35),
            "Phase A: Train Base Models on X_train",
            font_size=16, color=ACCENT_BLUE, bold=True)

base_models = [("SVM", ACCENT_BLUE), ("Random Forest", ACCENT_GREEN),
               ("MLP", NUS_ORANGE)]
x = Inches(1.3)
for name, clr in base_models:
    add_rounded_rect(slide, x, Inches(1.7), Inches(2.5), Inches(0.5),
                     clr, name, font_size=14, font_color=WHITE, bold=True)
    x += Inches(2.8)

# Phase B
add_textbox(slide, Inches(1.3), Inches(2.5), Inches(11), Inches(0.35),
            "Phase B: Each base model predicts on X_train "
            "→ probability outputs",
            font_size=16, color=ACCENT_GREEN, bold=True)

prob_models = [
    ("SVM → (7685, 9)", ACCENT_BLUE),
    ("RF → (7685, 9)", ACCENT_GREEN),
    ("MLP → (7685, 9)", NUS_ORANGE),
]
x = Inches(1.3)
for label, clr in prob_models:
    add_rounded_rect(slide, x, Inches(2.9), Inches(2.5), Inches(0.45),
                     clr, label, font_size=11, font_color=WHITE, bold=True)
    x += Inches(2.8)

# Stack arrow
add_textbox(slide, Inches(9.5), Inches(2.9), Inches(1.5), Inches(0.4),
            "→ Stack", font_size=14, color=WHITE, bold=True)

add_rounded_rect(slide, Inches(10.7), Inches(2.8), Inches(2.2), Inches(0.55),
                 ACCENT_PURPLE, "meta_X\n(7685, 27)", font_size=12,
                 font_color=WHITE, bold=True)

# Phase C
add_textbox(slide, Inches(1.3), Inches(3.7), Inches(11), Inches(0.35),
            "Phase C: Train LogisticRegression on meta_X",
            font_size=16, color=ACCENT_PURPLE, bold=True)

# Meta-learner visualization
add_rounded_rect(slide, Inches(1.3), Inches(4.2), Inches(11.5), Inches(1.6),
                 LIGHT_PURPLE_BG)

add_textbox(slide, Inches(1.5), Inches(4.3), Inches(11), Inches(0.35),
            "Meta-learner discovers which model to trust for each class:",
            font_size=14, color=NUS_ORANGE, bold=True)

trust_data = [
    ("git_operations:", "trust RF (0.6) > MLP (0.3) > SVM (0.1)"),
    ("coding_editing:", "trust SVM (0.5) > RF (0.3) > MLP (0.2)"),
    ("documentation:", "trust MLP (0.5) > SVM (0.3) > RF (0.2)"),
]

y = Inches(4.7)
for cls, weights in trust_data:
    add_textbox(slide, Inches(2.0), y, Inches(2.0), Inches(0.3),
                cls, font_size=12, color=ACCENT_PURPLE, bold=True,
                font_name="Courier New")
    add_textbox(slide, Inches(4.0), y, Inches(5.5), Inches(0.3),
                weights, font_size=12, color=NUS_ORANGE,
                font_name="Courier New")
    y += Inches(0.3)

# Training time
add_rounded_rect(slide, Inches(9.5), Inches(6.1), Inches(3.5), Inches(0.5),
                 ACCENT_PURPLE, "Training: 90 seconds", font_size=13,
                 font_color=WHITE, bold=True)

# Key insight
add_textbox(slide, Inches(1.3), Inches(6.2), Inches(8), Inches(0.3),
            "Stacking learns to combine strengths of different model families",
            font_size=13, color=LIGHT_GRAY)


# ============================================================
# SLIDE 12: Phase 4 -- Evaluation
# ============================================================
slide = add_content_slide(prs, "Phase 4 — How Models Are Evaluated",
                          "Testing on held-out data with standardized metrics")

# Prediction flow
add_rounded_rect(slide, Inches(1.3), Inches(1.3), Inches(2.5), Inches(0.55),
                 ACCENT_BLUE, "X_test (1924, 150)", font_size=13,
                 font_color=WHITE, bold=True)
add_arrow_right(slide, Inches(3.9), Inches(1.35), color=ACCENT_BLUE, size=20)
add_rounded_rect(slide, Inches(4.4), Inches(1.3), Inches(2.5), Inches(0.55),
                 ACCENT_GREEN, "model.predict()", font_size=13,
                 font_color=WHITE, bold=True)
add_arrow_right(slide, Inches(7.0), Inches(1.35), color=ACCENT_GREEN, size=20)
add_rounded_rect(slide, Inches(7.5), Inches(1.3), Inches(2.5), Inches(0.55),
                 NUS_ORANGE, "y_pred (1924,)", font_size=13,
                 font_color=WHITE, bold=True)
add_arrow_right(slide, Inches(10.1), Inches(1.35), color=NUS_ORANGE, size=20)
add_rounded_rect(slide, Inches(10.6), Inches(1.3), Inches(2.0), Inches(0.55),
                 ACCENT_PURPLE, "Metrics", font_size=13,
                 font_color=WHITE, bold=True)

# Metrics explained
add_textbox(slide, Inches(1.3), Inches(2.2), Inches(11), Inches(0.35),
            "Metrics Explained", font_size=18, color=WHITE, bold=True)

metrics = [
    ("Accuracy", "correct / total",
     "Simple but misleading with imbalanced classes", ACCENT_BLUE, LIGHT_BLUE_BG),
    ("F1 per Class", "2 × (Precision × Recall) / (Precision + Recall)",
     "Balances false positives and false negatives", ACCENT_GREEN, LIGHT_GREEN_BG),
    ("F1 Macro", "Average of all 9 class F1 scores",
     "PRIMARY METRIC — treats all classes equally", NUS_ORANGE,
     LIGHT_ORANGE_BG),
]

y = Inches(2.6)
for name, formula, desc, accent, bg in metrics:
    add_rounded_rect(slide, Inches(1.3), y, Inches(11.5), Inches(0.85), bg)
    add_rounded_rect(slide, Inches(1.4), y + Inches(0.1), Inches(1.8),
                     Inches(0.3), accent, name, font_size=12,
                     font_color=WHITE, bold=True)
    add_textbox(slide, Inches(3.5), y + Inches(0.05), Inches(5.0),
                Inches(0.35), formula, font_size=12, color=NUS_ORANGE,
                bold=True, font_name="Courier New")
    add_textbox(slide, Inches(3.5), y + Inches(0.42), Inches(9.0),
                Inches(0.35), desc, font_size=11, color=LIGHT_GRAY)
    y += Inches(0.95)

# Why F1 Macro callout
add_rounded_rect(slide, Inches(1.3), Inches(5.5), Inches(11.5), Inches(1.2),
                 LIGHT_RED_BG)
add_textbox(slide, Inches(1.5), Inches(5.6), Inches(11), Inches(0.35),
            "Why F1 Macro, not Accuracy?", font_size=16, color=ACCENT_RED,
            bold=True)

add_multiline_textbox(slide, Inches(1.5), Inches(6.0), Inches(11), Inches(0.6),
                      ['A model always predicting "other" gets 57% accuracy '
                       'but F1 Macro ≈ 0.06',
                       "F1 Macro treats all 9 classes equally — "
                       "minority classes matter",
                       "Latency measured with time.perf_counter() around predict()"],
                      font_size=12, color=NUS_ORANGE, spacing=Pt(5))


# ============================================================
# SLIDE 13: Training Results
# ============================================================
slide = add_content_slide(prs, "Training Results — 14 Models Compared",
                          "Sorted by F1 Macro (primary metric)")

results = [
    (1, "stacking", "tier3", "0.566", "0.189", "6951ms"),
    (2, "late_fusion", "tier3", "0.568", "0.186", "2551ms"),
    (3, "knn", "tier1", "0.518", "0.165", "344ms"),
    (4, "decision_tree", "tier1", "0.490", "0.161", "2ms"),
    (5, "random_forest", "tier1", "0.587", "0.160", "103ms"),
    (6, "xgboost", "tier1", "0.593", "0.158", "59ms"),
    (7, "naive_bayes", "tier1", "0.295", "0.152", "9ms"),
    (8, "mlp", "tier2", "0.570", "0.148", "12ms"),
    (9, "svm", "tier1", "0.558", "0.146", "1392ms"),
    (10, "transformer", "tier2", "0.560", "0.142", "18ms"),
    (11, "lstm", "tier2", "0.535", "0.140", "15ms"),
    (12, "lightgbm", "tier1", "0.574", "0.137", "37ms"),
    (13, "cnn", "tier2", "0.530", "0.131", "10ms"),
    (14, "logistic_reg", "tier1", "0.549", "0.128", "4ms"),
]

# Table header
y = Inches(1.2)
add_rect(slide, Inches(1.3), y, Inches(11.5), Inches(0.4), DARK_CARD)
headers = [
    (Inches(1.4), "#", Inches(0.4)),
    (Inches(1.8), "Model", Inches(2.2)),
    (Inches(4.0), "Tier", Inches(0.8)),
    (Inches(5.0), "Accuracy", Inches(1.2)),
    (Inches(6.4), "F1 Macro", Inches(1.2)),
    (Inches(7.8), "Latency", Inches(1.2)),
    (Inches(9.3), "", Inches(3.5)),
]
for hx, text, hw in headers:
    add_textbox(slide, hx, y + Inches(0.03), hw, Inches(0.35),
                text, font_size=11, color=WHITE, bold=True)

y += Inches(0.4)
tier_colors = {"tier1": ACCENT_BLUE, "tier2": ACCENT_GREEN,
               "tier3": ACCENT_PURPLE}

for rank, model, tier, acc, f1, latency in results:
    row_bg = CARD_BG if rank % 2 == 0 else LIGHT_BG
    add_rect(slide, Inches(1.3), y, Inches(11.5), Inches(0.32), row_bg)

    add_textbox(slide, Inches(1.4), y, Inches(0.4), Inches(0.32),
                str(rank), font_size=10, color=LIGHT_GRAY,
                alignment=PP_ALIGN.CENTER)
    add_textbox(slide, Inches(1.8), y, Inches(2.2), Inches(0.32),
                model, font_size=10, color=NUS_ORANGE, bold=True,
                font_name="Courier New")

    tc = tier_colors.get(tier, ACCENT_BLUE)
    add_rounded_rect(slide, Inches(4.0), y + Inches(0.03), Inches(0.7),
                     Inches(0.25), tc, tier, font_size=8,
                     font_color=WHITE, bold=True)

    add_textbox(slide, Inches(5.0), y, Inches(1.2), Inches(0.32),
                acc, font_size=10, color=NUS_ORANGE,
                alignment=PP_ALIGN.RIGHT)
    add_textbox(slide, Inches(6.4), y, Inches(1.2), Inches(0.32),
                f1, font_size=10, color=NUS_ORANGE if rank <= 2
                else NUS_ORANGE, bold=(rank <= 2),
                alignment=PP_ALIGN.RIGHT)
    add_textbox(slide, Inches(7.8), y, Inches(1.2), Inches(0.32),
                latency, font_size=10, color=NUS_ORANGE,
                alignment=PP_ALIGN.RIGHT)

    # Mini F1 bar
    f1_val = float(f1)
    bar_w = f1_val / 0.2 * 3.0
    bar_color = NUS_ORANGE if rank <= 2 else ACCENT_BLUE
    add_rect(slide, Inches(9.3), y + Inches(0.08),
             Inches(bar_w), Inches(0.16), bar_color)

    y += Inches(0.32)

# Key insights
insight_y = Inches(5.9)
insights = [
    ("Ensembles achieve best F1 — combining models reduces errors",
     ACCENT_PURPLE),
    ("XGBoost has best raw accuracy but lower F1 "
     "(biased toward majority class)", NUS_ORANGE),
    ("Decision Tree is fastest (2ms) — good for real-time",
     ACCENT_BLUE),
    ("Deep learning didn't outperform classical ML "
     "with engineered features", ACCENT_GREEN),
]

for text, clr in insights:
    add_rect(slide, Inches(1.3), insight_y, Inches(0.12), Inches(0.2), clr)
    add_textbox(slide, Inches(1.55), insight_y - Inches(0.02), Inches(11.3),
                Inches(0.3), text, font_size=11, color=NUS_ORANGE)
    insight_y += Inches(0.3)


# ============================================================
# SLIDE 14: What Gets Saved
# ============================================================
slide = add_content_slide(prs, "Trained Models → .pkl Files",
                          "What gets saved after training completes")

# Models directory
add_textbox(slide, Inches(1.3), Inches(1.3), Inches(5.5), Inches(0.4),
            "models/ directory", font_size=18, color=WHITE, bold=True)

model_files = [
    ("svm.pkl", "~2.1 MB", "Support vectors + kernel params"),
    ("naive_bayes.pkl", "~15 KB", "Class priors + likelihoods"),
    ("decision_tree.pkl", "~180 KB", "Tree structure + thresholds"),
    ("random_forest.pkl", "~12 MB", "100 tree structures"),
    ("knn.pkl", "~8.5 MB", "Full training data (lazy learner)"),
    ("xgboost.pkl", "~1.2 MB", "100 boosted trees"),
    ("lightgbm.pkl", "~900 KB", "Gradient boosted trees"),
    ("logistic_reg.pkl", "~12 KB", "Weight matrix (150 x 9)"),
    ("mlp.pkl", "~350 KB", "72,448 learned weights"),
    ("lstm.pkl", "~500 KB", "Gate weights + cell states"),
    ("cnn.pkl", "~280 KB", "Conv filters + FC weights"),
    ("transformer.pkl", "~600 KB", "Attention weights + FFN"),
    ("stacking.pkl", "~15 MB", "Base models + meta-learner"),
    ("late_fusion.pkl", "~10 MB", "Base models + fusion weights"),
]

# Table header
y = Inches(1.75)
add_rect(slide, Inches(1.3), y, Inches(5.5), Inches(0.35), DARK_CARD)
add_textbox(slide, Inches(1.4), y, Inches(2.2), Inches(0.35),
            "File", font_size=11, color=WHITE, bold=True)
add_textbox(slide, Inches(3.6), y, Inches(1.0), Inches(0.35),
            "Size", font_size=11, color=WHITE, bold=True,
            alignment=PP_ALIGN.RIGHT)
add_textbox(slide, Inches(4.7), y, Inches(2.0), Inches(0.35),
            "Contents", font_size=11, color=WHITE, bold=True)

y += Inches(0.35)
for i, (fname, size, contents) in enumerate(model_files):
    row_bg = CARD_BG if i % 2 == 0 else LIGHT_BG
    add_rect(slide, Inches(1.3), y, Inches(5.5), Inches(0.28), row_bg)
    add_textbox(slide, Inches(1.4), y, Inches(2.0), Inches(0.28),
                fname, font_size=9, color=ACCENT_BLUE,
                font_name="Courier New")
    add_textbox(slide, Inches(3.6), y, Inches(1.0), Inches(0.28),
                size, font_size=9, color=LIGHT_GRAY,
                alignment=PP_ALIGN.RIGHT)
    add_textbox(slide, Inches(4.7), y, Inches(2.0), Inches(0.28),
                contents, font_size=9, color=NUS_ORANGE)
    y += Inches(0.28)

# Key message
add_rounded_rect(slide, Inches(7.5), Inches(1.3), Inches(5.3), Inches(1.2),
                 LIGHT_BLUE_BG)
add_textbox(slide, Inches(7.7), Inches(1.4), Inches(4.9), Inches(0.35),
            "Each .pkl contains the learned weights/parameters",
            font_size=14, color=ACCENT_BLUE, bold=True)
add_textbox(slide, Inches(7.7), Inches(1.8), Inches(4.9), Inches(0.5),
            "Backend loads these on startup — no retraining needed. "
            "Inference uses the saved model directly.",
            font_size=12, color=NUS_ORANGE)

# Flow diagram
add_textbox(slide, Inches(7.5), Inches(3.0), Inches(5.3), Inches(0.35),
            "End-to-End Flow", font_size=16, color=WHITE, bold=True)

flow_steps = [
    ("train.py", ACCENT_BLUE),
    ("models/*.pkl", ACCENT_GREEN),
    ("ml_service loads", NUS_ORANGE),
    ("Ready for\nInference", ACCENT_PURPLE),
]

x = Inches(7.5)
for i, (label, clr) in enumerate(flow_steps):
    add_rounded_rect(slide, x, Inches(3.5), Inches(1.2), Inches(0.7),
                     clr, label, font_size=10, font_color=WHITE, bold=True)
    if i < 3:
        add_arrow_right(slide, x + Inches(1.2), Inches(3.65), color=clr,
                        size=18)
    x += Inches(1.4)

# What's inside a .pkl
add_rounded_rect(slide, Inches(7.5), Inches(4.5), Inches(5.3), Inches(2.2),
                 CARD_BG)
add_textbox(slide, Inches(7.7), Inches(4.6), Inches(4.9), Inches(0.35),
            "What's Inside a .pkl?", font_size=15, color=NUS_ORANGE, bold=True)

add_multiline_textbox(slide, Inches(7.7), Inches(5.0), Inches(4.9), Inches(1.5),
                      ["Serialized with Python's pickle / joblib",
                       "Contains:",
                       "  - Model architecture & hyperparameters",
                       "  - Trained weights / learned parameters",
                       "  - Feature scaler (if applicable)",
                       "  - Label encoder mapping",
                       "",
                       "Load: model = joblib.load('models/svm.pkl')"],
                      font_size=11, color=NUS_ORANGE, spacing=Pt(3),
                      font_name="Courier New")


# ============================================================
# Save
# ============================================================
import os
output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Video2Knowledge_Training.pptx")
prs.save(output_path)
print(f"Saved: {output_path}")
print(f"Slides: {len(prs.slides)}")
