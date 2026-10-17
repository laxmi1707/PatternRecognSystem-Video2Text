"""Generate Video2Knowledge complete code flow presentation as a PowerPoint."""
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


def add_code_block(slide, left, top, width, height, lines, font_size=9):
    """Add a dark code block with monospaced text."""
    add_rounded_rect(slide, left, top, width, height, DARK_CARD)
    add_multiline_textbox(slide, left + Inches(0.15), top + Inches(0.1),
                          width - Inches(0.3), height - Inches(0.2),
                          lines, font_size=font_size,
                          color=ACCENT_GREEN, font_name="Courier New",
                          spacing=Pt(2))


# ============================================================
# SLIDE 1: Title
# ============================================================
slide = add_title_slide(prs,
                        "Video2Knowledge: Complete Code Flow",
                        subtitle="Tracing a video from upload to classification results")

# Step indicators at bottom
step_labels = ["Upload", "Hook", "API", "Router", "Pipeline",
               "Frames", "Features", "Extractors", "ML", "Classifiers",
               "Compare", "Results", "Display"]
x_start = Inches(0.8)
for i, label in enumerate(step_labels):
    colors = [ACCENT_BLUE, ACCENT_BLUE, ACCENT_GREEN, ACCENT_GREEN,
              NUS_ORANGE, NUS_ORANGE, ACCENT_PURPLE, ACCENT_PURPLE,
              ACCENT_BLUE, ACCENT_BLUE, ACCENT_GREEN, ACCENT_GREEN,
              NUS_ORANGE]
    add_rounded_rect(slide, x_start + Inches(i * 0.92), Inches(5.5),
                     Inches(0.85), Inches(0.35), colors[i % len(colors)],
                     label, font_size=8, font_color=WHITE, bold=True)


# ============================================================
# SLIDE 2: Architecture Overview
# ============================================================
slide = add_content_slide(prs, "Architecture Overview",
                          "Three-layer architecture with key files in each layer")

# --- Frontend Layer ---
add_rounded_rect(slide, Inches(1.3), Inches(1.3), Inches(11.5), Inches(1.6),
                 LIGHT_BLUE_BG)
add_rounded_rect(slide, Inches(1.4), Inches(1.35), Inches(3.2), Inches(0.4),
                 ACCENT_BLUE, "Frontend (React + TypeScript + Vite) -- port 5173",
                 font_size=11, font_color=WHITE, bold=True)

fe_files = [
    ("UploadPage.tsx", "User drops video"),
    ("useVideoAnalysis.ts", "Orchestrates flow"),
    ("analysisService.ts", "API calls"),
    ("VideoResults.tsx", "Displays results"),
]
x_fe = Inches(1.5)
for fname, desc in fe_files:
    add_rounded_rect(slide, x_fe, Inches(1.9), Inches(2.5), Inches(0.7),
                     WHITE, font_size=10)
    add_textbox(slide, x_fe + Inches(0.1), Inches(1.92), Inches(2.3), Inches(0.3),
                fname, font_size=11, color=ACCENT_BLUE, bold=True)
    add_textbox(slide, x_fe + Inches(0.1), Inches(2.25), Inches(2.3), Inches(0.3),
                desc, font_size=9, color=LIGHT_GRAY)
    x_fe += Inches(2.7)

# Arrows between frontend files
for i in range(3):
    ax = Inches(4.05) + Inches(i * 2.7)
    add_textbox(slide, ax, Inches(2.1), Inches(0.3), Inches(0.3),
                "->", font_size=14, color=ACCENT_BLUE, bold=True,
                alignment=PP_ALIGN.CENTER)

# --- Backend Layer ---
add_rounded_rect(slide, Inches(1.3), Inches(3.2), Inches(11.5), Inches(1.6),
                 LIGHT_ORANGE_BG)
add_rounded_rect(slide, Inches(1.4), Inches(3.25), Inches(3.5), Inches(0.4),
                 NUS_ORANGE, "Backend (FastAPI + ML Pipeline) -- port 8000",
                 font_size=11, font_color=WHITE, bold=True)

be_files = [
    ("jobs.py", "Router entry point"),
    ("classification_service.py", "Pipeline orchestrator"),
    ("feature_assembler.py", "150-dim vectors"),
    ("ml_service.py", "Model hub"),
]
x_be = Inches(1.5)
for fname, desc in be_files:
    add_rounded_rect(slide, x_be, Inches(3.8), Inches(2.5), Inches(0.7),
                     WHITE, font_size=10)
    add_textbox(slide, x_be + Inches(0.1), Inches(3.82), Inches(2.3), Inches(0.3),
                fname, font_size=11, color=NUS_ORANGE, bold=True)
    add_textbox(slide, x_be + Inches(0.1), Inches(4.15), Inches(2.3), Inches(0.3),
                desc, font_size=9, color=LIGHT_GRAY)
    x_be += Inches(2.7)

# Arrows between backend files
for i in range(3):
    ax = Inches(4.05) + Inches(i * 2.7)
    add_textbox(slide, ax, Inches(4.0), Inches(0.3), Inches(0.3),
                "->", font_size=14, color=NUS_ORANGE, bold=True,
                alignment=PP_ALIGN.CENTER)

# --- Database Layer ---
add_rounded_rect(slide, Inches(1.3), Inches(5.1), Inches(11.5), Inches(1.2),
                 LIGHT_GREEN_BG)
add_rounded_rect(slide, Inches(1.4), Inches(5.15), Inches(3.5), Inches(0.4),
                 ACCENT_GREEN, "Database (PostgreSQL + pgvector) -- port 5434",
                 font_size=11, font_color=WHITE, bold=True)

db_items = [
    ("videos", "Video metadata + file paths"),
    ("jobs", "Job status + parameters"),
    ("classification_results", "Model predictions + probabilities"),
]
x_db = Inches(1.5)
for tname, desc in db_items:
    add_rounded_rect(slide, x_db, Inches(5.65), Inches(3.4), Inches(0.5),
                     WHITE, font_size=10)
    add_textbox(slide, x_db + Inches(0.1), Inches(5.67), Inches(3.2), Inches(0.22),
                tname, font_size=11, color=ACCENT_GREEN, bold=True)
    add_textbox(slide, x_db + Inches(0.1), Inches(5.9), Inches(3.2), Inches(0.22),
                desc, font_size=9, color=LIGHT_GRAY)
    x_db += Inches(3.7)

# Vertical arrows connecting layers
for x_pos in [Inches(2.8), Inches(5.5), Inches(8.2), Inches(10.9)]:
    add_textbox(slide, x_pos, Inches(2.9), Inches(0.4), Inches(0.3),
                "v", font_size=16, color=LIGHT_GRAY, bold=True,
                alignment=PP_ALIGN.CENTER)
    add_textbox(slide, x_pos, Inches(4.8), Inches(0.4), Inches(0.3),
                "v", font_size=16, color=LIGHT_GRAY, bold=True,
                alignment=PP_ALIGN.CENTER)


