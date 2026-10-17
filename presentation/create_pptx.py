"""Generate Video2Knowledge project presentation (NUS ISS template)."""
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from nus_iss_template import (
    create_presentation, add_title_slide, add_content_slide, add_section_slide,
    add_textbox, add_bullet_list, add_rect, add_rounded_rect,
    NUS_BLUE, NUS_ORANGE, WHITE, LIGHT_GRAY, SUBTLE_GRAY,
    ACCENT_BLUE, ACCENT_GREEN, ACCENT_PURPLE, ACCENT_RED,
    set_slide_bg, add_nus_logo, add_nus_footer,
)

TIER1_COLOR = ACCENT_BLUE
TIER2_COLOR = ACCENT_PURPLE
TIER3_COLOR = ACCENT_GREEN

prs = create_presentation()
W = prs.slide_width
H = prs.slide_height


# ============================================================
# SLIDE 1: Title
# ============================================================
add_title_slide(
    prs,
    title="Video2Knowledge",
    subtitle="A Multimodal Pattern Recognition Framework for\nScreen Activity Understanding and Knowledge Extraction",
    author="Muneeswaran Muthaiah",
    affiliation="M.Tech in Artificial Intelligence Systems\nNational University of Singapore",
    date_text="Pattern Recognition Systems  |  September 2026",
)


# ============================================================
# SLIDE 2: Agenda
# ============================================================
slide = add_content_slide(prs, "Agenda")

agenda_items = [
    "1.  Problem Statement & Motivation",
    "2.  Objectives",
    "3.  System Architecture",
    "4.  Feature Extraction Pipeline",
    "5.  Classification Models (3 Tiers, 14 Models)",
    "6.  Dataset — CUA-Suite",
    "7.  Training Pipeline & Results",
    "8.  Technology Stack",
    "9.  Live Demo",
    "10. Deployment (Docker + AWS)",
    "11. Challenges & Solutions",
    "12. Future Work & Conclusion",
]
add_bullet_list(slide, Inches(1.5), Inches(1.3), Inches(10), Inches(5.5),
                agenda_items, font_size=18, color=NUS_ORANGE, spacing=Pt(10))


# ============================================================
# SLIDE 3: Problem Statement
# ============================================================
slide = add_content_slide(prs, "Problem Statement")

problems = [
    "•  Screen recordings contain rich multimodal information (text, UI elements, visual patterns, user interactions) but are opaque to automated analysis",
    "•  Manually reviewing hours of screen activity recordings is time-consuming and error-prone",
    "•  Existing video classification approaches focus on natural video scenes, not screen activity patterns",
    "•  No unified framework combines OCR, UI detection, visual analysis, and interaction tracking for screen recordings",
]
add_bullet_list(slide, Inches(1.5), Inches(1.3), Inches(11), Inches(3),
                problems, font_size=17, color=NUS_ORANGE, spacing=Pt(16))

add_rounded_rect(slide, Inches(1.5), Inches(4.8), Inches(10), Inches(1.2),
                 RGBColor(0x00, 0x2A, 0x55),
                 "How can we automatically classify and understand screen activity\nfrom video recordings using multimodal pattern recognition?",
                 font_size=18, font_color=WHITE, bold=True)


# ============================================================
# SLIDE 4: Objectives
# ============================================================
slide = add_content_slide(prs, "Objectives")

objectives = [
    ("1", "Build a multimodal feature extraction pipeline combining OCR, UI detection, visual analysis, and interaction tracking into a unified 150-dimensional feature vector"),
    ("2", "Implement and benchmark 14 classification models across 3 tiers: Classical ML, Deep Learning, and Ensemble methods"),
    ("3", "Develop an end-to-end web application for video upload, analysis, and interactive model comparison"),
    ("4", "Train and evaluate on the CUA-Suite dataset (7,021 tasks, ~48 GB) for real-world screen activity classification"),
    ("5", "Deploy as a containerized microservice architecture using Docker and AWS"),
]

