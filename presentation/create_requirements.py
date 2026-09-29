"""Generate NUS ISS Practice Module Requirements Mapping presentation."""
from pptx.util import Inches, Pt, Emu
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor

from nus_iss_template import (
    create_presentation, add_title_slide, add_content_slide, add_section_slide,
    add_textbox, add_bullet_list, add_rect, add_rounded_rect, add_multiline_textbox,
    NUS_BLUE, NUS_ORANGE, WHITE, LIGHT_GRAY, SUBTLE_GRAY,
    ACCENT_BLUE, ACCENT_GREEN, ACCENT_PURPLE, ACCENT_RED,
    set_slide_bg, add_nus_logo, add_nus_footer,
    LIGHT_BLUE_BG, LIGHT_GREEN_BG, LIGHT_PURPLE_BG, LIGHT_ORANGE_BG, LIGHT_RED_BG,
    CARD_BG, LIGHT_BG,
)

DARK_CARD = RGBColor(0x00, 0x2A, 0x55)
DARK_TEXT = RGBColor(0x2D, 0x2D, 0x2D)


# --- Local helpers (not in template) ----------------------------------------

def add_multiline_shape(slide, left, top, width, height, fill_color, lines,
                        font_size=12, font_color=NUS_ORANGE, bold_first=False,
                        alignment=PP_ALIGN.LEFT, shape_type=5):
    """Add a shape with multiple lines of text."""
    shape = slide.shapes.add_shape(shape_type, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    shape.line.fill.background()
    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.15)
    tf.margin_right = Inches(0.15)
    tf.margin_top = Inches(0.1)
    tf.margin_bottom = Inches(0.1)
    for i, line in enumerate(lines):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = line
        p.font.size = Pt(font_size)
        p.font.color.rgb = font_color
        p.font.name = "Calibri"
        p.alignment = alignment
        if bold_first and i == 0:
            p.font.bold = True
        p.space_after = Pt(2)
    return shape


def add_code_ref(slide, left, top, width, items, font_size=11):
    """Add a code reference section."""
    add_textbox(slide, left, top, width, Inches(0.3),
                "Where in the code:", font_size=13,
                color=ACCENT_BLUE, bold=True)
    y = top + Inches(0.3)
    txBox = slide.shapes.add_textbox(left, y, width, Inches(len(items) * 0.25))
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = item
        p.font.size = Pt(font_size)
        p.font.color.rgb = LIGHT_GRAY
        p.font.name = "Consolas"
        p.space_after = Pt(3)
    return tf


def _add_check_badge(slide, x, y, color=ACCENT_GREEN):
    """Green checkmark badge."""
    check = slide.shapes.add_shape(9, x, y, Inches(0.6), Inches(0.6))
    check.fill.solid()
    check.fill.fore_color.rgb = color
    check.line.fill.background()
    tf = check.text_frame
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    tf.paragraphs[0].text = "✓"
    tf.paragraphs[0].font.size = Pt(28)
    tf.paragraphs[0].font.color.rgb = WHITE
    tf.paragraphs[0].font.bold = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    return check


# =============================================================================
# BUILD PRESENTATION
# =============================================================================
prs = create_presentation()


# =============================================================================
# SLIDE 1: Title
# =============================================================================
add_title_slide(
    prs,
    title="NUS ISS Practice Module",
    subtitle="Requirements Mapping — How Video2Knowledge meets all 4 project requirements",
    date_text="",
)

# Re-open last slide to add the four requirement badges
slide = prs.slides[len(prs.slides) - 1]
colors = [ACCENT_BLUE, ACCENT_GREEN, NUS_ORANGE, ACCENT_PURPLE]
labels = ["Supervised\nLearning", "ML / Deep\nLearning", "Hybrid /\nEnsemble", "Intelligent\nSensing"]
for i in range(4):
    x = Inches(2.5 + i * 2.3)
    add_rounded_rect(slide, x, Inches(5.5), Inches(1.8), Inches(0.9),
                     colors[i], labels[i], font_size=13, font_color=WHITE,
                     bold=True)


# =============================================================================
# SLIDE 2: Requirements Overview
# =============================================================================
slide = add_content_slide(prs, "Project Must Demonstrate At Least 3 of 4 Aspects")

requirements = [
    ("1", "Supervised learning / unsupervised learning scenarios"),
    ("2", "Machine learning / Deep learning techniques"),
    ("3", "Hybrid machine learning / Ensemble approach"),
    ("4", "Intelligent sensing / sense making techniques"),
]

