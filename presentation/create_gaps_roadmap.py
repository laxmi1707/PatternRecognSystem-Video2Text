"""
Generate Video2Knowledge Architecture Gaps & Roadmap presentation.

Creates an 8-slide deck covering:
  1. Title
  2. Audit Overview (category scores)
  3. Critical Gaps — Fixed (3x2 grid)
  4. Architecture Strengths
  5. Production Readiness Roadmap (phased timeline)
  6. Before vs After Comparison
  7. Partially Implemented Features
  8. Architecture Maturity Assessment
"""

from pptx.util import Inches, Pt
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


def score_color(score):
    """Return color based on score out of 10."""
    if score >= 8:
        return ACCENT_GREEN
    elif score >= 6:
        return NUS_ORANGE
    else:
        return ACCENT_RED


# ── Presentation Setup ────────────────────────────────────────────────────────

prs = create_presentation()


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 1 — Title
# ══════════════════════════════════════════════════════════════════════════════

add_title_slide(
    prs,
    "Architecture Audit & Roadmap",
    subtitle="Gaps identified, fixes applied, and production roadmap",
    author="Video2Knowledge  |  Pattern Recognition System",
)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 2 — Audit Overview
# ══════════════════════════════════════════════════════════════════════════════

slide = add_content_slide(prs, "Architecture Audit Summary")

categories = [
    {
        "name": "Security",
        "score": 6,
        "color": NUS_ORANGE,
        "bg": LIGHT_ORANGE_BG,
        "desc": "CORS, UUID filenames, non-root Docker.\nMissing: auth, file validation, rate limiting",
    },
    {
        "name": "Resilience",
        "score": 5,
        "color": NUS_ORANGE,
        "bg": LIGHT_ORANGE_BG,
        "desc": "Per-model error handling, job failure tracking.\nMissing: timeouts, retries, circuit breakers",
    },
    {
        "name": "Observability",
        "score": 4,
        "color": ACCENT_RED,
        "bg": LIGHT_RED_BG,
        "desc": "Basic logging, health check.\nMissing: structured logging, metrics, tracing",
    },
    {
        "name": "Performance",
        "score": 5,
        "color": NUS_ORANGE,
        "bg": LIGHT_ORANGE_BG,
        "desc": "Async DB, background tasks.\nMissing: caching, connection pooling, model warm-up",
    },
]

card_width = Inches(2.8)
card_height = Inches(4.2)
start_x = Inches(1.3)
gap = Inches(0.35)
card_top = Inches(1.3)

for i, cat in enumerate(categories):
    x = start_x + i * (card_width + gap)

    # Card background
    add_rounded_rect(slide, x, card_top, card_width, card_height, cat["bg"])

    # Category name
    add_textbox(slide, x + Inches(0.2), card_top + Inches(0.2),
                card_width - Inches(0.4), Inches(0.4),
                cat["name"], font_size=20, color=NUS_ORANGE, bold=True,
                alignment=PP_ALIGN.CENTER)

    # Score circle
    circle_x = x + (card_width - Inches(1.2)) / 2
    circle = slide.shapes.add_shape(
        9,  # Oval
        circle_x, card_top + Inches(0.8),
        Inches(1.2), Inches(1.2)
    )
    circle.fill.solid()
    circle.fill.fore_color.rgb = cat["color"]
    circle.line.fill.background()
    tf = circle.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = f"{cat['score']}/10"
    p.font.size = Pt(24)
    p.font.color.rgb = WHITE
    p.font.bold = True
    p.font.name = "Calibri"
    p.alignment = PP_ALIGN.CENTER
    tf.paragraphs[0].space_before = Pt(14)

    # Description
    desc_lines = cat["desc"].split("\n")
    add_multiline_textbox(
        slide, x + Inches(0.15), card_top + Inches(2.2),
        card_width - Inches(0.3), Inches(1.8),
        desc_lines, font_size=11, color=LIGHT_GRAY,
        alignment=PP_ALIGN.CENTER, spacing=Pt(6)
    )

# Bottom summary
add_rounded_rect(slide, Inches(1.3), Inches(5.8), Inches(11.0), Inches(0.6),
                 ACCENT_BLUE,
                 "10 areas audited, 6 critical gaps identified and fixed",
                 font_size=16, font_color=WHITE, bold=True)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 3 — Critical Gaps Fixed (3x2 grid)
# ══════════════════════════════════════════════════════════════════════════════