# ============================================================
# SLIDE 3: Steps 1-2 -- Frontend Upload & Hook
# ============================================================
slide = add_content_slide(prs, "Steps 1-2: Upload & Analysis Hook")

# Left side: UploadPage.tsx
add_rounded_rect(slide, Inches(1.3), Inches(1.3), Inches(5.3), Inches(5.2),
                 LIGHT_BLUE_BG)
add_rounded_rect(slide, Inches(1.4), Inches(1.35), Inches(2.8), Inches(0.4),
                 ACCENT_BLUE, "Step 1: UploadPage.tsx", font_size=13,
                 font_color=WHITE, bold=True)

add_multiline_textbox(slide, Inches(1.5), Inches(1.9), Inches(4.9), Inches(1.5),
                      [
                          {"text": "User drops video.mp4 on VideoDropzone", "bold": True},
                          "",
                          "onFileSelected(file) callback triggers",
                          "",
                          "Hands the file to the useVideoAnalysis hook",
                      ], font_size=14, color=NUS_ORANGE)

add_code_block(slide, Inches(1.5), Inches(3.3), Inches(4.9), Inches(1.8),
               [
                   "<VideoDropzone",
                   "  onFileSelected={handleFileSelected}",
                   "  accept='video/*'",
                   "/>",
                   "",
                   "// handleFileSelected calls:",
                   "const { startAnalysis } = useVideoAnalysis();",
                   "startAnalysis(file);",
               ], font_size=10)

add_textbox(slide, Inches(1.5), Inches(5.3), Inches(4.9), Inches(0.3),
            "SourceCode/frontend/src/pages/UploadPage.tsx",
            font_size=9, color=LIGHT_GRAY, font_name="Courier New")

# Arrow between panels
add_textbox(slide, Inches(6.6), Inches(3.3), Inches(0.5), Inches(0.5),
            "->", font_size=28, color=ACCENT_BLUE, bold=True,
            alignment=PP_ALIGN.CENTER)

# Right side: useVideoAnalysis.ts
add_rounded_rect(slide, Inches(7.1), Inches(1.3), Inches(5.5), Inches(5.2),
                 LIGHT_BLUE_BG)
add_rounded_rect(slide, Inches(7.2), Inches(1.35), Inches(3.2), Inches(0.4),
                 ACCENT_BLUE, "Step 2: useVideoAnalysis.ts", font_size=13,
                 font_color=WHITE, bold=True)

add_multiline_textbox(slide, Inches(7.4), Inches(1.9), Inches(5.0), Inches(1.8),
                      [
                          {"text": "startAnalysis(file) orchestrates the flow", "bold": True},
                          "",
                          "Sets screen to 'analyzing', creates video URL",
                          "",
                          "Calls analyzeVideo() from analysis service",
                          "",
                          "Progress bar starts: 0% -> 90%",
                      ], font_size=14, color=NUS_ORANGE)

add_code_block(slide, Inches(7.4), Inches(3.6), Inches(5.0), Inches(1.5),
               [
                   "const startAnalysis = async (file: File) => {",
                   "  setScreen('analyzing');",
                   "  const videoUrl = URL.createObjectURL(file);",
                   "  const result = await analyzeVideo(file);",
                   "  // result => { results, modelComparison,",
                   "  //              bestModel, workflowSteps }",
                   "};",
               ], font_size=10)

add_textbox(slide, Inches(7.4), Inches(5.3), Inches(5.0), Inches(0.3),
            "SourceCode/frontend/src/hooks/useVideoAnalysis.ts",
            font_size=9, color=LIGHT_GRAY, font_name="Courier New")


# ============================================================
# SLIDE 4: Step 3 -- API Calls
# ============================================================
slide = add_content_slide(prs, "Step 3: Two API Calls",
                          "SourceCode/frontend/src/services/analysisService.ts")

# Call 1
add_rounded_rect(slide, Inches(1.3), Inches(1.3), Inches(5.5), Inches(2.3),
                 LIGHT_BLUE_BG)
add_rounded_rect(slide, Inches(1.4), Inches(1.35), Inches(1.4), Inches(0.35),
                 ACCENT_BLUE, "Call 1", font_size=12, font_color=WHITE, bold=True)
add_textbox(slide, Inches(2.9), Inches(1.35), Inches(4), Inches(0.35),
            "Upload Video", font_size=14, color=NUS_ORANGE, bold=True)

add_code_block(slide, Inches(1.5), Inches(1.9), Inches(5.1), Inches(1.4),
               [
                   "POST /api/v1/videos/upload",
                   "  Content-Type: multipart/form-data",
                   "  Body: { file: video.mp4 }",
                   "",
                   "Response: { job_id: 42, id: 7 }",
               ], font_size=11)

# Arrow down
add_textbox(slide, Inches(3.8), Inches(3.65), Inches(0.5), Inches(0.4),
            "v", font_size=22, color=ACCENT_BLUE, bold=True,
            alignment=PP_ALIGN.CENTER)

# Call 2
add_rounded_rect(slide, Inches(1.3), Inches(4.0), Inches(5.5), Inches(2.3),
                 LIGHT_BLUE_BG)
add_rounded_rect(slide, Inches(1.4), Inches(4.05), Inches(1.4), Inches(0.35),
                 ACCENT_GREEN, "Call 2", font_size=12, font_color=WHITE, bold=True)
add_textbox(slide, Inches(2.9), Inches(4.05), Inches(4), Inches(0.35),
            "Run Classification", font_size=14, color=NUS_ORANGE, bold=True)

add_code_block(slide, Inches(1.5), Inches(4.6), Inches(5.1), Inches(1.4),
               [
                   "POST /api/v1/jobs/42/run",
                   "",
                   "Response: {",
                   "  results[], model_comparison[],",
                   "  best_model",
                   "}",
               ], font_size=11)

# Right side: Post-processing
add_rounded_rect(slide, Inches(7.2), Inches(1.3), Inches(5.5), Inches(5.0),
                 CARD_BG)
add_textbox(slide, Inches(7.4), Inches(1.4), Inches(5), Inches(0.4),
            "Post-Processing (Frontend)", font_size=16, color=NUS_ORANGE, bold=True)

processing_steps = [
    ("1. groupResultsByModel(results)",
     "Groups 98 raw results by model name"),
    ("2. mapResultsToSteps(bestResults)",
     "Converts best model's results -> WorkflowStep[]"),
    ("3. Builds modelComparison: ModelSummary[]",
     "14 entries with label, confidence, latency, tier"),
    ("4. Fallback: if backend unavailable",
     "Returns mock data so UI always works"),
]
y_proc = Inches(2.0)
for title, desc in processing_steps:
    add_rounded_rect(slide, Inches(7.4), y_proc, Inches(5.1), Inches(0.9),
                     WHITE)
    add_textbox(slide, Inches(7.6), y_proc + Inches(0.05), Inches(4.8), Inches(0.35),
                title, font_size=12, color=ACCENT_BLUE, bold=True,
                font_name="Courier New")
    add_textbox(slide, Inches(7.6), y_proc + Inches(0.4), Inches(4.8), Inches(0.35),
                desc, font_size=11, color=NUS_ORANGE)
    y_proc += Inches(1.05)