y = Inches(1.3)
for num, text in objectives:
    add_rounded_rect(slide, Inches(1.5), y, Inches(0.5), Inches(0.5),
                     NUS_ORANGE, num, font_size=16, font_color=WHITE, bold=True)
    add_textbox(slide, Inches(2.3), y, Inches(10), Inches(0.6),
                text, font_size=15, color=NUS_ORANGE)
    y += Inches(1.0)


# ============================================================
# SLIDE 5: System Architecture
# ============================================================
slide = add_content_slide(prs, "System Architecture")

# Pipeline flow boxes
boxes = [
    ("Upload\nVideo", ACCENT_BLUE),
    ("Feature\nExtraction", NUS_ORANGE),
    ("14 Classifiers\n(3 Tiers)", ACCENT_PURPLE),
    ("Model\nComparison", ACCENT_GREEN),
]

x = Inches(1.3)
for i, (label, color) in enumerate(boxes):
    add_rounded_rect(slide, x, Inches(1.5), Inches(2.5), Inches(1.2),
                     color, label, font_size=16, font_color=WHITE, bold=True)
    if i < len(boxes) - 1:
        add_textbox(slide, x + Inches(2.5), Inches(1.8), Inches(0.5), Inches(0.6),
                    "→", font_size=30, color=WHITE, alignment=PP_ALIGN.CENTER)
    x += Inches(2.9)

# Three-service architecture
services = [
    ("Frontend\nReact + TypeScript + Vite\nPort 5173", ACCENT_BLUE),
    ("Backend\nFastAPI + ML Pipeline\nPort 8000", NUS_ORANGE),
    ("Database\nPostgreSQL 16 + pgvector\nPort 5434", ACCENT_GREEN),
]

x = Inches(1.3)
for label, color in services:
    add_rounded_rect(slide, x, Inches(3.5), Inches(3.4), Inches(1.5),
                     color, label, font_size=14, font_color=WHITE, bold=True)
    x += Inches(3.6)

add_textbox(slide, Inches(1.3), Inches(5.3), Inches(11), Inches(0.5),
            "Docker Compose orchestrates all 3 services  |  SQLite for local dev, PostgreSQL for production",
            font_size=14, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)


# ============================================================
# SLIDE 6: Feature Extraction Pipeline
# ============================================================
slide = add_content_slide(prs, "Feature Extraction Pipeline",
                          "4 parallel extractors produce a unified 150-dimensional feature vector per video segment")

features = [
    ("OCR Features\n50 dimensions", "EasyOCR + Tesseract\nTF-IDF vectorization", ACCENT_BLUE),
    ("UI Detection\n30 dimensions", "YOLOv8 nano\n12 UI element classes", NUS_ORANGE),
    ("Visual Features\n40 dimensions", "OpenCV\nColor, edge, texture, layout", ACCENT_PURPLE),
    ("Interaction\n30 dimensions", "Action log parsing\n8 action types", ACCENT_GREEN),
]

x = Inches(1.0)
for title, desc, color in features:
    add_rounded_rect(slide, x, Inches(1.8), Inches(2.7), Inches(1.2),
                     color, title, font_size=15, font_color=WHITE, bold=True)
    add_textbox(slide, x + Inches(0.1), Inches(3.1), Inches(2.5), Inches(0.8),
                desc, font_size=12, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)
    x += Inches(3.0)

add_textbox(slide, Inches(3), Inches(4.0), Inches(7), Inches(0.5),
            "↓              ↓              ↓              ↓",
            font_size=24, color=WHITE, alignment=PP_ALIGN.CENTER)

add_rounded_rect(slide, Inches(3), Inches(4.5), Inches(7), Inches(0.8),
                 RGBColor(0x00, 0x2A, 0x55), "Concatenated 150-dim Feature Vector",
                 font_size=18, font_color=WHITE, bold=True)

add_textbox(slide, Inches(1.3), Inches(5.6), Inches(11), Inches(0.8),
            "[0-49] OCR  |  [50-79] UI Elements  |  [80-119] Visual  |  [120-149] Interaction",
            font_size=14, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)