slide = add_content_slide(prs, "6 Critical Gaps — Fixed")

fixes = [
    {
        "title": "File Upload Validation",
        "desc": "Added 500 MB size limit + extension whitelist\n(.mp4, .mov, .webm, .avi, .mkv).",
        "file": "routers/videos.py",
    },
    {
        "title": "Terraform Secrets in Git",
        "desc": "Added *.tfstate, terraform.tfvars, .env\nto .gitignore. Prevents credential exposure.",
        "file": ".gitignore",
    },
    {
        "title": "Event Loop Blocking",
        "desc": "Wrapped sync ML calls in asyncio.to_thread().\nPrevents UI freezes during classification.",
        "file": "routers/classification.py",
    },
    {
        "title": "No Error Handler",
        "desc": "Added global @app.exception_handler returning\nclean JSON instead of raw tracebacks.",
        "file": "main.py",
    },
    {
        "title": "No CI Tests",
        "desc": "Added test job (ruff lint + mypy type check +\npytest) that runs BEFORE deploy.",
        "file": "deploy-backend.yml",
    },
    {
        "title": "Hardcoded DB Credentials",
        "desc": "Changed to ${POSTGRES_PASSWORD:-postgres}\nenv vars with defaults.",
        "file": "docker-compose.yml",
    },
]

card_w = Inches(3.6)
card_h = Inches(2.5)
start_x = Inches(1.3)
col_gap = Inches(0.25)
row_gap = Inches(0.3)
start_y = Inches(1.3)

for idx, fix in enumerate(fixes):
    row = idx // 3
    col = idx % 3
    x = start_x + col * (card_w + col_gap)
    y = start_y + row * (card_h + row_gap)

    # Card background
    add_rounded_rect(slide, x, y, card_w, card_h, LIGHT_GREEN_BG)

    # Green checkmark circle
    check_circle = slide.shapes.add_shape(
        9, x + Inches(0.15), y + Inches(0.15), Inches(0.4), Inches(0.4)
    )
    check_circle.fill.solid()
    check_circle.fill.fore_color.rgb = ACCENT_GREEN
    check_circle.line.fill.background()
    tf_chk = check_circle.text_frame
    p_chk = tf_chk.paragraphs[0]
    p_chk.text = "✓"
    p_chk.font.size = Pt(18)
    p_chk.font.color.rgb = WHITE
    p_chk.font.bold = True
    p_chk.font.name = "Calibri"
    p_chk.alignment = PP_ALIGN.CENTER

    # Title
    add_textbox(slide, x + Inches(0.65), y + Inches(0.12),
                card_w - Inches(0.8), Inches(0.35),
                fix["title"], font_size=16, color=NUS_ORANGE, bold=True)

    # Description
    desc_lines = fix["desc"].split("\n")
    add_multiline_textbox(
        slide, x + Inches(0.25), y + Inches(0.6),
        card_w - Inches(0.5), Inches(1.3),
        desc_lines, font_size=12, color=LIGHT_GRAY, spacing=Pt(4)
    )

    # File reference
    add_textbox(slide, x + Inches(0.25), y + card_h - Inches(0.5),
                card_w - Inches(0.5), Inches(0.3),
                f"File: {fix['file']}", font_size=10, color=ACCENT_BLUE)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 4 — Architecture Strengths
# ══════════════════════════════════════════════════════════════════════════════

slide = add_content_slide(prs, "Architecture Strengths")

strengths = [
    "API versioning (/api/v1/) with OpenAPI/Swagger docs",
    "CORS properly configured from environment settings",
    "Async database operations (SQLAlchemy async + aiosqlite/asyncpg)",
    "Background job processing with real-time progress tracking",
    "Docker non-root user (security)",
    "CI/CD pipeline (GitHub Actions → ECR → App Runner)",
    "Comprehensive test suite (backend unit + API e2e + frontend)",
    "Pydantic request/response validation",
    "UUID-based filename sanitization (prevents path traversal)",
    "MLflow tracking scaffolding (ready to enable)",
    "S3 field prepared on Video model (ready to wire up)",
    "pgvector support in Docker image (ready for embeddings)",
]

# Two columns of 6 items each
col_items = [strengths[:6], strengths[6:]]
col_x = [Inches(1.3), Inches(7.0)]
item_y_start = Inches(1.3)
item_height = Inches(0.85)