# ============================================================
# SLIDE 5: Step 4 -- Backend Router
# ============================================================
slide = add_content_slide(prs, "Step 4: Jobs Router (Backend Entry Point)",
                          "SourceCode/backend/app/routers/jobs.py")

# Router function flow
add_rounded_rect(slide, Inches(1.3), Inches(1.3), Inches(11.5), Inches(5.5),
                 CARD_BG)

# Decorator
add_rounded_rect(slide, Inches(1.5), Inches(1.5), Inches(4.5), Inches(0.5),
                 ACCENT_BLUE, '@router.post("/{job_id}/run")',
                 font_size=14, font_color=WHITE, bold=True)

# Flow steps
router_steps = [
    ("1", "Fetch job and video from database",
     "job = db.query(Job).get(job_id)\nvideo = db.query(Video).get(job.video_id)",
     ACCENT_BLUE),
    ("2", "Resolve video_path and action_log_path",
     'video_path = f"uploads/{video.filename}"\naction_log_path = video_path.replace(".mp4", "_actions.json")',
     NUS_ORANGE),
    ("3", "THE CORE CALL -- run_classification_job()",
     "results = run_classification_job(\n    db, job, video_path, action_log_path\n)",
     ACCENT_GREEN),
    ("4", "Build model comparison from results",
     "model_comparison = [\n    ModelComparison(model, label, confidence, latency)\n    for result in results\n]",
     ACCENT_PURPLE),
    ("5", "Return JobResultsResponse",
     "return JobResultsResponse(\n    job_id=job_id, status='completed',\n    results=results, model_comparison=mc,\n    best_model=best\n)",
     ACCENT_BLUE),
]

y_step = Inches(2.2)
for num, title, code, color in router_steps:
    # Step number circle
    add_rounded_rect(slide, Inches(1.6), y_step, Inches(0.4), Inches(0.4),
                     color, num, font_size=14, font_color=WHITE, bold=True)
    # Title
    add_textbox(slide, Inches(2.2), y_step, Inches(4), Inches(0.4),
                title, font_size=13, color=NUS_ORANGE, bold=True)
    # Code
    add_code_block(slide, Inches(6.2), y_step - Inches(0.05), Inches(6.3), Inches(0.85),
                   code.split("\n"), font_size=10)
    y_step += Inches(0.95)

# Highlight the core call
add_rounded_rect(slide, Inches(6.0), Inches(3.95), Inches(6.6), Inches(1.0),
                 RGBColor(0x28, 0xA7, 0x45))
add_textbox(slide, Inches(6.2), Inches(4.0), Inches(6.2), Inches(0.4),
            "THE CORE CALL", font_size=12, color=WHITE, bold=True)
add_multiline_textbox(slide, Inches(6.2), Inches(4.35), Inches(6.2), Inches(0.5),
                      [
                          "results = run_classification_job(db, job, video_path, action_log_path)",
                          "This single call triggers the entire ML pipeline (Slides 6-11)",
                      ], font_size=11, color=WHITE, font_name="Courier New")


# ============================================================
# SLIDE 6: Step 5 -- Classification Service
# ============================================================
slide = add_content_slide(prs, "Step 5: Classification Service -- The Heart of the Pipeline",
                          "SourceCode/backend/app/services/classification_service.py")

# Three phases
# Phase 1
add_rounded_rect(slide, Inches(1.3), Inches(1.3), Inches(3.5), Inches(3.5),
                 LIGHT_BLUE_BG)
add_rounded_rect(slide, Inches(1.4), Inches(1.35), Inches(3.0), Inches(0.4),
                 ACCENT_BLUE, "Phase 1: _extract_features()",
                 font_size=12, font_color=WHITE, bold=True)
add_textbox(slide, Inches(1.5), Inches(1.9), Inches(3.1), Inches(0.3),
            "Returns: (X, segments, used_yolo)", font_size=11,
            color=NUS_ORANGE, bold=True)

add_rounded_rect(slide, Inches(1.5), Inches(2.3), Inches(3.1), Inches(1.0),
                 WHITE)
add_textbox(slide, Inches(1.6), Inches(2.35), Inches(2.9), Inches(0.25),
            "Real path (Linux/Docker):", font_size=10, color=ACCENT_GREEN, bold=True)
add_textbox(slide, Inches(1.6), Inches(2.6), Inches(2.9), Inches(0.5),
            "YOLO + EasyOCR + OpenCV\nFull feature extraction from video frames",
            font_size=10, color=NUS_ORANGE)

add_rounded_rect(slide, Inches(1.5), Inches(3.4), Inches(3.1), Inches(0.8),
                 WHITE)
add_textbox(slide, Inches(1.6), Inches(3.45), Inches(2.9), Inches(0.25),
            "Synthetic path (macOS):", font_size=10, color=NUS_ORANGE, bold=True)
add_textbox(slide, Inches(1.6), Inches(3.7), Inches(2.9), Inches(0.4),
            "Random features fallback\nFor development and testing",
            font_size=10, color=NUS_ORANGE)

add_textbox(slide, Inches(1.5), Inches(4.3), Inches(3.1), Inches(0.3),
            "X shape: (n_segments, 150)", font_size=12,
            color=ACCENT_BLUE, bold=True)

# Phase 2
add_rounded_rect(slide, Inches(5.1), Inches(1.3), Inches(3.5), Inches(3.5),
                 LIGHT_ORANGE_BG)
add_rounded_rect(slide, Inches(5.2), Inches(1.35), Inches(3.0), Inches(0.4),
                 NUS_ORANGE, "Phase 2: _classify_all_models(X)",
                 font_size=12, font_color=WHITE, bold=True)
add_textbox(slide, Inches(5.3), Inches(1.9), Inches(3.1), Inches(0.3),
            "Returns: dict of predictions", font_size=11,
            color=NUS_ORANGE, bold=True)

# Tier lists
tier_data = [
    ("TIER 1 (7 models):", ACCENT_BLUE,
     ["svm", "naive_bayes", "decision_tree",
      "random_forest", "knn", "xgboost", "lightgbm"]),
    ("TIER 2 (4 models):", ACCENT_PURPLE,
     ["mlp", "cnn1d", "lstm", "transformer"]),
    ("TIER 3 (3 models):", ACCENT_GREEN,
     ["voting", "stacking", "late_fusion"]),
]
y_tier = Inches(2.3)
for tier_title, tier_color, models in tier_data:
    add_textbox(slide, Inches(5.3), y_tier, Inches(3.1), Inches(0.25),
                tier_title, font_size=10, color=tier_color, bold=True)
    add_textbox(slide, Inches(5.3), y_tier + Inches(0.25), Inches(3.1), Inches(0.3),
                ", ".join(models), font_size=9, color=NUS_ORANGE,
                font_name="Courier New")
    y_tier += Inches(0.65)