# ============================================================
# SLIDE 7: OCR & UI Detection Details
# ============================================================
slide = add_content_slide(prs, "Feature Details", "OCR & UI Detection")

# OCR section
add_rounded_rect(slide, Inches(1.3), Inches(1.3), Inches(5.3), Inches(0.6),
                 ACCENT_BLUE, "OCR Features — 50 dimensions", font_size=16, font_color=WHITE, bold=True)
ocr_items = [
    "•  Primary: EasyOCR (GPU-optional)",
    "•  Fallback: Tesseract (when confidence < 0.3)",
    "•  TF-IDF vectorization (max_features=50)",
    "•  English stop words removal",
    "•  Extracts text from video keyframes",
]
add_bullet_list(slide, Inches(1.5), Inches(2.0), Inches(5), Inches(3),
                ocr_items, font_size=14, color=NUS_ORANGE, spacing=Pt(6))

# UI section
add_rounded_rect(slide, Inches(7.2), Inches(1.3), Inches(5.3), Inches(0.6),
                 NUS_ORANGE, "UI Detection — 30 dimensions", font_size=16, font_color=WHITE, bold=True)
ui_items = [
    "•  Model: YOLOv8n (nano), conf > 0.25",
    "•  12 UI classes: button, text_field, menu,",
    "    dropdown, toolbar, sidebar, tab, dialog,",
    "    terminal, icon, scroll_bar, status_bar",
    "•  [0:12]  Element type distribution",
    "•  [12:20] Spatial layout stats",
    "•  [20:24] Detection confidence stats",
    "•  [24:30] UI complexity metrics",
]
add_bullet_list(slide, Inches(7.4), Inches(2.0), Inches(5.1), Inches(4),
                ui_items, font_size=14, color=NUS_ORANGE, spacing=Pt(4))


# ============================================================
# SLIDE 8: Visual & Interaction Details
# ============================================================
slide = add_content_slide(prs, "Feature Details", "Visual & Interaction")

# Visual section
add_rounded_rect(slide, Inches(1.3), Inches(1.3), Inches(5.3), Inches(0.6),
                 ACCENT_PURPLE, "Visual Features — 40 dimensions", font_size=16, font_color=WHITE, bold=True)
visual_items = [
    "•  [0:18]  Color histogram (6 bins x 3 RGB)",
    "•  [18:21] Edge density (Canny + Sobel)",
    "•  [21:27] Texture (Gabor filters, 3 orientations)",
    "•  [27:32] Scene (intensity, saturation, brightness)",
    "•  [32:40] Layout (2x2 quadrant grid analysis)",
    "•  Averaged across all keyframes per segment",
]
add_bullet_list(slide, Inches(1.5), Inches(2.0), Inches(5), Inches(3),
                visual_items, font_size=14, color=NUS_ORANGE, spacing=Pt(6))

# Interaction section
add_rounded_rect(slide, Inches(7.2), Inches(1.3), Inches(5.3), Inches(0.6),
                 ACCENT_GREEN, "Interaction Features — 30 dimensions", font_size=16, font_color=WHITE, bold=True)
interaction_items = [
    "•  8 action types: CLICK, MOVE_TO, TYPING,",
    "    DRAG_TO, HOTKEY, PRESS, MOUSE_DOWN/UP",
    "•  [0:8]   Action frequency distribution",
    "•  [8:12]  Click position statistics",
    "•  [12:18] Temporal metrics (duration, speed)",
    "•  [18:24] Mouse movement analysis",
    "•  [24:28] Typing behavior metrics",
    "•  [28:30] Keyboard shortcut frequency",
]
add_bullet_list(slide, Inches(7.4), Inches(2.0), Inches(5.1), Inches(4),
                interaction_items, font_size=14, color=NUS_ORANGE, spacing=Pt(4))


# ============================================================
# SLIDE 9: Classification Models — Overview
# ============================================================
slide = add_content_slide(prs, "Classification Models", "14 Models, 3 Tiers")

# Tier 1
add_rounded_rect(slide, Inches(1.0), Inches(1.3), Inches(3.8), Inches(0.6),
                 TIER1_COLOR, "Tier 1 — Classical ML (7 models)", font_size=15, font_color=WHITE, bold=True)