y_start = Inches(1.3)
for i, (num, text) in enumerate(requirements):
    y = y_start + Inches(i * 0.85)
    check_shape = slide.shapes.add_shape(9, Inches(1.3), y, Inches(0.5), Inches(0.5))
    check_shape.fill.solid()
    check_shape.fill.fore_color.rgb = ACCENT_GREEN
    check_shape.line.fill.background()
    tf = check_shape.text_frame
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    tf.paragraphs[0].text = "✓"
    tf.paragraphs[0].font.size = Pt(22)
    tf.paragraphs[0].font.color.rgb = WHITE
    tf.paragraphs[0].font.bold = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE

    add_textbox(slide, Inches(2.0), y + Inches(0.05), Inches(9), Inches(0.45),
                text, font_size=20, color=NUS_ORANGE)

# Big callout box
add_rounded_rect(slide, Inches(1.3), Inches(4.8), Inches(9.333), Inches(0.8),
                 ACCENT_GREEN,
                 "Video2Knowledge covers ALL 4 aspects",
                 font_size=26, font_color=WHITE, bold=True)

add_textbox(slide, Inches(1.3), Inches(5.9), Inches(10.333), Inches(0.6),
            "A practical application demonstrating pattern recognition and ML techniques to solve a real-world problem",
            font_size=16, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)


# =============================================================================
# SLIDE 3: Requirement 1 -- Supervised Learning
# =============================================================================
slide = add_content_slide(prs,
                          "1. Supervised Learning / Unsupervised Learning Scenarios")
_add_check_badge(slide, Inches(0.3), Inches(0.15), RGBColor(0x1E, 0x8E, 0x3E))

# LEFT section: What supervised learning means
add_textbox(slide, Inches(1.3), Inches(1.3), Inches(5.5), Inches(0.4),
            "What Supervised Learning Means", font_size=18,
            color=ACCENT_GREEN, bold=True)

add_multiline_shape(slide, Inches(1.3), Inches(1.8), Inches(5.5), Inches(1.0),
                    LIGHT_GREEN_BG,
                    ["• Models learn from LABELED examples",
                     "• Input: 150-dim feature vector",
                     "• Output: 1 of 9 activity labels"],
                    font_size=14, font_color=NUS_ORANGE, bold_first=False)

# Training process
add_textbox(slide, Inches(1.3), Inches(3.0), Inches(5.5), Inches(0.4),
            "Training Process", font_size=18,
            color=ACCENT_GREEN, bold=True)

training_items = [
    "• 9,514 labeled videos from CUA-Suite dataset",
    "• Labels: git_operations, docker_workflow,",
    "  kubernetes_ops, aws_console, jenkins_ci_cd,",
    "  coding_editing, debugging, documentation, other",
    "• 80/20 stratified train/test split",
    "  (7,685 train / 1,924 test)",
    "• model.fit(X_train, y_train) → predict → evaluate",
]
add_multiline_shape(slide, Inches(1.3), Inches(3.5), Inches(5.5), Inches(2.2),
                    CARD_BG, training_items,
                    font_size=13, font_color=NUS_ORANGE)

# RIGHT section: All 14 models use supervised learning
add_textbox(slide, Inches(7.3), Inches(1.3), Inches(5.5), Inches(0.4),
            "All 14 Models Use Supervised Learning", font_size=18,
            color=ACCENT_GREEN, bold=True)

tier_data = [
    ("Tier 1 — Classical ML (7 models)", ACCENT_BLUE,
     ["SVM, Naive Bayes, Decision Tree,",
      "Random Forest, KNN, XGBoost, LightGBM"]),
    ("Tier 2 — Deep Learning (4 models)", NUS_ORANGE,
     ["MLP, CNN-1D, LSTM, Transformer"]),
    ("Tier 3 — Ensemble (3 models)", ACCENT_PURPLE,
     ["Voting, Stacking, Late Fusion"]),
]

y_pos = Inches(1.8)
for title, color, items in tier_data:
    add_rounded_rect(slide, Inches(7.3), y_pos, Inches(5.0), Inches(0.4),
                     color, title, font_size=14, font_color=WHITE, bold=True)
    y_pos += Inches(0.45)
    add_multiline_shape(slide, Inches(7.3), y_pos, Inches(5.0), Inches(0.55),
                        CARD_BG, items, font_size=13, font_color=NUS_ORANGE,
                        alignment=PP_ALIGN.CENTER)
    y_pos += Inches(0.7)

# Code reference
add_code_ref(slide, Inches(7.3), Inches(4.6), Inches(5.0), [
    "train.py: clf.fit(X_train, y_train)",
    "ml_service.py: clf.predict(features)",
    "dataset_loader.py: derive_activity_label() assigns labels",
])