# Phase 3
add_rounded_rect(slide, Inches(8.9), Inches(1.3), Inches(3.9), Inches(3.5),
                 LIGHT_GREEN_BG)
add_rounded_rect(slide, Inches(9.0), Inches(1.35), Inches(3.5), Inches(0.4),
                 ACCENT_GREEN, "Phase 3: Save to Database",
                 font_size=12, font_color=WHITE, bold=True)
add_textbox(slide, Inches(9.1), Inches(1.9), Inches(3.5), Inches(0.3),
            "ClassificationResult per model", font_size=11,
            color=NUS_ORANGE, bold=True)

add_code_block(slide, Inches(9.1), Inches(2.3), Inches(3.5), Inches(2.2),
               [
                   "ClassificationResult(",
                   "  job_id = 42,",
                   "  model_name = 'xgboost',",
                   "  predicted_label = 'git_ops',",
                   "  confidence = 0.91,",
                   "  latency_ms = 59.2,",
                   "  probabilities = {...},",
                   "  tier = 'tier1'",
                   ")",
               ], font_size=9)

# Arrows between phases
add_textbox(slide, Inches(4.8), Inches(2.8), Inches(0.3), Inches(0.4),
            "->", font_size=20, color=ACCENT_BLUE, bold=True,
            alignment=PP_ALIGN.CENTER)
add_textbox(slide, Inches(8.6), Inches(2.8), Inches(0.3), Inches(0.4),
            "->", font_size=20, color=NUS_ORANGE, bold=True,
            alignment=PP_ALIGN.CENTER)

# Bottom summary
add_rounded_rect(slide, Inches(1.3), Inches(5.1), Inches(11.5), Inches(1.5),
                 DARK_CARD)
add_multiline_textbox(slide, Inches(1.5), Inches(5.2), Inches(11.0), Inches(1.3),
                      [
                          "def run_classification_job(db, job, video_path, action_log_path):",
                          "    X, segments, used_yolo = _extract_features(video_path, action_log_path)     # Phase 1",
                          "    predictions = _classify_all_models(X)                                       # Phase 2",
                          "    for model_name, preds in predictions.items():                               # Phase 3",
                          "        db.add(ClassificationResult(job_id=job.id, model_name=model_name, ...))",
                          "    return results",
                      ], font_size=11, color=ACCENT_GREEN, font_name="Courier New",
                      spacing=Pt(3))


# ============================================================
# SLIDE 7: Step 6 -- Video Processor
# ============================================================
slide = add_content_slide(prs, "Step 6: Video Processor (Frame Extraction)",
                          "SourceCode/backend/app/services/video_processor.py")

# Config box
add_rounded_rect(slide, Inches(1.3), Inches(1.3), Inches(5.2), Inches(1.2),
                 DARK_CARD)
add_multiline_textbox(slide, Inches(1.5), Inches(1.4), Inches(4.8), Inches(1.0),
                      [
                          "Config:",
                          "  sample_fps = 1.0          # 1 frame per second",
                          "  target_size = (640, 480)   # Resize all frames",
                          "  cluster_gap = 2.0s         # Group actions within 2 seconds",
                      ], font_size=11, color=ACCENT_GREEN, font_name="Courier New",
                      spacing=Pt(2))

# Main function
add_rounded_rect(slide, Inches(1.3), Inches(2.8), Inches(5.2), Inches(3.7),
                 LIGHT_BLUE_BG)
add_textbox(slide, Inches(1.5), Inches(2.9), Inches(4.8), Inches(0.4),
            "extract_segments(video_path, actions)", font_size=14,
            color=NUS_ORANGE, bold=True)

add_rounded_rect(slide, Inches(1.5), Inches(3.4), Inches(4.8), Inches(0.6),
                 WHITE)
add_rounded_rect(slide, Inches(1.6), Inches(3.45), Inches(0.4), Inches(0.3),
                 ACCENT_BLUE, "1", font_size=12, font_color=WHITE, bold=True)
add_textbox(slide, Inches(2.1), Inches(3.45), Inches(4.0), Inches(0.5),
            "_cluster_actions(actions)\nGroup by 2-second time gaps",
            font_size=11, color=NUS_ORANGE)

add_rounded_rect(slide, Inches(1.5), Inches(4.1), Inches(4.8), Inches(0.6),
                 WHITE)
add_rounded_rect(slide, Inches(1.6), Inches(4.15), Inches(0.4), Inches(0.3),
                 ACCENT_BLUE, "2", font_size=12, font_color=WHITE, bold=True)
add_textbox(slide, Inches(2.1), Inches(4.15), Inches(4.0), Inches(0.5),
            "For each cluster -> create SegmentData\nwith keyframes + actions",
            font_size=11, color=NUS_ORANGE)

add_rounded_rect(slide, Inches(1.5), Inches(4.8), Inches(4.8), Inches(0.6),
                 WHITE)
add_rounded_rect(slide, Inches(1.6), Inches(4.85), Inches(0.4), Inches(0.3),
                 ACCENT_BLUE, "3", font_size=12, font_color=WHITE, bold=True)
add_textbox(slide, Inches(2.1), Inches(4.85), Inches(4.0), Inches(0.5),
            "Extract keyframes at sample_fps rate\nResize to target_size",
            font_size=11, color=NUS_ORANGE)

# SegmentData structure
add_rounded_rect(slide, Inches(6.8), Inches(1.3), Inches(5.8), Inches(5.2),
                 CARD_BG)
add_textbox(slide, Inches(7.0), Inches(1.4), Inches(5.4), Inches(0.4),
            "SegmentData Structure", font_size=16, color=NUS_ORANGE, bold=True)

add_code_block(slide, Inches(7.0), Inches(1.9), Inches(5.4), Inches(3.0),
               [
                   "@dataclass",
                   "class SegmentData:",
                   "    segment_index: int          # 0, 1, 2, ...",
                   "    start_time: float            # e.g., 0.0",
                   "    end_time: float              # e.g., 7.2",
                   "",
                   "    keyframes: list[FrameData]   # Actual video frames",
                   "    # FrameData.frame: np.ndarray (640x480 BGR)",
                   "    # FrameData.timestamp: float",
                   "",
                   "    actions: list[dict]           # User interactions",
                   "    # {'type': 'click', 'x': 512, 'y': 340, 't': 2.1}",
                   "    # {'type': 'type',  'text': 'git pull', 't': 3.5}",
                   "    # {'type': 'press', 'key': 'Enter',     't': 4.0}",
               ], font_size=10)

# Visual example
add_rounded_rect(slide, Inches(7.0), Inches(5.1), Inches(5.4), Inches(1.2),
                 WHITE)
add_textbox(slide, Inches(7.2), Inches(5.15), Inches(5.0), Inches(0.3),
            "Example: 53s video -> 7 segments", font_size=12,
            color=ACCENT_BLUE, bold=True)