tier1 = ["SVM", "Naive Bayes", "Decision Tree", "Random Forest", "KNN", "XGBoost", "LightGBM"]
y = Inches(2.0)
for m in tier1:
    add_textbox(slide, Inches(1.3), y, Inches(3.2), Inches(0.35),
                "•  " + m, font_size=14, color=NUS_ORANGE)
    y += Inches(0.35)

# Tier 2
add_rounded_rect(slide, Inches(5.2), Inches(1.3), Inches(3.5), Inches(0.6),
                 TIER2_COLOR, "Tier 2 — Deep Learning (4)", font_size=15, font_color=WHITE, bold=True)
tier2 = ["MLP (Multi-Layer Perceptron)", "CNN-1D", "LSTM", "Transformer"]
y = Inches(2.0)
for m in tier2:
    add_textbox(slide, Inches(5.5), y, Inches(3.2), Inches(0.35),
                "•  " + m, font_size=14, color=NUS_ORANGE)
    y += Inches(0.35)

# Tier 3
add_rounded_rect(slide, Inches(9.1), Inches(1.3), Inches(3.8), Inches(0.6),
                 TIER3_COLOR, "Tier 3 — Ensemble (3 models)", font_size=15, font_color=WHITE, bold=True)
tier3 = [
    ("Voting", "Soft voting: SVM + RF + MLP"),
    ("Stacking", "Base: SVM + RF + MLP"),
    ("Late Fusion", "Branches: SVM + RF"),
]
y = Inches(2.0)
for name, desc in tier3:
    add_textbox(slide, Inches(9.4), y, Inches(3.5), Inches(0.35),
                f"•  {name}", font_size=14, color=NUS_ORANGE, bold=True)
    add_textbox(slide, Inches(9.6), y + Inches(0.3), Inches(3.3), Inches(0.3),
                desc, font_size=12, color=LIGHT_GRAY)
    y += Inches(0.6)

# Bottom note
add_rounded_rect(slide, Inches(1.5), Inches(5.2), Inches(10), Inches(0.8),
                 RGBColor(0x00, 0x2A, 0x55),
                 "All 14 models run on the same 150-dim feature vector and produce comparable predictions with confidence scores",
                 font_size=14, font_color=NUS_ORANGE)


# ============================================================
# SLIDE 10: Dataset — CUA-Suite
# ============================================================
slide = add_content_slide(prs, "Dataset", "CUA-Suite (VideoCUA)")

# Stats boxes
stats = [
    ("7,021", "Tasks"),
    ("6,991", "Videos"),
    ("~48 GB", "Total Size"),
    ("MIT", "License"),
]
x = Inches(1.3)
for val, label in stats:
    add_rounded_rect(slide, x, Inches(1.3), Inches(2.5), Inches(1.2),
                     RGBColor(0x00, 0x2A, 0x55))
    add_textbox(slide, x, Inches(1.4), Inches(2.5), Inches(0.6),
                val, font_size=28, color=NUS_ORANGE, bold=True, alignment=PP_ALIGN.CENTER)
    add_textbox(slide, x, Inches(1.9), Inches(2.5), Inches(0.4),
                label, font_size=14, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)
    x += Inches(2.8)

add_textbox(slide, Inches(1.3), Inches(2.7), Inches(11), Inches(0.5),
            "Source: ServiceNow/VideoCUA on HuggingFace", font_size=14, color=LIGHT_GRAY)

# Activity labels
add_textbox(slide, Inches(1.3), Inches(3.2), Inches(11), Inches(0.5),
            "10 Activity Labels", font_size=20, color=WHITE, bold=True)

labels = [
    "git_operations", "docker_workflow", "kubernetes_ops", "terraform_iac", "aws_console",
    "jenkins_ci_cd", "coding_editing", "debugging", "documentation", "other",
]
x = Inches(1.3)
y = Inches(3.9)
for i, label in enumerate(labels):
    add_rounded_rect(slide, x, y, Inches(2.2), Inches(0.5),
                     NUS_ORANGE, label, font_size=12, font_color=WHITE)
    x += Inches(2.4)
    if (i + 1) % 5 == 0:
        x = Inches(1.3)
        y += Inches(0.65)

