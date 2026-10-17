"""
Generate Video2Knowledge System Architecture presentation (NUS ISS template).

Creates a comprehensive 9-slide architecture deck covering:
  1. Title
  2. C4 Context Diagram
  3. Container (Docker) Architecture
  4. Backend Component Architecture
  5. Feature Extraction Pipeline
  6. 3-Tier Classification Architecture
  7. End-to-End Data Flow
  8. Training Architecture
  9. Deployment Architecture
"""

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

# ── Local accent variants (not in template) ─────────────────────────────────

DARK_BLUE = RGBColor(0x00, 0x56, 0x99)
DARK_ORANGE = RGBColor(0xC4, 0x63, 0x00)
DARK_GREEN = RGBColor(0x1E, 0x7B, 0x34)
DARK_PURPLE = RGBColor(0x57, 0x33, 0x9A)

OCR_COLOR = ACCENT_BLUE
UI_COLOR = NUS_ORANGE
VISUAL_COLOR = ACCENT_PURPLE
INTERACTION_COLOR = ACCENT_GREEN


# ── Architecture-specific helpers (not provided by template) ─────────────────

def add_outlined_rect(slide, left, top, width, height, line_color,
                      fill_color=None, line_width=Pt(2)):
    """Add a rectangle with a colored border (outline), optional fill."""
    shape = slide.shapes.add_shape(1, left, top, width, height)
    if fill_color:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
    else:
        shape.fill.background()
    shape.line.color.rgb = line_color
    shape.line.width = line_width
    return shape


def add_dashed_rect(slide, left, top, width, height, line_color,
                    fill_color=None, line_width=Pt(1.5)):
    """Add a rectangle with a dashed border."""
    shape = slide.shapes.add_shape(1, left, top, width, height)
    if fill_color:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
    else:
        shape.fill.background()
    shape.line.color.rgb = line_color
    shape.line.width = line_width
    shape.line.dash_style = 2  # DASH
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
        p = tf.paragraphs[0]
        p.text = text
        p.font.size = Pt(font_size)
        p.font.color.rgb = font_color
        p.font.bold = bold
        p.font.name = "Calibri"
    return shape