seg_examples = [
    "Seg 0: 0.0-7.2s  | 7 frames | [click, click]",
    "Seg 1: 7.2-16.0s | 9 frames | [click, type('cd project')]",
    "Seg 2: 16.0-29.0s| 13 frames| [type('git pull'), press(Enter)]",
]
y_seg = Inches(5.5)
for seg in seg_examples:
    add_textbox(slide, Inches(7.2), y_seg, Inches(5.0), Inches(0.2),
                seg, font_size=9, color=NUS_ORANGE, font_name="Courier New")
    y_seg += Inches(0.2)


# ============================================================
# SLIDE 8: Step 7 -- Feature Assembler
# ============================================================
slide = add_content_slide(prs, "Step 7: Feature Assembler (150-dim Vector)",
                          "SourceCode/backend/app/services/feature_assembler.py")

# MODALITY_MAP visualization
add_rounded_rect(slide, Inches(1.3), Inches(1.3), Inches(11.5), Inches(1.5),
                 DARK_CARD)
add_textbox(slide, Inches(1.5), Inches(1.35), Inches(3), Inches(0.35),
            "MODALITY_MAP", font_size=14, color=WHITE, bold=True)

# Colored segments for the 150-dim vector
modality_data = [
    ("ocr_text", "[0, 50)", "50 dims", ACCENT_BLUE, Inches(1.5), Inches(2.85)),
    ("ui_elements", "[50, 80)", "30 dims", NUS_ORANGE, Inches(4.45), Inches(1.5)),
    ("visual", "[80, 120)", "40 dims", ACCENT_PURPLE, Inches(6.45), Inches(2.0)),
    ("interaction", "[120, 150)", "30 dims", ACCENT_GREEN, Inches(9.25), Inches(1.5)),
]

bar_y = Inches(1.85)
bar_h = Inches(0.55)
x_pos = Inches(1.5)
for i, (name, rng, dims, color, _, w) in enumerate(modality_data):
    add_rounded_rect(slide, x_pos, bar_y, w, bar_h, color,
                     f"{name}: {rng}", font_size=11, font_color=WHITE, bold=True)
    add_textbox(slide, x_pos, bar_y + bar_h, w, Inches(0.25),
                dims, font_size=10, color=color, bold=True,
                alignment=PP_ALIGN.CENTER)
    x_pos += w + Inches(0.1)

# extract_segment_features function
add_rounded_rect(slide, Inches(1.3), Inches(3.1), Inches(5.5), Inches(3.5),
                 CARD_BG)
add_textbox(slide, Inches(1.5), Inches(3.2), Inches(5.1), Inches(0.4),
            "extract_segment_features(segment)", font_size=14,
            color=NUS_ORANGE, bold=True)

flow_steps = [
    ("1", "Allocate zeros(150)", "vector = np.zeros(150, dtype=np.float32)",
     ACCENT_BLUE),
    ("2", "If keyframes exist:", "Run OCR, UI, and Visual extractors",
     NUS_ORANGE),
    ("3", "OCR -> [0:50]", "vector[0:50] = ocr_extractor.extract(frames)",
     ACCENT_BLUE),
    ("4", "UI -> [50:80]", "vector[50:80] = ui_detector.extract(frames)",
     NUS_ORANGE),
    ("5", "Visual -> [80:120]", "vector[80:120] = visual_features.extract(frames)",
     ACCENT_PURPLE),
    ("6", "Interaction -> [120:150]", "vector[120:150] = interaction.extract(actions)",
     ACCENT_GREEN),
]

y_flow = Inches(3.7)
for num, title, code, color in flow_steps:
    add_rounded_rect(slide, Inches(1.5), y_flow, Inches(0.35), Inches(0.3),
                     color, num, font_size=10, font_color=WHITE, bold=True)
    add_textbox(slide, Inches(1.95), y_flow, Inches(1.8), Inches(0.3),
                title, font_size=10, color=NUS_ORANGE, bold=True)
    add_textbox(slide, Inches(3.8), y_flow, Inches(2.8), Inches(0.3),
                code, font_size=9, color=LIGHT_GRAY, font_name="Courier New")
    y_flow += Inches(0.42)

# Output vector visualization
add_rounded_rect(slide, Inches(7.1), Inches(3.1), Inches(5.5), Inches(3.5),
                 DARK_CARD)
add_textbox(slide, Inches(7.3), Inches(3.2), Inches(5.1), Inches(0.4),
            "Output: 150-dim float32 vector", font_size=14,
            color=WHITE, bold=True)

vector_sections = [
    ("OCR [0:50]", ACCENT_BLUE,
     "TF-IDF word scores\n'git'->0.82  'pull'->0.75  'install'->0.68"),
    ("UI [50:80]", NUS_ORANGE,
     "Element counts + layout\nterminal=1  tabs=3  sidebar=1  density=0.4"),
    ("Visual [80:120]", ACCENT_PURPLE,
     "Color + edges + texture\ndark_theme=0.8  edge_density=0.6  lines=0.7"),
    ("Interaction [120:150]", ACCENT_GREEN,
     "Action patterns\ntyping_speed=3.5  clicks=2  key_presses=5"),
]

y_vec = Inches(3.7)
for label, color, desc in vector_sections:
    add_rounded_rect(slide, Inches(7.3), y_vec, Inches(5.1), Inches(0.8),
                     color)
    add_textbox(slide, Inches(7.5), y_vec + Inches(0.03), Inches(2), Inches(0.25),
                label, font_size=11, color=WHITE, bold=True)
    add_textbox(slide, Inches(7.5), y_vec + Inches(0.3), Inches(4.7), Inches(0.4),
                desc, font_size=9, color=RGBColor(0xE0, 0xE0, 0xE0),
                font_name="Courier New")
    y_vec += Inches(0.87)


# ============================================================
# SLIDE 9: Steps 8-11 -- The Four Extractors
# ============================================================
slide = add_content_slide(prs, "Steps 8-11: Four Feature Extractors",
                          "Each extractor fills its slice of the 150-dim vector")