add_textbox(slide, Inches(1.3), Inches(5.3), Inches(11), Inches(0.5),
            "Labels derived from task instructions via keyword matching in dataset_loader.py",
            font_size=14, color=LIGHT_GRAY)


# ============================================================
# SLIDE 11: Training Pipeline
# ============================================================
slide = add_content_slide(prs, "Training Pipeline")

steps = [
    ("1", "Discover", "Scan dataset directory\n(nested dirs, .zip, .jsonl)"),
    ("2", "Split", "80/20 train/test\nstratified by task"),
    ("3", "Extract", "150-dim features\nvia FeatureAssembler"),
    ("4", "Augment", "5x augmentation if\n< 100 training samples"),
    ("5", "Train", "All 14 models\nsequentially"),
    ("6", "Evaluate", "Accuracy, F1-macro\nlatency, training time"),
]

x = Inches(0.8)
for num, title, desc in steps:
    add_rounded_rect(slide, x, Inches(1.5), Inches(1.9), Inches(0.5),
                     NUS_ORANGE, f"{num}. {title}", font_size=13, font_color=WHITE, bold=True)
    add_textbox(slide, x + Inches(0.1), Inches(2.1), Inches(1.7), Inches(0.8),
                desc, font_size=11, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)
    if num != "6":
        add_textbox(slide, x + Inches(1.9), Inches(1.55), Inches(0.3), Inches(0.4),
                    "→", font_size=20, color=WHITE, alignment=PP_ALIGN.CENTER)
    x += Inches(2.05)

# Training command
add_rounded_rect(slide, Inches(1.3), Inches(3.5), Inches(10.5), Inches(0.7),
                 RGBColor(0x00, 0x2A, 0x55),
                 "python -m app.train --dataset-root ./dataset --model-dir ./models",
                 font_size=14, font_color=ACCENT_GREEN)

# Sample results table
add_textbox(slide, Inches(1.3), Inches(4.5), Inches(11), Inches(0.5),
            "Sample Results (80-task subset)", font_size=18, color=WHITE, bold=True)

results_header = ["#", "Model", "Tier", "Accuracy", "F1 Macro", "Latency"]
results_data = [
    ["1", "Random Forest", "Tier 1", "0.8491", "0.6583", "27.6ms"],
    ["2", "Decision Tree", "Tier 1", "0.8868", "0.5808", "0.2ms"],
    ["3", "SVM", "Tier 1", "0.7925", "0.4964", "1.5ms"],
]

col_widths = [Inches(0.4), Inches(2.2), Inches(1.2), Inches(1.5), Inches(1.5), Inches(1.5)]
x_start = Inches(2)

# Header row
x = x_start
y = Inches(5.0)
for i, h in enumerate(results_header):
    add_rect(slide, x, y, col_widths[i], Inches(0.35), NUS_ORANGE)
    add_textbox(slide, x, y, col_widths[i], Inches(0.35),
                h, font_size=12, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)
    x += col_widths[i]

# Data rows
for row in results_data:
    y += Inches(0.35)
    x = x_start
    for i, cell in enumerate(row):
        add_rect(slide, x, y, col_widths[i], Inches(0.35), RGBColor(0x00, 0x2A, 0x55))
        add_textbox(slide, x, y, col_widths[i], Inches(0.35),
                    cell, font_size=12, color=NUS_ORANGE, alignment=PP_ALIGN.CENTER)
        x += col_widths[i]


# ============================================================
# SLIDE 12: Technology Stack
# ============================================================
slide = add_content_slide(prs, "Technology Stack")

# Backend
add_rounded_rect(slide, Inches(1.0), Inches(1.3), Inches(3.8), Inches(0.5),
                 ACCENT_BLUE, "Backend (Python 3.11)", font_size=14, font_color=WHITE, bold=True)
