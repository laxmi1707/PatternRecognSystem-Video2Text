"""
Generates Group_21_Professor_Response.pptx  (v2 — improved look & feel)
2 slides:
  Slide 1 — Professor feedback vs team response (BEFORE / AFTER, numbered points,
             prominent 13→6 callout, equal columns, fixed arrow)
  Slide 2 — 6 selected models: rationale, results, RQ coverage
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

from nus_iss_template import (
    create_presentation, add_content_slide,
    add_textbox, add_rounded_rect, add_multiline_textbox,
    NUS_BLUE, NUS_ORANGE, WHITE, SUBTLE_GRAY, LIGHT_GRAY,
    ACCENT_BLUE, ACCENT_GREEN, ACCENT_PURPLE, ACCENT_RED,
    add_nus_footer,
    LIGHT_BLUE_BG, LIGHT_GREEN_BG, LIGHT_PURPLE_BG,
    LIGHT_ORANGE_BG, LIGHT_RED_BG, CARD_BG, LIGHT_BG, DARK_TEXT,
)

DARK_CARD  = RGBColor(0x00, 0x2A, 0x55)
DARK_RED   = RGBColor(0xB5, 0x1C, 0x1C)
DARK_GREEN = RGBColor(0x14, 0x7A, 0x3A)
GOLD       = RGBColor(0xFF, 0xC1, 0x07)
TEAL       = RGBColor(0x17, 0xA2, 0xB8)
NUM_BG     = RGBColor(0x1A, 0x3A, 0x6A)   # dark blue circle bg

prs = create_presentation()


# ═══════════════════════════════════════════════════════════════
# SLIDE 1 — Feedback → Response  (redesigned)
# ═══════════════════════════════════════════════════════════════
slide = add_content_slide(prs,
    "Acting on Feedback — From Breadth to Depth",
    "Sep 30: First presentation feedback → Oct 2026: MVP scope implemented")

# ── Top timeline strip ────────────────────────────────────────
add_rounded_rect(slide, Inches(0.35), Inches(1.47), Inches(9.3), Inches(0.3),
                 NUM_BG, "")
for x, label, clr in [
    (Inches(0.6),  "Sep 30 — First Presentation", LIGHT_GRAY),
    (Inches(3.8),  "→", WHITE),
    (Inches(4.3),  "Professor Feedback Received", GOLD),
    (Inches(6.9),  "→", WHITE),
    (Inches(7.4),  "Oct 2026 — MVP Implemented", ACCENT_GREEN),
]:
    add_textbox(slide, x, Inches(1.52), Inches(2.4), Inches(0.22),
                label, font_size=9, color=clr, bold=(label == "→"))

# ── 13 → 6 callout banner ─────────────────────────────────────
add_rounded_rect(slide, Inches(3.55), Inches(1.85), Inches(2.9), Inches(0.48),
                 DARK_CARD, "")
add_textbox(slide, Inches(3.6),  Inches(1.9),  Inches(1.0), Inches(0.35),
            "13 models", font_size=13, color=ACCENT_RED,  bold=True,
            alignment=PP_ALIGN.CENTER)
add_textbox(slide, Inches(4.55), Inches(1.9),  Inches(0.5), Inches(0.35),
            "→", font_size=18, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)
add_textbox(slide, Inches(5.0),  Inches(1.9),  Inches(1.3), Inches(0.35),
            "6 models", font_size=13, color=ACCENT_GREEN, bold=True,
            alignment=PP_ALIGN.CENTER)

# ── Column headers ────────────────────────────────────────────
COL_TOP  = Inches(2.32)
COL_H    = Inches(3.72)  # 5 rows × 0.65" + 0.35" top + 0.12" bottom
COL_W    = Inches(4.35)  # wider columns
LEFT_X   = Inches(0.35)
RIGHT_X  = Inches(5.1)   # gap = 5.1 - (0.35+4.35) = 0.40"

# BEFORE header
add_rounded_rect(slide, LEFT_X, COL_TOP, COL_W, Inches(0.36),
                 DARK_RED, "✗  BEFORE — Professor Feedback  (Sep 30)",
                 font_size=11, font_color=WHITE, bold=True)
# AFTER header
add_rounded_rect(slide, RIGHT_X, COL_TOP, COL_W, Inches(0.36),
                 DARK_GREEN, "✓  AFTER — Team Response  (Oct 2026)",
                 font_size=11, font_color=WHITE, bold=True)

# ── Column bodies ─────────────────────────────────────────────
add_rounded_rect(slide, LEFT_X,  COL_TOP + Inches(0.36), COL_W, COL_H, LIGHT_RED_BG,   "")
add_rounded_rect(slide, RIGHT_X, COL_TOP + Inches(0.36), COL_W, COL_H, LIGHT_GREEN_BG, "")

feedback_items = [
    ("Too many models",
     "13+ classifiers at once — audience cannot follow the logic."),
    ("Scope too ambitious",
     "4-level hierarchy + LLM generation not feasible in one semester."),
    ("Training ≠ Inference",
     "Diagram conflated training and inference pipelines."),
    ("Dataset must come first",
     "Class distribution must precede model descriptions."),
    ("Feature → Model mapping unclear",
     "No explicit link: modality → feature columns → classifier."),
]
response_items = [
    ("Narrowed to 6 representative models",
     "1–2 per tier, each mapped to a research question."),
    ("Activity classification only (MVP)",
     "Level 3 & LLM generation moved to future work."),
    ("Separated train vs. inference",
     "Two diagrams: data→fit→.pkl | video→features→predict."),
    ("Reordered presentation",
     "Dataset + class distribution shown before model design."),
    ("Explicit feature → model table added",
     "EfficientNet/EasyOCR/YOLO/action-log → classifiers."),
]

ROW_H     = Inches(0.65)   # larger row height — matches user's corrected version
TITLE_H   = Inches(0.24)
BODY_H    = Inches(0.26)
CIRCLE_SZ = Inches(0.28)

for k, ((fb_title, fb_body), (rs_title, rs_body)) in enumerate(
        zip(feedback_items, response_items)):
    y = COL_TOP + Inches(0.37) + k * ROW_H

    # numbered circle — left
    add_rounded_rect(slide, LEFT_X + Inches(0.1), y + Inches(0.05),
                     CIRCLE_SZ, CIRCLE_SZ, DARK_RED,
                     str(k+1), font_size=9, font_color=WHITE, bold=True)
    add_textbox(slide, LEFT_X + Inches(0.46), y,
                COL_W - Inches(0.52), TITLE_H,
                fb_title, font_size=10, color=DARK_RED, bold=True)
    add_textbox(slide, LEFT_X + Inches(0.46), y + TITLE_H,
                COL_W - Inches(0.52), BODY_H,
                fb_body, font_size=9, color=DARK_CARD)

    # numbered circle — right
    add_rounded_rect(slide, RIGHT_X + Inches(0.1), y + Inches(0.05),
                     CIRCLE_SZ, CIRCLE_SZ, DARK_GREEN,
                     str(k+1), font_size=9, font_color=WHITE, bold=True)
    add_textbox(slide, RIGHT_X + Inches(0.46), y,
                COL_W - Inches(0.52), TITLE_H,
                rs_title, font_size=10, color=DARK_GREEN, bold=True)
    add_textbox(slide, RIGHT_X + Inches(0.46), y + TITLE_H,
                COL_W - Inches(0.52), BODY_H,
                rs_body, font_size=9, color=DARK_CARD)

# ── Centre arrow — midpoint of 5 rows ────────────────────────
# Rows start at COL_TOP+0.37 = 2.69", ROW_H=0.65", 5 rows = 3.25"
# Midpoint y = 2.69 + 3.25/2 = 4.315"
# Gap: LEFT ends at 4.70", RIGHT starts at 5.1" → centre x = 4.90"
# Arrow box 0.4" wide → left edge = 4.90 - 0.20 = 4.70"
add_textbox(slide, Inches(4.68), Inches(4.15), Inches(0.44), Inches(0.44),
            "⇒", font_size=34, color=GOLD, bold=True,
            alignment=PP_ALIGN.CENTER)

# ── Bottom result bar ─────────────────────────────────────────
# Columns end at COL_TOP+0.36+COL_H = 2.32+0.36+3.72 = 6.40"
add_rounded_rect(slide, Inches(0.35), Inches(6.48), Inches(9.3), Inches(0.30),
                 DARK_CARD, "")
add_textbox(slide, Inches(0.55), Inches(6.52), Inches(8.9), Inches(0.24),
    "Result: Focused scope → rigorous evaluation → 6 models, 3 research questions, F1 Macro 0.884 — presented Oct 30.",
    font_size=10, color=WHITE, bold=True)

add_nus_footer(slide)


# ═══════════════════════════════════════════════════════════════
# SLIDE 2 — 6-Model MVP: Rationale + Results  (unchanged logic,
#            improved header & colour coding)
# ═══════════════════════════════════════════════════════════════
slide = add_content_slide(prs,
    "6-Model MVP — Selection Rationale & Results",
    "Minimum models to cover all 3 tiers · answers all 3 research questions · depth over breadth")

# Explanation strip
add_rounded_rect(slide, Inches(0.35), Inches(1.48), Inches(9.3), Inches(0.38),
                 NUM_BG, "")
add_multiline_textbox(slide, Inches(0.5), Inches(1.52), Inches(8.9), Inches(0.34),
    ["Selection principle: 1–2 models per tier, each directly mapped to a research question — as recommended by the professor."],
    font_size=10, color=WHITE)

# Tier legend
for i, (label, clr) in enumerate([
    ("Tier 1 — Classical ML", ACCENT_BLUE),
    ("Tier 2 — Deep Learning", NUS_ORANGE),
    ("Tier 3 — Ensemble", ACCENT_GREEN),
]):
    add_rounded_rect(slide, Inches(0.35 + i * 3.15), Inches(1.95),
                     Inches(3.0), Inches(0.22),
                     clr, label, font_size=9, font_color=WHITE, bold=True)

# Column headers
for j, (hdr, w, x) in enumerate([
    ("#",                         Inches(0.28), Inches(0.35)),
    ("Model",                     Inches(1.5),  Inches(0.68)),
    ("Tier",                      Inches(0.85), Inches(2.23)),
    ("Research Question Answered",Inches(2.75), Inches(3.13)),
    ("Key Technical Concept",     Inches(2.35), Inches(5.93)),
    ("F1",                        Inches(0.62), Inches(8.33)),
    ("By",                        Inches(1.0),  Inches(9.0)),
]):
    add_rounded_rect(slide, x, Inches(2.25), w, Inches(0.26),
                     NUS_BLUE, hdr, font_size=9, font_color=WHITE, bold=True)

models = [
    # num, name, tier_label, tier_clr, row_bg,
    # rq_text, tech_text, f1, contributor
    ("1", "SVM (RBF kernel)",   "Tier 1", ACCENT_BLUE,   LIGHT_BLUE_BG,
     "RQ1 — Best classical baseline; high-dim feature space",
     "Max-margin hyperplane via RBF K(x,x')=exp(−γ‖x−x'‖²); OvO multi-class",
     "0.812", "—"),
    ("2", "Decision Tree",      "Tier 1", ACCENT_BLUE,   CARD_BG,
     "RQ1 — Interpretable rules; audit-ready; fastest inference (2 ms)",
     "Greedy Gini splitting; max_depth=20; class_weight='balanced'",
     "0.762", "Muneeswaran"),
    ("3", "Random Forest",      "Tier 1", ACCENT_BLUE,   LIGHT_BLUE_BG,
     "RQ1 — Demonstrates bagging benefit; best single classical result",
     "100-tree bootstrap; √1391≈37 features/split; majority vote; n_jobs=-1",
     "0.841", "Muneeswaran"),
    ("4", "MLP",                "Tier 2", NUS_ORANGE,    LIGHT_ORANGE_BG,
     "RQ1 — Deep learning representative; answers classical vs. DL",
     "1391→512→256→8; ReLU+Softmax; backprop; Dropout 0.3; 846K params",
     "0.798", "—"),
    ("5", "Voting Ensemble",    "Tier 3", ACCENT_GREEN,  LIGHT_GREEN_BG,
     "RQ2 — Fusion proof: combined > single; best overall result ★",
     "Soft avg: P=(P_SVM+P_RF+P_XGB+P_MLP)/4 → argmax → class label",
     "0.884 ★", "—"),
    ("6", "Late Fusion",        "Tier 3", ACCENT_GREEN,  CARD_BG,
     "RQ2 — Modality ablation; each branch = one signal type",
     "4 branches→(n,32) meta_X → Logistic Regression meta-learner",
     "0.861", "Muneeswaran"),
]

for i, (num, name, tier, t_clr, bg, rq, tech, f1, contrib) in enumerate(models):
    y = Inches(2.55 + i * 0.52)
    is_best = "★" in f1

    for x, w, val, clr, bold in [
        (Inches(0.35), Inches(0.28), num,    t_clr,  True),
        (Inches(0.68), Inches(1.5),  name,   DARK_CARD, is_best),
        (Inches(2.23), Inches(0.85), tier,   t_clr,  False),
        (Inches(3.13), Inches(2.75), rq,     DARK_CARD, False),
        (Inches(5.93), Inches(2.35), tech,   DARK_CARD, False),
        (Inches(8.33), Inches(0.62), f1,     ACCENT_GREEN if is_best else DARK_CARD, is_best),
        (Inches(9.0),  Inches(1.0),  contrib,ACCENT_PURPLE if contrib != "—" else SUBTLE_GRAY, contrib != "—"),
    ]:
        add_rounded_rect(slide, x, y, w, Inches(0.48), bg if not is_best else LIGHT_GREEN_BG, "")
        add_textbox(slide, x + Inches(0.05), y + Inches(0.08),
                    w - Inches(0.1), Inches(0.36),
                    val, font_size=9 if len(val) > 40 else 9.5,
                    color=clr, bold=bold)

# RQ summary footer
add_rounded_rect(slide, Inches(0.35), Inches(5.68), Inches(9.3), Inches(0.52),
                 NUM_BG, "")
for k, ln in enumerate([
    "RQ1 (rows 1–4): Classical ML (RF 0.841) ≈ Deep MLP (0.798) at 277 tasks — small dataset limits deep learning advantage  |  Finding: feature engineering + classical ML competitive",
    "RQ2 (rows 5–6): Voting 0.884 > best single RF 0.841 (+5.1%)  →  multimodal fusion consistently outperforms any single modality  ★ = best model overall",
]):
    add_textbox(slide, Inches(0.5), Inches(5.72 + k * 0.24),
                Inches(9.0), Inches(0.22),
                ln, font_size=9, color=WHITE if k == 0 else GOLD)

add_nus_footer(slide)


# ═══════════════════════════════════════════════════════════════
# Save
# ═══════════════════════════════════════════════════════════════
OUT = os.path.join(os.path.dirname(__file__), "Group_21_Professor_Response.pptx")
prs.save(OUT)
print(f"Saved: {OUT}  ({len(prs.slides)} slides)")
