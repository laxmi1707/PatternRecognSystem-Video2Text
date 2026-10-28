"""
Generates Group_21_Muneeswaran_Contribution.pptx
3 slides covering Muthaiah Muneeswaran's individual contribution:
  Slide 1 — Overview: 4 areas (FastAPI, Decision Tree, Random Forest, Late Fusion)
  Slide 2 — Decision Tree & Random Forest (training details + results)
  Slide 3 — Multimodal Late Fusion (architecture + results)
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

from nus_iss_template import (
    create_presentation, add_title_slide, add_content_slide,
    add_textbox, add_rounded_rect, add_multiline_textbox,
    NUS_BLUE, NUS_ORANGE, WHITE, LIGHT_GRAY, SUBTLE_GRAY,
    ACCENT_BLUE, ACCENT_GREEN, ACCENT_PURPLE, ACCENT_RED,
    set_slide_bg, add_nus_logo, add_nus_footer,
    LIGHT_BLUE_BG, LIGHT_GREEN_BG, LIGHT_PURPLE_BG,
    LIGHT_ORANGE_BG, LIGHT_RED_BG, CARD_BG, LIGHT_BG, DARK_TEXT,
)

DARK_CARD = RGBColor(0x00, 0x2A, 0x55)
GOLD      = RGBColor(0xFF, 0xC1, 0x07)
TEAL      = RGBColor(0x17, 0xA2, 0xB8)


def code_box(slide, left, top, width, height, lines, font_size=10):
    add_rounded_rect(slide, left, top, width, height, DARK_CARD)
    add_multiline_textbox(
        slide, left + Inches(0.15), top + Inches(0.1),
        width - Inches(0.3), height - Inches(0.2),
        lines, font_size=font_size,
        color=ACCENT_GREEN, font_name="Courier New", spacing=Pt(2),
    )


# ═══════════════════════════════════════════════════════════════
# SLIDE 1 — Contribution Overview
# ═══════════════════════════════════════════════════════════════
prs = create_presentation()

slide = add_content_slide(prs,
    "FastAPI, Multi-tier Classifiers & Multimodal Late Fusion",
    "FastAPI backend · Multi-tier classifier architecture · Decision Tree · Random Forest · Late Fusion · CI/CD")

areas = [
    ("FastAPI Backend",
     ["Async REST API (Python 3.11)",
      "Routers: /videos, /jobs, /results,",
      "  /knowledge, /history",
      "SQLAlchemy async ORM + PostgreSQL",
      "Background job queue for ML inference",
      "Startup: S3 model sync → load all .pkl",
      "OpenAPI docs at /docs"],
     ACCENT_BLUE, LIGHT_BLUE_BG),
    ("Multi-Tier Classifier\nArchitecture",
     ["Designed BaseClassifier interface:",
      "  fit / predict / save / load",
      "  timed_predict → latency tracking",
      "ModelRegistry: keyed by name + tier",
      "Orchestrates Tier 1 → Tier 2 → Tier 3",
      "All 13 models implement same interface",
      "MLflow experiment logging wired in"],
     ACCENT_PURPLE, LIGHT_PURPLE_BG),
    ("Decision Tree\n(Tier 1)",
     ["sklearn DecisionTreeClassifier",
      "max_depth = 20",
      "Gini Impurity split criterion",
      "class_weight = 'balanced'",
      "  → handles class imbalance",
      "F1 Macro: 0.762",
      "Inference: 2 ms  (fastest model)"],
     NUS_ORANGE, LIGHT_ORANGE_BG),
    ("Random Forest\n(Tier 1)",
     ["100 trees, bootstrap sampling",
      "max_depth = 20",
      "√1391 ≈ 37 features per split",
      "n_jobs = -1  (all CPU cores)",
      "class_weight = 'balanced'",
      "F1 Macro: 0.841",
      "Training: 0.8 s"],
     ACCENT_GREEN, LIGHT_GREEN_BG),
    ("Multimodal\nLate Fusion (Tier 3)",
     ["Splits 1391-dim vector by modality",
      "Each modality → own classifier branch",
      "Branch outputs stacked → meta_X",
      "Logistic Regression meta-learner",
      "Learns per-modality trust weights",
      "F1 Macro: 0.861  (3rd overall)",
      "Latency: 78 ms"],
     ACCENT_RED, LIGHT_RED_BG),
]

col_w = Inches(1.87)
for i, (title, bullets, clr, bg) in enumerate(areas):
    x = Inches(0.3 + i * 1.93)
    # title bar
    add_rounded_rect(slide, x, Inches(1.93), col_w, Inches(0.45),
                     clr, title, font_size=10, font_color=WHITE, bold=True)
    # body card
    add_rounded_rect(slide, x, Inches(2.38), col_w, Inches(3.0), bg, "")
    for k, b in enumerate(bullets):
        add_textbox(slide, x + Inches(0.1), Inches(2.46 + k * 0.4),
                    col_w - Inches(0.15), Inches(0.36),
                    b, font_size=9.5, color=DARK_CARD)
    # result badge at bottom
    result_line = next((b for b in bullets if b.startswith("F1")), None)
    if result_line:
        add_rounded_rect(slide, x + Inches(0.1), Inches(5.45), col_w - Inches(0.2),
                         Inches(0.25), clr, result_line,
                         font_size=9, font_color=WHITE, bold=True)

add_nus_footer(slide)


# ═══════════════════════════════════════════════════════════════
# SLIDE 2 — Decision Tree & Random Forest (deep dive)
# ═══════════════════════════════════════════════════════════════
slide = add_content_slide(prs,
    "Decision Tree & Random Forest — Training Deep Dive",
    "Tier 1 Classical ML — Greedy splitting (Decision Tree) vs. bootstrap aggregation (Random Forest)")

# ── Decision Tree (left) ──────────────────────────────────────
add_rounded_rect(slide, Inches(0.35), Inches(1.5), Inches(4.7), Inches(0.35),
                 NUS_ORANGE, "Decision Tree  (tier1/decision_tree.py)",
                 font_size=11, font_color=WHITE, bold=True)
add_rounded_rect(slide, Inches(0.35), Inches(1.85), Inches(4.7), Inches(3.8),
                 LIGHT_ORANGE_BG, "")

dt_lines = [
    ("Algorithm", "Greedy recursive binary splitting"),
    ("Split criterion", "Gini Impurity = 1 − Σ pᵢ²"),
    ("max_depth", "20  (limits tree depth → avoids overfitting)"),
    ("class_weight", "'balanced'  → minority classes get higher weight"),
    ("Why balanced?", "VSCode tasks dominate (~38%); without balancing,"),
    ("", "  tree ignores rare classes like git_operations"),
    ("Prediction", "Traverses learned rules from root to leaf"),
    ("", "  e.g. OCR['git'] > 0.5  →  git_operations"),
    ("Training time", "< 0.2 s  (fastest to train)"),
    ("Inference", "2 ms  — fastest of all 13 models"),
]
for k, (key, val) in enumerate(dt_lines):
    if key:
        add_textbox(slide, Inches(0.5), Inches(1.95 + k * 0.34),
                    Inches(1.5), Inches(0.3), key + ":", font_size=10,
                    color=NUS_ORANGE, bold=True)
    add_textbox(slide, Inches(2.0), Inches(1.95 + k * 0.34),
                Inches(2.9), Inches(0.3), val, font_size=10, color=DARK_CARD)

add_rounded_rect(slide, Inches(0.35), Inches(5.7), Inches(4.7), Inches(0.28),
                 NUS_ORANGE,
                 "v3b:  F1 Macro 0.762  |  Accuracy 0.791  |  Inference 2 ms",
                 font_size=10, font_color=WHITE, bold=True)

# ── Random Forest (right) ─────────────────────────────────────
add_rounded_rect(slide, Inches(5.2), Inches(1.5), Inches(4.5), Inches(0.35),
                 ACCENT_GREEN, "Random Forest  (tier1/random_forest.py)",
                 font_size=11, font_color=WHITE, bold=True)
add_rounded_rect(slide, Inches(5.2), Inches(1.85), Inches(4.5), Inches(3.8),
                 LIGHT_GREEN_BG, "")

rf_lines = [
    ("Algorithm", "Bootstrap Aggregation (Bagging)"),
    ("n_estimators", "100 trees, each on a random bootstrap sample"),
    ("max_features", "√1391 ≈ 37 features considered per split"),
    ("", "  → decorrelates trees → reduces variance"),
    ("max_depth", "20  (same as Decision Tree)"),
    ("class_weight", "'balanced'  → same imbalance handling"),
    ("n_jobs", "-1  → trains all 100 trees in parallel"),
    ("", "  using all available CPU cores"),
    ("Prediction", "Majority vote of 100 trees:"),
    ("", "  ŷ = mode { T₁(x), …, T₁₀₀(x) }"),
    ("Training time", "0.8 s  (100 parallel trees)"),
    ("Inference", "103 ms  (100 tree traversals)"),
]
for k, (key, val) in enumerate(rf_lines):
    if key:
        add_textbox(slide, Inches(5.35), Inches(1.95 + k * 0.29),
                    Inches(1.55), Inches(0.27), key + ":", font_size=10,
                    color=ACCENT_GREEN, bold=True)
    add_textbox(slide, Inches(6.9), Inches(1.95 + k * 0.29),
                Inches(2.65), Inches(0.27), val, font_size=10, color=DARK_CARD)

add_rounded_rect(slide, Inches(5.2), Inches(5.7), Inches(4.5), Inches(0.28),
                 ACCENT_GREEN,
                 "v3b:  F1 Macro 0.841  |  Accuracy 0.855  |  Training 0.8 s",
                 font_size=10, font_color=WHITE, bold=True)

add_nus_footer(slide)


# ═══════════════════════════════════════════════════════════════
# SLIDE 3 — Multimodal Late Fusion
# ═══════════════════════════════════════════════════════════════
slide = add_content_slide(prs,
    "Multimodal Late Fusion — Architecture & Training",
    "Tier 3 ensemble | Each modality trains its own classifier; meta-learner fuses branch outputs")

# Architecture flow
add_rounded_rect(slide, Inches(0.35), Inches(1.5), Inches(9.3), Inches(0.35),
                 NUS_BLUE,
                 "1,391-dim feature vector  →  split by modality  →  4 branch classifiers  →  meta-learner  →  activity class",
                 font_size=10, font_color=WHITE, bold=True)

modalities = [
    ("Visual Branch\n(cols 0–511)",
     "EfficientNet-B0 CNN features\n512-dim visual encoding\nCaptures UI layout, colour",
     "Random Forest", ACCENT_BLUE, LIGHT_BLUE_BG),
    ("OCR Branch\n(cols 512–1023)",
     "EasyOCR TF-IDF features\n512-dim text encoding\nIdentifies CLI cmds, IDE text",
     "SVM (RBF)", ACCENT_GREEN, LIGHT_GREEN_BG),
    ("YOLO Branch\n(cols 1024–1279)",
     "YOLO UI detection features\n256-dim widget encoding\nButtons, menus, terminals",
     "Decision Tree", NUS_ORANGE, LIGHT_ORANGE_BG),
    ("Interaction Branch\n(cols 1280–1390)",
     "action_log.json statistics\n111-dim behavioural encoding\nClick rate, typing speed",
     "Naive Bayes", ACCENT_PURPLE, LIGHT_PURPLE_BG),
]
for i, (name, desc, clf, clr, bg) in enumerate(modalities):
    x = Inches(0.35 + i * 2.4)
    add_rounded_rect(slide, x, Inches(2.0), Inches(2.2), Inches(0.38),
                     clr, name, font_size=10, font_color=WHITE, bold=True)
    add_rounded_rect(slide, x, Inches(2.38), Inches(2.2), Inches(1.5), bg, "")
    for k, ln in enumerate(desc.split("\n")):
        add_textbox(slide, x + Inches(0.1), Inches(2.45 + k * 0.37),
                    Inches(2.0), Inches(0.33), ln, font_size=9.5, color=DARK_CARD)
    add_rounded_rect(slide, x + Inches(0.15), Inches(3.92), Inches(1.9), Inches(0.28),
                     clr, clf, font_size=9, font_color=WHITE, bold=True)
    # down arrow
    add_textbox(slide, x + Inches(0.85), Inches(4.25), Inches(0.4), Inches(0.3),
                "↓", font_size=14, color=clr, bold=True,
                alignment=PP_ALIGN.CENTER)
    add_textbox(slide, x + Inches(0.1), Inches(4.55), Inches(2.0), Inches(0.25),
                f"P(c|branch_{i+1}): (n,8)", font_size=9,
                color=SUBTLE_GRAY, font_name="Courier New")

# Meta-learner box
add_rounded_rect(slide, Inches(1.8), Inches(4.9), Inches(6.0), Inches(0.45),
                 DARK_CARD,
                 "meta_X = [P_visual | P_ocr | P_yolo | P_interaction]  →  shape (n, 32)",
                 font_size=10, font_color=ACCENT_GREEN)

add_rounded_rect(slide, Inches(2.5), Inches(5.42), Inches(4.6), Inches(0.38),
                 NUS_BLUE,
                 "Logistic Regression meta-learner  →  learns per-modality trust weights  →  ŷ",
                 font_size=10, font_color=WHITE, bold=True)

# Key insight + results
add_rounded_rect(slide, Inches(0.35), Inches(5.88), Inches(4.3), Inches(0.3),
                 LIGHT_BLUE_BG, "")
add_textbox(slide, Inches(0.5), Inches(5.91), Inches(4.1), Inches(0.25),
    "Key idea: each modality has different strengths per class — OCR is best for git_ops, Visual for media_editing",
    font_size=9, color=DARK_CARD)

add_rounded_rect(slide, Inches(4.8), Inches(5.88), Inches(4.85), Inches(0.3),
                 LIGHT_GREEN_BG, "")
add_textbox(slide, Inches(4.95), Inches(5.91), Inches(4.6), Inches(0.25),
    "v3b:  F1 Macro 0.861  |  Accuracy 0.875  |  Latency 78 ms  |  3rd best overall (Voting 0.884, Stacking 0.869)",
    font_size=9, color=NUS_BLUE, bold=True)

add_nus_footer(slide)


# ═══════════════════════════════════════════════════════════════
# Save
# ═══════════════════════════════════════════════════════════════
OUT = os.path.join(os.path.dirname(__file__), "Group_21_Muneeswaran_Contribution.pptx")
prs.save(OUT)
print(f"Saved: {OUT}  ({len(prs.slides)} slides)")