# 2x2 Grid
extractors = [
    {
        "title": "OCR Extractor",
        "file": "ocr_extractor.py",
        "color": ACCENT_BLUE,
        "bg": LIGHT_BLUE_BG,
        "dims": "50 dims [0:50]",
        "pipeline": [
            "EasyOCR reads text from keyframes",
            "Tesseract fallback if EasyOCR fails",
            "TF-IDF vectorization (max_features=50)",
            "Output: 50-dim word importance scores",
        ],
        "example": '"git pull origin main" -> [0.82, 0.75, ...]',
        "pos": (Inches(1.3), Inches(1.3)),
    },
    {
        "title": "UI Detector",
        "file": "ui_detector.py",
        "color": NUS_ORANGE,
        "bg": LIGHT_ORANGE_BG,
        "dims": "30 dims [50:80]",
        "pipeline": [
            "YOLOv8n (conf > 0.25)",
            "12 UI classes: button, textbox, tab, ...",
            "Counts + layout + confidence + complexity",
            "Output: 30-dim UI feature vector",
        ],
        "example": "terminal=1, tabs=3 -> [0.0, ..., 0.8, ...]",
        "pos": (Inches(7.0), Inches(1.3)),
    },
    {
        "title": "Visual Features",
        "file": "visual_features.py",
        "color": ACCENT_PURPLE,
        "bg": LIGHT_PURPLE_BG,
        "dims": "40 dims [80:120]",
        "pipeline": [
            "OpenCV image analysis",
            "Color histogram: 18 dims",
            "Edge detection: 3 dims",
            "Texture (LBP): 6 dims",
            "Scene complexity: 5 dims",
            "Layout features: 8 dims",
        ],
        "example": "dark_theme=0.8, edges=0.6 -> [0.8, 0.1, ...]",
        "pos": (Inches(1.3), Inches(4.1)),
    },
    {
        "title": "Interaction Features",
        "file": "interaction_features.py",
        "color": ACCENT_GREEN,
        "bg": LIGHT_GREEN_BG,
        "dims": "30 dims [120:150]",
        "pipeline": [
            "8 action types parsed from log",
            "Frequency features: action counts/rates",
            "Position features: click coordinates",
            "Temporal features: timing/intervals",
            "Mouse/typing/keyboard features",
        ],
        "example": "3 clicks, 25 chars typed -> [0.29, 0.14, ...]",
        "pos": (Inches(7.0), Inches(4.1)),
    },
]

for ext in extractors:
    x, y = ext["pos"]
    w, h = Inches(5.5), Inches(2.5)

    add_rounded_rect(slide, x, y, w, h, ext["bg"])

    # Title bar
    add_rounded_rect(slide, x + Inches(0.1), y + Inches(0.05),
                     Inches(2.5), Inches(0.35), ext["color"],
                     ext["title"], font_size=12, font_color=WHITE, bold=True)
    add_textbox(slide, x + Inches(2.7), y + Inches(0.05),
                Inches(2.5), Inches(0.35),
                ext["dims"], font_size=12, color=ext["color"], bold=True)

    # Pipeline steps
    y_pipe = y + Inches(0.5)
    for step in ext["pipeline"]:
        add_textbox(slide, x + Inches(0.2), y_pipe, Inches(5.1), Inches(0.22),
                    "  " + step, font_size=10, color=NUS_ORANGE)
        y_pipe += Inches(0.22)

    # File reference
    add_textbox(slide, x + Inches(0.2), y + h - Inches(0.55),
                Inches(5.1), Inches(0.2),
                ext["file"], font_size=9, color=LIGHT_GRAY,
                font_name="Courier New")
    # Example
    add_textbox(slide, x + Inches(0.2), y + h - Inches(0.35),
                Inches(5.1), Inches(0.2),
                ext["example"], font_size=9, color=ext["color"],
                font_name="Courier New")


# ============================================================
# SLIDE 10: Step 12 -- ML Service
# ============================================================
slide = add_content_slide(prs, "Step 12: ML Service (Model Hub)",
                          "SourceCode/backend/app/services/ml_service.py")

# Singleton
add_rounded_rect(slide, Inches(1.3), Inches(1.3), Inches(3.8), Inches(1.0),
                 DARK_CARD)
add_multiline_textbox(slide, Inches(1.5), Inches(1.4), Inches(3.4), Inches(0.8),
                      [
                          "# Singleton pattern",
                          "ml_service = MLService()",
                      ], font_size=12, color=ACCENT_GREEN, font_name="Courier New",
                      spacing=Pt(3))

# On startup
add_rounded_rect(slide, Inches(5.4), Inches(1.3), Inches(3.8), Inches(1.0),
                 LIGHT_BLUE_BG)
add_textbox(slide, Inches(5.6), Inches(1.35), Inches(3.4), Inches(0.3),
            "On startup:", font_size=12, color=ACCENT_BLUE, bold=True)
add_textbox(slide, Inches(5.6), Inches(1.65), Inches(3.4), Inches(0.5),
            "Registers 7 Tier 1 models\nLoads .pkl files from disk",
            font_size=11, color=NUS_ORANGE)

# On demand
add_rounded_rect(slide, Inches(9.5), Inches(1.3), Inches(3.3), Inches(1.0),
                 LIGHT_ORANGE_BG)
add_textbox(slide, Inches(9.7), Inches(1.35), Inches(2.9), Inches(0.3),
            "On demand:", font_size=12, color=NUS_ORANGE, bold=True)
add_textbox(slide, Inches(9.7), Inches(1.65), Inches(2.9), Inches(0.5),
            "register_deep_models()\nAdds Tier 2 + Tier 3",
            font_size=11, color=NUS_ORANGE)

# classify() function -- main flow
add_rounded_rect(slide, Inches(1.3), Inches(2.6), Inches(11.5), Inches(4.0),
                 CARD_BG)
add_textbox(slide, Inches(1.5), Inches(2.7), Inches(11), Inches(0.4),
            "classify(features, model_name) -> dict", font_size=16,
            color=NUS_ORANGE, bold=True)

classify_steps = [
    {
        "num": "1",
        "title": "_ensure_trained(model_name)",
        "desc": "Loads from .pkl file or trains on synthetic data if no saved model exists",
        "color": ACCENT_BLUE,
        "code": [
            "if model_name in self._trained:",
            "    return  # Already loaded",
            "path = f'models/{model_name}.pkl'",
            "if path.exists(): clf = joblib.load(path)",
            "else: clf.fit(X_synthetic, y_synthetic)",
        ],
    },
    {
        "num": "2",
        "title": "clf.predict(features) -> PredictionResult",
        "desc": "Runs the classifier and measures latency",
        "color": NUS_ORANGE,
        "code": [
            "start = time.time()",
            "result = clf.predict(features)",
            "# PredictionResult(",
            "#   labels=[3, 1, 3, 0, ...],",
            "#   probabilities=[[0.02, 0.91, ...]],",
            "#   latency_ms=59.2)",
        ],
    },
    {
        "num": "3",
        "title": "Map integer labels -> ACTIVITY_LABELS strings",
        "desc": "Converts numeric predictions to human-readable labels",
        "color": ACCENT_GREEN,
        "code": [
            "ACTIVITY_LABELS = [",
            '  "browsing", "coding", "communication",',
            '  "data_entry", "debugging", "document_editing",',
            '  "git_operations", "system_admin", "testing"',
            "]",
        ],
    },
    {
        "num": "4",
        "title": "Return result dict",
        "desc": "{label, confidence, latency_ms, probabilities}",
        "color": ACCENT_PURPLE,
        "code": [
            "return {",
            '  "label": "git_operations",',
            '  "confidence": 0.91,',
            '  "latency_ms": 59.2,',
            '  "probabilities": {0: 0.02, ...}',
            "}",
        ],
    },
]