for col_idx, items in enumerate(col_items):
    for row_idx, item in enumerate(items):
        x = col_x[col_idx]
        y = item_y_start + row_idx * item_height

        # Green checkmark circle
        check_circle = slide.shapes.add_shape(
            9, x, y + Inches(0.05), Inches(0.35), Inches(0.35)
        )
        check_circle.fill.solid()
        check_circle.fill.fore_color.rgb = ACCENT_GREEN
        check_circle.line.fill.background()
        tf_chk = check_circle.text_frame
        p_chk = tf_chk.paragraphs[0]
        p_chk.text = "✓"
        p_chk.font.size = Pt(16)
        p_chk.font.color.rgb = WHITE
        p_chk.font.bold = True
        p_chk.font.name = "Calibri"
        p_chk.alignment = PP_ALIGN.CENTER

        # Item text
        add_textbox(slide, x + Inches(0.5), y, Inches(5.5), Inches(0.45),
                    item, font_size=14, color=NUS_ORANGE)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 5 — Production Readiness Roadmap (phased timeline)
# ══════════════════════════════════════════════════════════════════════════════

slide = add_content_slide(prs, "Production Readiness Roadmap")

phases = [
    {
        "name": "Phase 1 — Security",
        "priority": "HIGH",
        "color": ACCENT_RED,
        "bg": LIGHT_RED_BG,
        "items": [
            "Authentication & Authorization (JWT/OAuth2)",
            "Rate limiting (slowapi middleware)",
            "Replace pickle with safer serialization (joblib + checksums)",
            "Input sanitization beyond Pydantic",
        ],
    },
    {
        "name": "Phase 2 — Data Management",
        "priority": "HIGH",
        "color": NUS_ORANGE,
        "bg": LIGHT_ORANGE_BG,
        "items": [
            "Alembic database migrations (schema versioning)",
            "S3 integration for video storage (field exists, needs wiring)",
            "Data retention/cleanup policy",
            "Backup strategy",
        ],
    },
    {
        "name": "Phase 3 — Observability",
        "priority": "MEDIUM",
        "color": ACCENT_BLUE,
        "bg": LIGHT_BLUE_BG,
        "items": [
            "Structured JSON logging with correlation IDs",
            "Prometheus /metrics endpoint",
            "Deep health check (verify DB + models + disk)",
            "OpenTelemetry distributed tracing",
        ],
    },
    {
        "name": "Phase 4 — Performance",
        "priority": "MEDIUM",
        "color": ACCENT_BLUE,
        "bg": LIGHT_BLUE_BG,
        "items": [
            "Redis caching layer for predictions",
            "Connection pooling configuration",
            "Model warm-up on startup",
            "Response compression (gzip)",
            "Streaming file uploads (avoid memory spikes)",
        ],
    },
    {
        "name": "Phase 5 — Scalability",
        "priority": "LOW",
        "color": ACCENT_GREEN,
        "bg": LIGHT_GREEN_BG,
        "items": [
            "Celery + Redis job queue (persistent background tasks)",
            "User management & multi-tenancy",
            "Model A/B testing",
            "Webhook notifications for job completion",
            "Graceful shutdown with drain logic",
        ],
    },
]

phase_width = Inches(2.2)
phase_gap = Inches(0.15)
phase_start_x = Inches(1.3)
phase_top = Inches(1.3)
phase_height = Inches(5.5)

for i, phase in enumerate(phases):
    x = phase_start_x + i * (phase_width + phase_gap)

    # Phase card background
    add_rounded_rect(slide, x, phase_top, phase_width, phase_height,
                     phase["bg"])

    # Phase header bar
    add_rounded_rect(slide, x, phase_top, phase_width, Inches(0.55),
                     phase["color"], phase["name"],
                     font_size=12, font_color=WHITE, bold=True)

    # Priority badge
    add_rounded_rect(slide, x + Inches(0.2), phase_top + Inches(0.7),
                     Inches(1.75), Inches(0.35),
                     phase["color"],
                     f"Priority: {phase['priority']}",
                     font_size=10, font_color=WHITE, bold=True)

    # Items
    item_y = phase_top + Inches(1.25)
    for item in phase["items"]:
        # Bullet dot
        dot = slide.shapes.add_shape(
            9, x + Inches(0.15), item_y + Inches(0.06),
            Inches(0.12), Inches(0.12)
        )
        dot.fill.solid()
        dot.fill.fore_color.rgb = phase["color"]
        dot.line.fill.background()

        # Item text
        add_textbox(slide, x + Inches(0.35), item_y,
                    phase_width - Inches(0.5), Inches(0.7),
                    item, font_size=10, color=NUS_ORANGE)
        item_y += Inches(0.75)

    # Arrow connector between phases (except last)
    if i < len(phases) - 1:
        arrow_x = x + phase_width + Inches(0.02)
        arrow = slide.shapes.add_shape(
            13,  # Right arrow
            arrow_x, phase_top + Inches(0.1),
            Inches(0.12), Inches(0.35)
        )
        arrow.fill.solid()
        arrow.fill.fore_color.rgb = LIGHT_GRAY
        arrow.line.fill.background()


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 6 — Before vs After Comparison
# ══════════════════════════════════════════════════════════════════════════════