backend_items = [
    "•  FastAPI + Uvicorn",
    "•  PyTorch (Deep Learning)",
    "•  scikit-learn, XGBoost, LightGBM",
    "•  OpenCV (Computer Vision)",
    "•  EasyOCR + Tesseract (OCR)",
    "•  Ultralytics YOLOv8 (UI Detection)",
    "•  SQLAlchemy async + Pydantic",
]
add_bullet_list(slide, Inches(1.2), Inches(1.9), Inches(3.5), Inches(3.5),
                backend_items, font_size=13, color=NUS_ORANGE, spacing=Pt(4))

# Frontend
add_rounded_rect(slide, Inches(5.2), Inches(1.3), Inches(3.3), Inches(0.5),
                 NUS_ORANGE, "Frontend", font_size=14, font_color=WHITE, bold=True)
frontend_items = [
    "•  React + TypeScript",
    "•  Vite (build tool)",
    "•  nginx (production)",
    "•  Model comparison UI",
]
add_bullet_list(slide, Inches(5.4), Inches(1.9), Inches(3.1), Inches(2),
                frontend_items, font_size=13, color=NUS_ORANGE, spacing=Pt(4))

# Infrastructure
add_rounded_rect(slide, Inches(9.0), Inches(1.3), Inches(3.8), Inches(0.5),
                 ACCENT_GREEN, "Infrastructure", font_size=14, font_color=WHITE, bold=True)
infra_items = [
    "•  Docker Compose (3 services)",
    "•  PostgreSQL 16 + pgvector",
    "•  Terraform (IaC)",
    "•  AWS EC2 (training)",
    "•  HuggingFace Hub (dataset)",
]
add_bullet_list(slide, Inches(9.2), Inches(1.9), Inches(3.5), Inches(2.5),
                infra_items, font_size=13, color=NUS_ORANGE, spacing=Pt(4))

# Dev tools
add_rounded_rect(slide, Inches(5.2), Inches(3.4), Inches(3.3), Inches(0.5),
                 ACCENT_PURPLE, "Dev & Testing", font_size=14, font_color=WHITE, bold=True)
dev_items = [
    "•  pytest + pytest-asyncio",
    "•  ruff (linting), mypy (typing)",
    "•  Alembic (migrations)",
]
add_bullet_list(slide, Inches(5.4), Inches(4.0), Inches(3.1), Inches(1.5),
                dev_items, font_size=13, color=NUS_ORANGE, spacing=Pt(4))


# ============================================================
# SLIDE 13: Live Demo
# ============================================================
slide = add_section_slide(prs, "Live Demo",
                          "Upload a screen recording  →  Feature extraction  →  14 classifiers  →  Results")

add_textbox(slide, Inches(1), Inches(4.8), Inches(11), Inches(0.5),
            "http://localhost:5173", font_size=18, color=WHITE,
            alignment=PP_ALIGN.CENTER)


# ============================================================
# SLIDE 14: Demo — Upload Flow
# ============================================================
slide = add_content_slide(prs, "Demo", "Upload & Analysis Flow")

flow_steps = [
    ("1", "Upload", "Drop MP4/MOV/WebM\nscreen recording", ACCENT_BLUE),
    ("2", "Extract", "OCR + YOLO + OpenCV\n+ Action parsing", NUS_ORANGE),
    ("3", "Classify", "All 14 models run\non 150-dim vector", ACCENT_PURPLE),
    ("4", "Compare", "Ranked table with\nconfidence & latency", ACCENT_GREEN),
]

x = Inches(1.0)
for num, title, desc, color in flow_steps:
    add_rounded_rect(slide, x, Inches(1.5), Inches(2.8), Inches(1.8),
                     color, f"{title}", font_size=20, font_color=WHITE, bold=True)
    add_textbox(slide, x + Inches(0.2), Inches(2.5), Inches(2.4), Inches(0.8),
                desc, font_size=13, color=WHITE, alignment=PP_ALIGN.CENTER)
    x += Inches(3.0)