# =============================================================================
# SLIDE 4: Requirement 2 -- Machine Learning / Deep Learning
# =============================================================================
slide = add_content_slide(prs,
                          "2. Machine Learning / Deep Learning Techniques")
_add_check_badge(slide, Inches(0.3), Inches(0.15))

# LEFT: Machine Learning (Tier 1)
add_rounded_rect(slide, Inches(1.3), Inches(1.3), Inches(5.0), Inches(0.5),
                 ACCENT_BLUE, "Machine Learning  —  Tier 1 (7 Models)",
                 font_size=18, font_color=WHITE, bold=True)

ml_models = [
    "• SVM (Support Vector Machine)",
    "• Naive Bayes",
    "• Decision Tree",
    "• Random Forest",
    "• KNN (K-Nearest Neighbors)",
    "• XGBoost (Gradient Boosting)",
    "• LightGBM (Gradient Boosting)",
]
add_multiline_shape(slide, Inches(1.3), Inches(1.95), Inches(5.0), Inches(2.7),
                    LIGHT_BLUE_BG, ml_models,
                    font_size=15, font_color=NUS_ORANGE)

add_rounded_rect(slide, Inches(2.0), Inches(4.8), Inches(3.5), Inches(0.45),
                 ACCENT_BLUE, "scikit-learn library",
                 font_size=15, font_color=WHITE, bold=True)

# RIGHT: Deep Learning (Tier 2)
add_rounded_rect(slide, Inches(7.3), Inches(1.3), Inches(5.0), Inches(0.5),
                 NUS_ORANGE, "Deep Learning  —  Tier 2 (4 Models)",
                 font_size=18, font_color=WHITE, bold=True)

dl_models = [
    "• MLP (Multi-Layer Perceptron)",
    "   3 fully-connected layers",
    "• CNN-1D",
    "   Convolutional filters on feature sequences",
    "• LSTM",
    "   Recurrent network with memory gates",
    "• Transformer",
    "   Self-attention mechanism",
]
add_multiline_shape(slide, Inches(7.3), Inches(1.95), Inches(5.0), Inches(2.7),
                    LIGHT_ORANGE_BG, dl_models,
                    font_size=15, font_color=NUS_ORANGE)

add_rounded_rect(slide, Inches(8.0), Inches(4.8), Inches(3.5), Inches(0.45),
                 NUS_ORANGE, "PyTorch framework",
                 font_size=15, font_color=WHITE, bold=True)

# Divider line
div = slide.shapes.add_shape(1, Inches(6.55), Inches(1.3), Inches(0.04), Inches(4.0))
div.fill.solid()
div.fill.fore_color.rgb = LIGHT_GRAY
div.line.fill.background()

# Code reference
add_textbox(slide, Inches(1.3), Inches(5.5), Inches(5.0), Inches(0.3),
            "Where in the code:", font_size=13,
            color=ACCENT_BLUE, bold=True)
code_items = [
    "classifiers/tier1/*.py: 7 classical ML implementations",
    "classifiers/tier2/*.py: 4 PyTorch neural networks",
    "Each model: fit(), predict(), save(), load()",
]
txBox = slide.shapes.add_textbox(Inches(1.3), Inches(5.85), Inches(6.0), Inches(1.0))
tf = txBox.text_frame
tf.word_wrap = True
for i, item in enumerate(code_items):
    if i == 0:
        p = tf.paragraphs[0]
    else:
        p = tf.add_paragraph()
    p.text = item
    p.font.size = Pt(11)
    p.font.color.rgb = LIGHT_GRAY
    p.font.name = "Consolas"
    p.space_after = Pt(3)


# =============================================================================
# SLIDE 5: Requirement 3 -- Hybrid / Ensemble Approach
# =============================================================================
slide = add_content_slide(prs,
                          "3. Hybrid Machine Learning / Ensemble Approach")
_add_check_badge(slide, Inches(0.3), Inches(0.15))

# Section: Tier 3 -- 3 Ensemble Models
add_textbox(slide, Inches(1.3), Inches(1.3), Inches(11.0), Inches(0.4),
            "Tier 3 — 3 Ensemble Models", font_size=20,
            color=ACCENT_PURPLE, bold=True)

# 3 cards for each ensemble method
ensemble_data = [
    ("Voting Ensemble", ACCENT_BLUE,
     ["Combines SVM + Random Forest",
      "+ MLP predictions",
      "",
      "Soft voting: averages",
      "probability outputs from",
      "all 3 base models"]),
    ("Stacking Ensemble", ACCENT_GREEN,
     ["SVM + RF + MLP produce",
      "probability outputs",
      "",
      "Logistic Regression",
      "meta-learner combines",
      "stacked probabilities"]),
    ("Late Fusion", NUS_ORANGE,
     ["SVM on text features +",
      "RF on visual features",
      "",
      "Meta-learner fuses",
      "modality-specific",
      "prediction branches"]),
]

