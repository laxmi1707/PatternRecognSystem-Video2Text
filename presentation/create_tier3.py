"""Generate Video2Knowledge Tier 3 Ensemble Methods presentation."""
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
TIER3_COLOR = ACCENT_GREEN

prs = create_presentation()

# ============================================================
# SLIDE 1: Title
# ============================================================
add_title_slide(
    prs,
    "Tier 3: Ensemble Methods",
    subtitle="Combining multiple models for better predictions",
)

# ============================================================
# SLIDE 2: Why Ensembles?
# ============================================================
slide = add_content_slide(prs, "Why Ensembles?")

add_textbox(slide, Inches(1.3), Inches(1.3), Inches(11), Inches(0.5),
            "Different models make different mistakes",
            font_size=20, color=NUS_ORANGE, bold=True)

# Model comparison cards showing strengths/weaknesses
models_info = [
    ("SVM", "Good at: git_ops", "Bad at: documentation", ACCENT_BLUE),
    ("Random Forest", "Good at: coding_editing", "Bad at: debugging", ACCENT_GREEN),
    ("MLP", "Good at: documentation", "Bad at: git_ops", ACCENT_PURPLE),
    ("Combined", "Good at: ALL categories", "", TIER3_COLOR),
]

x = Inches(1.3)
for name, good, bad, color in models_info:
    add_rounded_rect(slide, x, Inches(2.1), Inches(2.6), Inches(0.6),
                     color, name, font_size=16, font_color=WHITE, bold=True)
    add_textbox(slide, x + Inches(0.1), Inches(2.85), Inches(2.4), Inches(0.4),
                good, font_size=13, color=ACCENT_GREEN, alignment=PP_ALIGN.CENTER)
    if bad:
        add_textbox(slide, x + Inches(0.1), Inches(3.25), Inches(2.4), Inches(0.4),
                    bad, font_size=13, color=ACCENT_RED,
                    alignment=PP_ALIGN.CENTER)
    if name != "Combined":
        add_textbox(slide, x + Inches(2.6), Inches(2.25), Inches(0.3), Inches(0.4),
                    "+", font_size=24, color=WHITE, alignment=PP_ALIGN.CENTER)
    x += Inches(2.85)

add_textbox(slide, Inches(1.3), Inches(4.0), Inches(11), Inches(0.5),
            "By combining diverse models, errors cancel out",
            font_size=18, color=NUS_ORANGE)

# Key principle box
add_rounded_rect(slide, Inches(1.5), Inches(4.8), Inches(10), Inches(1.2),
                 LIGHT_GREEN_BG,
                 'The wisdom of crowds — multiple imperfect models > one "perfect" model',
                 font_size=20, font_color=TIER3_COLOR, bold=True)


# ============================================================
# SLIDE 3: The 3 Ensemble Strategies
# ============================================================
slide = add_content_slide(prs, "The 3 Ensemble Strategies")

# Three columns side by side
strategies = [
    ("Voting", "Average the predictions", "(simplest)", ACCENT_BLUE,
     "SVM + Random Forest + MLP", None),
    ("Stacking", "Learn WHICH model to trust", "(smartest)", ACCENT_PURPLE,
     "SVM + Random Forest + MLP", "Meta-learner"),
    ("Late Fusion", "Different models see\ndifferent features", "(most specialized)",
     NUS_ORANGE, "SVM (OCR+UI) +\nRandom Forest (Visual+Interaction)", "Meta-learner"),
]