slide = add_content_slide(prs, "Before vs After Audit Fixes")

before_items = [
    "Any file type/size uploaded",
    "Terraform secrets committed to git",
    "Sync ML blocks event loop → UI freezes",
    "Raw Python tracebacks shown to users",
    "Deploy without running tests",
    "Hardcoded database password",
]

after_items = [
    "File type (.mp4/.mov/.webm) + 500 MB limit enforced",
    "Terraform state/secrets in .gitignore",
    "ML runs in thread pool → UI stays responsive",
    "Clean JSON error responses with logging",
    "Lint + type check + pytest gate before deploy",
    "Environment variables with secure defaults",
]

col_width = Inches(5.3)
col_height = Inches(5.0)

# "Before" column (left, red-tinted)
before_x = Inches(1.3)
before_y = Inches(1.3)
add_rounded_rect(slide, before_x, before_y, col_width, col_height, LIGHT_RED_BG)

# Before header
add_rounded_rect(slide, before_x, before_y, col_width, Inches(0.6),
                 ACCENT_RED, "BEFORE", font_size=20, font_color=WHITE,
                 bold=True)

for idx, item in enumerate(before_items):
    y = before_y + Inches(0.8) + idx * Inches(0.65)
    # Red X
    add_textbox(slide, before_x + Inches(0.3), y,
                Inches(0.4), Inches(0.35),
                "✗", font_size=18, color=ACCENT_RED, bold=True)
    # Text
    add_textbox(slide, before_x + Inches(0.7), y,
                col_width - Inches(1.0), Inches(0.35),
                item, font_size=14, color=NUS_ORANGE)

# "After" column (right, green-tinted)
after_x = Inches(7.0)
after_y = Inches(1.3)
add_rounded_rect(slide, after_x, after_y, col_width, col_height, LIGHT_GREEN_BG)

# After header
add_rounded_rect(slide, after_x, after_y, col_width, Inches(0.6),
                 ACCENT_GREEN, "AFTER", font_size=20, font_color=WHITE,
                 bold=True)

for idx, item in enumerate(after_items):
    y = after_y + Inches(0.8) + idx * Inches(0.65)
    # Green check
    add_textbox(slide, after_x + Inches(0.3), y,
                Inches(0.4), Inches(0.35),
                "✓", font_size=18, color=ACCENT_GREEN, bold=True)
    # Text
    add_textbox(slide, after_x + Inches(0.7), y,
                col_width - Inches(1.0), Inches(0.35),
                item, font_size=14, color=NUS_ORANGE)

# Center arrow
arrow = slide.shapes.add_shape(
    13,  # Right arrow
    Inches(6.3), Inches(3.5), Inches(1.0), Inches(0.5)
)
arrow.fill.solid()
arrow.fill.fore_color.rgb = ACCENT_BLUE
arrow.line.fill.background()


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 7 — Partially Implemented Features
# ══════════════════════════════════════════════════════════════════════════════

slide = add_content_slide(prs, "Partially Implemented Features")

partial_features = [
    {
        "name": "MLflow Experiment Tracking",
        "status": "Code exists in tracking.py",
        "works": "log_training_run(), log_evaluation(), log_ablation_study()",
        "missing": "MLflow server not deployed, not in required deps",
        "enable": "pip install mlflow, set MLFLOW_TRACKING_URI, deploy MLflow server",
    },
    {
        "name": "S3 Video Storage",
        "status": "s3_key column exists on Video model",
        "works": "Database field ready",
        "missing": "boto3 upload logic, presigned URL generation",
        "enable": "Add boto3, configure AWS_S3_BUCKET, update upload endpoint",
    },
    {
        "name": "pgvector Embeddings",
        "status": "pgvector Docker image used",
        "works": "PostgreSQL with vector extension installed",
        "missing": "No embedding generation, no similarity search endpoints",
        "enable": "Add embedding model, create vector column, add search API",
    },
]