add_textbox(slide, Inches(1.3), Inches(3.8), Inches(11), Inches(1),
            "Progress bar shows real-time status: extracting frames → running OCR → detecting UI → analyzing visuals → reading interactions → classifying",
            font_size=15, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

# Screenshot placeholder
add_rounded_rect(slide, Inches(2.5), Inches(4.8), Inches(8), Inches(1.5),
                 RGBColor(0x00, 0x2A, 0x55),
                 "[Insert screenshot of the results page here]",
                 font_size=16, font_color=LIGHT_GRAY)


# ============================================================
# SLIDE 15: Deployment Architecture
# ============================================================
slide = add_content_slide(prs, "Deployment Architecture")

# Docker
add_rounded_rect(slide, Inches(1.0), Inches(1.3), Inches(5.5), Inches(0.6),
                 ACCENT_BLUE, "Docker Compose — Local Development", font_size=15, font_color=WHITE, bold=True)

docker_items = [
    "•  3 services: frontend, backend, database",
    "•  Backend: 6 GB memory limit for ML models",
    "•  PostgreSQL 16 + pgvector for embeddings",
    "•  Dataset mounted as read-only volume",
    "•  Models persisted in named volume",
    "•  Single command: docker compose up --build",
]
add_bullet_list(slide, Inches(1.2), Inches(2.0), Inches(5.3), Inches(3),
                docker_items, font_size=14, color=NUS_ORANGE, spacing=Pt(6))

# AWS
add_rounded_rect(slide, Inches(7.2), Inches(1.3), Inches(5.3), Inches(0.6),
                 NUS_ORANGE, "AWS EC2 — Training & Production", font_size=15, font_color=WHITE, bold=True)

aws_items = [
    "•  Instance: t3.xlarge (4 vCPU, 16 GB RAM)",
    "•  Storage: 100 GB EBS (gp3)",
    "•  AMI: Ubuntu 24.04",
    "•  Terraform IaC for resource provisioning",
    "•  All resources tagged: Project=video2knowledge",
    "•  Estimated training cost: ~$1.50-2.00",
]
add_bullet_list(slide, Inches(7.4), Inches(2.0), Inches(5.1), Inches(3),
                aws_items, font_size=14, color=NUS_ORANGE, spacing=Pt(6))

# Volume mapping diagram
add_textbox(slide, Inches(1.3), Inches(4.8), Inches(11), Inches(0.5),
            "Dataset → Docker Volume Mapping", font_size=18, color=WHITE, bold=True)
add_rounded_rect(slide, Inches(1.3), Inches(5.3), Inches(10.5), Inches(0.8),
                 RGBColor(0x00, 0x2A, 0x55),
                 "Host: ./dataset/VideoCUA/  ──volume (ro)──▶  Container: /app/dataset/\n"
                 "Host: ./models/            ──volume (rw)──▶  Container: /app/models/",
                 font_size=13, font_color=ACCENT_GREEN)


# ============================================================
# SLIDE 16: Challenges & Solutions
# ============================================================
slide = add_content_slide(prs, "Challenges & Solutions")

challenges = [
    ("macOS OpenMP Crash", "YOLO + PyTorch conflict on macOS", "Auto-detect OS; fallback to synthetic features locally, real extraction in Docker/Linux"),
    ("Large Dataset (48 GB)", "Cannot fit in memory or train locally", "Streaming dataset loader; AWS EC2 for cloud training; Google Colab as free alternative"),
    ("Slow CPU Inference", "YOLO on CPU takes minutes per video", "Batched frame processing; pin_memory disabled on CPU; GPU support via Docker"),
    ("Class Imbalance", "Uneven activity label distribution", "Stratified train/test split; 5x augmentation for datasets < 100 samples; F1-macro as primary metric"),
]

y = Inches(1.3)
for title, challenge, solution in challenges:
    add_rounded_rect(slide, Inches(1.3), y, Inches(2.5), Inches(0.5),
                     RGBColor(0x80, 0x2A, 0x00), title, font_size=13, font_color=WHITE, bold=True)
    add_textbox(slide, Inches(4.0), y, Inches(3.5), Inches(0.5),
                challenge, font_size=13, color=NUS_ORANGE)
    add_textbox(slide, Inches(7.8), y, Inches(5), Inches(1),
                solution, font_size=13, color=ACCENT_GREEN)
    y += Inches(1.2)


# ============================================================
# SLIDE 17: Future Work
# ============================================================
slide = add_content_slide(prs, "Future Work")

future_items = [
    ("RAG Pipeline", "Add retrieval-augmented generation for knowledge extraction from classified video segments"),
    ("MLflow Integration", "Experiment tracking, model versioning, and automated model selection"),
    ("GPU Optimization", "CUDA-accelerated inference for real-time video analysis"),
    ("Additional Datasets", "Extend beyond CUA-Suite to cover more diverse screen activity patterns"),
    ("Active Learning", "Iterative model improvement with user feedback on misclassified segments"),
]

y = Inches(1.3)
for title, desc in future_items:
    add_rounded_rect(slide, Inches(1.3), y, Inches(0.08), Inches(0.7), NUS_ORANGE)
    add_textbox(slide, Inches(1.7), y, Inches(3), Inches(0.4),
                title, font_size=16, color=WHITE, bold=True)
    add_textbox(slide, Inches(1.7), y + Inches(0.35), Inches(10.5), Inches(0.4),
                desc, font_size=14, color=NUS_ORANGE)
    y += Inches(0.95)


# ============================================================
# SLIDE 18: Conclusion
# ============================================================
slide = add_content_slide(prs, "Conclusion")

conclusions = [
    "✓  Built a multimodal feature extraction pipeline (150-dim vector from 4 modalities)",
    "✓  Implemented 14 classification models across 3 tiers with benchmarking",
    "✓  Developed a full-stack web application for video analysis and model comparison",
    "✓  Containerized with Docker and provisioned AWS infrastructure with Terraform",
    "✓  Validated on CUA-Suite dataset with 10 activity classes",
]

y = Inches(1.4)
for item in conclusions:
    add_textbox(slide, Inches(1.5), y, Inches(11), Inches(0.5),
                item, font_size=17, color=NUS_ORANGE)
    y += Inches(0.7)

# Key numbers
add_textbox(slide, Inches(1.3), Inches(4.9), Inches(11), Inches(0.5),
            "Key Numbers", font_size=20, color=WHITE, bold=True)

key_stats = [
    ("150", "Feature\nDimensions"),
    ("14", "Classification\nModels"),
    ("4", "Feature\nModalities"),
    ("10", "Activity\nClasses"),
]
x = Inches(1.8)
for val, label in key_stats:
    add_rounded_rect(slide, x, Inches(5.4), Inches(2.2), Inches(1.0),
                     NUS_ORANGE)
    add_textbox(slide, x, Inches(5.45), Inches(2.2), Inches(0.5),
                val, font_size=32, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)
    add_textbox(slide, x, Inches(5.85), Inches(2.2), Inches(0.5),
                label, font_size=12, color=WHITE, alignment=PP_ALIGN.CENTER)
    x += Inches(2.5)


# ============================================================
# SLIDE 19: Thank You / Q&A
# ============================================================
slide = add_section_slide(prs, "Thank You", "Questions & Discussion")

add_textbox(slide, Inches(1), Inches(4.5), Inches(11), Inches(0.5),
            "Muneeswaran Muthaiah  |  muthaiah_muneeswaran@u.nus.edu", font_size=16,
            color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

add_textbox(slide, Inches(1), Inches(5.2), Inches(11), Inches(0.5),
            "github.com/laxmi1707/PatternRecognSystem-Video2Text", font_size=14,
            color=WHITE, alignment=PP_ALIGN.CENTER)


# ============================================================
# Save
# ============================================================
output_path = "/Users/muneeswaranm/Projects/PRS/PatternRecognSystem-Video2Text/presentation/Video2Knowledge_Presentation.pptx"
prs.save(output_path)
print(f"Presentation saved to: {output_path}")
print(f"Total slides: {len(prs.slides)}")
