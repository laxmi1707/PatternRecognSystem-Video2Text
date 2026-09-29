"""Generate Tier 1 Classical ML Classifiers presentation (NUS ISS template)."""
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

# --- Derived constants ---
DARK_CARD = RGBColor(0x00, 0x2A, 0x55)
TIER1_COLOR = ACCENT_BLUE


# --- Local helpers (not in template) ------------------------------------

def add_oval(slide, left, top, width, height, fill_color, text="",
             font_size=10, font_color=WHITE, bold=False):
    shape = slide.shapes.add_shape(9, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    shape.line.fill.background()
    if text:
        tf = shape.text_frame
        tf.word_wrap = True
        tf.paragraphs[0].alignment = PP_ALIGN.CENTER
        tf.paragraphs[0].text = text
        tf.paragraphs[0].font.size = Pt(font_size)
        tf.paragraphs[0].font.color.rgb = font_color
        tf.paragraphs[0].font.bold = bold
    return shape


def add_diamond(slide, left, top, width, height, fill_color, text="",
                font_size=10, font_color=WHITE, bold=False):
    shape = slide.shapes.add_shape(4, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    shape.line.fill.background()
    if text:
        tf = shape.text_frame
        tf.word_wrap = True
        tf.paragraphs[0].alignment = PP_ALIGN.CENTER
        tf.paragraphs[0].text = text
        tf.paragraphs[0].font.size = Pt(font_size)
        tf.paragraphs[0].font.color.rgb = font_color
        tf.paragraphs[0].font.bold = bold
    return shape


def add_strengths_weaknesses(slide, left, top, strengths, weaknesses,
                             width=Inches(5.2)):
    """Add a strengths/weaknesses two-column section."""
    add_rounded_rect(slide, left, top, width, Inches(0.35),
                     ACCENT_GREEN, "Strengths", font_size=13,
                     font_color=WHITE, bold=True)
    y = top + Inches(0.4)
    for s in strengths:
        add_textbox(slide, left + Inches(0.15), y, width - Inches(0.3),
                    Inches(0.3), f"+  {s}", font_size=12, color=ACCENT_GREEN)
        y += Inches(0.28)

    weak_left = left + width + Inches(0.4)
    add_rounded_rect(slide, weak_left, top, width, Inches(0.35),
                     NUS_ORANGE, "Weaknesses", font_size=13,
                     font_color=WHITE, bold=True)
    y = top + Inches(0.4)
    for w in weaknesses:
        add_textbox(slide, weak_left + Inches(0.15), y, width - Inches(0.3),
                    Inches(0.3), f"-  {w}", font_size=12, color=NUS_ORANGE)
        y += Inches(0.28)


# ========================================================================
prs = create_presentation()

# ============================================================
# SLIDE 1: Title
# ============================================================
add_title_slide(
    prs,
    "Tier 1: Classical Machine Learning",
    subtitle="7 proven algorithms for screen activity classification",
    author="Video2Knowledge",
    affiliation="Pattern Recognition Systems  |  NUS ISS",
    date_text="September 2026",
)

# ============================================================
# SLIDE 2: Overview
# ============================================================
slide = add_content_slide(prs, "Tier 1 Overview")

add_textbox(slide, Inches(1.3), Inches(1.3), Inches(11.5), Inches(0.5),
            "All classifiers take the same input: 150-dim feature vector"
            "  ->  predict 1 of 9 activity labels",
            font_size=17, color=NUS_ORANGE, bold=True)

# 7 algorithm cards
algo_info = [
    ("SVM", "Support Vector Machine", TIER1_COLOR),
    ("NB", "Naive Bayes", RGBColor(0x17, 0xA2, 0xB8)),
    ("DT", "Decision Tree", ACCENT_GREEN),
    ("RF", "Random Forest", RGBColor(0x20, 0xC9, 0x97)),
    ("KNN", "K-Nearest Neighbors", ACCENT_PURPLE),
    ("XGB", "XGBoost", NUS_ORANGE),
    ("LGBM", "LightGBM", RGBColor(0xE8, 0x3E, 0x8C)),
]

x = Inches(1.3)
y_cards = Inches(2.0)
card_w = Inches(1.55)
for abbr, full_name, clr in algo_info:
    add_rounded_rect(slide, x, y_cards, card_w, Inches(0.85), clr,
                     abbr, font_size=18, font_color=WHITE, bold=True)
    add_textbox(slide, x, y_cards + Inches(0.9), card_w, Inches(0.4),
                full_name, font_size=9, color=LIGHT_GRAY,
                alignment=PP_ALIGN.CENTER)
    x += card_w + Inches(0.12)

# Pipeline diagram
y_pipe = Inches(3.7)
add_textbox(slide, Inches(1.3), y_pipe - Inches(0.35), Inches(11), Inches(0.35),
            "How every Tier 1 classifier works:", font_size=16,
            color=NUS_ORANGE, bold=True)

# Input box
add_rounded_rect(slide, Inches(1.3), y_pipe + Inches(0.1), Inches(3.2),
                 Inches(1.8), DARK_CARD)
add_textbox(slide, Inches(1.4), y_pipe + Inches(0.15), Inches(3), Inches(0.35),
            "INPUT: 150-dim Feature Vector", font_size=13, color=TIER1_COLOR,
            bold=True)
input_items = [
    "OCR features (50 dims)  --  text content",
    "YOLO features (30 dims)  --  UI elements",
    "OpenCV features (40 dims)  --  visual patterns",
    "Action features (30 dims)  --  user interactions",
]
y_inp = y_pipe + Inches(0.55)
for item in input_items:
    add_textbox(slide, Inches(1.6), y_inp, Inches(2.8), Inches(0.25),
                item, font_size=10, color=NUS_ORANGE)
    y_inp += Inches(0.25)
add_textbox(slide, Inches(1.4), y_inp + Inches(0.05), Inches(3), Inches(0.25),
            "[0.82, 0.15, 0.0, 1.0, 0.67, ...]",
            font_size=11, color=LIGHT_GRAY, font_name="Courier New")

# Arrow
add_textbox(slide, Inches(4.6), y_pipe + Inches(0.6), Inches(0.8), Inches(0.6),
            "->", font_size=40, color=TIER1_COLOR, alignment=PP_ALIGN.CENTER,
            bold=True)

# Model box
add_rounded_rect(slide, Inches(5.4), y_pipe + Inches(0.1), Inches(3.2),
                 Inches(1.8), DARK_CARD)
add_textbox(slide, Inches(5.5), y_pipe + Inches(0.15), Inches(3), Inches(0.35),
            "CLASSIFIER", font_size=13, color=NUS_ORANGE, bold=True)
add_textbox(slide, Inches(5.5), y_pipe + Inches(0.55), Inches(3), Inches(0.3),
            "Any of the 7 algorithms", font_size=11, color=LIGHT_GRAY)
add_rounded_rect(slide, Inches(5.8), y_pipe + Inches(0.9), Inches(2.5),
                 Inches(0.35), TIER1_COLOR, "fit(X_train, y_train)",
                 font_size=11, font_color=WHITE, bold=True)
add_rounded_rect(slide, Inches(5.8), y_pipe + Inches(1.35), Inches(2.5),
                 Inches(0.35), ACCENT_PURPLE, "predict(X_new)",
                 font_size=11, font_color=WHITE, bold=True)

# Arrow
add_textbox(slide, Inches(8.7), y_pipe + Inches(0.6), Inches(0.8), Inches(0.6),
            "->", font_size=40, color=TIER1_COLOR, alignment=PP_ALIGN.CENTER,
            bold=True)

# Output box
add_rounded_rect(slide, Inches(9.5), y_pipe + Inches(0.1), Inches(3.5),
                 Inches(1.8), DARK_CARD)
add_textbox(slide, Inches(9.6), y_pipe + Inches(0.15), Inches(3.3), Inches(0.35),
            "OUTPUT: Label + Probability", font_size=13, color=ACCENT_GREEN,
            bold=True)
labels = [
    '"git_operations"      87.3%',
    '"coding_editing"      5.2%',
    '"debugging"           3.1%',
    '"web_browsing"        1.8%',
    '"documentation"       1.1%',
    '... (9 labels total)',
]
y_lbl = y_pipe + Inches(0.55)
for lbl in labels:
    add_textbox(slide, Inches(9.8), y_lbl, Inches(3.1), Inches(0.22),
                lbl, font_size=10, color=NUS_ORANGE, font_name="Courier New")
    y_lbl += Inches(0.2)

# 9 activity labels at bottom
add_textbox(slide, Inches(1.3), Inches(6.2), Inches(11.5), Inches(0.35),
            "9 Activity Labels:  coding_editing  |  debugging  |  git_operations"
            "  |  web_browsing  |  documentation  |  terminal_ops  |  "
            "file_management  |  communication  |  other",
            font_size=11, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)


# ============================================================
# SLIDE 3: SVM (Support Vector Machine)
# ============================================================
slide = add_content_slide(prs, "SVM (Support Vector Machine)",
                          "Finds the optimal boundary (hyperplane) between classes "
                          "in 150-dimensional space")

# 2D visualization
viz_left = Inches(1.3)
viz_top = Inches(1.3)
viz_w = Inches(5.5)
viz_h = Inches(3.5)
add_rounded_rect(slide, viz_left, viz_top, viz_w, viz_h, DARK_CARD)
add_textbox(slide, viz_left + Inches(0.2), viz_top + Inches(0.1),
            Inches(4), Inches(0.3),
            "2D Visualization (simplified from 150D)", font_size=11,
            color=LIGHT_GRAY)

# Class A points (blue circles) - git_ops cluster
class_a_points = [
    (1.5, 2.5), (1.8, 2.8), (2.2, 3.0), (1.3, 3.2), (2.0, 3.5),
    (1.7, 3.8), (2.5, 2.7), (1.0, 3.0), (2.3, 3.3), (1.6, 3.6),
]
for px, py in class_a_points:
    add_oval(slide, viz_left + Inches(px), viz_top + Inches(py * 0.7 + 0.2),
             Inches(0.22), Inches(0.22), TIER1_COLOR)

# Class B points (orange circles) - coding cluster
class_b_points = [
    (3.5, 0.8), (3.8, 1.2), (4.0, 0.5), (3.3, 1.5), (4.2, 1.0),
    (3.7, 0.3), (4.5, 0.7), (3.9, 1.8), (4.3, 1.4), (3.6, 0.9),
]
for px, py in class_b_points:
    add_oval(slide, viz_left + Inches(px), viz_top + Inches(py * 0.7 + 0.2),
             Inches(0.22), Inches(0.22), NUS_ORANGE)

# Hyperplane
line_x = viz_left + Inches(2.75)
add_rect(slide, line_x, viz_top + Inches(0.3), Inches(0.04), Inches(2.9),
         ACCENT_RED)

# Margin lines
add_rect(slide, line_x - Inches(0.4), viz_top + Inches(0.3),
         Inches(0.02), Inches(2.9), LIGHT_GRAY)
add_rect(slide, line_x + Inches(0.42), viz_top + Inches(0.3),
         Inches(0.02), Inches(2.9), LIGHT_GRAY)

# Labels
add_textbox(slide, line_x - Inches(0.7), viz_top + Inches(3.1),
            Inches(1.5), Inches(0.3),
            "Hyperplane", font_size=10, color=ACCENT_RED,
            bold=True, alignment=PP_ALIGN.CENTER)
add_textbox(slide, line_x - Inches(0.6), viz_top + Inches(0.05),
            Inches(1.2), Inches(0.25),
            "<- margin ->", font_size=9, color=LIGHT_GRAY,
            alignment=PP_ALIGN.CENTER)

# Legend
add_oval(slide, viz_left + Inches(3.8), viz_top + Inches(3.1),
         Inches(0.18), Inches(0.18), TIER1_COLOR)
add_textbox(slide, viz_left + Inches(4.05), viz_top + Inches(3.1),
            Inches(0.8), Inches(0.2), "git_ops", font_size=9, color=NUS_ORANGE)
add_oval(slide, viz_left + Inches(4.7), viz_top + Inches(3.1),
         Inches(0.18), Inches(0.18), NUS_ORANGE)
add_textbox(slide, viz_left + Inches(4.95), viz_top + Inches(3.1),
            Inches(0.8), Inches(0.2), "coding", font_size=9, color=NUS_ORANGE)

# Key concepts
concept_left = Inches(7.3)
concept_top = Inches(1.3)
add_rounded_rect(slide, concept_left, concept_top, Inches(5.5), Inches(1.4),
                 DARK_CARD)
add_textbox(slide, concept_left + Inches(0.2), concept_top + Inches(0.1),
            Inches(5.1), Inches(0.3),
            "Key Concepts", font_size=15, color=NUS_ORANGE, bold=True)

concepts = [
    "Maximizes the margin between classes",
    "Uses kernel trick to handle non-linear boundaries",
    "RBF kernel maps data to higher dimensions",
    "Support vectors = points closest to the boundary",
]
y_c = concept_top + Inches(0.4)
for c in concepts:
    add_textbox(slide, concept_left + Inches(0.3), y_c, Inches(5.0), Inches(0.25),
                f"*  {c}", font_size=12, color=NUS_ORANGE)
    y_c += Inches(0.25)

# Strengths / Weaknesses
add_strengths_weaknesses(
    slide, Inches(1.3), Inches(5.2),
    strengths=[
        "Works well with high-dimensional data (150 features)",
        "Effective when classes have clear margins",
    ],
    weaknesses=[
        "Slow on large datasets (5617ms latency)",
        "Sensitive to feature scaling",
    ],
    width=Inches(5.2),
)


# ============================================================
# SLIDE 4: Naive Bayes
# ============================================================
slide = add_content_slide(prs, "Naive Bayes",
                          "Uses Bayes' Theorem to calculate probability of each class")

# Bayes formula
formula_top = Inches(1.3)
add_rounded_rect(slide, Inches(1.5), formula_top, Inches(10.3), Inches(1.2),
                 DARK_CARD)
add_textbox(slide, Inches(1.7), formula_top + Inches(0.1),
            Inches(9.9), Inches(0.5),
            "P(class | features) = P(features | class) x P(class) / P(features)",
            font_size=24, color=TIER1_COLOR, bold=True,
            alignment=PP_ALIGN.CENTER, font_name="Cambria Math")
add_textbox(slide, Inches(1.7), formula_top + Inches(0.65),
            Inches(9.9), Inches(0.45),
            "posterior          =        likelihood        x   prior    /   evidence",
            font_size=13, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

# "Naive" assumption
add_textbox(slide, Inches(1.3), Inches(2.7), Inches(11.5), Inches(0.4),
            'Assumes all features are independent (the "naive" assumption)',
            font_size=17, color=NUS_ORANGE, bold=True)

# Worked example
ex_top = Inches(3.3)
add_rounded_rect(slide, Inches(1.3), ex_top, Inches(11.5), Inches(1.6),
                 DARK_CARD)
add_textbox(slide, Inches(1.5), ex_top + Inches(0.1), Inches(3), Inches(0.3),
            "Worked Example", font_size=14, color=NUS_ORANGE, bold=True)

add_rounded_rect(slide, Inches(1.5), ex_top + Inches(0.5), Inches(3.0),
                 Inches(0.4), TIER1_COLOR,
                 'Observation: "git" in OCR text', font_size=11,
                 font_color=WHITE, bold=True)
add_textbox(slide, Inches(4.6), ex_top + Inches(0.5), Inches(0.5),
            Inches(0.4), "+", font_size=20, color=NUS_ORANGE,
            alignment=PP_ALIGN.CENTER, bold=True)
add_rounded_rect(slide, Inches(5.0), ex_top + Inches(0.5), Inches(2.8),
                 Inches(0.4), ACCENT_PURPLE,
                 "Observation: terminal present", font_size=11,
                 font_color=WHITE, bold=True)
add_textbox(slide, Inches(7.9), ex_top + Inches(0.5), Inches(0.5),
            Inches(0.4), "->", font_size=20, color=NUS_ORANGE,
            alignment=PP_ALIGN.CENTER, bold=True)
add_rounded_rect(slide, Inches(8.4), ex_top + Inches(0.5), Inches(3.8),
                 Inches(0.4), ACCENT_GREEN,
                 "P(git_operations | features) = HIGH", font_size=11,
                 font_color=WHITE, bold=True)

add_textbox(slide, Inches(1.5), ex_top + Inches(1.05), Inches(11), Inches(0.45),
            "Each feature independently increases or decreases the probability "
            "of each class label.\n"
            "Final prediction = class with highest posterior probability.",
            font_size=12, color=LIGHT_GRAY)

# Strengths / Weaknesses
add_strengths_weaknesses(
    slide, Inches(1.3), Inches(5.3),
    strengths=[
        "Very fast inference (16ms latency)",
        "Works well with small training datasets",
    ],
    weaknesses=[
        "Independence assumption rarely true in practice",
        "Lowest accuracy in our results",
    ],
    width=Inches(5.2),
)


# ============================================================
# SLIDE 5: Decision Tree
# ============================================================
slide = add_content_slide(prs, "Decision Tree",
                          "Asks yes/no questions about features in a tree structure")

# Tree diagram
tree_top = Inches(1.3)

# Root node
root_x = Inches(5.0)
root_y = tree_top
add_diamond(slide, root_x, root_y, Inches(3.5), Inches(0.8),
            TIER1_COLOR, 'OCR contains "git"?', font_size=12,
            font_color=WHITE, bold=True)

# Yes/No labels
add_textbox(slide, root_x - Inches(0.7), root_y + Inches(0.6),
            Inches(1), Inches(0.3),
            "Yes", font_size=13, color=ACCENT_GREEN, bold=True)
add_textbox(slide, root_x + Inches(3.2), root_y + Inches(0.6),
            Inches(1), Inches(0.3),
            "No", font_size=13, color=NUS_ORANGE, bold=True)

# Arrows
add_textbox(slide, root_x + Inches(0.5), root_y + Inches(0.7),
            Inches(0.5), Inches(0.5),
            "\\", font_size=22, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)
add_textbox(slide, root_x + Inches(2.5), root_y + Inches(0.7),
            Inches(0.5), Inches(0.5),
            "/", font_size=22, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

# Level 2 - Left node
l2_left_x = Inches(2.0)
l2_y = tree_top + Inches(1.3)
add_diamond(slide, l2_left_x, l2_y, Inches(3.0), Inches(0.8),
            ACCENT_PURPLE, "Has terminal?", font_size=12,
            font_color=WHITE, bold=True)

# Level 2 - Right node
l2_right_x = Inches(8.4)
add_diamond(slide, l2_right_x, l2_y, Inches(3.0), Inches(0.8),
            ACCENT_PURPLE, "Many clicks?", font_size=12,
            font_color=WHITE, bold=True)

# Yes/No for left branch
add_textbox(slide, l2_left_x - Inches(0.5), l2_y + Inches(0.6),
            Inches(0.7), Inches(0.3),
            "Yes", font_size=11, color=ACCENT_GREEN, bold=True)
add_textbox(slide, l2_left_x + Inches(2.8), l2_y + Inches(0.6),
            Inches(0.7), Inches(0.3),
            "No", font_size=11, color=NUS_ORANGE, bold=True)

# Arrows left
add_textbox(slide, l2_left_x + Inches(0.3), l2_y + Inches(0.7),
            Inches(0.5), Inches(0.5),
            "\\", font_size=18, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)
add_textbox(slide, l2_left_x + Inches(2.2), l2_y + Inches(0.7),
            Inches(0.5), Inches(0.5),
            "/", font_size=18, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

# Yes/No for right branch
add_textbox(slide, l2_right_x - Inches(0.5), l2_y + Inches(0.6),
            Inches(0.7), Inches(0.3),
            "Yes", font_size=11, color=ACCENT_GREEN, bold=True)
add_textbox(slide, l2_right_x + Inches(2.8), l2_y + Inches(0.6),
            Inches(0.7), Inches(0.3),
            "No", font_size=11, color=NUS_ORANGE, bold=True)

# Arrows right
add_textbox(slide, l2_right_x + Inches(0.3), l2_y + Inches(0.7),
            Inches(0.5), Inches(0.5),
            "\\", font_size=18, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)
add_textbox(slide, l2_right_x + Inches(2.2), l2_y + Inches(0.7),
            Inches(0.5), Inches(0.5),
            "/", font_size=18, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

# Leaf nodes
leaf_y = tree_top + Inches(2.7)
leaf_h = Inches(0.55)

add_rounded_rect(slide, Inches(1.3), leaf_y, Inches(2.2), leaf_h,
                 ACCENT_GREEN, "git_operations", font_size=13,
                 font_color=WHITE, bold=True)
add_rounded_rect(slide, Inches(3.8), leaf_y, Inches(2.2), leaf_h,
                 NUS_ORANGE, "debugging", font_size=13,
                 font_color=WHITE, bold=True)
add_rounded_rect(slide, Inches(7.2), leaf_y, Inches(2.2), leaf_h,
                 TIER1_COLOR, "coding_editing", font_size=13,
                 font_color=WHITE, bold=True)
add_rounded_rect(slide, Inches(10.2), leaf_y, Inches(2.2), leaf_h,
                 SUBTLE_GRAY, "other", font_size=13,
                 font_color=WHITE, bold=True)

# Explanation text
add_textbox(slide, Inches(1.3), Inches(4.5), Inches(11.5), Inches(0.5),
            "Each internal node tests one feature. Follow the branches "
            "until reaching a leaf node (the prediction).",
            font_size=14, color=NUS_ORANGE)

# Strengths / Weaknesses
add_strengths_weaknesses(
    slide, Inches(1.3), Inches(5.2),
    strengths=[
        "Interpretable  --  can visualize the decision path",
        "Fast inference (2ms latency), no feature scaling needed",
    ],
    weaknesses=[
        "Overfits easily to training data",
        "Unstable  --  small data changes produce a different tree",
    ],
    width=Inches(5.2),
)


# ============================================================
# SLIDE 6: Random Forest
# ============================================================
slide = add_content_slide(prs, "Random Forest",
                          "Builds 100 decision trees, each on a random subset of data. "
                          "Takes majority vote.")

# Individual trees
tree_y = Inches(1.3)
tree_data = [
    ("Tree 1", "git_ops", TIER1_COLOR),
    ("Tree 2", "git_ops", TIER1_COLOR),
    ("Tree 3", "coding", NUS_ORANGE),
    ("Tree 4", "git_ops", TIER1_COLOR),
    ("Tree 5", "git_ops", TIER1_COLOR),
]

x_t = Inches(1.3)
for name, pred, clr in tree_data:
    add_rounded_rect(slide, x_t, tree_y, Inches(1.8), Inches(1.6), DARK_CARD)
    add_textbox(slide, x_t, tree_y + Inches(0.05), Inches(1.8), Inches(0.3),
                name, font_size=12, color=NUS_ORANGE, bold=True,
                alignment=PP_ALIGN.CENTER)
    add_diamond(slide, x_t + Inches(0.55), tree_y + Inches(0.35),
                Inches(0.7), Inches(0.35), SUBTLE_GRAY)
    add_rect(slide, x_t + Inches(0.3), tree_y + Inches(0.75),
             Inches(0.45), Inches(0.25), LIGHT_GRAY)
    add_rect(slide, x_t + Inches(1.05), tree_y + Inches(0.75),
             Inches(0.45), Inches(0.25), LIGHT_GRAY)
    add_rounded_rect(slide, x_t + Inches(0.15), tree_y + Inches(1.15),
                     Inches(1.5), Inches(0.35), clr,
                     pred, font_size=11, font_color=WHITE, bold=True)
    x_t += Inches(2.0)

# "..." for remaining trees
add_textbox(slide, x_t + Inches(0.1), tree_y + Inches(0.6),
            Inches(0.6), Inches(0.5),
            "...", font_size=30, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

# Arrows to vote
add_textbox(slide, Inches(1.3), tree_y + Inches(1.7), Inches(11), Inches(0.5),
            "v                v                v                "
            "v                v",
            font_size=18, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

# Majority vote box
vote_y = tree_y + Inches(2.2)
add_rounded_rect(slide, Inches(2.5), vote_y, Inches(8), Inches(0.7),
                 ACCENT_GREEN)
add_textbox(slide, Inches(2.5), vote_y + Inches(0.05), Inches(8),
            Inches(0.6),
            "Majority Vote:  git_operations (4/5 = 80%)     "
            "->     Final Prediction: git_ops (87%)",
            font_size=15, color=WHITE, bold=True,
            alignment=PP_ALIGN.CENTER)

# Key insight
add_textbox(slide, Inches(1.3), Inches(4.3), Inches(11.5), Inches(0.5),
            "Each tree sees different features and different data samples "
            "(bootstrap aggregating = bagging)",
            font_size=15, color=NUS_ORANGE, bold=True)

# Strengths / Weaknesses
add_strengths_weaknesses(
    slide, Inches(1.3), Inches(5.1),
    strengths=[
        "Robust  --  averaging reduces overfitting",
        "Good accuracy (58.7%), handles noisy data",
    ],
    weaknesses=[
        "Slower than single tree (103ms latency)",
        "Less interpretable  --  100 trees are hard to visualize",
    ],
    width=Inches(5.2),
)


# ============================================================
# SLIDE 7: KNN (K-Nearest Neighbors)
# ============================================================
slide = add_content_slide(prs, "KNN (K-Nearest Neighbors)",
                          "Finds the K most similar training examples and takes a vote")

# Visualization area
viz_left = Inches(1.3)
viz_top = Inches(1.3)
viz_w = Inches(5.5)
viz_h = Inches(3.5)
add_rounded_rect(slide, viz_left, viz_top, viz_w, viz_h, DARK_CARD)
add_textbox(slide, viz_left + Inches(0.2), viz_top + Inches(0.1),
            Inches(4), Inches(0.3),
            "K=5 Nearest Neighbors", font_size=11, color=LIGHT_GRAY)

# Stored points - git_ops cluster (blue)
git_points = [
    (1.0, 1.0), (1.3, 1.5), (0.8, 1.8), (1.5, 0.7), (1.2, 2.0),
    (0.5, 1.3), (1.7, 1.2), (0.9, 0.5),
]
for px, py in git_points:
    add_oval(slide, viz_left + Inches(px), viz_top + Inches(py * 0.9 + 0.4),
             Inches(0.2), Inches(0.2), TIER1_COLOR)

# Stored points - coding cluster (orange)
coding_points = [
    (3.5, 0.5), (4.0, 1.0), (3.8, 1.5), (4.2, 0.3), (3.3, 0.8),
    (4.5, 1.2), (3.7, 1.8), (4.0, 2.0),
]
for px, py in coding_points:
    add_oval(slide, viz_left + Inches(px), viz_top + Inches(py * 0.9 + 0.4),
             Inches(0.2), Inches(0.2), NUS_ORANGE)

# New point with neighborhood circle
new_x = viz_left + Inches(1.8)
new_y = viz_top + Inches(1.5)
add_oval(slide, new_x - Inches(0.7), new_y - Inches(0.7),
         Inches(2.2), Inches(2.2),
         RGBColor(0x33, 0x55, 0x77))
# Neighbor git points inside
neighbor_git = [(1.3, 1.5), (1.5, 0.7), (1.2, 2.0), (1.7, 1.2)]
for px, py in neighbor_git:
    add_oval(slide, viz_left + Inches(px), viz_top + Inches(py * 0.9 + 0.4),
             Inches(0.22), Inches(0.22), TIER1_COLOR)
# 1 coding neighbor inside
add_oval(slide, viz_left + Inches(3.3), viz_top + Inches(0.8 * 0.9 + 0.4),
         Inches(0.22), Inches(0.22), NUS_ORANGE)

# New point (green, prominent)
add_oval(slide, new_x, new_y, Inches(0.28), Inches(0.28),
         ACCENT_GREEN, "?", font_size=10, font_color=WHITE, bold=True)

# Legend
add_oval(slide, viz_left + Inches(3.2), viz_top + Inches(3.1),
         Inches(0.18), Inches(0.18), TIER1_COLOR)
add_textbox(slide, viz_left + Inches(3.45), viz_top + Inches(3.1),
            Inches(0.8), Inches(0.2), "git_ops", font_size=9, color=NUS_ORANGE)
add_oval(slide, viz_left + Inches(4.1), viz_top + Inches(3.1),
         Inches(0.18), Inches(0.18), NUS_ORANGE)
add_textbox(slide, viz_left + Inches(4.35), viz_top + Inches(3.1),
            Inches(0.8), Inches(0.2), "coding", font_size=9, color=NUS_ORANGE)
add_oval(slide, viz_left + Inches(4.9), viz_top + Inches(3.1),
         Inches(0.18), Inches(0.18), ACCENT_GREEN)
add_textbox(slide, viz_left + Inches(5.15), viz_top + Inches(3.08),
            Inches(0.5), Inches(0.2), "new", font_size=9, color=NUS_ORANGE)

# Right side: step-by-step
step_left = Inches(7.3)
step_top = Inches(1.3)
add_rounded_rect(slide, step_left, step_top, Inches(5.5), Inches(3.0),
                 DARK_CARD)
add_textbox(slide, step_left + Inches(0.2), step_top + Inches(0.1),
            Inches(5), Inches(0.3),
            "How KNN classifies a new sample:", font_size=14,
            color=NUS_ORANGE, bold=True)

steps = [
    ("1", "Compute distance to every training sample", TIER1_COLOR),
    ("2", "Select K=5 nearest neighbors", ACCENT_PURPLE),
    ("3", "Count votes:  4 git_ops  +  1 coding", ACCENT_GREEN),
    ("4", 'Predict: "git_operations" (80%)', ACCENT_GREEN),
]
y_s = step_top + Inches(0.5)
for num, txt, clr in steps:
    add_rounded_rect(slide, step_left + Inches(0.2), y_s,
                     Inches(0.4), Inches(0.4), clr,
                     num, font_size=14, font_color=WHITE, bold=True)
    add_textbox(slide, step_left + Inches(0.75), y_s + Inches(0.05),
                Inches(4.5), Inches(0.35), txt, font_size=13, color=NUS_ORANGE)
    y_s += Inches(0.55)

# Key insight
add_textbox(slide, step_left + Inches(0.2), y_s + Inches(0.15),
            Inches(5.1), Inches(0.35),
            "No training needed  --  compares against all stored\n"
            "examples at prediction time (lazy learner)",
            font_size=12, color=LIGHT_GRAY)

# Strengths / Weaknesses
add_strengths_weaknesses(
    slide, Inches(1.3), Inches(5.2),
    strengths=[
        "Simple, no training phase, adapts to any data shape",
        "Non-parametric  --  no assumptions about data distribution",
    ],
    weaknesses=[
        "Slow prediction (344ms)  --  compares every stored sample",
        "Sensitive to irrelevant features and curse of dimensionality",
    ],
    width=Inches(5.2),
)


# ============================================================
# SLIDE 8: XGBoost
# ============================================================
slide = add_content_slide(prs, "XGBoost",
                          "Extreme Gradient Boosting  --  builds trees sequentially, "
                          "each fixing previous errors")

# Sequential improvement diagram
boost_y = Inches(1.3)
stages = [
    ("Tree 1", "60%", NUS_ORANGE),
    ("Tree 2\nfixes 20%", "80%", RGBColor(0xCC, 0x99, 0x00)),
    ("Tree 3\nfixes 10%", "90%", RGBColor(0x66, 0xBB, 0x33)),
    ("Tree 4\nfixes 3%", "93%", ACCENT_GREEN),
]

x_b = Inches(1.3)
for i, (name, acc, clr) in enumerate(stages):
    add_rounded_rect(slide, x_b, boost_y, Inches(2.5), Inches(1.4), DARK_CARD)
    add_textbox(slide, x_b, boost_y + Inches(0.05), Inches(2.5), Inches(0.5),
                name, font_size=13, color=NUS_ORANGE, bold=True,
                alignment=PP_ALIGN.CENTER)

    bar_y = boost_y + Inches(0.7)
    add_rounded_rect(slide, x_b + Inches(0.2), bar_y,
                     Inches(2.1), Inches(0.3),
                     RGBColor(0x33, 0x55, 0x77))
    fill_w = Inches(2.1 * int(acc.rstrip('%')) / 100)
    add_rounded_rect(slide, x_b + Inches(0.2), bar_y, fill_w, Inches(0.3),
                     clr, acc, font_size=10, font_color=WHITE, bold=True)

    add_textbox(slide, x_b, boost_y + Inches(1.05), Inches(2.5), Inches(0.25),
                "accuracy", font_size=9, color=LIGHT_GRAY,
                alignment=PP_ALIGN.CENTER)

    if i < len(stages) - 1:
        add_textbox(slide, x_b + Inches(2.5), boost_y + Inches(0.4),
                    Inches(0.5), Inches(0.5),
                    "->", font_size=24, color=NUS_ORANGE,
                    alignment=PP_ALIGN.CENTER)
    x_b += Inches(3.0)

add_textbox(slide, Inches(1.3), boost_y + Inches(1.5), Inches(12), Inches(0.4),
            "^ Each new tree focuses on the errors of all previous trees "
            "(gradient descent on the loss function)",
            font_size=13, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

# Key features in cards
feat_y = Inches(3.4)
features = [
    ("Regularization", "L1 & L2 penalties prevent\noverfitting", TIER1_COLOR),
    ("Column Sampling", "Each tree uses random\nsubset of features",
     ACCENT_PURPLE),
    ("Gradient Descent", "Minimizes prediction\nerrors iteratively",
     NUS_ORANGE),
    ("Tree Pruning", "Removes branches that\ndon't improve accuracy",
     ACCENT_GREEN),
]
x_f = Inches(1.3)
for title, desc, clr in features:
    add_rounded_rect(slide, x_f, feat_y, Inches(2.8), Inches(0.35), clr,
                     title, font_size=12, font_color=WHITE, bold=True)
    add_textbox(slide, x_f + Inches(0.15), feat_y + Inches(0.4),
                Inches(2.6), Inches(0.5), desc, font_size=11, color=NUS_ORANGE)
    x_f += Inches(3.0)

# Strengths / Weaknesses
add_strengths_weaknesses(
    slide, Inches(1.3), Inches(5.1),
    strengths=[
        "Often best accuracy (59.3% in our benchmarks)",
        "Handles imbalanced data, fast inference (59ms)",
    ],
    weaknesses=[
        "Many hyperparameters to tune",
        "Can overfit with too many boosting rounds",
    ],
    width=Inches(5.2),
)


# ============================================================
# SLIDE 9: LightGBM
# ============================================================
slide = add_content_slide(prs, "LightGBM",
                          "Light Gradient Boosting Machine  --  same concept as "
                          "XGBoost but grows trees leaf-wise")

# Comparison: XGBoost vs LightGBM
comp_y = Inches(1.3)

# XGBoost - Level-wise
xgb_left = Inches(1.3)
add_rounded_rect(slide, xgb_left, comp_y, Inches(5.5), Inches(3.2),
                 DARK_CARD)
add_rounded_rect(slide, xgb_left + Inches(0.15), comp_y + Inches(0.1),
                 Inches(3.0), Inches(0.35), NUS_ORANGE,
                 "XGBoost: Level-wise Growth", font_size=12,
                 font_color=WHITE, bold=True)

# Level-wise tree
add_rounded_rect(slide, xgb_left + Inches(2.0), comp_y + Inches(0.6),
                 Inches(1.2), Inches(0.35), NUS_ORANGE,
                 "Root", font_size=10, font_color=WHITE)
add_rounded_rect(slide, xgb_left + Inches(0.8), comp_y + Inches(1.2),
                 Inches(1.2), Inches(0.35), NUS_ORANGE,
                 "L1-Left", font_size=10, font_color=WHITE)
add_rounded_rect(slide, xgb_left + Inches(3.3), comp_y + Inches(1.2),
                 Inches(1.2), Inches(0.35), NUS_ORANGE,
                 "L1-Right", font_size=10, font_color=WHITE)
positions_l2 = [0.2, 1.4, 2.6, 3.9]
for p in positions_l2:
    add_rounded_rect(slide, xgb_left + Inches(p), comp_y + Inches(1.8),
                     Inches(1.1), Inches(0.35), NUS_ORANGE,
                     "L2", font_size=9, font_color=WHITE)

add_textbox(slide, xgb_left + Inches(1.5), comp_y + Inches(0.9),
            Inches(0.5), Inches(0.3), "\\", font_size=14, color=LIGHT_GRAY,
            alignment=PP_ALIGN.CENTER)
add_textbox(slide, xgb_left + Inches(3.2), comp_y + Inches(0.9),
            Inches(0.5), Inches(0.3), "/", font_size=14, color=LIGHT_GRAY,
            alignment=PP_ALIGN.CENTER)

add_textbox(slide, xgb_left + Inches(0.15), comp_y + Inches(2.3),
            Inches(5.2), Inches(0.7),
            "Expands ALL nodes at each level before going deeper.\n"
            "Balanced tree  --  thorough but slower.",
            font_size=12, color=NUS_ORANGE)

# LightGBM - Leaf-wise
lgb_left = Inches(7.3)
add_rounded_rect(slide, lgb_left, comp_y, Inches(5.5), Inches(3.2),
                 DARK_CARD)
add_rounded_rect(slide, lgb_left + Inches(0.15), comp_y + Inches(0.1),
                 Inches(3.0), Inches(0.35), ACCENT_GREEN,
                 "LightGBM: Leaf-wise Growth", font_size=12,
                 font_color=WHITE, bold=True)

add_rounded_rect(slide, lgb_left + Inches(2.0), comp_y + Inches(0.6),
                 Inches(1.2), Inches(0.35), ACCENT_GREEN,
                 "Root", font_size=10, font_color=WHITE)
add_rounded_rect(slide, lgb_left + Inches(0.8), comp_y + Inches(1.2),
                 Inches(1.2), Inches(0.35), ACCENT_GREEN,
                 "L1-Left", font_size=10, font_color=WHITE)
add_rounded_rect(slide, lgb_left + Inches(3.3), comp_y + Inches(1.2),
                 Inches(1.2), Inches(0.35), SUBTLE_GRAY,
                 "Leaf", font_size=10, font_color=WHITE)
add_rounded_rect(slide, lgb_left + Inches(0.2), comp_y + Inches(1.8),
                 Inches(1.1), Inches(0.35), ACCENT_GREEN,
                 "L2", font_size=9, font_color=WHITE)
add_rounded_rect(slide, lgb_left + Inches(1.5), comp_y + Inches(1.8),
                 Inches(1.1), Inches(0.35), SUBTLE_GRAY,
                 "Leaf", font_size=9, font_color=WHITE)

add_textbox(slide, lgb_left + Inches(1.5), comp_y + Inches(0.9),
            Inches(0.5), Inches(0.3), "\\", font_size=14, color=LIGHT_GRAY,
            alignment=PP_ALIGN.CENTER)
add_textbox(slide, lgb_left + Inches(3.2), comp_y + Inches(0.9),
            Inches(0.5), Inches(0.3), "/", font_size=14, color=LIGHT_GRAY,
            alignment=PP_ALIGN.CENTER)

add_textbox(slide, lgb_left + Inches(0.15), comp_y + Inches(2.3),
            Inches(5.2), Inches(0.7),
            "Only expands the leaf with HIGHEST LOSS.\n"
            "Deeper on one side  --  faster convergence, lower memory.",
            font_size=12, color=NUS_ORANGE)

# Summary bar
add_rounded_rect(slide, Inches(3.0), comp_y + Inches(3.4), Inches(7.3),
                 Inches(0.45), DARK_CARD,
                 "Faster training  *  Lower memory  *  Similar accuracy",
                 font_size=15, font_color=TIER1_COLOR, bold=True)

# Strengths / Weaknesses
add_strengths_weaknesses(
    slide, Inches(1.3), Inches(5.2),
    strengths=[
        "Fastest training among boosting methods",
        "Handles categorical features natively",
    ],
    weaknesses=[
        "Can overfit on small datasets",
        "Leaf-wise growth may miss patterns in balanced data",
    ],
    width=Inches(5.2),
)


# ============================================================
# SLIDE 10: Tier 1 Comparison Table
# ============================================================
slide = add_content_slide(prs, "Tier 1 Comparison",
                          "All 7 classical ML models benchmarked on CUA-Suite dataset")

# Results table
table_top = Inches(1.3)
col_widths = [Inches(2.2), Inches(1.8), Inches(1.8), Inches(1.8),
              Inches(2.2), Inches(2.2)]
headers = ["Model", "Accuracy", "F1 Macro", "Latency", "Training Time", "Note"]
row_h = Inches(0.45)

# Header row
x = Inches(1.3)
for hdr, w in zip(headers, col_widths):
    add_rect(slide, x, table_top, w - Inches(0.03), row_h,
             TIER1_COLOR, hdr, font_size=13, font_color=WHITE, bold=True)
    x += w

# Data rows
model_data = [
    ("XGBoost", "59.3%", "0.397", "59 ms", "2.1 sec",
     "Best accuracy", True),
    ("Random Forest", "58.7%", "0.389", "103 ms", "1.8 sec",
     "Most robust", False),
    ("LightGBM", "58.5%", "0.385", "45 ms", "0.9 sec",
     "Fastest training", False),
    ("Decision Tree", "50.2%", "0.321", "2 ms", "0.3 sec",
     "Fastest inference", False),
    ("KNN", "48.9%", "0.298", "344 ms", "0.0 sec",
     "No training", False),
    ("SVM", "47.1%", "0.271", "5617 ms", "12.4 sec",
     "Slowest", False),
    ("Naive Bayes", "35.8%", "0.198", "16 ms", "0.1 sec",
     "Simplest", False),
]

GOLD_HIGHLIGHT = RGBColor(0x33, 0x55, 0x00)
EVEN_ROW = DARK_CARD
ODD_ROW = RGBColor(0x00, 0x33, 0x66)

for row_idx, (name, acc, f1, lat, train_t, note, highlight) in enumerate(model_data):
    y = table_top + (row_idx + 1) * row_h
    bg = GOLD_HIGHLIGHT if highlight else (EVEN_ROW if row_idx % 2 == 0 else ODD_ROW)
    vals = [name, acc, f1, lat, train_t, note]
    x = Inches(1.3)
    for col_idx, (val, w) in enumerate(zip(vals, col_widths)):
        add_rect(slide, x, y, w - Inches(0.03), row_h, bg,
                 val, font_size=12,
                 font_color=NUS_ORANGE,
                 bold=(col_idx == 0 or highlight))
        x += w

# Annotations
add_rounded_rect(slide, Inches(1.3), table_top + Inches(4.1),
                 Inches(0.3), Inches(0.3), ACCENT_GREEN,
                 "*", font_size=14, font_color=WHITE)
add_textbox(slide, Inches(1.7), table_top + Inches(4.1), Inches(4), Inches(0.3),
            "XGBoost = best overall accuracy among Tier 1 models",
            font_size=12, color=ACCENT_GREEN, bold=True)

add_rounded_rect(slide, Inches(6.3), table_top + Inches(4.1),
                 Inches(0.3), Inches(0.3), TIER1_COLOR,
                 "!", font_size=14, font_color=WHITE)
add_textbox(slide, Inches(6.7), table_top + Inches(4.1), Inches(4), Inches(0.3),
            "Decision Tree = fastest inference (2ms latency)",
            font_size=12, color=TIER1_COLOR, bold=True)

# Key takeaway
add_textbox(slide, Inches(1.3), Inches(6.0), Inches(11.5), Inches(0.5),
            "Key Takeaway:  Boosting methods (XGBoost, LightGBM, Random Forest) "
            "consistently outperform individual models.  "
            "Trade-off between accuracy and latency depends on deployment needs.",
            font_size=14, color=NUS_ORANGE, bold=True,
            alignment=PP_ALIGN.CENTER)


# ============================================================
# SAVE
# ============================================================
out_path = "/Users/muneeswaranm/Projects/PRS/PatternRecognSystem-Video2Text/presentation/Video2Knowledge_Tier1_ClassicalML.pptx"
prs.save(out_path)
print(f"Saved: {out_path}")
print(f"Slides: {len(prs.slides)}")