feat_width = Inches(3.6)
feat_height = Inches(5.3)
feat_gap = Inches(0.3)
feat_start_x = Inches(1.3)
feat_top = Inches(1.3)

for i, feat in enumerate(partial_features):
    x = feat_start_x + i * (feat_width + feat_gap)

    # Card background
    add_rounded_rect(slide, x, feat_top, feat_width, feat_height, CARD_BG)

    # Feature name header
    add_rounded_rect(slide, x, feat_top, feat_width, Inches(0.55),
                     ACCENT_PURPLE, feat["name"],
                     font_size=15, font_color=WHITE, bold=True)

    # Status
    row_y = feat_top + Inches(0.75)
    add_textbox(slide, x + Inches(0.2), row_y, feat_width - Inches(0.4),
                Inches(0.25), "Status:", font_size=11, color=LIGHT_GRAY,
                bold=True)
    add_textbox(slide, x + Inches(0.2), row_y + Inches(0.25),
                feat_width - Inches(0.4), Inches(0.35),
                feat["status"], font_size=12, color=NUS_ORANGE)

    # What works
    row_y += Inches(0.8)
    add_textbox(slide, x + Inches(0.2), row_y, feat_width - Inches(0.4),
                Inches(0.25), "What works:", font_size=11,
                color=ACCENT_GREEN, bold=True)
    add_textbox(slide, x + Inches(0.2), row_y + Inches(0.25),
                feat_width - Inches(0.4), Inches(0.5),
                feat["works"], font_size=11, color=NUS_ORANGE)

    # What's missing
    row_y += Inches(0.95)
    add_textbox(slide, x + Inches(0.2), row_y, feat_width - Inches(0.4),
                Inches(0.25), "What's missing:", font_size=11,
                color=ACCENT_RED, bold=True)
    add_textbox(slide, x + Inches(0.2), row_y + Inches(0.25),
                feat_width - Inches(0.4), Inches(0.5),
                feat["missing"], font_size=11, color=NUS_ORANGE)

    # To enable
    row_y += Inches(0.95)
    add_textbox(slide, x + Inches(0.2), row_y, feat_width - Inches(0.4),
                Inches(0.25), "To enable:", font_size=11,
                color=ACCENT_BLUE, bold=True)
    add_textbox(slide, x + Inches(0.2), row_y + Inches(0.25),
                feat_width - Inches(0.4), Inches(0.5),
                feat["enable"], font_size=11, color=NUS_ORANGE)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 8 — Architecture Maturity Assessment (Table)
# ══════════════════════════════════════════════════════════════════════════════

slide = add_content_slide(prs, "Architecture Maturity Assessment")

maturity_data = [
    ("Security", "7/10", NUS_ORANGE,
     "After fixes: file validation, .gitignore. Still needs auth."),
    ("API Design", "8/10", ACCENT_GREEN,
     "Versioned, typed, documented. Needs pagination."),
    ("Resilience", "6/10", NUS_ORANGE,
     "Error handling, job tracking. Needs retries, timeouts."),
    ("Observability", "4/10", ACCENT_RED,
     "Basic logging only. Needs metrics, tracing."),
    ("Performance", "6/10", NUS_ORANGE,
     "Async DB, background tasks. Needs caching, warm-up."),
    ("Testing", "7/10", NUS_ORANGE,
     "Good coverage. Needs security tests, load tests."),
    ("CI/CD", "8/10", ACCENT_GREEN,
     "After fix: test gate added. Needs staging env."),
    ("Documentation", "9/10", ACCENT_GREEN,
     "Excellent. README, guides, architecture docs."),
    ("Data Management", "5/10", NUS_ORANGE,
     "Needs migrations, backups, retention policy."),
    ("Scalability", "3/10", ACCENT_RED,
     "Single process. Needs job queue, multi-tenancy."),
]

# Table dimensions
table_left = Inches(1.3)
table_top = Inches(1.3)
table_width = Inches(11.0)
num_rows = len(maturity_data) + 1  # +1 for header
num_cols = 4
row_height = Inches(0.48)