for i, (title, color, items) in enumerate(ensemble_data):
    x = Inches(1.3 + i * 3.8)
    add_rounded_rect(slide, x, Inches(1.8), Inches(3.5), Inches(0.45),
                     color, title, font_size=16, font_color=WHITE, bold=True)
    add_multiline_shape(slide, x, Inches(2.35), Inches(3.5), Inches(1.6),
                        CARD_BG, items,
                        font_size=13, font_color=NUS_ORANGE,
                        alignment=PP_ALIGN.CENTER)

# Hybrid explanation
add_textbox(slide, Inches(1.3), Inches(4.2), Inches(11.0), Inches(0.35),
            "Hybrid = Combines Classical ML (Tier 1) + Deep Learning (Tier 2)",
            font_size=17, color=ACCENT_PURPLE, bold=True)

# Flow: Tier 1 + Tier 2 --> Tier 3
add_rounded_rect(slide, Inches(1.3), Inches(4.7), Inches(2.5), Inches(0.5),
                 ACCENT_BLUE, "Tier 1: Classical ML",
                 font_size=14, font_color=WHITE, bold=True)
add_rounded_rect(slide, Inches(4.3), Inches(4.7), Inches(2.5), Inches(0.5),
                 NUS_ORANGE, "Tier 2: Deep Learning",
                 font_size=14, font_color=WHITE, bold=True)

# Arrow
arrow = slide.shapes.add_shape(1, Inches(7.1), Inches(4.85), Inches(1.0), Inches(0.04))
arrow.fill.solid()
arrow.fill.fore_color.rgb = WHITE
arrow.line.fill.background()
add_textbox(slide, Inches(7.2), Inches(4.65), Inches(0.8), Inches(0.3),
            "▶", font_size=14, color=WHITE, alignment=PP_ALIGN.CENTER)

add_rounded_rect(slide, Inches(8.3), Inches(4.7), Inches(2.8), Inches(0.5),
                 ACCENT_PURPLE, "Tier 3: Ensemble",
                 font_size=14, font_color=WHITE, bold=True)

# Key insight
add_rounded_rect(slide, Inches(1.3), Inches(5.5), Inches(10.5), Inches(0.55),
                 ACCENT_GREEN,
                 "Key Insight: Stacking achieved the BEST F1 score (0.292) across all 14 models",
                 font_size=17, font_color=WHITE, bold=True)

# Code reference
add_code_ref(slide, Inches(1.3), Inches(6.2), Inches(11.0), [
    "classifiers/tier3/voting.py: soft voting over 3 base models",
    "classifiers/tier3/stacking.py: meta-learner on stacked probabilities",
    "classifiers/tier3/late_fusion.py: modality-specific branches + fusion",
])


# =============================================================================
# SLIDE 6: Requirement 4 -- Intelligent Sensing / Sense Making
# =============================================================================
slide = add_content_slide(prs,
                          "4. Intelligent Sensing / Sense Making Techniques")
_add_check_badge(slide, Inches(0.3), Inches(0.15))

# 4 sensing modalities in a 2x2 grid
sensing_data = [
    ("OCR Sensing", "EasyOCR + Tesseract", ACCENT_BLUE, LIGHT_BLUE_BG,
     ['"Reads text from screen recordings"',
      "• TF-IDF vectorization",
      "• Fallback OCR pipeline",
      "• Text extraction from video frames",
      "→ 50 features"]),
    ("UI Sensing", "YOLOv8", ACCENT_GREEN, LIGHT_GREEN_BG,
     ['"Detects UI elements on screen"',
      "• Object detection: buttons, terminals,",
      "  menus, dialogs, tabs, sidebars",
      "→ 30 features"]),
    ("Visual Sensing", "OpenCV", NUS_ORANGE, LIGHT_ORANGE_BG,
     ['"Analyzes visual patterns"',
      "• Color histograms",
      "• Edge detection, texture analysis",
      "• Layout analysis",
      "→ 40 features"]),
    ("Behavioral Sensing", "Action Log Parser", ACCENT_PURPLE, LIGHT_PURPLE_BG,
     ['"Understands user behavior"',
      "• Mouse clicks, typing patterns",
      "• Keyboard shortcuts",
      "• Movement analysis",
      "→ 30 features"]),
]