def add_arrow_shape(slide, left, top, width, height, color=ACCENT_BLUE):
    """Add a right-pointing arrow shape."""
    shape = slide.shapes.add_shape(13, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    return shape


def add_chevron(slide, left, top, width, height, color=ACCENT_BLUE):
    """Add a chevron (right-pointing) shape."""
    shape = slide.shapes.add_shape(55, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    return shape


def add_down_arrow(slide, left, top, width, height, color=ACCENT_BLUE):
    """Add a down-pointing arrow shape."""
    shape = slide.shapes.add_shape(36, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    return shape


def add_connector(slide, x1, y1, x2, y2, color=ACCENT_BLUE, width=Pt(2)):
    """Add a straight line connector between two points."""
    connector = slide.shapes.add_connector(1, x1, y1, x2, y2)
    connector.line.color.rgb = color
    connector.line.width = width
    return connector


def add_card(slide, left, top, width, height, title, items,
             accent_color=ACCENT_BLUE, bg_color=WHITE, title_size=13,
             item_size=10, title_color=None):
    """Add a card with colored top bar, title, and bullet items."""
    card = add_rounded_rect(slide, left, top, width, height, bg_color)
    card.line.color.rgb = RGBColor(0xDD, 0xDD, 0xDD)
    card.line.width = Pt(1)
    add_rect(slide, left, top, width, Pt(4), accent_color)
    t_color = title_color if title_color else accent_color
    add_textbox(slide, left + Inches(0.1), top + Pt(8), width - Inches(0.2),
                Inches(0.3), title, font_size=title_size, color=t_color,
                bold=True)
    if items:
        add_multiline_textbox(
            slide, left + Inches(0.1), top + Pt(8) + Inches(0.28),
            width - Inches(0.2), height - Inches(0.5),
            items, font_size=item_size, color=LIGHT_GRAY,
            spacing=Pt(2)
        )


def add_section_label(slide, left, top, width, text, color=LIGHT_GRAY,
                      font_size=10):
    """Add a small section label / category tag."""
    add_textbox(slide, left, top, width, Inches(0.25), text,
                font_size=font_size, color=color, bold=True)


# ── Presentation Setup ───────────────────────────────────────────────────────

prs = create_presentation()


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 1: Title
# ══════════════════════════════════════════════════════════════════════════════

add_title_slide(
    prs,
    title="Video2Knowledge",
    subtitle="System Architecture — Senior Solution Architecture Design",
    author="Muneeswaran Muthaiah",
    affiliation="A Multimodal Pattern Recognition Framework for\n"
                "Screen Activity Understanding and Knowledge Extraction",
    date_text="NUS ISS  |  Pattern Recognition Systems  |  September 2026",
)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 2: Solution Overview -- C4 Context Level
# ══════════════════════════════════════════════════════════════════════════════

slide2 = add_content_slide(prs, "Solution Overview — Context Diagram",
                           "C4 Model  |  Level 1: System Context")

# --- External Actor: User (left) ---
user_x, user_y = Inches(1.3), Inches(2.4)
add_oval(slide2, user_x, user_y, Inches(1.4), Inches(1.4),
         ACCENT_BLUE, "\U0001F464\nUser", font_size=14, font_color=WHITE)
add_textbox(slide2, user_x - Inches(0.3), user_y + Inches(1.5),
            Inches(2.0), Inches(0.6),
            "Uploads screen recordings,\nviews analysis results",
            font_size=9, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

# --- External System: CUA-Suite (bottom left) ---
cua_x, cua_y = Inches(1.3), Inches(5.0)
add_rounded_rect(slide2, cua_x, cua_y, Inches(2.0), Inches(1.0),
                 SUBTLE_GRAY, "CUA-Suite\nDataset", font_size=12,
                 font_color=WHITE, bold=True)
add_textbox(slide2, cua_x - Inches(0.2), cua_y + Inches(1.05),
            Inches(2.4), Inches(0.5),
            "9,514 training videos\nfrom HuggingFace",
            font_size=9, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

# --- System Boundary: Video2Knowledge (center) ---
sys_x, sys_y = Inches(4.3), Inches(1.4)
sys_w, sys_h = Inches(5.5), Inches(5.2)
add_dashed_rect(slide2, sys_x, sys_y, sys_w, sys_h,
                ACCENT_BLUE, fill_color=LIGHT_BLUE_BG, line_width=Pt(2.5))
add_textbox(slide2, sys_x + Inches(0.2), sys_y + Inches(0.15),
            sys_w - Inches(0.4), Inches(0.3),
            "Video2Knowledge System Boundary", font_size=14,
            color=ACCENT_BLUE, bold=True, alignment=PP_ALIGN.CENTER)

# Inner system box
inner_x = sys_x + Inches(0.5)
inner_y = sys_y + Inches(0.7)
inner_w = sys_w - Inches(1.0)
inner_h = Inches(3.8)
add_rounded_rect(slide2, inner_x, inner_y, inner_w, inner_h,
                 ACCENT_BLUE, "", font_size=12)
# System text
add_textbox(slide2, inner_x + Inches(0.2), inner_y + Inches(0.3),
            inner_w - Inches(0.4), Inches(0.5),
            "Multimodal Pattern Recognition Framework",
            font_size=16, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)
add_multiline_textbox(
    slide2, inner_x + Inches(0.3), inner_y + Inches(0.85),
    inner_w - Inches(0.6), Inches(2.5),
    [
        "Classifies screen activities from video recordings",
        "Extracts 150-dim multimodal feature vectors",
        "Compares 14 ML models across 3 tiers",
        "Generates knowledge artifacts (SOP, Runbook)",
        "",
        "Tech: React + FastAPI + PostgreSQL + PyTorch",
        "Infrastructure: Docker Compose + AWS EC2 GPU",
    ],
    font_size=11, color=RGBColor(0xDD, 0xEE, 0xFF),
    alignment=PP_ALIGN.CENTER, spacing=Pt(4)
)

# --- External System: AWS EC2 (right) ---
aws_x, aws_y = Inches(10.5), Inches(2.4)
add_rounded_rect(slide2, aws_x, aws_y, Inches(2.0), Inches(1.2),
                 RGBColor(0xFF, 0x99, 0x00), "AWS EC2\ng4dn.xlarge",
                 font_size=12, font_color=WHITE, bold=True)
add_textbox(slide2, aws_x - Inches(0.2), aws_y + Inches(1.3),
            Inches(2.4), Inches(0.5),
            "GPU training\ninfrastructure (T4)",
            font_size=9, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

# --- Arrows ---
# User -> System
add_arrow_shape(slide2, Inches(2.9), Inches(2.7), Inches(1.2), Inches(0.3),
                ACCENT_BLUE)
add_textbox(slide2, Inches(2.8), Inches(2.35), Inches(1.4), Inches(0.3),
            "uploads video", font_size=8, color=DARK_BLUE, bold=True,
            alignment=PP_ALIGN.CENTER)

# System -> User (return)
add_arrow_shape(slide2, Inches(2.9), Inches(3.5), Inches(1.2), Inches(0.3),
                ACCENT_GREEN)
add_textbox(slide2, Inches(2.7), Inches(3.8), Inches(1.6), Inches(0.3),
            "← classification results", font_size=8, color=DARK_GREEN,
            bold=True, alignment=PP_ALIGN.CENTER)

# CUA-Suite -> System
add_arrow_shape(slide2, Inches(3.5), Inches(5.1), Inches(0.7), Inches(0.25),
                SUBTLE_GRAY)
add_textbox(slide2, Inches(3.4), Inches(4.8), Inches(1.0), Inches(0.3),
            "training data", font_size=8, color=LIGHT_GRAY, bold=True,
            alignment=PP_ALIGN.CENTER)

# System <-> AWS EC2
add_arrow_shape(slide2, Inches(9.9), Inches(2.8), Inches(0.5), Inches(0.25),
                NUS_ORANGE)
add_textbox(slide2, Inches(9.7), Inches(2.45), Inches(1.0), Inches(0.3),
            "training ↔ models", font_size=8, color=DARK_ORANGE,
            bold=True, alignment=PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 3: Container Diagram -- Docker Architecture
# ══════════════════════════════════════════════════════════════════════════════

slide3 = add_content_slide(prs, "Container Architecture (Docker Compose)",
                           "C4 Model  |  Level 2: Container Diagram")

# Docker Compose boundary
dc_x, dc_y = Inches(1.3), Inches(1.3)
dc_w, dc_h = Inches(11.5), Inches(5.9)
add_dashed_rect(slide3, dc_x, dc_y, dc_w, dc_h,
                SUBTLE_GRAY, fill_color=RGBColor(0x00, 0x2A, 0x55),
                line_width=Pt(2))
add_textbox(slide3, dc_x + Inches(0.15), dc_y + Inches(0.08),
            Inches(4), Inches(0.3),
            "\U0001F40B  Docker Compose Boundary",
            font_size=11, color=LIGHT_GRAY, bold=True)

# Container 1: Frontend (Blue)
fe_x, fe_y = Inches(1.6), Inches(1.7)
fe_w, fe_h = Inches(3.3), Inches(5.2)
add_outlined_rect(slide3, fe_x, fe_y, fe_w, fe_h,
                  ACCENT_BLUE, fill_color=LIGHT_BLUE_BG, line_width=Pt(2))
add_rect(slide3, fe_x, fe_y, fe_w, Inches(0.55), ACCENT_BLUE)
add_textbox(slide3, fe_x + Inches(0.1), fe_y + Inches(0.08),
            fe_w - Inches(0.2), Inches(0.4),
            "Frontend  |  Port 5173", font_size=14, color=WHITE, bold=True)
add_textbox(slide3, fe_x + Inches(0.1), fe_y + Inches(0.6),
            fe_w - Inches(0.2), Inches(0.3),
            "React 18 + TypeScript + Vite", font_size=11, color=DARK_BLUE,
            bold=True)
add_multiline_textbox(
    slide3, fe_x + Inches(0.15), fe_y + Inches(1.0),
    fe_w - Inches(0.3), Inches(3.5),
    [
        "Runtime: nginx (prod) / Vite dev server",
        "",
        "Components:",
        "  • UploadPage — drag & drop upload",
        "  • AnalyzingProgress — real-time progress",
        "  • VideoResults — classification display",
        "  • ModelComparison — 14-model table",
        "",
        "Services:",
        "  • analysisService.ts — REST client",
        "  • React Query — cache + polling",
        "",
        "Image: node:20-alpine (build)",
        "       nginx:alpine (production)",
    ],
    font_size=10, color=NUS_ORANGE, spacing=Pt(2)
)

# Container 2: Backend (Orange)
be_x, be_y = Inches(5.3), Inches(1.7)
be_w, be_h = Inches(3.8), Inches(5.2)
add_outlined_rect(slide3, be_x, be_y, be_w, be_h,
                  NUS_ORANGE, fill_color=LIGHT_ORANGE_BG, line_width=Pt(2))
add_rect(slide3, be_x, be_y, be_w, Inches(0.55), NUS_ORANGE)
add_textbox(slide3, be_x + Inches(0.1), be_y + Inches(0.08),
            be_w - Inches(0.2), Inches(0.4),
            "Backend  |  Port 8000", font_size=14, color=WHITE, bold=True)
add_textbox(slide3, be_x + Inches(0.1), be_y + Inches(0.6),
            be_w - Inches(0.2), Inches(0.3),
            "FastAPI + ML Pipeline", font_size=11, color=DARK_ORANGE,
            bold=True)
add_multiline_textbox(
    slide3, be_x + Inches(0.15), be_y + Inches(1.0),
    be_w - Inches(0.3), Inches(3.5),
    [
        "Base Image: NVIDIA CUDA 12.4 (runtime)",
        "",
        "Sub-components:",
        "  • API Layer — FastAPI routers",
        "  • Video Processor — frame extraction",
        "  • Feature Assembler — 4-modality fusion",
        "  • ML Service — 14 model management",
        "",
        "Libraries: PyTorch, scikit-learn, XGBoost,",
        "  LightGBM, EasyOCR, YOLOv8, OpenCV",
        "",
        "Volumes:",
        "  • ./dataset → /app/dataset (ro)",
        "  • ./models → /app/models",
    ],
    font_size=10, color=NUS_ORANGE, spacing=Pt(2)
)

# Container 3: Database (Green)
db_x, db_y = Inches(9.5), Inches(1.7)
db_w, db_h = Inches(3.1), Inches(5.2)
add_outlined_rect(slide3, db_x, db_y, db_w, db_h,
                  ACCENT_GREEN, fill_color=LIGHT_GREEN_BG, line_width=Pt(2))
add_rect(slide3, db_x, db_y, db_w, Inches(0.55), ACCENT_GREEN)
add_textbox(slide3, db_x + Inches(0.1), db_y + Inches(0.08),
            db_w - Inches(0.2), Inches(0.4),
            "Database  |  Port 5434", font_size=14, color=WHITE, bold=True)
add_textbox(slide3, db_x + Inches(0.1), db_y + Inches(0.6),
            db_w - Inches(0.2), Inches(0.3),
            "PostgreSQL 16 + pgvector", font_size=11, color=DARK_GREEN,
            bold=True)
add_multiline_textbox(
    slide3, db_x + Inches(0.15), db_y + Inches(1.0),
    db_w - Inches(0.3), Inches(3.5),
    [
        "Tables:",
        "  • videos",
        "  • analysis_jobs",
        "  • classification_results",
        "  • model_evaluations",
        "",
        "Extensions: pgvector",
        "",
        "Volume: pgdata (named)",
        "",
        "Driver: SQLAlchemy async",
        "  + asyncpg",
    ],
    font_size=10, color=NUS_ORANGE, spacing=Pt(2)
)

# Arrows between containers
# Frontend -> Backend
add_arrow_shape(slide3, Inches(4.95), Inches(3.8), Inches(0.3), Inches(0.25),
                ACCENT_BLUE)
add_textbox(slide3, Inches(4.6), Inches(3.5), Inches(1.0), Inches(0.3),
            "HTTP REST", font_size=8, color=DARK_BLUE, bold=True,
            alignment=PP_ALIGN.CENTER)

# Backend -> Database
add_arrow_shape(slide3, Inches(9.15), Inches(3.8), Inches(0.3), Inches(0.25),
                NUS_ORANGE)
add_textbox(slide3, Inches(8.7), Inches(3.5), Inches(1.1), Inches(0.3),
            "SQLAlchemy async", font_size=8, color=DARK_ORANGE, bold=True,
            alignment=PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 4: Backend Component Architecture
# ══════════════════════════════════════════════════════════════════════════════

slide4 = add_content_slide(prs, "Backend Component Architecture",
                           "Layered Architecture  |  Separation of Concerns")

layer_x = Inches(1.3)
layer_w = Inches(11.5)

# Layer 1: API Layer
api_y = Inches(1.3)
api_h = Inches(1.25)
add_outlined_rect(slide4, layer_x, api_y, layer_w, api_h,
                  ACCENT_BLUE, fill_color=LIGHT_BLUE_BG)
add_textbox(slide4, layer_x + Inches(0.15), api_y + Inches(0.05),
            Inches(2.0), Inches(0.3),
            "API Layer (FastAPI Routers)", font_size=13, color=ACCENT_BLUE,
            bold=True)

api_cards = [
    ("routers/videos.py", ["POST /upload", "GET /list"]),
    ("routers/jobs.py", ["POST /run", "GET /progress", "GET /results"]),
    ("routers/knowledge.py", ["POST /sop", "POST /runbook"]),
    ("routers/evaluation.py", ["GET /models", "POST /evaluate"]),
]
for i, (title, items) in enumerate(api_cards):
    cx = layer_x + Inches(0.15) + Inches(i * 2.82)
    add_card(slide4, cx, api_y + Inches(0.35), Inches(2.65), Inches(0.82),
             title, items, accent_color=ACCENT_BLUE, bg_color=WHITE,
             title_size=11, item_size=9)

# Down arrow
add_down_arrow(slide4, Inches(6.8), Inches(2.57), Inches(0.35), Inches(0.28),
               ACCENT_BLUE)

# Layer 2: Service Layer
svc_y = Inches(2.87)
svc_h = Inches(1.25)
add_outlined_rect(slide4, layer_x, svc_y, layer_w, svc_h,
                  NUS_ORANGE, fill_color=LIGHT_ORANGE_BG)
add_textbox(slide4, layer_x + Inches(0.15), svc_y + Inches(0.05),
            Inches(3.0), Inches(0.3),
            "Service Layer (Business Logic)", font_size=13,
            color=NUS_ORANGE, bold=True)

svc_cards = [
    ("classification_service.py", ["Pipeline orchestrator", "Coordinates all stages"]),
    ("ml_service.py", ["Model management (singleton)", "Load / predict / compare"]),
    ("job_service.py", ["Job status tracking", "Progress reporting"]),
    ("video_service.py", ["Video file management", "Metadata persistence"]),
]
for i, (title, items) in enumerate(svc_cards):
    cx = layer_x + Inches(0.15) + Inches(i * 2.82)
    add_card(slide4, cx, svc_y + Inches(0.35), Inches(2.65), Inches(0.82),
             title, items, accent_color=NUS_ORANGE, bg_color=WHITE,
             title_size=11, item_size=9)

# Down arrow
add_down_arrow(slide4, Inches(6.8), Inches(4.14), Inches(0.35), Inches(0.28),
               NUS_ORANGE)

# Layer 3: Pipeline Layer
pip_y = Inches(4.44)
pip_h = Inches(1.25)
add_outlined_rect(slide4, layer_x, pip_y, layer_w, pip_h,
                  ACCENT_PURPLE, fill_color=LIGHT_PURPLE_BG)
add_textbox(slide4, layer_x + Inches(0.15), pip_y + Inches(0.05),
            Inches(3.0), Inches(0.3),
            "Pipeline Layer (Feature Extraction)", font_size=13,
            color=ACCENT_PURPLE, bold=True)

pip_cards = [
    ("video_processor.py", ["Segment extraction", "Keyframe sampling @ 1fps"]),
    ("feature_assembler.py", ["4-modality fusion", "→ 150-dim feature vector"]),
    ("temporal_encoder.py", ["Sequence encoding", "Time-series features"]),
]
for i, (title, items) in enumerate(pip_cards):
    cx = layer_x + Inches(0.15) + Inches(i * 3.78)
    add_card(slide4, cx, pip_y + Inches(0.35), Inches(3.55), Inches(0.82),
             title, items, accent_color=ACCENT_PURPLE, bg_color=WHITE,
             title_size=11, item_size=9)

# Down arrow
add_down_arrow(slide4, Inches(6.8), Inches(5.71), Inches(0.35), Inches(0.28),
               ACCENT_PURPLE)

# Layer 4: ML Layer
ml_y = Inches(6.01)
ml_h = Inches(1.2)
add_outlined_rect(slide4, layer_x, ml_y, layer_w, ml_h,
                  ACCENT_GREEN, fill_color=LIGHT_GREEN_BG)
add_textbox(slide4, layer_x + Inches(0.15), ml_y + Inches(0.05),
            Inches(3.0), Inches(0.3),
            "ML Layer (Classification Models)", font_size=13,
            color=ACCENT_GREEN, bold=True)

ml_cards = [
    ("base.py / registry.py", ["BaseClassifier interface", "ModelRegistry singleton"]),
    ("config.py", ["MLConfig parameters", "ACTIVITY_LABELS (9 classes)"]),
    ("classifiers/tier1/", ["7 classical ML models", "SVM, NB, DT, RF, KNN, XGB, LGBM"]),
    ("classifiers/tier2/", ["4 deep learning models", "MLP, CNN-1D, LSTM, Transformer"]),
    ("classifiers/tier3/", ["3 ensemble models", "Voting, Stacking, Late Fusion"]),
]
for i, (title, items) in enumerate(ml_cards):
    cx = layer_x + Inches(0.15) + Inches(i * 2.26)
    add_card(slide4, cx, ml_y + Inches(0.35), Inches(2.1), Inches(0.78),
             title, items, accent_color=ACCENT_GREEN, bg_color=WHITE,
             title_size=10, item_size=9)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 5: Feature Extraction Pipeline -- Detailed
# ══════════════════════════════════════════════════════════════════════════════

slide5 = add_content_slide(prs, "Multimodal Feature Extraction Pipeline",
                           "4 Parallel Extractors  |  150-Dimensional Feature Vector")

# Input
inp_x, inp_y = Inches(1.3), Inches(1.3)
add_rounded_rect(slide5, inp_x, inp_y, Inches(1.6), Inches(0.9),
                 NUS_BLUE, "Input\n.mp4 + .json", font_size=11,
                 font_color=WHITE, bold=True)

# Arrow from input to VideoProcessor
add_arrow_shape(slide5, inp_x + Inches(1.65), inp_y + Inches(0.3),
                Inches(0.35), Inches(0.2), SUBTLE_GRAY)

# Step 1: VideoProcessor
vp_x, vp_y = Inches(3.4), Inches(1.2)
add_outlined_rect(slide5, vp_x, vp_y, Inches(2.2), Inches(1.1),
                  NUS_ORANGE, fill_color=LIGHT_ORANGE_BG)
add_textbox(slide5, vp_x + Inches(0.1), vp_y + Inches(0.05),
            Inches(2.0), Inches(0.25),
            "VideoProcessor", font_size=11, color=NUS_ORANGE, bold=True)
add_multiline_textbox(
    slide5, vp_x + Inches(0.1), vp_y + Inches(0.3),
    Inches(2.0), Inches(0.7),
    ["extract_frames() @ 1fps", "cluster_actions() 2s gaps",
     "extract_segments() → SegmentData"],
    font_size=8, color=NUS_ORANGE, spacing=Pt(1)
)

# Arrow down from VideoProcessor
add_down_arrow(slide5, Inches(4.3), Inches(2.35), Inches(0.3), Inches(0.25),
               NUS_ORANGE)

# Four parallel streams label
add_textbox(slide5, Inches(1.3), Inches(2.65), Inches(11.5), Inches(0.25),
            "4 Parallel Feature Extractors", font_size=12, color=NUS_ORANGE,
            bold=True)

# Stream dimensions
stream_top = Inches(2.95)
stream_h = Inches(3.5)
stream_w = Inches(2.8)
gap = Inches(0.15)

# Stream A: OCR (Blue)
sa_x = Inches(1.3)
add_outlined_rect(slide5, sa_x, stream_top, stream_w, stream_h,
                  OCR_COLOR, fill_color=LIGHT_BLUE_BG)
add_rect(slide5, sa_x, stream_top, stream_w, Inches(0.35), OCR_COLOR)
add_textbox(slide5, sa_x + Inches(0.05), stream_top + Inches(0.05),
            stream_w - Inches(0.1), Inches(0.25),
            "A: OCR Extractor  |  50-dim  [0:50]", font_size=10,
            color=WHITE, bold=True)
add_multiline_textbox(
    slide5, sa_x + Inches(0.1), stream_top + Inches(0.4),
    stream_w - Inches(0.2), stream_h - Inches(0.5),
    [
        "EasyOCR (GPU-accelerated)",
        "  → TextRegion(text, bbox, conf)",
        "",
        "Tesseract fallback (conf < 0.3)",
        "",
        "TF-IDF Vectorizer",
        "  max_features = 50",
        "  → 50-dimensional vector",
        "",
        "Feature Index: [0 : 50]",
    ],
    font_size=9, color=NUS_ORANGE, spacing=Pt(1)
)

# Stream B: UI (Orange)
sb_x = sa_x + stream_w + gap
add_outlined_rect(slide5, sb_x, stream_top, stream_w, stream_h,
                  UI_COLOR, fill_color=LIGHT_ORANGE_BG)
add_rect(slide5, sb_x, stream_top, stream_w, Inches(0.35), UI_COLOR)
add_textbox(slide5, sb_x + Inches(0.05), stream_top + Inches(0.05),
            stream_w - Inches(0.1), Inches(0.25),
            "B: UI Detector  |  30-dim  [50:80]", font_size=10,
            color=WHITE, bold=True)
add_multiline_textbox(
    slide5, sb_x + Inches(0.1), stream_top + Inches(0.4),
    stream_w - Inches(0.2), stream_h - Inches(0.5),
    [
        "YOLOv8 nano (conf > 0.25)",
        "  → UIElement(class, bbox, conf)",
        "",
        "12 UI classes: button, text_field,",
        "  menu, dropdown, toolbar, sidebar,",
        "  tab, dialog, terminal, icon,",
        "  scroll_bar, status_bar",
        "",
        "[0:12] counts  [12:20] spatial",
        "[20:24] conf   [24:30] complexity",
        "Feature Index: [50 : 80]",
    ],
    font_size=9, color=NUS_ORANGE, spacing=Pt(1)
)

# Stream C: Visual (Purple)
sc_x = sb_x + stream_w + gap
add_outlined_rect(slide5, sc_x, stream_top, stream_w, stream_h,
                  VISUAL_COLOR, fill_color=LIGHT_PURPLE_BG)
add_rect(slide5, sc_x, stream_top, stream_w, Inches(0.35), VISUAL_COLOR)
add_textbox(slide5, sc_x + Inches(0.05), stream_top + Inches(0.05),
            stream_w - Inches(0.1), Inches(0.25),
            "C: Visual Features  |  40-dim  [80:120]", font_size=10,
            color=WHITE, bold=True)
add_multiline_textbox(
    slide5, sc_x + Inches(0.1), stream_top + Inches(0.4),
    stream_w - Inches(0.2), stream_h - Inches(0.5),
    [
        "Color histogram (6 bins x 3 RGB = 18)",
        "Edge density (Canny + Sobel = 3)",
        "Texture (Gabor 3x2 = 6)",
        "Scene stats (5)",
        "Layout 2x2 grid (8)",
        "",
        "→ 40-dimensional vector",
        "",
        "Feature Index: [80 : 120]",
    ],
    font_size=9, color=NUS_ORANGE, spacing=Pt(1)
)

# Stream D: Interaction (Green)
sd_x = sc_x + stream_w + gap
add_outlined_rect(slide5, sd_x, stream_top, stream_w, stream_h,
                  INTERACTION_COLOR, fill_color=LIGHT_GREEN_BG)
add_rect(slide5, sd_x, stream_top, stream_w, Inches(0.35), INTERACTION_COLOR)
add_textbox(slide5, sd_x + Inches(0.05), stream_top + Inches(0.05),
            stream_w - Inches(0.1), Inches(0.25),
            "D: Interaction  |  30-dim  [120:150]", font_size=10,
            color=WHITE, bold=True)
add_multiline_textbox(
    slide5, sd_x + Inches(0.1), stream_top + Inches(0.4),
    stream_w - Inches(0.2), stream_h - Inches(0.5),
    [
        "8 action types: CLICK, MOVE_TO,",
        "  TYPING, DRAG_TO, HOTKEY, PRESS,",
        "  MOUSE_DOWN, MOUSE_UP",
        "",
        "[0:8] frequency  [8:12] position",
        "[12:18] temporal [18:24] mouse",
        "[24:28] typing   [28:30] keyboard",
        "",
        "Feature Index: [120 : 150]",
    ],
    font_size=9, color=NUS_ORANGE, spacing=Pt(1)
)

# Concatenation bar at bottom
concat_y = stream_top + stream_h + Inches(0.15)
add_rect(slide5, Inches(1.3), concat_y, Inches(9.0), Inches(0.4),
         NUS_BLUE, "Concatenation → 150-dim Feature Vector  |  [0:50] + [50:80] + [80:120] + [120:150]",
         font_size=11, font_color=WHITE, bold=True)

# Arrow to classification
add_arrow_shape(slide5, Inches(10.4), concat_y + Inches(0.05),
                Inches(0.5), Inches(0.25), ACCENT_PURPLE)
add_rounded_rect(slide5, Inches(10.95), concat_y - Inches(0.05),
                 Inches(2.0), Inches(0.5),
                 ACCENT_PURPLE, "→ Classification (14 models)",
                 font_size=11, font_color=WHITE, bold=True)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 6: Classification Architecture -- 3 Tiers
# ══════════════════════════════════════════════════════════════════════════════

slide6 = add_content_slide(prs, "3-Tier Classification Architecture",
                           "14 Models  |  Classical ML + Deep Learning + Ensemble")

# Input vector
vec_x, vec_y = Inches(1.3), Inches(1.3)
add_rounded_rect(slide6, vec_x, vec_y, Inches(1.5), Inches(0.6),
                 NUS_BLUE, "150-dim\nFeature Vector", font_size=11,
                 font_color=WHITE, bold=True)

# Arrow from input to tiers
add_arrow_shape(slide6, Inches(2.85), Inches(1.42), Inches(0.35), Inches(0.2),
                SUBTLE_GRAY)

# Tier 1: Classical ML
t1_x, t1_y = Inches(3.4), Inches(1.1)
t1_w, t1_h = Inches(4.0), Inches(2.0)
add_outlined_rect(slide6, t1_x, t1_y, t1_w, t1_h,
                  ACCENT_BLUE, fill_color=LIGHT_BLUE_BG)
add_rect(slide6, t1_x, t1_y, t1_w, Inches(0.35), ACCENT_BLUE)
add_textbox(slide6, t1_x + Inches(0.1), t1_y + Inches(0.05),
            t1_w - Inches(0.2), Inches(0.25),
            "Tier 1 — Classical ML (scikit-learn)  |  7 models",
            font_size=11, color=WHITE, bold=True)

# Model boxes for Tier 1
t1_models = ["SVM", "NB", "DT", "RF", "KNN", "XGBoost", "LightGBM"]
for i, m in enumerate(t1_models):
    row = i // 4
    col = i % 4
    mx = t1_x + Inches(0.15) + Inches(col * 0.97)
    my = t1_y + Inches(0.45) + Inches(row * 0.55)
    add_rounded_rect(slide6, mx, my, Inches(0.85), Inches(0.45),
                     ACCENT_BLUE, m, font_size=10, font_color=WHITE, bold=True)

add_textbox(slide6, t1_x + Inches(0.1), t1_y + t1_h - Inches(0.3),
            t1_w - Inches(0.2), Inches(0.25),
            "Output: PredictionResult(labels, probabilities, latency_ms) → 9-class probability vector",
            font_size=8, color=DARK_BLUE)

# Tier 2: Deep Learning
t2_x, t2_y = Inches(3.4), Inches(3.3)
t2_w, t2_h = Inches(4.0), Inches(1.7)
add_outlined_rect(slide6, t2_x, t2_y, t2_w, t2_h,
                  ACCENT_PURPLE, fill_color=LIGHT_PURPLE_BG)
add_rect(slide6, t2_x, t2_y, t2_w, Inches(0.35), ACCENT_PURPLE)
add_textbox(slide6, t2_x + Inches(0.1), t2_y + Inches(0.05),
            t2_w - Inches(0.2), Inches(0.25),
            "Tier 2 — Deep Learning (PyTorch)  |  4 models",
            font_size=11, color=WHITE, bold=True)

t2_info = [
    ("MLP", "150→256→128→9"),
    ("CNN-1D", "Conv1d filters"),
    ("LSTM", "(10,15) h=64"),
    ("Transformer", "Self-attn Q/K/V"),
]
for i, (name, desc) in enumerate(t2_info):
    mx = t2_x + Inches(0.15) + Inches(i * 0.97)
    my = t2_y + Inches(0.45)
    add_rounded_rect(slide6, mx, my, Inches(0.85), Inches(0.45),
                     ACCENT_PURPLE, name, font_size=10, font_color=WHITE,
                     bold=True)
    add_textbox(slide6, mx - Inches(0.05), my + Inches(0.5),
                Inches(0.95), Inches(0.25),
                desc, font_size=7, color=DARK_PURPLE,
                alignment=PP_ALIGN.CENTER)

# Tier 3: Ensemble
t3_x, t3_y = Inches(7.8), Inches(1.1)
t3_w, t3_h = Inches(5.0), Inches(3.9)
add_outlined_rect(slide6, t3_x, t3_y, t3_w, t3_h,
                  ACCENT_GREEN, fill_color=LIGHT_GREEN_BG)
add_rect(slide6, t3_x, t3_y, t3_w, Inches(0.35), ACCENT_GREEN)
add_textbox(slide6, t3_x + Inches(0.1), t3_y + Inches(0.05),
            t3_w - Inches(0.2), Inches(0.25),
            "Tier 3 — Ensemble (Hybrid)  |  3 models",
            font_size=11, color=WHITE, bold=True)

ensemble_info = [
    ("Voting", "average(SVM + RF + MLP probabilities)"),
    ("Stacking", "[SVM_proba + RF_proba + MLP_proba]\n→ LogisticRegression → 9 classes"),
    ("Late Fusion", "SVM(features[0:75]) + RF(features[75:150])\n→ LogisticRegression → 9 classes"),
]
for i, (name, desc) in enumerate(ensemble_info):
    my = t3_y + Inches(0.5) + Inches(i * 1.1)
    add_rounded_rect(slide6, t3_x + Inches(0.15), my,
                     Inches(1.4), Inches(0.5), ACCENT_GREEN, name,
                     font_size=11, font_color=WHITE, bold=True)
    add_textbox(slide6, t3_x + Inches(1.7), my + Inches(0.05),
                Inches(3.1), Inches(0.8),
                desc, font_size=9, color=DARK_GREEN)

# Arrows from T1/T2 into T3
add_textbox(slide6, Inches(7.4), Inches(1.8), Inches(0.5), Inches(0.3),
            "feeds\n→", font_size=9, color=LIGHT_GRAY, bold=True,
            alignment=PP_ALIGN.CENTER)
add_textbox(slide6, Inches(7.4), Inches(3.8), Inches(0.5), Inches(0.3),
            "feeds\n→", font_size=9, color=LIGHT_GRAY, bold=True,
            alignment=PP_ALIGN.CENTER)

# Output section
out_y = Inches(5.3)
add_rect(slide6, Inches(1.3), out_y, Inches(11.5), Inches(0.5),
         RGBColor(0x00, 0x2A, 0x55),
         "Output: Best model selected by highest avg confidence  →  Activity Label (1 of 9 classes)",
         font_size=13, font_color=WHITE, bold=True)

# 9 activity labels
label_y = out_y + Inches(0.65)
labels = [
    "using_web_browser", "using_text_editor", "using_terminal",
    "navigating_file_system", "using_spreadsheet", "using_communication_app",
    "installing_software", "using_media_player", "using_settings"
]
for i, lbl in enumerate(labels):
    lx = Inches(1.3) + Inches(i * 1.3)
    add_rounded_rect(slide6, lx, label_y, Inches(1.2), Inches(0.4),
                     CARD_BG, lbl.replace("_", " "), font_size=7,
                     font_color=NUS_ORANGE, bold=False)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 7: Data Flow Architecture -- End to End
# ══════════════════════════════════════════════════════════════════════════════

slide7 = add_content_slide(prs, "End-to-End Data Flow",
                           "Request Lifecycle  |  Upload → Analysis → Results")

# Row 1: User interaction flow
row1_y = Inches(1.3)

add_rounded_rect(slide7, Inches(1.3), row1_y, Inches(1.2), Inches(0.7),
                 ACCENT_BLUE, "User\ndrops video", font_size=9,
                 font_color=WHITE, bold=True)
add_chevron(slide7, Inches(2.55), row1_y + Inches(0.2), Inches(0.25),
            Inches(0.25), SUBTLE_GRAY)

add_rounded_rect(slide7, Inches(2.85), row1_y, Inches(1.5), Inches(0.7),
                 ACCENT_BLUE, "Browser\nPOST /videos/upload", font_size=9,
                 font_color=WHITE, bold=True)
add_chevron(slide7, Inches(4.4), row1_y + Inches(0.2), Inches(0.25),
            Inches(0.25), SUBTLE_GRAY)

add_rounded_rect(slide7, Inches(4.7), row1_y, Inches(1.7), Inches(0.7),
                 NUS_ORANGE, "Save file\nCreate job → {job_id}", font_size=9,
                 font_color=WHITE, bold=True)
add_chevron(slide7, Inches(6.45), row1_y + Inches(0.2), Inches(0.25),
            Inches(0.25), SUBTLE_GRAY)

add_rounded_rect(slide7, Inches(6.75), row1_y, Inches(1.7), Inches(0.7),
                 ACCENT_BLUE, "POST /jobs/{id}/run\n→ {status: processing}", font_size=9,
                 font_color=WHITE, bold=True)
add_chevron(slide7, Inches(8.5), row1_y + Inches(0.2), Inches(0.25),
            Inches(0.25), SUBTLE_GRAY)

add_rounded_rect(slide7, Inches(8.8), row1_y, Inches(1.9), Inches(0.7),
                 ACCENT_BLUE, "Poll GET /jobs/{id}\nevery 1s → progress_pct", font_size=9,
                 font_color=WHITE, bold=True)
add_chevron(slide7, Inches(10.75), row1_y + Inches(0.2), Inches(0.25),
            Inches(0.25), SUBTLE_GRAY)

add_rounded_rect(slide7, Inches(11.05), row1_y, Inches(1.8), Inches(0.7),
                 ACCENT_GREEN, "Completed →\nGET /jobs/{id}/results", font_size=9,
                 font_color=WHITE, bold=True)

# Row 2: Background task detail
add_textbox(slide7, Inches(1.3), Inches(2.2), Inches(11.5), Inches(0.3),
            "Background Processing Pipeline (runs asynchronously after POST /jobs/{id}/run)",
            font_size=12, color=NUS_ORANGE, bold=True)

row2_y = Inches(2.55)
bg_steps = [
    ("video.mp4", SUBTLE_GRAY),
    ("VideoProcessor\n→ SegmentData[]", NUS_ORANGE),
    ("FeatureAssembler\n→ (n, 150) matrix", ACCENT_PURPLE),
    ("_classify_all_models\n→ 14 x PredictionResult", ACCENT_GREEN),
    ("ClassificationResult\nsaved to DB", ACCENT_GREEN),
    ("Job status\n→ completed", ACCENT_BLUE),
]
for i, (text, color) in enumerate(bg_steps):
    bx = Inches(1.3) + Inches(i * 1.95)
    add_rounded_rect(slide7, bx, row2_y, Inches(1.8), Inches(0.7),
                     color, text, font_size=9, font_color=WHITE, bold=True)
    if i < len(bg_steps) - 1:
        add_chevron(slide7, bx + Inches(1.83), row2_y + Inches(0.2),
                    Inches(0.1), Inches(0.2), SUBTLE_GRAY)

# Row 3: Response rendering
add_textbox(slide7, Inches(1.3), Inches(3.5), Inches(11.5), Inches(0.3),
            "Response: JobResultsResponse", font_size=12, color=NUS_ORANGE,
            bold=True)

row3_y = Inches(3.85)
resp_items = [
    ("results\n[ClassificationResult[]]", NUS_ORANGE),
    ("model_comparison\n[14 models with metrics]", ACCENT_PURPLE),
    ("best_model\n[highest avg confidence]", ACCENT_GREEN),
]
for i, (text, color) in enumerate(resp_items):
    rx = Inches(1.3) + Inches(i * 3.9)
    add_rounded_rect(slide7, rx, row3_y, Inches(3.7), Inches(0.65),
                     color, text, font_size=10, font_color=WHITE, bold=True)

# Row 4: UI renders
add_textbox(slide7, Inches(1.3), Inches(4.75), Inches(11.5), Inches(0.3),
            "Browser Renders", font_size=12, color=NUS_ORANGE, bold=True)

row4_y = Inches(5.1)
ui_items = [
    ("ModelComparison Table\n14 models ranked by accuracy, F1, latency", ACCENT_BLUE),
    ("WorkflowSteps\nClassified activity sequence with icons", ACCENT_PURPLE),
    ("Video Player\nSynchronized playback with annotations", NUS_ORANGE),
    ("Knowledge Artifacts\nGenerated SOP / Runbook (optional)", ACCENT_GREEN),
]
for i, (text, color) in enumerate(ui_items):
    ux = Inches(1.3) + Inches(i * 2.9)
    add_card(slide7, ux, row4_y, Inches(2.7), Inches(1.0),
             text.split("\n")[0], [text.split("\n")[1]] if "\n" in text else [],
             accent_color=color, bg_color=WHITE, title_size=11, item_size=9)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 8: Training Architecture
# ══════════════════════════════════════════════════════════════════════════════

slide8 = add_content_slide(prs, "Model Training Architecture",
                           "CUA-Suite Dataset  |  Feature Extraction  |  14 Models  |  Evaluation")

# Row 1: Data preparation flow
add_section_label(slide8, Inches(1.3), Inches(1.3), Inches(3.0),
                  "DATA PREPARATION", color=ACCENT_BLUE, font_size=10)

r1_y = Inches(1.55)
data_steps = [
    ("CUA-Suite\n(HuggingFace)", SUBTLE_GRAY),
    ("Download\n87 zip files", ACCENT_BLUE),
    ("Extract\n9,514 video tasks\n+ action_log.json", ACCENT_BLUE),
    ("dataset_loader.py\ndiscover_tasks()\n→ TaskMetadata[]", NUS_ORANGE),
    ("task_level_split\n80/20", NUS_ORANGE),
]
for i, (text, color) in enumerate(data_steps):
    dx = Inches(1.3) + Inches(i * 2.3)
    add_rounded_rect(slide8, dx, r1_y, Inches(2.1), Inches(0.85),
                     color, text, font_size=9, font_color=WHITE, bold=True)
    if i < len(data_steps) - 1:
        add_chevron(slide8, dx + Inches(2.13), r1_y + Inches(0.28),
                    Inches(0.15), Inches(0.2), SUBTLE_GRAY)

# Split result boxes
split_y = Inches(2.55)
add_rounded_rect(slide8, Inches(1.3), split_y, Inches(2.8), Inches(0.55),
                 ACCENT_GREEN, "Train: 7,685 samples → X_train(7685, 150), y_train",
                 font_size=10, font_color=WHITE, bold=True)
add_rounded_rect(slide8, Inches(4.3), split_y, Inches(2.8), Inches(0.55),
                 NUS_ORANGE, "Test: 1,924 samples → X_test(1924, 150), y_test",
                 font_size=10, font_color=WHITE, bold=True)

add_textbox(slide8, Inches(7.3), split_y + Inches(0.1), Inches(3.5), Inches(0.4),
            "Label remapping → 9 contiguous classes  |  Augmentation if < 100 samples",
            font_size=9, color=LIGHT_GRAY)

# Down arrow
add_down_arrow(slide8, Inches(3.9), Inches(3.15), Inches(0.3), Inches(0.25),
               NUS_ORANGE)

# Row 2: Training pipeline
add_section_label(slide8, Inches(1.3), Inches(3.45), Inches(3.0),
                  "TRAINING PIPELINE", color=NUS_ORANGE, font_size=10)

train_y = Inches(3.7)

add_rounded_rect(slide8, Inches(1.3), train_y, Inches(2.5), Inches(1.0),
                 NUS_ORANGE,
                 "FeatureAssembler\nbuild_dataset()\nX(7685, 150), y(7685,)",
                 font_size=10, font_color=WHITE, bold=True)
add_chevron(slide8, Inches(3.85), train_y + Inches(0.35),
            Inches(0.2), Inches(0.2), SUBTLE_GRAY)

# 3 Tier boxes
tier_x = Inches(4.2)
tier_labels = [
    ("Tier 1: 7 Classical", "SVM, NB, DT, RF, KNN,\nXGBoost, LightGBM", ACCENT_BLUE),
    ("Tier 2: 4 Deep Learning", "MLP, CNN-1D,\nLSTM, Transformer", ACCENT_PURPLE),
    ("Tier 3: 3 Ensemble", "Voting, Stacking,\nLate Fusion", ACCENT_GREEN),
]
for i, (title, models, color) in enumerate(tier_labels):
    ty = train_y + Inches(i * 0.65)
    tw = Inches(2.4)
    add_rounded_rect(slide8, tier_x, ty, tw, Inches(0.55),
                     color, f"{title}: {models.split(chr(10))[0]}",
                     font_size=8, font_color=WHITE, bold=True)

add_chevron(slide8, Inches(6.65), train_y + Inches(0.35),
            Inches(0.2), Inches(0.2), SUBTLE_GRAY)

# Save output
add_rounded_rect(slide8, Inches(7.0), train_y, Inches(2.3), Inches(1.0),
                 ACCENT_GREEN,
                 "clf.fit(X_train, y_train)\nclf.save(models/{name}.pkl)\n→ 14 .pkl files",
                 font_size=10, font_color=WHITE, bold=True)

# Row 3: Evaluation
add_section_label(slide8, Inches(1.3), Inches(4.85), Inches(3.0),
                  "EVALUATION", color=ACCENT_GREEN, font_size=10)

eval_y = Inches(5.1)
add_rounded_rect(slide8, Inches(1.3), eval_y, Inches(2.5), Inches(0.7),
                 ACCENT_GREEN,
                 "clf.predict(X_test)\n→ accuracy, F1-macro, latency",
                 font_size=10, font_color=WHITE, bold=True)
add_chevron(slide8, Inches(3.85), eval_y + Inches(0.2),
            Inches(0.2), Inches(0.2), SUBTLE_GRAY)

add_rounded_rect(slide8, Inches(4.2), eval_y, Inches(2.7), Inches(0.7),
                 ACCENT_PURPLE,
                 "Comparison Table\n14 models ranked by metrics",
                 font_size=10, font_color=WHITE, bold=True)
add_chevron(slide8, Inches(6.95), eval_y + Inches(0.2),
            Inches(0.2), Inches(0.2), SUBTLE_GRAY)

add_rounded_rect(slide8, Inches(7.3), eval_y, Inches(2.3), Inches(0.7),
                 NUS_BLUE,
                 "Output: 14 .pkl files\n+ comparison table",
                 font_size=10, font_color=WHITE, bold=True)

# Infrastructure box (right column)
infra_x, infra_y = Inches(10.0), Inches(1.55)
infra_w, infra_h = Inches(2.8), Inches(4.25)
add_outlined_rect(slide8, infra_x, infra_y, infra_w, infra_h,
                  RGBColor(0xFF, 0x99, 0x00),
                  fill_color=RGBColor(0xFF, 0xF8, 0xE1))
add_rect(slide8, infra_x, infra_y, infra_w, Inches(0.35),
         RGBColor(0xFF, 0x99, 0x00))
add_textbox(slide8, infra_x + Inches(0.1), infra_y + Inches(0.05),
            infra_w - Inches(0.2), Inches(0.25),
            "Infrastructure", font_size=12, color=WHITE, bold=True)
add_multiline_textbox(
    slide8, infra_x + Inches(0.15), infra_y + Inches(0.45),
    infra_w - Inches(0.3), infra_h - Inches(0.5),
    [
        "AWS EC2 g4dn.xlarge",
        "  • NVIDIA T4 GPU (16 GB)",
        "  • 4 vCPU, 16 GB RAM",
        "  • 125 GB gp3 SSD",
        "",
        "Terraform IaC",
        "  • VPC + Subnet + IGW",
        "  • Security Group",
        "  • EC2 + EBS",
        "  • All tagged: Project=v2k",
        "",
        "Docker Compose",
        "  + docker-compose.gpu.yml",
        "  (NVIDIA runtime)",
    ],
    font_size=9, color=NUS_ORANGE, spacing=Pt(2)
)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 9: Deployment Architecture
# ══════════════════════════════════════════════════════════════════════════════

slide9 = add_content_slide(prs, "Deployment Architecture",
                           "Local Development  |  AWS Production/Training  |  Model Transfer")

# LEFT: Local Development
local_x, local_y = Inches(1.3), Inches(1.3)
local_w, local_h = Inches(5.3), Inches(4.4)
add_outlined_rect(slide9, local_x, local_y, local_w, local_h,
                  ACCENT_BLUE, fill_color=LIGHT_BLUE_BG, line_width=Pt(2))
add_rect(slide9, local_x, local_y, local_w, Inches(0.45), ACCENT_BLUE)
add_textbox(slide9, local_x + Inches(0.1), local_y + Inches(0.07),
            local_w - Inches(0.2), Inches(0.3),
            "Local Development", font_size=16, color=WHITE, bold=True)

add_multiline_textbox(
    slide9, local_x + Inches(0.2), local_y + Inches(0.55),
    local_w - Inches(0.4), local_h - Inches(0.6),
    [
        "Platform: macOS / Linux",
        "",
        "Launch: docker compose up --build",
        "",
        "Database: SQLite (local) or PostgreSQL (Docker)",
        "",
        "Compute: CPU-only",
        "  • macOS synthetic features fallback",
        "  • No GPU required for inference",
        "",
        "Fast Mode (default):",
        "  • 5 models (SVM, RF, MLP, Voting, Stacking)",
        "  • ~30 seconds per video",
        "  • Uses pre-trained .pkl files",
        "",
        "Full Mode (optional):",
        "  • 14 models, may retrain if needed",
        "  • Longer processing time",
    ],
    font_size=11, color=NUS_ORANGE, spacing=Pt(3)
)

# RIGHT: AWS Production
aws_x2, aws_y2 = Inches(7.0), Inches(1.3)
aws_w2, aws_h2 = Inches(5.5), Inches(4.4)
add_outlined_rect(slide9, aws_x2, aws_y2, aws_w2, aws_h2,
                  NUS_ORANGE, fill_color=LIGHT_ORANGE_BG, line_width=Pt(2))
add_rect(slide9, aws_x2, aws_y2, aws_w2, Inches(0.45), NUS_ORANGE)
add_textbox(slide9, aws_x2 + Inches(0.1), aws_y2 + Inches(0.07),
            aws_w2 - Inches(0.2), Inches(0.3),
            "AWS Production / Training", font_size=16, color=WHITE, bold=True)

add_multiline_textbox(
    slide9, aws_x2 + Inches(0.2), aws_y2 + Inches(0.55),
    aws_w2 - Inches(0.4), aws_h2 - Inches(0.6),
    [
        "Instance: EC2 g4dn.xlarge (T4 GPU)",
        "",
        "Launch: docker compose",
        "  + docker-compose.gpu.yml (NVIDIA runtime)",
        "",
        "Database: PostgreSQL 16 + pgvector",
        "",
        "Compute: GPU-accelerated",
        "  • EasyOCR on CUDA",
        "  • YOLOv8 on CUDA",
        "  • PyTorch models on GPU",
        "",
        "Full Mode:",
        "  • 14 models with real video features",
        "  • Real OCR + YOLO detection",
        "",
        "Terraform IaC: all resources tagged",
        "  Project = video2knowledge",
    ],
    font_size=11, color=NUS_ORANGE, spacing=Pt(3)
)

# Model transfer arrow
transfer_y = Inches(5.9)
add_rect(slide9, Inches(1.3), transfer_y, Inches(11.2), Inches(0.6),
         NUS_BLUE)
add_textbox(slide9, Inches(1.4), transfer_y + Inches(0.08),
            Inches(11.0), Inches(0.45),
            "Model Transfer: Train on AWS (GPU) → .pkl files → Copy locally → Used for inference (CPU)",
            font_size=14, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)

# Security box
sec_y = Inches(6.6)
add_outlined_rect(slide9, Inches(1.3), sec_y, Inches(11.2), Inches(0.6),
                  ACCENT_RED, fill_color=LIGHT_RED_BG)
add_textbox(slide9, Inches(1.4), sec_y + Inches(0.1),
            Inches(11.0), Inches(0.4),
            "\U0001F512  Security: Security group allows SSH (22), API (8000), Frontend (5173) from user IP only  |  "
            "Private key auth  |  Tagged resources  |  gp3 encrypted EBS",
            font_size=11, color=ACCENT_RED, bold=True, alignment=PP_ALIGN.CENTER)


# ── Save ──────────────────────────────────────────────────────────────────────

output_path = "/Users/muneeswaranm/Projects/PRS/PatternRecognSystem-Video2Text/presentation/Video2Knowledge_Architecture.pptx"
prs.save(output_path)
print(f"Saved: {output_path}")
print(f"Slides: {len(prs.slides)}")