y_cls = Inches(3.2)
for step in classify_steps:
    add_rounded_rect(slide, Inches(1.5), y_cls, Inches(0.4), Inches(0.35),
                     step["color"], step["num"], font_size=12,
                     font_color=WHITE, bold=True)
    add_textbox(slide, Inches(2.0), y_cls, Inches(4.3), Inches(0.25),
                step["title"], font_size=11, color=NUS_ORANGE, bold=True)
    add_textbox(slide, Inches(2.0), y_cls + Inches(0.25), Inches(4.3), Inches(0.2),
                step["desc"], font_size=9, color=LIGHT_GRAY)

    add_code_block(slide, Inches(6.5), y_cls - Inches(0.05),
                   Inches(6.0), Inches(0.88),
                   step["code"], font_size=9)
    y_cls += Inches(0.95)


# ============================================================
# SLIDE 11: Step 13 -- Classifier Examples
# ============================================================
slide = add_content_slide(prs, "Step 13: How Classifiers Predict",
                          "BaseClassifier interface: fit(X, y), predict(X) -> PredictionResult")

# Three examples side by side
# Tier 1: SVM
add_rounded_rect(slide, Inches(1.3), Inches(1.3), Inches(3.7), Inches(5.3),
                 LIGHT_BLUE_BG)
add_rounded_rect(slide, Inches(1.4), Inches(1.35), Inches(2.5), Inches(0.4),
                 ACCENT_BLUE, "Tier 1: SVM", font_size=14,
                 font_color=WHITE, bold=True)

add_multiline_textbox(slide, Inches(1.5), Inches(1.9), Inches(3.4), Inches(1.0),
                      [
                          {"text": "sklearn.svm.SVC(kernel='rbf')", "bold": True},
                          "",
                          "Input: 150-dim feature vector",
                          "Output: predict() + predict_proba()",
                      ], font_size=11, color=NUS_ORANGE)

add_code_block(slide, Inches(1.5), Inches(3.1), Inches(3.4), Inches(2.2),
               [
                   "class SVMClassifier(BaseClassifier):",
                   "    def __init__(self):",
                   "        self.model = SVC(",
                   "            kernel='rbf',",
                   "            probability=True",
                   "        )",
                   "",
                   "    def predict(self, X):",
                   "        labels = self.model.predict(X)",
                   "        proba = self.model.predict_proba(X)",
                   "        return PredictionResult(",
                   "            labels, proba, latency)",
               ], font_size=8)

add_textbox(slide, Inches(1.5), Inches(5.4), Inches(3.4), Inches(0.3),
            "Fast: ~59ms | Good for linearly separable data",
            font_size=9, color=ACCENT_BLUE, bold=True)

# Tier 2: LSTM
add_rounded_rect(slide, Inches(5.2), Inches(1.3), Inches(3.7), Inches(5.3),
                 LIGHT_PURPLE_BG)
add_rounded_rect(slide, Inches(5.3), Inches(1.35), Inches(2.5), Inches(0.4),
                 ACCENT_PURPLE, "Tier 2: LSTM", font_size=14,
                 font_color=WHITE, bold=True)

add_multiline_textbox(slide, Inches(5.4), Inches(1.9), Inches(3.4), Inches(1.0),
                      [
                          {"text": "reshape(150) -> (10, 15)", "bold": True},
                          "",
                          "10 timesteps x 15 features",
                          "Treats modalities as a sequence",
                      ], font_size=11, color=NUS_ORANGE)

add_code_block(slide, Inches(5.4), Inches(3.1), Inches(3.4), Inches(2.2),
               [
                   "class LSTMClassifier(BaseClassifier):",
                   "    def __init__(self):",
                   "        self.lstm = nn.LSTM(",
                   "            input_size=15,",
                   "            hidden_size=64,",
                   "            batch_first=True)",
                   "        self.fc = nn.Linear(64, 9)",
                   "",
                   "    def forward(self, x):",
                   "        x = x.reshape(-1, 10, 15)",
                   "        _, (h, _) = self.lstm(x)",
                   "        return F.softmax(self.fc(h))",
               ], font_size=8)

add_textbox(slide, Inches(5.4), Inches(5.4), Inches(3.4), Inches(0.3),
            "Moderate: ~180ms | Captures sequential patterns",
            font_size=9, color=ACCENT_PURPLE, bold=True)

# Tier 3: Stacking
add_rounded_rect(slide, Inches(9.1), Inches(1.3), Inches(3.7), Inches(5.3),
                 LIGHT_GREEN_BG)
add_rounded_rect(slide, Inches(9.2), Inches(1.35), Inches(2.5), Inches(0.4),
                 ACCENT_GREEN, "Tier 3: Stacking", font_size=14,
                 font_color=WHITE, bold=True)

add_multiline_textbox(slide, Inches(9.3), Inches(1.9), Inches(3.4), Inches(1.0),
                      [
                          {"text": "SVM + RF + MLP -> hstack", "bold": True},
                          "",
                          "Base model predictions stacked",
                          "Meta-learner: LogisticRegression",
                      ], font_size=11, color=NUS_ORANGE)

add_code_block(slide, Inches(9.3), Inches(3.1), Inches(3.4), Inches(2.2),
               [
                   "class StackingClassifier(Base...):",
                   "    base_models = [",
                   "        SVMClassifier(),",
                   "        RandomForestClassifier(),",
                   "        MLPClassifier(),",
                   "    ]",
                   "    meta = LogisticRegression()",
                   "",
                   "    def predict(self, X):",
                   "        preds = [m.predict(X)",
                   "                 for m in self.base_models]",
                   "        stacked = np.hstack(preds)",
                   "        return self.meta.predict(stacked)",
               ], font_size=8)

add_textbox(slide, Inches(9.3), Inches(5.4), Inches(3.4), Inches(0.3),
            "Slow: ~6500ms | Combines model strengths",
            font_size=9, color=ACCENT_GREEN, bold=True)


# ============================================================
# SLIDE 12: Steps 14-15 -- Results Return to Frontend
# ============================================================
slide = add_content_slide(prs, "Steps 14-15: Results Display",
                          "Data flows back from backend to frontend components")

# Left side: JSON response
add_rounded_rect(slide, Inches(1.3), Inches(1.3), Inches(5.3), Inches(5.3),
                 DARK_CARD)
add_textbox(slide, Inches(1.5), Inches(1.35), Inches(4.8), Inches(0.4),
            "JSON Response Structure", font_size=16, color=WHITE, bold=True)

add_multiline_textbox(slide, Inches(1.5), Inches(1.9), Inches(4.8), Inches(4.5),
                      [
                          "{",
                          '  "job_id": 42,',
                          '  "status": "completed",',
                          "",
                          '  "results": [',
                          '    // 14 models x 7 segments = 98 results',
                          '    { "model": "xgboost", "segment": 0,',
                          '      "label": "git_operations",',
                          '      "confidence": 0.91 },',
                          "    ...",
                          "  ],",
                          "",
                          '  "model_comparison": [',
                          '    { "model": "xgboost", "tier": "tier1",',
                          '      "avg_confidence": 0.91,',
                          '      "latency_ms": 59 },',
                          "    ... // 14 entries",
                          "  ],",
                          "",
                          '  "best_model": "xgboost"',
                          "}",
                      ], font_size=10, color=ACCENT_GREEN, font_name="Courier New",
                      spacing=Pt(2))