table_shape = slide.shapes.add_table(
    num_rows, num_cols, table_left, table_top, table_width,
    Inches(row_height.inches * num_rows)
)
table = table_shape.table

# Set column widths
table.columns[0].width = Inches(2.0)
table.columns[1].width = Inches(1.0)
table.columns[2].width = Inches(1.2)
table.columns[3].width = Inches(6.8)

# Header row
headers = ["Dimension", "Score", "Status", "Notes"]
for col_idx, header in enumerate(headers):
    cell = table.cell(0, col_idx)
    cell.text = header
    for paragraph in cell.text_frame.paragraphs:
        paragraph.font.size = Pt(13)
        paragraph.font.color.rgb = WHITE
        paragraph.font.bold = True
        paragraph.font.name = "Calibri"
        paragraph.alignment = PP_ALIGN.CENTER
    cell.fill.solid()
    cell.fill.fore_color.rgb = ACCENT_BLUE
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE

# Data rows
for row_idx, (dim, score_text, color, notes) in enumerate(maturity_data):
    row = row_idx + 1

    # Dimension
    cell = table.cell(row, 0)
    cell.text = dim
    for p in cell.text_frame.paragraphs:
        p.font.size = Pt(12)
        p.font.color.rgb = NUS_ORANGE
        p.font.bold = True
        p.font.name = "Calibri"
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    cell.fill.solid()
    cell.fill.fore_color.rgb = CARD_BG if row % 2 == 0 else LIGHT_BG

    # Score
    cell = table.cell(row, 1)
    cell.text = score_text
    for p in cell.text_frame.paragraphs:
        p.font.size = Pt(13)
        p.font.color.rgb = color
        p.font.bold = True
        p.font.name = "Calibri"
        p.alignment = PP_ALIGN.CENTER
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    cell.fill.solid()
    cell.fill.fore_color.rgb = CARD_BG if row % 2 == 0 else LIGHT_BG

    # Status indicator
    score_val = int(score_text.split("/")[0])
    if score_val >= 8:
        status_text = "Good"
        status_color = ACCENT_GREEN
    elif score_val >= 6:
        status_text = "Fair"
        status_color = NUS_ORANGE
    else:
        status_text = "Needs Work"
        status_color = ACCENT_RED

    cell = table.cell(row, 2)
    cell.text = status_text
    for p in cell.text_frame.paragraphs:
        p.font.size = Pt(11)
        p.font.color.rgb = status_color
        p.font.bold = True
        p.font.name = "Calibri"
        p.alignment = PP_ALIGN.CENTER
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    cell.fill.solid()
    cell.fill.fore_color.rgb = CARD_BG if row % 2 == 0 else LIGHT_BG

    # Notes
    cell = table.cell(row, 3)
    cell.text = notes
    for p in cell.text_frame.paragraphs:
        p.font.size = Pt(11)
        p.font.color.rgb = LIGHT_GRAY
        p.font.name = "Calibri"
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    cell.fill.solid()
    cell.fill.fore_color.rgb = CARD_BG if row % 2 == 0 else LIGHT_BG

# Overall score box
overall_y = table_top + Inches(row_height.inches * num_rows) + Inches(0.3)
add_rounded_rect(slide, Inches(1.3), overall_y, Inches(11.0), Inches(0.7),
                 DARK_CARD)

# Overall score text — use manual runs for mixed formatting
txBox = slide.shapes.add_textbox(Inches(1.5), overall_y + Inches(0.05),
                                 Inches(10.6), Inches(0.6))
tf = txBox.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.alignment = PP_ALIGN.CENTER

run1 = p.add_run()
run1.text = "Overall Score: 6.3/10"
run1.font.size = Pt(20)
run1.font.color.rgb = WHITE
run1.font.bold = True
run1.font.name = "Calibri"

run2 = p.add_run()
run2.text = "  —  Strong for course project, clear path to production"
run2.font.size = Pt(16)
run2.font.color.rgb = LIGHT_GRAY
run2.font.bold = False
run2.font.name = "Calibri"


# ── Save ──────────────────────────────────────────────────────────────────────

output_path = "/Users/muneeswaranm/Projects/PRS/PatternRecognSystem-Video2Text/presentation/Video2Knowledge_GapsRoadmap.pptx"
prs.save(output_path)
print(f"Presentation saved: {output_path}")
print(f"Total slides: {len(prs.slides)}")