positions = [
    (Inches(1.3), Inches(1.3)),    # top-left
    (Inches(7.3), Inches(1.3)),    # top-right
    (Inches(1.3), Inches(3.7)),    # bottom-left
    (Inches(7.3), Inches(3.7)),    # bottom-right
]

for (title, tool, accent, bg_color, items), (x, y) in zip(sensing_data, positions):
    add_rounded_rect(slide, x, y, Inches(5.5), Inches(0.45),
                     accent, f"{title}  ({tool})",
                     font_size=15, font_color=WHITE, bold=True)
    add_multiline_shape(slide, x, y + Inches(0.5), Inches(5.5), Inches(1.6),
                        bg_color, items,
                        font_size=13, font_color=NUS_ORANGE)

# Sense Making section
add_rounded_rect(slide, Inches(1.3), Inches(5.85), Inches(11.0), Inches(0.45),
                 DARK_CARD,
                 "Sense Making: 4 modalities fused into 150-dim multimodal representation",
                 font_size=17, font_color=WHITE, bold=True)

add_textbox(slide, Inches(1.3), Inches(6.35), Inches(5.5), Inches(0.35),
            "Pattern recognition transforms raw video into structured knowledge",
            font_size=13, color=LIGHT_GRAY)
add_textbox(slide, Inches(7.3), Inches(6.35), Inches(5.0), Inches(0.35),
            "Output: classified activity labels + workflow step descriptions",
            font_size=13, color=LIGHT_GRAY)


# =============================================================================
# SLIDE 7: Summary -- All 4 Requirements Mapped
# =============================================================================
slide = add_content_slide(prs, "Complete Requirements Coverage")

# 2x2 grid of requirements
grid_data = [
    ("Supervised Learning", ACCENT_GREEN, LIGHT_GREEN_BG,
     ["✓ 9,514 labeled videos from CUA-Suite",
      "✓ 14 trained models (all supervised)",
      "✓ F1-macro evaluation metric",
      "✓ 80/20 stratified train/test split"]),
    ("ML / Deep Learning", ACCENT_BLUE, LIGHT_BLUE_BG,
     ["✓ 7 classical ML models (scikit-learn)",
      "✓ 4 neural network models (PyTorch)",
      "✓ SVM, RF, KNN, XGBoost, LightGBM",
      "✓ MLP, CNN-1D, LSTM, Transformer"]),
    ("Hybrid / Ensemble", ACCENT_PURPLE, LIGHT_PURPLE_BG,
     ["✓ 3 ensemble methods in Tier 3",
      "✓ Voting, Stacking, Late Fusion",
      "✓ Combines Tier 1 + Tier 2 models",
      "✓ Meta-learning / probability fusion"]),
    ("Intelligent Sensing", NUS_ORANGE, LIGHT_ORANGE_BG,
     ["✓ 4 modalities: OCR, YOLO, OpenCV, Actions",
      "✓ 150-dim multimodal feature vector",
      "✓ TF-IDF, object detection, histograms",
      "✓ Behavioral analysis + fusion"]),
]

grid_positions = [
    (Inches(1.3), Inches(1.3)),     # top-left
    (Inches(7.3), Inches(1.3)),     # top-right
    (Inches(1.3), Inches(3.9)),     # bottom-left
    (Inches(7.3), Inches(3.9)),     # bottom-right
]

for (title, accent, bg_color, items), (x, y) in zip(grid_data, grid_positions):
    add_rounded_rect(slide, x, y, Inches(5.5), Inches(0.5),
                     accent, title,
                     font_size=17, font_color=WHITE, bold=True)
    add_multiline_shape(slide, x, y + Inches(0.55), Inches(5.5), Inches(1.7),
                        bg_color, items,
                        font_size=14, font_color=NUS_ORANGE)

# Bottom summary text
add_textbox(slide, Inches(1.3), Inches(6.15), Inches(11.0), Inches(0.4),
            "Real-world application: Screen Activity Classification from Video Recordings",
            font_size=18, color=NUS_ORANGE, bold=True, alignment=PP_ALIGN.CENTER)

add_textbox(slide, Inches(1.3), Inches(6.5), Inches(11.0), Inches(0.4),
            "Full-stack implementation: React frontend, FastAPI backend, Docker deployment, AWS infrastructure",
            font_size=15, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)


# =============================================================================
# SAVE
# =============================================================================
output_path = "/Users/muneeswaranm/Projects/PRS/PatternRecognSystem-Video2Text/presentation/Video2Knowledge_Requirements.pptx"
prs.save(output_path)
print(f"Presentation saved to: {output_path}")
print(f"Total slides: {len(prs.slides)}")