# Right side: Frontend components
add_rounded_rect(slide, Inches(6.9), Inches(1.3), Inches(5.8), Inches(5.3),
                 CARD_BG)
add_textbox(slide, Inches(7.1), Inches(1.35), Inches(5), Inches(0.4),
            "Frontend Components", font_size=16, color=NUS_ORANGE, bold=True)

# VideoResults.tsx
add_rounded_rect(slide, Inches(7.1), Inches(1.9), Inches(5.4), Inches(1.3),
                 WHITE)
add_rounded_rect(slide, Inches(7.2), Inches(1.95), Inches(2.5), Inches(0.3),
                 ACCENT_BLUE, "VideoResults.tsx", font_size=11,
                 font_color=WHITE, bold=True)
add_multiline_textbox(slide, Inches(7.2), Inches(2.35), Inches(5.2), Inches(0.8),
                      [
                          "selectedModel state: tracks which model user is viewing",
                          "Shows selected model's workflow steps",
                          "Passes modelComparison to child components",
                      ], font_size=10, color=NUS_ORANGE, spacing=Pt(3))

# ModelComparison.tsx
add_rounded_rect(slide, Inches(7.1), Inches(3.4), Inches(5.4), Inches(1.5),
                 WHITE)
add_rounded_rect(slide, Inches(7.2), Inches(3.45), Inches(2.8), Inches(0.3),
                 NUS_ORANGE, "ModelComparison.tsx", font_size=11,
                 font_color=WHITE, bold=True)
add_multiline_textbox(slide, Inches(7.2), Inches(3.85), Inches(5.2), Inches(1.0),
                      [
                          "14-row comparison table",
                          "Color-coded by tier (blue=T1, purple=T2, green=T3)",
                          "Click any row to switch the selected model",
                          "Columns: Model | Tier | Confidence | Latency",
                      ], font_size=10, color=NUS_ORANGE, spacing=Pt(3))

# WorkflowSteps
add_rounded_rect(slide, Inches(7.1), Inches(5.1), Inches(5.4), Inches(1.3),
                 WHITE)
add_rounded_rect(slide, Inches(7.2), Inches(5.15), Inches(2.5), Inches(0.3),
                 ACCENT_GREEN, "WorkflowSteps", font_size=11,
                 font_color=WHITE, bold=True)
add_multiline_textbox(slide, Inches(7.2), Inches(5.55), Inches(5.2), Inches(0.7),
                      [
                          "Timeline of predicted activities with timestamps",
                          'e.g., "Ran shell command: git pull" (0:16-0:29)',
                          "Visual step-by-step display with icons",
                      ], font_size=10, color=NUS_ORANGE, spacing=Pt(3))


# ============================================================
# SLIDE 13: Complete Data Flow Diagram
# ============================================================
slide = add_content_slide(prs, "Complete Data Flow",
                          "Full flow from User -> Frontend -> Backend -> Features -> Models -> Results -> Display")

# Flow nodes
flow_nodes = [
    ("User", "Drops video.mp4", ACCENT_BLUE, Inches(1.3), Inches(1.6)),
    ("Frontend", "Upload + Hook", ACCENT_BLUE, Inches(3.3), Inches(1.6)),
    ("API", "POST /upload\nPOST /run", ACCENT_GREEN, Inches(5.3), Inches(1.6)),
    ("Router", "jobs.py", ACCENT_GREEN, Inches(7.3), Inches(1.6)),
    ("Pipeline", "classification\n_service.py", NUS_ORANGE, Inches(9.3), Inches(1.6)),
    ("Extractors", "4 modules", ACCENT_PURPLE, Inches(11.0), Inches(1.6)),
]

for label, desc, color, x, y in flow_nodes:
    add_rounded_rect(slide, x, y, Inches(1.6), Inches(0.9),
                     color, label, font_size=12, font_color=WHITE, bold=True)
    add_textbox(slide, x, y + Inches(0.9), Inches(1.6), Inches(0.4),
                desc, font_size=8, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

# Arrows between top row
for i in range(5):
    ax = Inches(2.9) + Inches(i * 2.0)
    add_textbox(slide, ax, Inches(1.8), Inches(0.3), Inches(0.3),
                "->", font_size=16, color=NUS_ORANGE, bold=True,
                alignment=PP_ALIGN.CENTER)

# Key data transformations
add_textbox(slide, Inches(1.3), Inches(3.1), Inches(12), Inches(0.4),
            "Key Data Transformations", font_size=18,
            color=NUS_ORANGE, bold=True)
add_rect(slide, Inches(1.3), Inches(3.5), Inches(1.5), Inches(0.04),
         ACCENT_BLUE)

transforms = [
    {
        "from": "File",
        "arrow": "->",
        "to": "job_id",
        "desc": "POST /upload saves file, creates Job record, returns job_id",
        "color": ACCENT_BLUE,
    },
    {
        "from": "Video frames",
        "arrow": "->",
        "to": "(n_segments, 150) matrix",
        "desc": "Video processor segments, 4 extractors produce 150-dim vectors per segment",
        "color": NUS_ORANGE,
    },
    {
        "from": "150-dim vector",
        "arrow": "->",
        "to": "14 x PredictionResult",
        "desc": "Each of 14 classifiers (3 tiers) produces predictions + probabilities",
        "color": ACCENT_PURPLE,
    },
    {
        "from": "PredictionResult",
        "arrow": "->",
        "to": "ModelSummary[] + WorkflowStep[]",
        "desc": "Frontend groups results by model, maps best model's results to workflow steps",
        "color": ACCENT_GREEN,
    },
    {
        "from": "Final render",
        "arrow": "->",
        "to": "Comparison table + Timeline",
        "desc": "14-model comparison table with color-coded tiers, clickable timeline of activities",
        "color": NUS_BLUE,
    },
]

y_t = Inches(3.8)
for t in transforms:
    add_rounded_rect(slide, Inches(1.3), y_t, Inches(2.2), Inches(0.5),
                     t["color"], t["from"], font_size=11,
                     font_color=WHITE, bold=True)
    add_textbox(slide, Inches(3.55), y_t + Inches(0.05), Inches(0.4), Inches(0.4),
                t["arrow"], font_size=16, color=NUS_ORANGE, bold=True,
                alignment=PP_ALIGN.CENTER)
    add_rounded_rect(slide, Inches(4.0), y_t, Inches(3.5), Inches(0.5),
                     t["color"], t["to"], font_size=11,
                     font_color=WHITE, bold=True)
    add_textbox(slide, Inches(7.8), y_t + Inches(0.05), Inches(5.0), Inches(0.4),
                t["desc"], font_size=10, color=NUS_ORANGE)
    y_t += Inches(0.62)


# ============================================================
# Save
# ============================================================
output_path = "/Users/muneeswaranm/Projects/PRS/PatternRecognSystem-Video2Text/presentation/Video2Knowledge_CodeFlow.pptx"
prs.save(output_path)
print(f"Saved to: {output_path}")
print(f"Total slides: {len(prs.slides)}")
