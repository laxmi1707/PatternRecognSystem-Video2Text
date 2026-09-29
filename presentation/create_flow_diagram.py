"""Generate Video2Knowledge end-to-end flow diagram as a PowerPoint."""
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


# ============================================================
# SLIDE 1: Title - E2E Flow
# ============================================================
slide = add_title_slide(
    prs,
    "End-to-End Video Analysis Flow",
    subtitle="What happens when a user uploads a screen recording",
)
add_textbox(slide, Inches(1), Inches(4.6), Inches(11), Inches(0.5),
            'Example: 53-second recording of "git pull" then "npm install" in VSCode',
            font_size=16, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)


# ============================================================
# SLIDE 2: High-Level Pipeline
# ============================================================
slide = add_content_slide(prs, "High-Level Pipeline")

# User upload
add_rounded_rect(slide, Inches(0.5), Inches(1.5), Inches(2.5), Inches(1),
                 ACCENT_BLUE, "User Uploads\nvideo.mp4", font_size=16, font_color=WHITE, bold=True)
add_textbox(slide, Inches(0.5), Inches(2.6), Inches(2.5), Inches(0.3),
            "http://localhost:5173", font_size=10, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

# Arrow
add_textbox(slide, Inches(3.0), Inches(1.7), Inches(0.5), Inches(0.5),
            "→", font_size=28, color=NUS_ORANGE, alignment=PP_ALIGN.CENTER)

# Frontend
add_rounded_rect(slide, Inches(3.5), Inches(1.5), Inches(2.2), Inches(1),
                 RGBColor(0x34, 0x98, 0xDB), "Frontend\nReact + Vite", font_size=16, font_color=WHITE, bold=True)
add_textbox(slide, Inches(3.5), Inches(2.6), Inches(2.2), Inches(0.3),
            "Progress bar + results UI", font_size=10, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

# Arrow
add_textbox(slide, Inches(5.7), Inches(1.7), Inches(0.5), Inches(0.5),
            "→", font_size=28, color=NUS_ORANGE, alignment=PP_ALIGN.CENTER)
add_textbox(slide, Inches(5.5), Inches(2.2), Inches(1), Inches(0.3),
            "POST /api/v1\n/jobs/analyze", font_size=8, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

# Backend box (large)
add_rounded_rect(slide, Inches(6.2), Inches(1.2), Inches(6.5), Inches(5.5),
                 CARD_BG)
add_textbox(slide, Inches(6.4), Inches(1.3), Inches(3), Inches(0.4),
            "Backend (FastAPI)", font_size=18, color=ACCENT_BLUE, bold=True)

# Step 1 - Segment
add_rounded_rect(slide, Inches(6.5), Inches(1.8), Inches(6), Inches(1.3),
                 WHITE)
add_rounded_rect(slide, Inches(6.6), Inches(1.85), Inches(1.8), Inches(0.35),
                 ACCENT_BLUE, "Step 1: Segment", font_size=11, font_color=WHITE, bold=True)
segments = [
    "Seg 1: 0:00-0:07  Opening editor",
    "Seg 2: 0:07-0:16  Opening terminal",
    "Seg 3: 0:16-0:29  git pull",
    "Seg 4: 0:29-0:58  npm install",
    "Seg 5: 0:58-1:12  Open browser",
    "Seg 6: 1:12-1:35  Check localhost",
    "Seg 7: 1:35-1:47  Verify app",
]
x_seg = Inches(6.7)
y_seg = Inches(2.3)
for seg in segments:
    add_textbox(slide, x_seg, y_seg, Inches(2.8), Inches(0.2),
                seg, font_size=8, color=NUS_ORANGE)
    y_seg += Inches(0.14)

# Arrow between steps
add_textbox(slide, Inches(9.2), Inches(2.2), Inches(0.4), Inches(0.6),
            "→", font_size=24, color=ACCENT_BLUE, alignment=PP_ALIGN.CENTER)

# Step 2 - Extract Features
add_rounded_rect(slide, Inches(9.5), Inches(1.85), Inches(2.8), Inches(0.35),
                 NUS_ORANGE, "Step 2: Extract Features", font_size=11, font_color=WHITE, bold=True)

extractors = [
    ("EasyOCR", "50-dim", ACCENT_BLUE, '"git pull origin main"'),
    ("YOLOv8", "30-dim", NUS_ORANGE, "terminal, tab, sidebar"),
    ("OpenCV", "40-dim", ACCENT_PURPLE, "dark theme, edges"),
    ("Actions", "30-dim", ACCENT_GREEN, "typing, clicks, Enter"),
]
y_ext = Inches(2.3)
for name, dim, color, desc in extractors:
    add_rounded_rect(slide, Inches(9.6), y_ext, Inches(1.2), Inches(0.22),
                     color, name, font_size=8, font_color=WHITE, bold=True)
    add_textbox(slide, Inches(10.85), y_ext, Inches(1.5), Inches(0.22),
                f"{dim}: {desc}", font_size=7, color=NUS_ORANGE)
    y_ext += Inches(0.25)

# 150-dim vector
add_rounded_rect(slide, Inches(9.6), Inches(3.35), Inches(2.8), Inches(0.25),
                 DARK_CARD, "= 150-dim feature vector", font_size=9, font_color=WHITE, bold=True)

# Step 3 - Classify
add_rounded_rect(slide, Inches(6.5), Inches(3.8), Inches(6), Inches(1.6),
                 WHITE)
add_rounded_rect(slide, Inches(6.6), Inches(3.85), Inches(1.8), Inches(0.35),
                 ACCENT_PURPLE, "Step 3: Classify", font_size=11, font_color=WHITE, bold=True)

models = [
    ("SVM", "git_ops 72%", "Tier 1"),
    ("Random Forest", "git_ops 89%", "Tier 1"),
    ("XGBoost", "git_ops 91%", "Tier 1"),
    ("LSTM", "coding 65%", "Tier 2"),
    ("Stacking", "git_ops 85%", "Tier 3"),
]

x_m = Inches(6.7)
y_m = Inches(4.3)
for name, result, tier in models:
    add_rounded_rect(slide, x_m, y_m, Inches(1.3), Inches(0.22),
                     ACCENT_PURPLE, name, font_size=8, font_color=WHITE)
    add_textbox(slide, x_m + Inches(1.4), y_m, Inches(1.4), Inches(0.22),
                f"→ {result}", font_size=8, color=NUS_ORANGE)
    add_textbox(slide, x_m + Inches(2.8), y_m, Inches(0.6), Inches(0.22),
                tier, font_size=7, color=LIGHT_GRAY)
    y_m += Inches(0.23)

add_textbox(slide, Inches(10), Inches(4.3), Inches(2.5), Inches(0.5),
            "... 14 models total\nAll run on the same\n150-dim vector", font_size=9, color=LIGHT_GRAY)

# Step 4 & 5
add_rounded_rect(slide, Inches(6.5), Inches(5.6), Inches(2.8), Inches(0.9),
                 WHITE)
add_rounded_rect(slide, Inches(6.6), Inches(5.65), Inches(2), Inches(0.3),
                 ACCENT_GREEN, "Step 4: Best Model", font_size=10, font_color=WHITE, bold=True)
add_textbox(slide, Inches(6.7), Inches(6.0), Inches(2.5), Inches(0.4),
            '"git_operations" 91%\n(XGBoost)', font_size=10, color=NUS_ORANGE, bold=True)

add_rounded_rect(slide, Inches(9.5), Inches(5.6), Inches(3), Inches(0.9),
                 WHITE)
add_rounded_rect(slide, Inches(9.6), Inches(5.65), Inches(2.5), Inches(0.3),
                 ACCENT_GREEN, "Step 5: Workflow Description", font_size=10, font_color=WHITE, bold=True)
add_textbox(slide, Inches(9.7), Inches(6.0), Inches(2.8), Inches(0.4),
            '"Ran a shell command:\ngit pull origin main"', font_size=10, color=NUS_ORANGE)

# Return arrow to frontend
add_textbox(slide, Inches(3.5), Inches(3.0), Inches(2.2), Inches(0.3),
            "JSON response ←", font_size=10, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

# Frontend result
add_rounded_rect(slide, Inches(0.3), Inches(3.3), Inches(5.5), Inches(3.8),
                 LIGHT_BLUE_BG)
add_textbox(slide, Inches(0.5), Inches(3.4), Inches(3), Inches(0.35),
            "ANALYSIS COMPLETE", font_size=14, color=ACCENT_GREEN, bold=True)
add_textbox(slide, Inches(0.5), Inches(3.75), Inches(4), Inches(0.3),
            "video.mp4 — 1:47 — 7 steps", font_size=12, color=NUS_ORANGE, bold=True)

# Model comparison table
add_textbox(slide, Inches(0.5), Inches(4.15), Inches(3), Inches(0.3),
            "Model Comparison — 14 Classifiers", font_size=11, color=NUS_ORANGE, bold=True)

table_data = [
    ("Model", "Tier", "Conf", "Latency"),
    ("XGBoost ★", "T1", "91%", "59ms"),
    ("Random Forest", "T1", "89%", "103ms"),
    ("Stacking", "T3", "85%", "6508ms"),
]
y_t = Inches(4.45)
for i, (m, t, c, l) in enumerate(table_data):
    bg = ACCENT_BLUE if i == 0 else WHITE
    fc = WHITE if i == 0 else NUS_ORANGE
    fs = 8
    add_rounded_rect(slide, Inches(0.5), y_t, Inches(5), Inches(0.22), bg)
    add_textbox(slide, Inches(0.6), y_t, Inches(1.5), Inches(0.22),
                m, font_size=fs, color=fc, bold=(i <= 1))
    add_textbox(slide, Inches(2.2), y_t, Inches(0.6), Inches(0.22),
                t, font_size=fs, color=fc)
    add_textbox(slide, Inches(3.0), y_t, Inches(0.8), Inches(0.22),
                c, font_size=fs, color=fc)
    add_textbox(slide, Inches(4.0), y_t, Inches(0.8), Inches(0.22),
                l, font_size=fs, color=fc)
    y_t += Inches(0.23)

# Workflow steps
add_textbox(slide, Inches(0.5), Inches(5.4), Inches(3), Inches(0.3),
            "Workflow Steps:", font_size=11, color=NUS_ORANGE, bold=True)
steps = [
    "1. Opened the code editor (0:00-0:07)",
    "2. Opened the integrated terminal (0:07-0:16)",
    "3. Ran shell command: git pull (0:16-0:29)",
    "4. Installed dependencies: npm install (0:29-0:58)",
    "5. Opened a browser tab (0:58-1:12)",
    "6. Checked localhost (1:12-1:35)",
    "7. Verified the app (1:35-1:47)",
]
y_s = Inches(5.7)
for step in steps:
    add_textbox(slide, Inches(0.6), y_s, Inches(4.5), Inches(0.18),
                step, font_size=8, color=NUS_ORANGE)
    y_s += Inches(0.16)


# ============================================================
# SLIDE 3: Feature Extraction Deep Dive
# ============================================================
slide = add_content_slide(prs, "Step 2 Deep Dive: Feature Extraction",
                          subtitle='Segment 3 keyframe — terminal showing "git pull origin main"')

# Frame placeholder
add_rounded_rect(slide, Inches(0.5), Inches(1.6), Inches(4), Inches(2.5),
                 RGBColor(0x2D, 0x2D, 0x2D))
add_multiline_textbox(slide, Inches(0.7), Inches(1.7), Inches(3.6), Inches(2.3),
                      [
                          "$ git pull origin main",
                          "Already up to date.",
                          "$ npm install",
                          "added 347 packages in 12s",
                          "",
                          "ubuntu@dev:~/project$",
                      ], font_size=11, color=ACCENT_GREEN)
add_textbox(slide, Inches(0.5), Inches(4.2), Inches(4), Inches(0.3),
            "Video keyframe (simulated terminal)", font_size=9, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

# Arrow
add_textbox(slide, Inches(4.5), Inches(2.5), Inches(0.5), Inches(0.5),
            "→", font_size=28, color=NUS_ORANGE, alignment=PP_ALIGN.CENTER)

# Four extractors
# OCR
add_rounded_rect(slide, Inches(5.2), Inches(1.6), Inches(3.7), Inches(1.1),
                 LIGHT_BLUE_BG)
add_rounded_rect(slide, Inches(5.3), Inches(1.65), Inches(2.2), Inches(0.3),
                 ACCENT_BLUE, "EasyOCR → TF-IDF", font_size=11, font_color=WHITE, bold=True)
add_textbox(slide, Inches(7.6), Inches(1.65), Inches(1.2), Inches(0.3),
            "50 dims", font_size=11, color=ACCENT_BLUE, bold=True)
add_multiline_textbox(slide, Inches(5.3), Inches(2.0), Inches(3.5), Inches(0.6),
                      [
                          'Reads: "git pull origin main Already up to date"',
                          'TF-IDF: git→0.82, pull→0.75, install→0.68, npm→0.71',
                          'Output: [0.82, 0.75, 0.68, 0.71, 0.01, 0.0, ...]',
                      ], font_size=8, color=NUS_ORANGE)

# UI Detection
add_rounded_rect(slide, Inches(5.2), Inches(2.85), Inches(3.7), Inches(1.1),
                 LIGHT_ORANGE_BG)
add_rounded_rect(slide, Inches(5.3), Inches(2.9), Inches(2.2), Inches(0.3),
                 NUS_ORANGE, "YOLOv8 nano", font_size=11, font_color=WHITE, bold=True)
add_textbox(slide, Inches(7.6), Inches(2.9), Inches(1.2), Inches(0.3),
            "30 dims", font_size=11, color=NUS_ORANGE, bold=True)
add_multiline_textbox(slide, Inches(5.3), Inches(3.25), Inches(3.5), Inches(0.6),
                      [
                          "Detects: terminal(1), tab(3), sidebar(1)",
                          "Layout: element positions, density, confidence",
                          "Complexity: has_terminal=1, has_sidebar=1",
                      ], font_size=8, color=NUS_ORANGE)

# Visual
add_rounded_rect(slide, Inches(5.2), Inches(4.1), Inches(3.7), Inches(1.1),
                 LIGHT_PURPLE_BG)
add_rounded_rect(slide, Inches(5.3), Inches(4.15), Inches(2.2), Inches(0.3),
                 ACCENT_PURPLE, "OpenCV", font_size=11, font_color=WHITE, bold=True)
add_textbox(slide, Inches(7.6), Inches(4.15), Inches(1.2), Inches(0.3),
            "40 dims", font_size=11, color=ACCENT_PURPLE, bold=True)
add_multiline_textbox(slide, Inches(5.3), Inches(4.5), Inches(3.5), Inches(0.6),
                      [
                          "Color: dark theme (low RGB bins)",
                          "Edges: high density (text + UI borders)",
                          "Texture: regular line patterns (code)",
                      ], font_size=8, color=NUS_ORANGE)

# Interaction
add_rounded_rect(slide, Inches(5.2), Inches(5.35), Inches(3.7), Inches(1.1),
                 LIGHT_GREEN_BG)
add_rounded_rect(slide, Inches(5.3), Inches(5.4), Inches(2.2), Inches(0.3),
                 ACCENT_GREEN, "Action Log Parser", font_size=11, font_color=WHITE, bold=True)
add_textbox(slide, Inches(7.6), Inches(5.4), Inches(1.2), Inches(0.3),
            "30 dims", font_size=11, color=ACCENT_GREEN, bold=True)
add_multiline_textbox(slide, Inches(5.3), Inches(5.75), Inches(3.5), Inches(0.6),
                      [
                          'Actions: TYPING("git pull"), PRESS(Enter), CLICK',
                          "Temporal: 7 actions, 0.58 actions/sec",
                          "Typing: 25 chars, speed=3.5 chars/sec",
                      ], font_size=8, color=NUS_ORANGE)

# Arrow to combined vector
add_textbox(slide, Inches(9.0), Inches(3.0), Inches(0.5), Inches(0.5),
            "→", font_size=28, color=NUS_ORANGE, alignment=PP_ALIGN.CENTER)

# Combined 150-dim vector
add_rounded_rect(slide, Inches(9.5), Inches(1.6), Inches(3.3), Inches(5.0),
                 DARK_CARD)
add_textbox(slide, Inches(9.6), Inches(1.7), Inches(3.1), Inches(0.4),
            "150-dim Feature Vector", font_size=14, color=WHITE, bold=True,
            alignment=PP_ALIGN.CENTER)

vector_parts = [
    ("[0-49]", "OCR", "0.82, 0.75, 0.68, ...", ACCENT_BLUE),
    ("[50-79]", "UI", "0.0, 0.0, ..., 0.8, ...", NUS_ORANGE),
    ("[80-119]", "Visual", "0.8, 0.1, 0.05, ...", ACCENT_PURPLE),
    ("[120-149]", "Interact", "0.29, 0.14, ...", ACCENT_GREEN),
]
y_v = Inches(2.2)
for idx, label, vals, color in vector_parts:
    add_rounded_rect(slide, Inches(9.7), y_v, Inches(2.9), Inches(0.9),
                     color)
    add_textbox(slide, Inches(9.8), y_v + Inches(0.05), Inches(1.2), Inches(0.25),
                f"{idx} {label}", font_size=10, color=WHITE, bold=True)
    add_textbox(slide, Inches(9.8), y_v + Inches(0.35), Inches(2.7), Inches(0.4),
                vals, font_size=9, color=RGBColor(0xE0, 0xE0, 0xE0))
    y_v += Inches(1.0)

add_textbox(slide, Inches(9.5), Inches(6.3), Inches(3.3), Inches(0.3),
            "Fed to all 14 classifiers →", font_size=11, color=LIGHT_GRAY,
            alignment=PP_ALIGN.CENTER)


# ============================================================
# SLIDE 4: Classification & Results
# ============================================================
slide = add_content_slide(prs, "Step 3-5: Classify, Compare, Display Results")

# 150-dim input
add_rounded_rect(slide, Inches(0.3), Inches(1.4), Inches(2.2), Inches(0.6),
                 DARK_CARD, "150-dim vector", font_size=13, font_color=WHITE, bold=True)

# Arrow
add_textbox(slide, Inches(2.5), Inches(1.5), Inches(0.4), Inches(0.4),
            "→", font_size=24, color=NUS_ORANGE, alignment=PP_ALIGN.CENTER)

# 14 Models box
add_rounded_rect(slide, Inches(3.0), Inches(1.2), Inches(4.5), Inches(5.0),
                 CARD_BG)
add_textbox(slide, Inches(3.2), Inches(1.3), Inches(4), Inches(0.4),
            "14 Classifiers (3 Tiers)", font_size=16, color=NUS_ORANGE, bold=True)

# Tier 1
add_rounded_rect(slide, Inches(3.2), Inches(1.8), Inches(4.1), Inches(0.3),
                 ACCENT_BLUE, "Tier 1 — Classical ML", font_size=10, font_color=WHITE, bold=True)
tier1_models = [
    ("SVM", "git_ops", "72%"),
    ("Naive Bayes", "other", "45%"),
    ("Decision Tree", "git_ops", "78%"),
    ("Random Forest", "git_ops", "89%"),
    ("KNN", "git_ops", "70%"),
    ("XGBoost", "git_ops", "91%"),
    ("LightGBM", "git_ops", "86%"),
]
y_m = Inches(2.15)
for name, pred, conf in tier1_models:
    add_textbox(slide, Inches(3.3), y_m, Inches(1.3), Inches(0.18),
                name, font_size=8, color=NUS_ORANGE)
    add_textbox(slide, Inches(4.7), y_m, Inches(1), Inches(0.18),
                f"→ {pred}", font_size=8, color=ACCENT_BLUE)
    add_textbox(slide, Inches(5.8), y_m, Inches(0.5), Inches(0.18),
                conf, font_size=8, color=NUS_ORANGE, bold=True)
    y_m += Inches(0.17)

# Tier 2
add_rounded_rect(slide, Inches(3.2), Inches(3.4), Inches(4.1), Inches(0.3),
                 ACCENT_PURPLE, "Tier 2 — Deep Learning", font_size=10, font_color=WHITE, bold=True)
tier2_models = [
    ("MLP", "git_ops", "68%"),
    ("CNN-1D", "git_ops", "74%"),
    ("LSTM", "coding", "65%"),
    ("Transformer", "git_ops", "71%"),
]
y_m = Inches(3.75)
for name, pred, conf in tier2_models:
    add_textbox(slide, Inches(3.3), y_m, Inches(1.3), Inches(0.18),
                name, font_size=8, color=NUS_ORANGE)
    add_textbox(slide, Inches(4.7), y_m, Inches(1), Inches(0.18),
                f"→ {pred}", font_size=8, color=ACCENT_PURPLE)
    add_textbox(slide, Inches(5.8), y_m, Inches(0.5), Inches(0.18),
                conf, font_size=8, color=NUS_ORANGE, bold=True)
    y_m += Inches(0.17)

# Tier 3
add_rounded_rect(slide, Inches(3.2), Inches(4.55), Inches(4.1), Inches(0.3),
                 ACCENT_GREEN, "Tier 3 — Ensemble", font_size=10, font_color=WHITE, bold=True)
tier3_models = [
    ("Voting", "git_ops", "82%"),
    ("Stacking", "git_ops", "85%"),
    ("Late Fusion", "git_ops", "83%"),
]
y_m = Inches(4.9)
for name, pred, conf in tier3_models:
    add_textbox(slide, Inches(3.3), y_m, Inches(1.3), Inches(0.18),
                name, font_size=8, color=NUS_ORANGE)
    add_textbox(slide, Inches(4.7), y_m, Inches(1), Inches(0.18),
                f"→ {pred}", font_size=8, color=ACCENT_GREEN)
    add_textbox(slide, Inches(5.8), y_m, Inches(0.5), Inches(0.18),
                conf, font_size=8, color=NUS_ORANGE, bold=True)
    y_m += Inches(0.17)

# Arrow to results
add_textbox(slide, Inches(7.5), Inches(3.0), Inches(0.5), Inches(0.5),
            "→", font_size=28, color=NUS_ORANGE, alignment=PP_ALIGN.CENTER)

# Best model
add_rounded_rect(slide, Inches(8.0), Inches(1.4), Inches(4.8), Inches(1.2),
                 ACCENT_GREEN)
add_textbox(slide, Inches(8.2), Inches(1.5), Inches(4.4), Inches(0.3),
            "Best Model: XGBoost", font_size=16, color=WHITE, bold=True)
add_textbox(slide, Inches(8.2), Inches(1.85), Inches(4.4), Inches(0.6),
            '"git_operations" — 91% confidence\nLatency: 59ms per prediction', font_size=12, color=WHITE)

# Result display
add_rounded_rect(slide, Inches(8.0), Inches(2.9), Inches(4.8), Inches(3.5),
                 LIGHT_BLUE_BG)
add_textbox(slide, Inches(8.2), Inches(3.0), Inches(4), Inches(0.35),
            "Results Displayed to User", font_size=14, color=NUS_ORANGE, bold=True)

# Comparison table
add_textbox(slide, Inches(8.2), Inches(3.4), Inches(4), Inches(0.25),
            "Model Comparison Table:", font_size=11, color=NUS_ORANGE, bold=True)
result_rows = [
    ("# ", "Model", "Tier", "Confidence", "Latency"),
    ("1", "XGBoost ★", "T1", "91%", "59ms"),
    ("2", "Random Forest", "T1", "89%", "103ms"),
    ("3", "LightGBM", "T1", "86%", "281ms"),
    ("4", "Stacking", "T3", "85%", "6509ms"),
    ("5", "Late Fusion", "T3", "83%", "2705ms"),
]
y_r = Inches(3.7)
for i, row in enumerate(result_rows):
    bg = ACCENT_BLUE if i == 0 else WHITE
    fc = WHITE if i == 0 else NUS_ORANGE
    add_rounded_rect(slide, Inches(8.2), y_r, Inches(4.4), Inches(0.2), bg)
    add_textbox(slide, Inches(8.3), y_r, Inches(0.3), Inches(0.2), row[0], font_size=7, color=fc)
    add_textbox(slide, Inches(8.6), y_r, Inches(1.3), Inches(0.2), row[1], font_size=7, color=fc, bold=(i <= 1))
    add_textbox(slide, Inches(10.0), y_r, Inches(0.5), Inches(0.2), row[2], font_size=7, color=fc)
    add_textbox(slide, Inches(10.6), y_r, Inches(0.8), Inches(0.2), row[3], font_size=7, color=fc)
    add_textbox(slide, Inches(11.5), y_r, Inches(0.8), Inches(0.2), row[4], font_size=7, color=fc)
    y_r += Inches(0.22)

# Workflow
add_textbox(slide, Inches(8.2), Inches(5.1), Inches(4), Inches(0.25),
            "Workflow Timeline:", font_size=11, color=NUS_ORANGE, bold=True)
workflow = [
    "1. Opened the code editor (0:00-0:07)",
    "2. Opened the integrated terminal (0:07-0:16)",
    "3. Ran shell command: git pull (0:16-0:29)",
    "4. Installed dependencies: npm install (0:29-0:58)",
    "5. Opened a browser tab (0:58-1:12)",
]
y_w = Inches(5.35)
for step in workflow:
    add_textbox(slide, Inches(8.3), y_w, Inches(4.3), Inches(0.18),
                step, font_size=8, color=NUS_ORANGE)
    y_w += Inches(0.16)


# ============================================================
# Save
# ============================================================
output_path = "/Users/muneeswaranm/Projects/PRS/PatternRecognSystem-Video2Text/presentation/Video2Knowledge_FlowDiagram.pptx"
prs.save(output_path)
print(f"Saved to: {output_path}")
print(f"Total slides: {len(prs.slides)}")
