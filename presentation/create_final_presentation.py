"""Generate Video2Knowledge Final Presentation (15 slides) — NUS ISS template."""
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
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

prs = create_presentation()


# ── Local helpers (not in template) ──────────────────────────────────────────

def add_rounded_rect_multi(slide, left, top, width, height, fill_color, lines,
                           font_size=14, font_color=WHITE, bold=False,
                           alignment=PP_ALIGN.LEFT, line_spacing=Pt(4)):
    """Rounded rectangle with multiple text paragraphs."""
    shape = slide.shapes.add_shape(5, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    shape.line.fill.background()
    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.15)
    tf.margin_right = Inches(0.15)
    tf.margin_top = Inches(0.1)
    tf.margin_bottom = Inches(0.1)
    for i, line_info in enumerate(lines):
        if isinstance(line_info, str):
            text, sz, clr, b = line_info, font_size, font_color, bold
        else:
            text = line_info.get("text", "")
            sz = line_info.get("size", font_size)
            clr = line_info.get("color", font_color)
            b = line_info.get("bold", bold)
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = text
        p.font.size = Pt(sz)
        p.font.color.rgb = clr
        p.font.bold = b
        p.font.name = "Calibri"
        p.alignment = alignment
        p.space_after = line_spacing
    return shape


def add_chevron_arrow(slide, left, top, width, height, color=ACCENT_BLUE):
    """Add a simple right-pointing triangle as arrow."""
    shape = slide.shapes.add_shape(55, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    return shape


def add_oval(slide, left, top, width, height, fill_color, text="",
             font_size=14, font_color=WHITE, bold=True):
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
        tf.paragraphs[0].font.name = "Calibri"
    return shape


# ── SLIDE 1: Title ────────────────────────────────────────────────────────────

add_title_slide(
    prs,
    title="Video2Knowledge",
    subtitle="A Multimodal Pattern Recognition Framework for\n"
             "Screen Activity Understanding and Knowledge Extraction",
    author="[Team Member 1]  |  [Team Member 2]  |  [Team Member 3]  |  [Team Member 4]",
    affiliation="NUS ISS  —  Pattern Recognition Systems  —  September 2026",
)


# ── SLIDE 2: Background ──────────────────────────────────────────────────────

slide = add_content_slide(prs, "Background",
    "Privileged users have deleted core systems, on purpose and by mistake")

# Left big card - Singapore case
add_rounded_rect_multi(slide, Inches(1.3), Inches(1.3), Inches(4.2), Inches(3.5),
                       DARK_CARD, [
    {"text": "S$918,000", "size": 36, "color": ACCENT_RED, "bold": True},
    {"text": "loss after a dismissed system administrator", "size": 14, "color": WHITE},
    {"text": "deleted 180 virtual servers", "size": 16, "color": ACCENT_RED, "bold": True},
    {"text": "at a Singapore IT firm (2023)", "size": 14, "color": WHITE},
    {"text": "", "size": 8, "color": WHITE},
    {"text": "Sentenced to 2 years 8 months in jail", "size": 14, "color": LIGHT_GRAY},
], alignment=PP_ALIGN.CENTER, line_spacing=Pt(4))

# Right side: 3 case cards
case_left = Inches(5.8)
case_width = Inches(6.733)

# Case 1: Intentional Singapore
add_rounded_rect_multi(slide, case_left, Inches(1.3), case_width, Inches(1.0),
                       DARK_CARD, [
    {"text": "INTENTIONAL  |  SINGAPORE, 2023", "size": 10, "color": ACCENT_RED, "bold": True},
    {"text": "A fired admin whose access was never revoked ran a script to delete all 180 servers of a test system, one by one.",
     "size": 13, "color": WHITE},
], line_spacing=Pt(3))

# Case 2: Intentional USA
add_rounded_rect_multi(slide, case_left, Inches(2.45), case_width, Inches(1.0),
                       DARK_CARD, [
    {"text": "INTENTIONAL  |  UNITED STATES", "size": 10, "color": ACCENT_RED, "bold": True},
    {"text": "A former worker deleted critical boot files on company servers, crippling operations for two weeks and forcing paper records.",
     "size": 13, "color": WHITE},
], line_spacing=Pt(3))

# Case 3: Accidental
add_rounded_rect_multi(slide, case_left, Inches(3.6), case_width, Inches(1.0),
                       DARK_CARD, [
    {"text": "ACCIDENTAL  |  EVERYWHERE", "size": 10, "color": NUS_ORANGE, "bold": True},
    {"text": "Well-meaning admins also run destructive commands on the wrong server. Different intent, same damage.",
     "size": 13, "color": WHITE},
], line_spacing=Pt(3))

# Bottom bold statement
add_rounded_rect(slide, Inches(1.3), Inches(5.0), Inches(11.233), Inches(0.9),
                 RGBColor(0x00, 0x2A, 0x55),
                 "Why this project: admin sessions can be recorded, but no one can review hours of video for risky actions.",
                 font_size=16, font_color=WHITE, bold=True)

# Sources
add_textbox(slide, Inches(1.3), Inches(6.2), Inches(11.233), Inches(0.5),
            "Sources: CNA, The Straits Times, US DOJ public records",
            font_size=10, color=LIGHT_GRAY)


# ── SLIDE 3: Problem Statement ───────────────────────────────────────────────

slide = add_content_slide(prs, "Problem Statement")

add_textbox(slide, Inches(1.3), Inches(1.3), Inches(11.233), Inches(0.8),
            "Users with privileged access can accidentally or knowingly delete core Windows and Linux\n"
            "files and trigger security incidents, and these actions are usually found only after the damage is done.",
            font_size=15, color=LIGHT_GRAY)

# 4 connected boxes
box_w = Inches(2.4)
box_h = Inches(2.5)
arrow_w = Inches(0.35)
start_x = Inches(1.0)
gap = Inches(0.35)

boxes = [
    ("1", "Privileged action",
     "An admin works on a Windows or Linux server; the session is screen-recorded.",
     DARK_CARD, WHITE),
    ("2", "Risky action",
     "Core files are deleted, services stopped or settings changed.",
     DARK_CARD, WHITE),
    ("3", "Damage",
     "Outage, data loss and recovery cost.",
     DARK_CARD, WHITE),
    ("4", "Found too late",
     "Reviewers must watch hours of video by hand, if they look at all.",
     ACCENT_RED, WHITE),
]

for i, (num, title, desc, bg_color, txt_color) in enumerate(boxes):
    x = start_x + i * (box_w + gap + arrow_w)

    add_rounded_rect_multi(slide, x, Inches(2.2), box_w, box_h, bg_color, [
        {"text": num, "size": 28, "color": txt_color, "bold": True},
        {"text": title, "size": 18, "color": txt_color, "bold": True},
        {"text": "", "size": 6, "color": txt_color},
        {"text": desc, "size": 13, "color": LIGHT_GRAY if bg_color != ACCENT_RED else WHITE},
    ], alignment=PP_ALIGN.CENTER, line_spacing=Pt(4))

    # Arrow between boxes (except after last)
    if i < 3:
        arrow_x = x + box_w + Inches(0.05)
        add_chevron_arrow(slide, arrow_x, Inches(3.2), arrow_w, Inches(0.5),
                          color=RGBColor(0x44, 0x55, 0x77))

# Bottom: two intents
add_rounded_rect_multi(slide, Inches(3.0), Inches(5.2), Inches(7.333), Inches(0.7),
                       RGBColor(0x00, 0x2A, 0x55), [
    {"text": "Two intents, one outcome:    Accidental   |   Deliberate",
     "size": 18, "color": WHITE, "bold": True},
], alignment=PP_ALIGN.CENTER)


# ── SLIDE 4: Objective ───────────────────────────────────────────────────────

slide = add_content_slide(prs, "Objective")

add_textbox(slide, Inches(1.3), Inches(1.3), Inches(11.233), Inches(0.8),
            "Automatically understand what was done in server screen recordings,\n"
            "so risky actions can be caught early and incidents prevented at scale.",
            font_size=16, color=LIGHT_GRAY)

# 3 columns with red numbered circles
col_w = Inches(3.4)
col_gap = Inches(0.35)
col_start = Inches(1.3)

objectives = [
    ("1", "Identify",
     "Analyse recorded sessions with a tiered pipeline (frame features, sequence model, classifier) to recognise which action was performed."),
    ("2", "Explain",
     "Generate a plain-language summary of the actions so reviewers do not have to watch the full video."),
    ("3", "Prevent",
     "Flag high-risk actions such as deleting core files early, across many admins and organisations, not only after an incident."),
]

for i, (num, title, desc) in enumerate(objectives):
    x = col_start + i * (col_w + col_gap)

    # Card background
    add_rounded_rect(slide, x, Inches(2.2), col_w, Inches(3.8), DARK_CARD)

    # Red circle with number
    circle_x = x + (col_w - Inches(0.6)) / 2
    add_oval(slide, circle_x, Inches(2.4), Inches(0.6), Inches(0.6),
             ACCENT_RED, num, font_size=20, font_color=WHITE, bold=True)

    # Title
    add_textbox(slide, x + Inches(0.2), Inches(3.1), col_w - Inches(0.4), Inches(0.5),
                title, font_size=24, color=NUS_ORANGE, bold=True,
                alignment=PP_ALIGN.CENTER)

    # Description
    add_textbox(slide, x + Inches(0.25), Inches(3.6), col_w - Inches(0.5), Inches(2.2),
                desc, font_size=14, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

# Bottom scope
add_rounded_rect(slide, Inches(3.0), Inches(6.3), Inches(7.333), Inches(0.6),
                 ACCENT_BLUE,
                 "Scope:  Windows and Linux server administration recordings",
                 font_size=14, font_color=WHITE, bold=True)


# ── SLIDE 5: System Architecture ─────────────────────────────────────────────

slide = add_content_slide(prs, "System Architecture")

# Docker compose wrapper
add_rounded_rect(slide, Inches(1.8), Inches(1.3), Inches(10.2), Inches(5.4),
                 RGBColor(0x00, 0x2A, 0x55))
add_textbox(slide, Inches(2.0), Inches(1.35), Inches(3.0), Inches(0.4),
            "Docker Compose", font_size=12, color=LIGHT_GRAY, bold=True)

# User icon
add_rounded_rect(slide, Inches(0.5), Inches(3.2), Inches(1.1), Inches(0.8),
                 ACCENT_BLUE, "User\nUploads Video", font_size=11, font_color=WHITE, bold=True)

# Frontend box
add_rounded_rect_multi(slide, Inches(2.1), Inches(1.8), Inches(2.2), Inches(1.4),
                       ACCENT_BLUE, [
    {"text": "Frontend", "size": 16, "color": WHITE, "bold": True},
    {"text": "React + TypeScript", "size": 11, "color": RGBColor(0xCC, 0xDD, 0xFF)},
    {"text": "Vite (port 5173)", "size": 11, "color": RGBColor(0xCC, 0xDD, 0xFF)},
    {"text": "Model Comparison UI", "size": 11, "color": RGBColor(0xCC, 0xDD, 0xFF)},
], alignment=PP_ALIGN.CENTER, line_spacing=Pt(2))

# Arrow: User -> Frontend
add_chevron_arrow(slide, Inches(1.65), Inches(3.4), Inches(0.35), Inches(0.3), ACCENT_BLUE)

# Arrow: Frontend -> Backend
add_textbox(slide, Inches(4.0), Inches(2.0), Inches(1.0), Inches(0.3),
            "POST /api/v1", font_size=9, color=LIGHT_GRAY, bold=True)
add_chevron_arrow(slide, Inches(4.35), Inches(2.3), Inches(0.35), Inches(0.3), ACCENT_BLUE)

# Backend box
backend_x = Inches(4.8)
backend_y = Inches(1.8)
add_rounded_rect(slide, backend_x, backend_y, Inches(4.5), Inches(4.8),
                 RGBColor(0x00, 0x33, 0x66))
add_textbox(slide, backend_x + Inches(0.15), backend_y + Inches(0.1),
            Inches(3.0), Inches(0.4),
            "Backend  (FastAPI, port 8000)", font_size=14, color=NUS_ORANGE, bold=True)

# Sub-components inside backend
add_rounded_rect_multi(slide, backend_x + Inches(0.2), backend_y + Inches(0.6),
                       Inches(4.1), Inches(1.0),
                       ACCENT_BLUE, [
    {"text": "Video Processor", "size": 13, "color": WHITE, "bold": True},
    {"text": "Segment extraction  |  Keyframe extraction", "size": 11, "color": RGBColor(0xCC, 0xDD, 0xFF)},
], alignment=PP_ALIGN.CENTER, line_spacing=Pt(2))

add_rounded_rect_multi(slide, backend_x + Inches(0.2), backend_y + Inches(1.75),
                       Inches(4.1), Inches(1.0),
                       RGBColor(0x00, 0x66, 0xAA), [
    {"text": "Feature Assembler", "size": 13, "color": WHITE, "bold": True},
    {"text": "4 extractors  →  150-dim feature vector", "size": 11, "color": RGBColor(0xCC, 0xDD, 0xFF)},
], alignment=PP_ALIGN.CENTER, line_spacing=Pt(2))

add_rounded_rect_multi(slide, backend_x + Inches(0.2), backend_y + Inches(2.9),
                       Inches(4.1), Inches(1.0),
                       RGBColor(0x00, 0x55, 0x88), [
    {"text": "ML Service", "size": 13, "color": WHITE, "bold": True},
    {"text": "14 models  |  3 tiers  |  Comparison engine", "size": 11, "color": RGBColor(0xCC, 0xDD, 0xFF)},
], alignment=PP_ALIGN.CENTER, line_spacing=Pt(2))

# Down arrows inside backend
add_textbox(slide, backend_x + Inches(1.8), backend_y + Inches(1.55),
            Inches(0.5), Inches(0.3), "▼", font_size=16, color=ACCENT_BLUE,
            alignment=PP_ALIGN.CENTER)
add_textbox(slide, backend_x + Inches(1.8), backend_y + Inches(2.65),
            Inches(0.5), Inches(0.3), "▼", font_size=16, color=ACCENT_BLUE,
            alignment=PP_ALIGN.CENTER)

# Database box
db_x = Inches(9.8)
add_rounded_rect_multi(slide, db_x, Inches(2.5), Inches(2.3), Inches(1.8),
                       ACCENT_GREEN, [
    {"text": "Database", "size": 16, "color": WHITE, "bold": True},
    {"text": "PostgreSQL 16", "size": 12, "color": RGBColor(0xCC, 0xFF, 0xDD)},
    {"text": "+ pgvector", "size": 12, "color": RGBColor(0xCC, 0xFF, 0xDD)},
    {"text": "port 5434", "size": 11, "color": RGBColor(0xCC, 0xFF, 0xDD)},
], alignment=PP_ALIGN.CENTER, line_spacing=Pt(2))

# Arrow: Backend -> DB
add_chevron_arrow(slide, Inches(9.4), Inches(3.2), Inches(0.35), Inches(0.3), ACCENT_GREEN)

# Results return arrow (bottom)
add_textbox(slide, Inches(2.8), Inches(5.5), Inches(2.5), Inches(0.3),
            "◀  Results returned  ◀", font_size=11, color=LIGHT_GRAY,
            alignment=PP_ALIGN.CENTER, bold=True)

# Frontend results display
add_rounded_rect_multi(slide, Inches(2.1), Inches(4.8), Inches(2.2), Inches(1.0),
                       RGBColor(0x00, 0x66, 0xAA), [
    {"text": "Results Display", "size": 13, "color": WHITE, "bold": True},
    {"text": "Model comparison +", "size": 11, "color": RGBColor(0xCC, 0xDD, 0xFF)},
    {"text": "Workflow steps", "size": 11, "color": RGBColor(0xCC, 0xDD, 0xFF)},
], alignment=PP_ALIGN.CENTER, line_spacing=Pt(2))


# ── SLIDE 6: Pipeline Detail ─────────────────────────────────────────────────

slide = add_content_slide(prs, "Multimodal Feature Extraction Pipeline")

# Video Input
add_rounded_rect(slide, Inches(0.5), Inches(1.5), Inches(1.5), Inches(0.8),
                 RGBColor(0x00, 0x2A, 0x55), "Video Input", font_size=14, font_color=WHITE, bold=True)

# Arrow
add_chevron_arrow(slide, Inches(2.05), Inches(1.7), Inches(0.3), Inches(0.3), ACCENT_BLUE)

# VideoProcessor
add_rounded_rect(slide, Inches(2.4), Inches(1.5), Inches(1.8), Inches(0.8),
                 ACCENT_BLUE, "VideoProcessor\nSegments + Keyframes",
                 font_size=12, font_color=WHITE, bold=True)

# Arrow
add_chevron_arrow(slide, Inches(4.25), Inches(1.7), Inches(0.3), Inches(0.3), ACCENT_BLUE)

# 4 parallel extractors
extractor_x = Inches(4.7)
extractors = [
    ("EasyOCR (text)", "TF-IDF → 50 dims", ACCENT_BLUE),
    ("YOLOv8 (UI elements)", "counts/layout → 30 dims", ACCENT_GREEN),
    ("OpenCV (visual)", "color/edge/texture → 40 dims", NUS_ORANGE),
    ("Action Parser (behavior)", "freq/temporal → 30 dims", ACCENT_PURPLE),
]

for i, (name, dims, color) in enumerate(extractors):
    y = Inches(1.2) + i * Inches(1.25)
    add_rounded_rect_multi(slide, extractor_x, y, Inches(3.2), Inches(1.0),
                           color, [
        {"text": name, "size": 13, "color": WHITE, "bold": True},
        {"text": dims, "size": 11, "color": RGBColor(0xEE, 0xEE, 0xEE)},
    ], alignment=PP_ALIGN.CENTER, line_spacing=Pt(2))

# Arrows from extractors to concatenate
for i in range(4):
    y = Inches(1.55) + i * Inches(1.25)
    add_chevron_arrow(slide, Inches(7.95), y, Inches(0.3), Inches(0.3), LIGHT_GRAY)

# Concatenate box
add_rounded_rect(slide, Inches(8.35), Inches(2.3), Inches(1.5), Inches(1.2),
                 RGBColor(0x00, 0x2A, 0x55), "Concatenate\n→ 150-dim\nfeature vector",
                 font_size=12, font_color=WHITE, bold=True)

# Arrow
add_chevron_arrow(slide, Inches(9.9), Inches(2.7), Inches(0.3), Inches(0.3), ACCENT_BLUE)

# Classifiers
add_rounded_rect_multi(slide, Inches(10.3), Inches(1.8), Inches(1.5), Inches(1.8),
                       ACCENT_BLUE, [
    {"text": "14", "size": 32, "color": WHITE, "bold": True},
    {"text": "Classifiers", "size": 14, "color": WHITE, "bold": True},
    {"text": "(3 tiers)", "size": 12, "color": RGBColor(0xCC, 0xDD, 0xFF)},
], alignment=PP_ALIGN.CENTER, line_spacing=Pt(2))

# Arrow to output
add_chevron_arrow(slide, Inches(11.85), Inches(2.5), Inches(0.3), Inches(0.3), ACCENT_GREEN)

# Output
add_rounded_rect_multi(slide, Inches(12.2), Inches(2.0), Inches(1.0), Inches(1.5),
                       ACCENT_GREEN, [
    {"text": "Activity", "size": 13, "color": WHITE, "bold": True},
    {"text": "Label", "size": 13, "color": WHITE, "bold": True},
    {"text": "+", "size": 11, "color": WHITE},
    {"text": "Confidence", "size": 12, "color": WHITE, "bold": True},
], alignment=PP_ALIGN.CENTER, line_spacing=Pt(2))

# Bottom: "Each segment" note
add_rounded_rect(slide, Inches(1.3), Inches(5.9), Inches(11.233), Inches(0.6),
                 RGBColor(0x00, 0x2A, 0x55),
                 "Each video segment is independently processed through all 4 extractors in parallel, "
                 "producing a unified 150-dimensional feature vector",
                 font_size=13, font_color=NUS_ORANGE)


# ── SLIDE 7: Classification Models ───────────────────────────────────────────

slide = add_content_slide(prs, "14 Classification Models Across 3 Tiers")

# Tier 1 - Classical ML (Blue)
add_rounded_rect_multi(slide, Inches(0.8), Inches(1.3), Inches(5.5), Inches(2.3),
                       ACCENT_BLUE, [
    {"text": "Tier 1 — Classical ML  (7 models)", "size": 18, "color": WHITE, "bold": True},
], alignment=PP_ALIGN.LEFT, line_spacing=Pt(4))

tier1_models = ["SVM", "Naive Bayes", "Decision Tree", "Random Forest",
                "KNN", "XGBoost", "LightGBM"]
for i, model in enumerate(tier1_models):
    row = i // 4
    col = i % 4
    x = Inches(1.0) + col * Inches(1.35)
    y = Inches(2.0) + row * Inches(0.7)
    add_rounded_rect(slide, x, y, Inches(1.2), Inches(0.5), RGBColor(0x00, 0x2A, 0x55),
                     model, font_size=11, font_color=WHITE, bold=True)

# Tier 2 - Deep Learning (Purple)
add_rounded_rect_multi(slide, Inches(6.8), Inches(1.3), Inches(5.833), Inches(2.3),
                       ACCENT_PURPLE, [
    {"text": "Tier 2 — Deep Learning  (4 models)", "size": 18, "color": WHITE, "bold": True},
], alignment=PP_ALIGN.LEFT, line_spacing=Pt(4))

tier2_models = ["MLP", "CNN-1D", "LSTM", "Transformer"]
for i, model in enumerate(tier2_models):
    x = Inches(7.0) + i * Inches(1.5)
    add_rounded_rect(slide, x, Inches(2.0), Inches(1.3), Inches(0.5), RGBColor(0x00, 0x2A, 0x55),
                     model, font_size=12, font_color=WHITE, bold=True)

# Arrow: Tier 1 + Tier 2 -> Tier 3
add_textbox(slide, Inches(3.0), Inches(3.8), Inches(7.333), Inches(0.4),
            "Tier 1 + Tier 2 predictions feed into ▼",
            font_size=13, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER, bold=True)

# Tier 3 - Ensemble (Green)
add_rounded_rect_multi(slide, Inches(2.5), Inches(4.3), Inches(8.333), Inches(2.0),
                       ACCENT_GREEN, [
    {"text": "Tier 3 — Ensemble  (3 models)", "size": 18, "color": WHITE, "bold": True},
], alignment=PP_ALIGN.LEFT, line_spacing=Pt(4))

tier3_models = ["Voting", "Stacking", "Late Fusion"]
for i, model in enumerate(tier3_models):
    x = Inches(3.5) + i * Inches(2.5)
    add_rounded_rect(slide, x, Inches(5.0), Inches(2.0), Inches(0.6), RGBColor(0x00, 0x2A, 0x55),
                     model, font_size=14, font_color=WHITE, bold=True)

# Bottom note
add_textbox(slide, Inches(1.3), Inches(6.6), Inches(11.233), Inches(0.4),
            "All models run on the same 150-dim feature vector and produce comparable predictions",
            font_size=14, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)


# ── SLIDE 8: Dataset ─────────────────────────────────────────────────────────

slide = add_content_slide(prs, "Training Dataset: CUA-Suite (VideoCUA)")

# Stats row
stats = [
    ("9,514", "Videos"),
    ("87", "Applications"),
    ("9", "Activity Classes"),
    ("~48 GB", "Total Size"),
]
for i, (num, label) in enumerate(stats):
    x = Inches(1.3) + i * Inches(2.9)
    add_rounded_rect_multi(slide, x, Inches(1.3), Inches(2.5), Inches(1.2),
                           DARK_CARD, [
        {"text": num, "size": 36, "color": ACCENT_BLUE, "bold": True},
        {"text": label, "size": 14, "color": LIGHT_GRAY, "bold": True},
    ], alignment=PP_ALIGN.CENTER, line_spacing=Pt(2))

# 9 activity labels as colored tags
add_textbox(slide, Inches(1.3), Inches(2.8), Inches(11.233), Inches(0.4),
            "Activity Classes", font_size=18, color=NUS_ORANGE, bold=True)

labels = [
    "click", "double_click", "drag", "key_press", "scroll",
    "select_text", "type", "wait", "navigate"
]
label_colors = [
    ACCENT_BLUE, ACCENT_GREEN, ACCENT_PURPLE, NUS_ORANGE, ACCENT_RED,
    RGBColor(0x00, 0x99, 0x88), RGBColor(0x88, 0x55, 0xCC),
    RGBColor(0x99, 0x66, 0x00), RGBColor(0x33, 0x66, 0x99),
]
for i, (label, color) in enumerate(zip(labels, label_colors)):
    row = i // 5
    col = i % 5
    x = Inches(1.3) + col * Inches(2.4)
    y = Inches(3.3) + row * Inches(0.6)
    add_rounded_rect(slide, x, y, Inches(2.1), Inches(0.45), color,
                     label, font_size=13, font_color=WHITE, bold=True)

# Train/test split
add_textbox(slide, Inches(1.3), Inches(4.8), Inches(11.233), Inches(0.4),
            "Train / Test Split", font_size=18, color=NUS_ORANGE, bold=True)

# Train bar
train_w = Inches(7.5)
test_w = Inches(2.0)
add_rounded_rect(slide, Inches(1.3), Inches(5.3), train_w, Inches(0.7),
                 ACCENT_BLUE, "Train: 7,685  (80.8%)", font_size=14,
                 font_color=WHITE, bold=True)
add_rounded_rect(slide, Inches(1.3) + train_w + Inches(0.1), Inches(5.3),
                 test_w, Inches(0.7), NUS_ORANGE,
                 "Test: 1,924  (19.2%)", font_size=14,
                 font_color=WHITE, bold=True)

# Source
add_rounded_rect(slide, Inches(1.3), Inches(6.3), Inches(11.233), Inches(0.6),
                 RGBColor(0x00, 0x2A, 0x55),
                 "Source: ServiceNow/VideoCUA on HuggingFace  (MIT License)",
                 font_size=14, font_color=NUS_ORANGE)


# ── SLIDE 9: Training Results ────────────────────────────────────────────────

slide = add_content_slide(prs, "Model Comparison Results")

# Results table
results = [
    ("late_fusion", "tier3", "0.660", "0.292"),
    ("stacking", "tier3", "0.656", "0.277"),
    ("xgboost", "tier1", "0.657", "0.256"),
    ("random_forest", "tier1", "0.678", "0.238"),
    ("lightgbm", "tier1", "0.650", "0.232"),
    ("knn", "tier1", "0.597", "0.225"),
    ("decision_tree", "tier1", "0.596", "0.199"),
    ("transformer", "tier2", "0.623", "0.181"),
    ("voting", "tier3", "0.653", "0.176"),
    ("mlp", "tier2", "0.630", "0.175"),
    ("lstm", "tier2", "0.601", "0.143"),
    ("cnn1d", "tier2", "0.607", "0.124"),
    ("svm", "tier1", "0.605", "0.116"),
    ("naive_bayes", "tier1", "0.023", "0.034"),
]

tier_colors = {"tier1": ACCENT_BLUE, "tier2": ACCENT_PURPLE, "tier3": ACCENT_GREEN}

# Table header
header_y = Inches(0.95)
col_positions = [Inches(1.0), Inches(3.3), Inches(5.8), Inches(7.8), Inches(9.8)]
col_widths = [Inches(2.3), Inches(2.3), Inches(1.8), Inches(1.8), Inches(2.5)]
headers = ["#  Model", "Tier", "Accuracy", "F1 Macro", ""]

add_rect(slide, Inches(0.9), header_y, Inches(11.833), Inches(0.38), NUS_ORANGE)
for j, (pos, w, h_text) in enumerate(zip(col_positions, col_widths, headers)):
    if h_text:
        add_textbox(slide, pos, header_y, w, Inches(0.38),
                    h_text, font_size=12, color=WHITE, bold=True)

# Table rows
for i, (model, tier, acc, f1) in enumerate(results):
    y = Inches(1.38) + i * Inches(0.38)
    bg = RGBColor(0x00, 0x2A, 0x55) if i % 2 == 0 else RGBColor(0x00, 0x33, 0x66)
    add_rect(slide, Inches(0.9), y, Inches(11.833), Inches(0.38), bg)

    # Rank + model name
    add_textbox(slide, col_positions[0], y, col_widths[0], Inches(0.38),
                f"{i+1}.  {model}", font_size=12, color=NUS_ORANGE,
                bold=(i < 3))

    # Tier tag
    tc = tier_colors[tier]
    add_rounded_rect(slide, col_positions[1] + Inches(0.1), y + Inches(0.04),
                     Inches(0.8), Inches(0.3), tc,
                     tier, font_size=10, font_color=WHITE, bold=True)

    # Accuracy
    add_textbox(slide, col_positions[2], y, col_widths[2], Inches(0.38),
                acc, font_size=12, color=NUS_ORANGE)

    # F1 Macro - highlight top 3
    f1_color = ACCENT_GREEN if i < 3 else NUS_ORANGE
    add_textbox(slide, col_positions[3], y, col_widths[3], Inches(0.38),
                f1, font_size=12, color=f1_color, bold=(i < 3))

    # F1 bar
    bar_max = Inches(2.3)
    bar_w = bar_max * float(f1) / 0.3  # scale relative to ~0.3
    if bar_w > bar_max:
        bar_w = bar_max
    bar_color = tier_colors[tier]
    add_rect(slide, col_positions[4], y + Inches(0.08),
             int(bar_w), Inches(0.22), bar_color)

# Key insights
add_rounded_rect_multi(slide, Inches(0.9), Inches(6.75), Inches(11.833), Inches(0.55),
                       RGBColor(0x00, 0x2A, 0x55), [
    {"text": "Key:  Ensembles achieve best F1  |  XGBoost best among classical  |  "
             "DL models did not outperform classical with engineered features",
     "size": 12, "color": NUS_ORANGE, "bold": True},
], alignment=PP_ALIGN.CENTER)


# ── SLIDE 10: Technology Stack ────────────────────────────────────────────────

slide = add_content_slide(prs, "Technology Stack")

tech_cards = [
    ("Backend", ACCENT_BLUE, [
        "Python 3.11", "FastAPI", "PyTorch",
        "scikit-learn", "XGBoost", "LightGBM",
        "OpenCV", "EasyOCR", "YOLOv8",
    ]),
    ("Frontend", ACCENT_GREEN, [
        "React", "TypeScript", "Vite",
    ]),
    ("Infrastructure", ACCENT_PURPLE, [
        "Docker Compose", "PostgreSQL 16 + pgvector",
        "Terraform (IaC)", "AWS EC2 (g4dn.xlarge GPU)",
    ]),
    ("Dev Tools", NUS_ORANGE, [
        "pytest", "ruff", "mypy", "Alembic",
    ]),
]

card_w = Inches(5.5)
card_h = Inches(2.5)
positions = [
    (Inches(1.0), Inches(1.3)),
    (Inches(7.0), Inches(1.3)),
    (Inches(1.0), Inches(4.0)),
    (Inches(7.0), Inches(4.0)),
]

for (title, color, techs), (cx, cy) in zip(tech_cards, positions):
    # Card background
    add_rounded_rect(slide, cx, cy, card_w, card_h, DARK_CARD)

    # Title bar
    add_rounded_rect(slide, cx, cy, card_w, Inches(0.5), color,
                     title, font_size=16, font_color=WHITE, bold=True)

    # Tech tags
    tag_x = cx + Inches(0.15)
    tag_y = cy + Inches(0.65)
    row_x = tag_x
    for tech in techs:
        tag_w = Inches(max(1.2, len(tech) * 0.11 + 0.3))
        if row_x + tag_w > cx + card_w - Inches(0.1):
            row_x = tag_x
            tag_y += Inches(0.5)
        add_rounded_rect(slide, row_x, tag_y, tag_w, Inches(0.4),
                         color, tech, font_size=11, font_color=WHITE, bold=True)
        row_x += tag_w + Inches(0.1)


# ── SLIDE 11: Live Demo ──────────────────────────────────────────────────────

slide = add_section_slide(prs, "Live Demo",
    "Upload a screen recording  →  Watch real-time progress  →  View model comparison")

# Fast vs Full mode cards
add_rounded_rect_multi(slide, Inches(2.0), Inches(4.5), Inches(4.0), Inches(2.0),
                       RGBColor(0x00, 0x2A, 0x55), [
    {"text": "Fast Mode", "size": 28, "color": ACCENT_GREEN, "bold": True},
    {"text": "", "size": 6, "color": WHITE},
    {"text": "9 models  (Tier 1 only)", "size": 16, "color": WHITE, "bold": True},
    {"text": "~30 seconds", "size": 20, "color": ACCENT_GREEN, "bold": True},
], alignment=PP_ALIGN.CENTER, line_spacing=Pt(2))

add_textbox(slide, Inches(6.0), Inches(5.0), Inches(1.333), Inches(0.5),
            "vs", font_size=24, color=LIGHT_GRAY,
            alignment=PP_ALIGN.CENTER, bold=True)

add_rounded_rect_multi(slide, Inches(7.333), Inches(4.5), Inches(4.0), Inches(2.0),
                       RGBColor(0x00, 0x2A, 0x55), [
    {"text": "Full Mode", "size": 28, "color": ACCENT_BLUE, "bold": True},
    {"text": "", "size": 6, "color": WHITE},
    {"text": "14 models  (All 3 tiers)", "size": 16, "color": WHITE, "bold": True},
    {"text": "~5 minutes", "size": 20, "color": ACCENT_BLUE, "bold": True},
], alignment=PP_ALIGN.CENTER, line_spacing=Pt(2))


# ── SLIDE 12: NUS Requirements Coverage ──────────────────────────────────────

slide = add_content_slide(prs, "Practice Module Requirements",
    "All 4 Covered")

requirements = [
    ("✓  Supervised Learning",
     "9,514 labeled videos, 14 trained models",
     ACCENT_BLUE),
    ("✓  ML / Deep Learning",
     "7 classical + 4 neural networks",
     ACCENT_PURPLE),
    ("✓  Hybrid / Ensemble",
     "3 ensemble methods combining Tier 1+2",
     ACCENT_GREEN),
    ("✓  Intelligent Sensing",
     "4 modalities, 150-dim multimodal fusion",
     NUS_ORANGE),
]

req_positions = [
    (Inches(1.0), Inches(1.3)),
    (Inches(7.0), Inches(1.3)),
    (Inches(1.0), Inches(4.0)),
    (Inches(7.0), Inches(4.0)),
]

for (title, desc, accent), (rx, ry) in zip(requirements, req_positions):
    card_w = Inches(5.5)
    card_h = Inches(2.3)
    add_rounded_rect(slide, rx, ry, card_w, card_h, RGBColor(0x00, 0x2A, 0x55))
    # Accent bar on left
    add_rect(slide, rx, ry, Inches(0.08), card_h, accent)
    # Check title
    add_textbox(slide, rx + Inches(0.3), ry + Inches(0.3), card_w - Inches(0.5), Inches(0.5),
                title, font_size=22, color=accent, bold=True)
    # Description
    add_textbox(slide, rx + Inches(0.3), ry + Inches(1.0), card_w - Inches(0.5), Inches(1.0),
                desc, font_size=16, color=NUS_ORANGE)


# ── SLIDE 13: Future Work ────────────────────────────────────────────────────

slide = add_content_slide(prs, "Future Work")

future_items = [
    ("RAG Pipeline",
     "Knowledge extraction from classified segments using retrieval-augmented generation",
     ACCENT_BLUE),
    ("MLflow Integration",
     "Experiment tracking and model versioning for reproducible training",
     ACCENT_GREEN),
    ("GPU-Optimized Inference",
     "Real-time analysis with GPU acceleration for production workloads",
     ACCENT_PURPLE),
    ("VLM Baseline Comparison",
     "Compare GPT-4V, Gemini vision models vs hand-crafted features",
     NUS_ORANGE),
    ("Active Learning",
     "User feedback on misclassifications to improve model accuracy iteratively",
     ACCENT_RED),
]

for i, (title, desc, color) in enumerate(future_items):
    y = Inches(1.3) + i * Inches(1.1)
    # Left color bar
    add_rounded_rect(slide, Inches(1.3), y, Inches(0.08), Inches(0.9), color)
    # Number circle
    add_oval(slide, Inches(1.6), y + Inches(0.15), Inches(0.5), Inches(0.5),
             color, str(i + 1), font_size=16, font_color=WHITE, bold=True)
    # Title + desc
    add_textbox(slide, Inches(2.3), y + Inches(0.05), Inches(10.233), Inches(0.4),
                title, font_size=20, color=NUS_ORANGE, bold=True)
    add_textbox(slide, Inches(2.3), y + Inches(0.45), Inches(10.233), Inches(0.5),
                desc, font_size=14, color=LIGHT_GRAY)


# ── SLIDE 14: Conclusion ─────────────────────────────────────────────────────

slide = add_content_slide(prs, "Conclusion")

conclusions = [
    "Built multimodal feature extraction pipeline (4 modalities → 150-dim vector)",
    "Implemented 14 classification models across 3 tiers with benchmarking",
    "Developed full-stack web application with real-time progress reporting",
    "Trained on CUA-Suite dataset (9,514 videos, 9 activity classes)",
    "Deployed with Docker + AWS infrastructure (Terraform IaC)",
]

for i, text in enumerate(conclusions):
    y = Inches(1.3) + i * Inches(0.95)
    # Green check circle
    add_oval(slide, Inches(1.3), y + Inches(0.05), Inches(0.45), Inches(0.45),
             ACCENT_GREEN, "✓", font_size=18, font_color=WHITE, bold=True)
    # Text
    add_textbox(slide, Inches(2.0), y, Inches(10.533), Inches(0.6),
                text, font_size=18, color=NUS_ORANGE)

# Key numbers bar at bottom
key_numbers = [
    ("150", "Features"),
    ("14", "Models"),
    ("4", "Modalities"),
    ("9", "Classes"),
]
for i, (num, label) in enumerate(key_numbers):
    x = Inches(1.8) + i * Inches(2.8)
    add_rounded_rect_multi(slide, x, Inches(6.0), Inches(2.3), Inches(1.0),
                           ACCENT_BLUE, [
        {"text": num, "size": 32, "color": WHITE, "bold": True},
        {"text": label, "size": 14, "color": RGBColor(0xCC, 0xDD, 0xFF)},
    ], alignment=PP_ALIGN.CENTER, line_spacing=Pt(2))


# ── SLIDE 15: Thank You ──────────────────────────────────────────────────────

slide = add_section_slide(prs, "Thank You", "Questions & Discussion")

add_textbox(slide, Inches(0.5), Inches(4.8), Inches(12.333), Inches(1.0),
            "[Team Member 1]  •  [Team Member 2]  •  [Team Member 3]  •  [Team Member 4]",
            font_size=16, color=LIGHT_GRAY,
            alignment=PP_ALIGN.CENTER)

add_textbox(slide, Inches(0.5), Inches(5.4), Inches(12.333), Inches(0.6),
            "[email1]@u.nus.edu  |  [email2]@u.nus.edu  |  [email3]@u.nus.edu  |  [email4]@u.nus.edu",
            font_size=13, color=LIGHT_GRAY,
            alignment=PP_ALIGN.CENTER)

add_textbox(slide, Inches(0.5), Inches(6.0), Inches(12.333), Inches(0.6),
            "github.com/[org]/Video2Knowledge",
            font_size=14, color=ACCENT_BLUE, alignment=PP_ALIGN.CENTER)

add_textbox(slide, Inches(0.5), Inches(6.5), Inches(12.333), Inches(0.5),
            "NUS ISS  —  Pattern Recognition Systems  —  September 2026",
            font_size=13, color=LIGHT_GRAY,
            alignment=PP_ALIGN.CENTER)


# ── Save ──────────────────────────────────────────────────────────────────────

output_path = "/Users/muneeswaranm/Projects/PRS/PatternRecognSystem-Video2Text/presentation/Video2Knowledge_Final.pptx"
prs.save(output_path)
print(f"Presentation saved to: {output_path}")
print(f"Total slides: {len(prs.slides)}")