x = Inches(1.3)
for name, desc, tag, color, base, meta in strategies:
    # Strategy header
    add_rounded_rect(slide, x, Inches(1.3), Inches(3.5), Inches(0.7),
                     color, name, font_size=22, font_color=WHITE, bold=True)
    # Description
    add_textbox(slide, x + Inches(0.2), Inches(2.15), Inches(3.1), Inches(0.8),
                desc, font_size=15, color=NUS_ORANGE, alignment=PP_ALIGN.CENTER)
    add_textbox(slide, x + Inches(0.2), Inches(2.8), Inches(3.1), Inches(0.4),
                tag, font_size=13, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

    # Base models section
    add_textbox(slide, x + Inches(0.2), Inches(3.4), Inches(3.1), Inches(0.3),
                "Base Models:", font_size=13, color=WHITE, bold=True)
    add_rounded_rect(slide, x + Inches(0.2), Inches(3.75), Inches(3.1), Inches(1.0),
                     DARK_CARD, base, font_size=12, font_color=LIGHT_GRAY)

    if meta:
        add_textbox(slide, x + Inches(1.2), Inches(4.75), Inches(1), Inches(0.3),
                    "↓", font_size=20, color=color, alignment=PP_ALIGN.CENTER)
        add_rounded_rect(slide, x + Inches(0.3), Inches(5.05), Inches(2.9), Inches(0.5),
                         color, meta, font_size=14, font_color=WHITE, bold=True)

    x += Inches(3.8)


# ============================================================
# SLIDE 4: Voting Classifier (Soft Voting)
# ============================================================
slide = add_content_slide(prs, "Voting Classifier (Soft Voting)")

add_textbox(slide, Inches(1.3), Inches(1.3), Inches(11), Inches(0.5),
            "Averages probability outputs from 3 base models",
            font_size=18, color=LIGHT_GRAY)

# Step-by-step probability outputs
prob_data = [
    ("SVM output:", "[0.72, 0.05, 0.03, ..., 0.08]", "(72% git_ops)", ACCENT_BLUE),
    ("Random Forest output:", "[0.89, 0.03, 0.01, ..., 0.02]", "(89% git_ops)", ACCENT_GREEN),
    ("MLP output:", "[0.45, 0.35, 0.05, ..., 0.05]", "(45% git_ops)", ACCENT_PURPLE),
]

y = Inches(1.9)
for label, probs, pct, color in prob_data:
    add_rounded_rect(slide, Inches(1.3), y, Inches(0.12), Inches(0.4), color)
    add_textbox(slide, Inches(1.6), y, Inches(2.5), Inches(0.4),
                label, font_size=14, color=NUS_ORANGE, bold=True)
    add_textbox(slide, Inches(4.1), y, Inches(5), Inches(0.4),
                probs, font_size=14, color=LIGHT_GRAY, font_name="Consolas")
    add_textbox(slide, Inches(9.3), y, Inches(2), Inches(0.4),
                pct, font_size=14, color=color, bold=True)
    y += Inches(0.5)

# Divider
add_rect(slide, Inches(1.5), Inches(3.45), Inches(10), Inches(0.03), SUBTLE_GRAY)

# Average result
add_rounded_rect(slide, Inches(1.3), Inches(3.6), Inches(0.12), Inches(0.4), TIER3_COLOR)
add_textbox(slide, Inches(1.6), Inches(3.6), Inches(2.5), Inches(0.4),
            "Average:", font_size=14, color=NUS_ORANGE, bold=True)
add_textbox(slide, Inches(4.1), Inches(3.6), Inches(5), Inches(0.4),
            "[0.69, 0.14, 0.03, ..., 0.05]", font_size=14, color=LIGHT_GRAY,
            font_name="Consolas")
add_rounded_rect(slide, Inches(9.3), Inches(3.55), Inches(3.5), Inches(0.5),
                 TIER3_COLOR, '→ "git_operations" (69%)',
                 font_size=14, font_color=WHITE, bold=True)

# Soft vs Hard voting explanation
add_rounded_rect(slide, Inches(1.3), Inches(4.3), Inches(5.5), Inches(0.5),
                 LIGHT_BLUE_BG,
                 "Soft voting = weighted average of probabilities",
                 font_size=14, font_color=ACCENT_BLUE, bold=True)
add_rounded_rect(slide, Inches(7.1), Inches(4.3), Inches(5.5), Inches(0.5),
                 DARK_CARD,
                 "Hard voting = majority vote on labels (not used here)",
                 font_size=14, font_color=LIGHT_GRAY)

# Strengths and Weaknesses
add_rounded_rect(slide, Inches(1.3), Inches(5.1), Inches(5.5), Inches(1.5),
                 LIGHT_GREEN_BG)
add_textbox(slide, Inches(1.5), Inches(5.2), Inches(5), Inches(0.4),
            "Strengths", font_size=16, color=ACCENT_GREEN, bold=True)
add_multiline_textbox(slide, Inches(1.5), Inches(5.6), Inches(5), Inches(0.9),
                      ["•  Simple, no additional training needed",
                       "•  Robust to individual model failures",
                       "•  Fast to implement and deploy"],
                      font_size=13, color=RGBColor(0x2D, 0x2D, 0x2D))

add_rounded_rect(slide, Inches(7.1), Inches(5.1), Inches(5.5), Inches(1.5),
                 LIGHT_ORANGE_BG)
add_textbox(slide, Inches(7.3), Inches(5.2), Inches(5), Inches(0.4),
            "Weaknesses", font_size=16, color=NUS_ORANGE, bold=True)
add_multiline_textbox(slide, Inches(7.3), Inches(5.6), Inches(5), Inches(0.9),
                      ["•  Treats all models equally (even bad ones)",
                       "•  Cannot learn per-class model trust",
                       "•  Limited by weakest model's noise"],
                      font_size=13, color=RGBColor(0x2D, 0x2D, 0x2D))


# ============================================================
# SLIDE 5: Stacking Classifier
# ============================================================
slide = add_content_slide(prs, "Stacking Classifier")

add_textbox(slide, Inches(1.3), Inches(1.3), Inches(11), Inches(0.5),
            "Uses a META-LEARNER that learns which base model to trust for each class",
            font_size=18, color=LIGHT_GRAY)

# Phase 1: Training
add_rounded_rect(slide, Inches(1.3), Inches(1.9), Inches(5.5), Inches(3.3),
                 LIGHT_PURPLE_BG)
add_rounded_rect(slide, Inches(1.5), Inches(2.0), Inches(2.5), Inches(0.5),
                 ACCENT_PURPLE, "Phase 1: Training", font_size=14,
                 font_color=WHITE, bold=True)

phase1_steps = [
    "1. Each base model makes predictions on training data",
    "2. Base model probabilities become NEW features",
    "   for the meta-learner",
    "3. Meta-learner (Logistic Regression) trains on",
    '   these "meta-features"',
]
add_multiline_textbox(slide, Inches(1.6), Inches(2.6), Inches(5.0), Inches(2.2),
                      phase1_steps, font_size=14,
                      color=RGBColor(0x2D, 0x2D, 0x2D), spacing=Pt(6))

# Feature size callout
add_rounded_rect(slide, Inches(1.6), Inches(4.5), Inches(4.8), Inches(0.5),
                 ACCENT_PURPLE,
                 "3 models × 9 classes = 27 meta-features",
                 font_size=13, font_color=WHITE, bold=True)

# Phase 2: Prediction
add_rounded_rect(slide, Inches(7.1), Inches(1.9), Inches(5.5), Inches(3.3),
                 LIGHT_BLUE_BG)
add_rounded_rect(slide, Inches(7.3), Inches(2.0), Inches(2.5), Inches(0.5),
                 ACCENT_BLUE, "Phase 2: Prediction", font_size=14,
                 font_color=WHITE, bold=True)

phase2_steps = [
    "1. New video → 3 base models produce probabilities",
    "2. Probabilities fed to meta-learner",
    "3. Meta-learner → final prediction",
]
add_multiline_textbox(slide, Inches(7.4), Inches(2.6), Inches(5.0), Inches(1.5),
                      phase2_steps, font_size=14,
                      color=RGBColor(0x2D, 0x2D, 0x2D), spacing=Pt(6))

# Trust insight
add_rounded_rect(slide, Inches(7.4), Inches(3.8), Inches(4.8), Inches(0.6),
                 ACCENT_GREEN,
                 "Meta-learner learns: Trust RF for git_ops, trust MLP for documentation",
                 font_size=12, font_color=WHITE, bold=True)

# Arrow between phases
add_textbox(slide, Inches(6.7), Inches(3.0), Inches(0.5), Inches(0.5),
            "→", font_size=28, color=WHITE, alignment=PP_ALIGN.CENTER)

# Strengths and Weaknesses
add_rounded_rect(slide, Inches(1.3), Inches(5.5), Inches(5.5), Inches(1.1),
                 LIGHT_GREEN_BG)
add_textbox(slide, Inches(1.5), Inches(5.55), Inches(5), Inches(0.4),
            "Strengths", font_size=16, color=ACCENT_GREEN, bold=True)
add_multiline_textbox(slide, Inches(1.5), Inches(5.9), Inches(5), Inches(0.6),
                      ["•  Learns optimal model weighting per class",
                       "•  Best F1 in our results (0.189)",
                       "•  Can correct systematic model biases"],
                      font_size=13, color=RGBColor(0x2D, 0x2D, 0x2D))

add_rounded_rect(slide, Inches(7.1), Inches(5.5), Inches(5.5), Inches(1.1),
                 LIGHT_ORANGE_BG)
add_textbox(slide, Inches(7.3), Inches(5.55), Inches(5), Inches(0.4),
            "Weaknesses", font_size=16, color=NUS_ORANGE, bold=True)
add_multiline_textbox(slide, Inches(7.3), Inches(5.9), Inches(5), Inches(0.6),
                      ["•  Slower inference (6951ms)",
                       "•  Risk of overfitting on small meta-feature set",
                       "•  Requires careful cross-validation"],
                      font_size=13, color=RGBColor(0x2D, 0x2D, 0x2D))


# ============================================================
# SLIDE 6: Late Fusion Classifier
# ============================================================
slide = add_content_slide(prs, "Late Fusion Classifier")

add_textbox(slide, Inches(1.3), Inches(1.3), Inches(11), Inches(0.5),
            "Each base model gets a DIFFERENT SUBSET of features (multimodal fusion)",
            font_size=18, color=LIGHT_GRAY)

# Branch 1 - SVM
add_rounded_rect(slide, Inches(1.3), Inches(2.0), Inches(5.2), Inches(2.0),
                 LIGHT_BLUE_BG)
add_rounded_rect(slide, Inches(1.5), Inches(2.1), Inches(3.0), Inches(0.5),
                 ACCENT_BLUE, "Branch 1: SVM", font_size=16,
                 font_color=WHITE, bold=True)
add_textbox(slide, Inches(1.6), Inches(2.7), Inches(4.7), Inches(0.4),
            "Gets features [0–74] = OCR (50) + UI (25)", font_size=14,
            color=RGBColor(0x2D, 0x2D, 0x2D), bold=True)
add_rounded_rect(slide, Inches(1.6), Inches(3.2), Inches(4.7), Inches(0.65),
                 WHITE,
                 '"Reads the screen"\nSpecializes in TEXT understanding',
                 font_size=13, font_color=ACCENT_BLUE)

# Branch 2 - Random Forest
add_rounded_rect(slide, Inches(6.8), Inches(2.0), Inches(5.8), Inches(2.0),
                 LIGHT_ORANGE_BG)
add_rounded_rect(slide, Inches(7.0), Inches(2.1), Inches(3.5), Inches(0.5),
                 NUS_ORANGE, "Branch 2: Random Forest", font_size=16,
                 font_color=WHITE, bold=True)
add_textbox(slide, Inches(7.1), Inches(2.7), Inches(5.3), Inches(0.4),
            "Gets features [75–149] = Visual (40) + Interaction (35)", font_size=14,
            color=RGBColor(0x2D, 0x2D, 0x2D), bold=True)
add_rounded_rect(slide, Inches(7.1), Inches(3.2), Inches(5.3), Inches(0.65),
                 WHITE,
                 '"Watches behavior"\nSpecializes in VISUAL + BEHAVIORAL patterns',
                 font_size=13, font_color=NUS_ORANGE)

# Arrows down to meta-learner
add_textbox(slide, Inches(3.7), Inches(4.05), Inches(0.5), Inches(0.4),
            "↓", font_size=24, color=ACCENT_BLUE, alignment=PP_ALIGN.CENTER)
add_textbox(slide, Inches(9.5), Inches(4.05), Inches(0.5), Inches(0.4),
            "↓", font_size=24, color=NUS_ORANGE, alignment=PP_ALIGN.CENTER)

# Meta-learner
add_rounded_rect(slide, Inches(3.5), Inches(4.5), Inches(6.5), Inches(0.6),
                 TIER3_COLOR, "Meta-learner combines both branches",
                 font_size=16, font_color=WHITE, bold=True)

# Why this is powerful
add_textbox(slide, Inches(1.3), Inches(5.3), Inches(11), Inches(0.4),
            "Why this is powerful:", font_size=16, color=WHITE, bold=True)

insights = [
    ("•  Simulates how humans process information", NUS_ORANGE),
    ("•  One model specializes in TEXT understanding", ACCENT_BLUE),
    ("•  Another model specializes in VISUAL + BEHAVIORAL patterns", NUS_ORANGE),
    ("•  Meta-learner fuses both perspectives", TIER3_COLOR),
]
y = Inches(5.7)
for text, color in insights:
    add_textbox(slide, Inches(1.5), y, Inches(6), Inches(0.3),
                text, font_size=13, color=color)
    y += Inches(0.3)


# ============================================================
# SLIDE 7: How Tiers Connect - Full Picture
# ============================================================
slide = add_content_slide(prs, "How Tiers Connect — Full Picture")

# Input vector
add_rounded_rect(slide, Inches(1.3), Inches(1.6), Inches(2.0), Inches(0.7),
                 DARK_CARD, "150-dim\nFeature Vector", font_size=14,
                 font_color=WHITE, bold=True)

# Arrow to Tier 1
add_textbox(slide, Inches(3.3), Inches(1.75), Inches(0.4), Inches(0.4),
            "→", font_size=24, color=WHITE, alignment=PP_ALIGN.CENTER)

# Tier 1 box
add_rounded_rect(slide, Inches(3.7), Inches(1.3), Inches(3.0), Inches(1.8),
                 LIGHT_BLUE_BG)
add_rounded_rect(slide, Inches(3.8), Inches(1.4), Inches(2.8), Inches(0.4),
                 ACCENT_BLUE, "Tier 1: Classical ML", font_size=13,
                 font_color=WHITE, bold=True)
tier1_models = ["SVM", "Random Forest", "Naive Bayes", "Decision Tree",
                "KNN", "XGBoost", "LightGBM"]
add_multiline_textbox(slide, Inches(3.9), Inches(1.9), Inches(2.6), Inches(1.1),
                      tier1_models, font_size=10,
                      color=RGBColor(0x2D, 0x2D, 0x2D), spacing=Pt(2))

# Arrow to Tier 2
add_textbox(slide, Inches(3.3), Inches(3.5), Inches(0.4), Inches(0.4),
            "→", font_size=24, color=WHITE, alignment=PP_ALIGN.CENTER)

# Tier 2 box
add_rounded_rect(slide, Inches(3.7), Inches(3.3), Inches(3.0), Inches(1.4),
                 LIGHT_PURPLE_BG)
add_rounded_rect(slide, Inches(3.8), Inches(3.4), Inches(2.8), Inches(0.4),
                 ACCENT_PURPLE, "Tier 2: Deep Learning", font_size=13,
                 font_color=WHITE, bold=True)
tier2_models = ["MLP", "CNN-1D", "LSTM", "Transformer"]
add_multiline_textbox(slide, Inches(3.9), Inches(3.9), Inches(2.6), Inches(0.7),
                      tier2_models, font_size=10,
                      color=RGBColor(0x2D, 0x2D, 0x2D), spacing=Pt(2))

# Arrows from T1 and T2 to Tier 3
add_textbox(slide, Inches(6.7), Inches(1.9), Inches(0.7), Inches(0.4),
            "→", font_size=24, color=WHITE, alignment=PP_ALIGN.CENTER)
add_textbox(slide, Inches(6.7), Inches(3.6), Inches(0.7), Inches(0.4),
            "→", font_size=24, color=WHITE, alignment=PP_ALIGN.CENTER)

# "Selected predictions" label
add_textbox(slide, Inches(6.5), Inches(2.6), Inches(1.2), Inches(0.6),
            "Selected\npredictions", font_size=9, color=LIGHT_GRAY,
            alignment=PP_ALIGN.CENTER)

# Tier 3 box
add_rounded_rect(slide, Inches(7.3), Inches(1.6), Inches(3.0), Inches(3.1),
                 LIGHT_GREEN_BG)
add_rounded_rect(slide, Inches(7.4), Inches(1.7), Inches(2.8), Inches(0.4),
                 TIER3_COLOR, "Tier 3: Ensemble", font_size=13,
                 font_color=WHITE, bold=True)

tier3_details = [
    "Voting",
    "  SVM + RF + MLP",
    "",
    "Stacking",
    "  SVM + RF + MLP → Meta",
    "",
    "Late Fusion",
    "  SVM + RF → Meta",
]
add_multiline_textbox(slide, Inches(7.5), Inches(2.2), Inches(2.7), Inches(2.3),
                      tier3_details, font_size=10,
                      color=RGBColor(0x2D, 0x2D, 0x2D), spacing=Pt(2))

# Arrow to comparison
add_textbox(slide, Inches(10.3), Inches(2.8), Inches(0.5), Inches(0.4),
            "→", font_size=24, color=WHITE, alignment=PP_ALIGN.CENTER)

# Model Comparison Table
add_rounded_rect(slide, Inches(10.8), Inches(1.6), Inches(2.0), Inches(3.1),
                 DARK_CARD)
add_textbox(slide, Inches(10.85), Inches(1.7), Inches(1.9), Inches(0.4),
            "Model Comparison", font_size=14, color=WHITE, bold=True,
            alignment=PP_ALIGN.CENTER)
add_textbox(slide, Inches(10.85), Inches(2.15), Inches(1.9), Inches(0.4),
            "All 14 predictions", font_size=11, color=LIGHT_GRAY,
            alignment=PP_ALIGN.CENTER)
add_textbox(slide, Inches(10.85), Inches(2.5), Inches(1.9), Inches(0.3),
            "↓", font_size=20, color=WHITE, alignment=PP_ALIGN.CENTER)
add_textbox(slide, Inches(10.85), Inches(2.8), Inches(1.9), Inches(0.4),
            "Best model selected", font_size=13, color=ACCENT_GREEN, bold=True,
            alignment=PP_ALIGN.CENTER)
add_textbox(slide, Inches(10.85), Inches(3.2), Inches(1.9), Inches(0.5),
            "Ranked by accuracy,\nF1, and latency", font_size=11,
            color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

# Dependency note at bottom
add_rounded_rect(slide, Inches(1.5), Inches(5.3), Inches(10), Inches(1.0),
                 LIGHT_ORANGE_BG,
                 "Tier 3 DEPENDS on Tier 1 and Tier 2 being trained first\n"
                 "Ensemble models use base model predictions as their inputs",
                 font_size=15, font_color=NUS_ORANGE, bold=True)


# ============================================================
# SLIDE 8: Tier 3 Results & Comparison
# ============================================================
slide = add_content_slide(prs, "Tier 3 Results & Comparison")

# Results table header
table_headers = ["Model", "Accuracy", "F1 Macro", "Latency", "Note"]
col_widths = [Inches(2.2), Inches(1.6), Inches(1.6), Inches(1.6), Inches(2.8)]
x_start = Inches(1.3)

# Header row
x = x_start
y = Inches(1.3)
for i, h in enumerate(table_headers):
    add_rect(slide, x, y, col_widths[i], Inches(0.5), TIER3_COLOR)
    add_textbox(slide, x, y + Inches(0.05), col_widths[i], Inches(0.4),
                h, font_size=15, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)
    x += col_widths[i]

# Data rows
table_data = [
    ("Voting", "0.573", "0.107", "6198ms", ""),
    ("Stacking", "0.566", "0.189", "6951ms", "BEST F1"),
    ("Late Fusion", "0.568", "0.186", "2551ms", ""),
]

y = Inches(1.8)
for row_idx, (model, acc, f1, lat, note) in enumerate(table_data):
    row_bg = DARK_CARD if row_idx % 2 == 0 else CARD_BG
    x = x_start
    vals = [model, acc, f1, lat, note]
    for i, val in enumerate(vals):
        add_rect(slide, x, y, col_widths[i], Inches(0.5), row_bg)
        text_color = NUS_ORANGE if row_bg == DARK_CARD else RGBColor(0x2D, 0x2D, 0x2D)
        is_bold = False
        if val == "BEST F1":
            text_color = TIER3_COLOR
            is_bold = True
        elif i == 0:
            is_bold = True
        add_textbox(slide, x, y + Inches(0.05), col_widths[i], Inches(0.4),
                    val, font_size=14, color=text_color, bold=is_bold,
                    alignment=PP_ALIGN.CENTER)
        x += col_widths[i]
    y += Inches(0.5)

# Highlight: Stacking best F1 row
add_rect(slide, Inches(1.25), Inches(2.3), Inches(0.05), Inches(0.5), TIER3_COLOR)

# Key insights section
add_textbox(slide, Inches(1.3), Inches(3.8), Inches(11), Inches(0.5),
            "Key Insights", font_size=22, color=WHITE, bold=True)

insights = [
    ("Stacking achieved the best F1 score of all 14 models",
     ACCENT_PURPLE, "★"),
    ("Late Fusion offers the best balance of accuracy and speed",
     NUS_ORANGE, "⚡"),
    ("Ensembles consistently outperform individual models on F1",
     TIER3_COLOR, "↑"),
]

y = Inches(4.4)
for text, color, icon in insights:
    add_rounded_rect(slide, Inches(1.3), y, Inches(0.5), Inches(0.5),
                     color, icon, font_size=18, font_color=WHITE, bold=True)
    add_textbox(slide, Inches(2.0), y + Inches(0.05), Inches(10), Inches(0.45),
                text, font_size=16, color=NUS_ORANGE)
    y += Inches(0.65)

# Bottom conclusion box
add_rounded_rect(slide, Inches(1.5), Inches(6.2), Inches(10), Inches(0.5),
                 LIGHT_GREEN_BG,
                 "Ensemble methods prove that combining diverse classifiers improves reliability",
                 font_size=17, font_color=TIER3_COLOR, bold=True)


# ============================================================
# Save
# ============================================================
output_path = "/Users/muneeswaranm/Projects/PRS/PatternRecognSystem-Video2Text/presentation/Video2Knowledge_Tier3_Ensemble.pptx"
prs.save(output_path)
print(f"Presentation saved to: {output_path}")
print(f"Total slides: {len(prs.slides)}")
