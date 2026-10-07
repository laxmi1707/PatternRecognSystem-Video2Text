"""Generate ScreenSense System Architecture Diagram (NUS ISS style)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# ── NUS ISS Colors ──────────────────────────────────────────────────────────
NUS_BLUE = "#003D7C"
NUS_ORANGE = "#EF7C00"
SIDEBAR_YELLOW = "#FFE033"
WHITE = "#FFFFFF"
LIGHT_GRAY = "#CCCCCC"
DARK_CARD = "#002A55"

ACCENT_BLUE = "#007ACC"
ACCENT_GREEN = "#28A745"
ACCENT_PURPLE = "#6F42C1"
ACCENT_RED = "#CC2233"
LIGHT_BLUE = "#1A5276"
MID_BLUE = "#004080"

fig, ax = plt.subplots(1, 1, figsize=(20, 14))
fig.patch.set_facecolor(NUS_BLUE)
ax.set_facecolor(NUS_BLUE)
ax.set_xlim(0, 20)
ax.set_ylim(0, 14)
ax.axis("off")


def draw_box(x, y, w, h, color, text, fontsize=10, text_color=WHITE, alpha=0.95,
             bold=True, radius=0.3):
    box = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0.1,rounding_size={radius}",
                         facecolor=color, edgecolor="none", alpha=alpha, zorder=2)
    ax.add_patch(box)
    weight = "bold" if bold else "normal"
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fontsize, color=text_color, fontweight=weight,
            fontfamily="sans-serif", zorder=3)


def draw_arrow(x1, y1, x2, y2, color=LIGHT_GRAY, style="->", lw=2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw,
                                connectionstyle="arc3,rad=0"),
                zorder=1)


def draw_section_label(x, y, text, color=WHITE, fontsize=11):
    ax.text(x, y, text, ha="left", va="center", fontsize=fontsize,
            color=color, fontweight="bold", fontfamily="sans-serif",
            fontstyle="italic", zorder=4)


def draw_dashed_box(x, y, w, h, color, label="", label_pos="top"):
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05,rounding_size=0.2",
                         facecolor="none", edgecolor=color, linestyle="--",
                         linewidth=1.5, alpha=0.6, zorder=1)
    ax.add_patch(box)
    if label:
        ly = y + h + 0.15 if label_pos == "top" else y - 0.25
        ax.text(x + w / 2, ly, label, ha="center", va="center",
                fontsize=9, color=color, fontweight="bold", fontfamily="sans-serif",
                zorder=4)


# ── Title ───────────────────────────────────────────────────────────────────

# NUS sidebar decoration
ax.add_patch(plt.Rectangle((0, 12.8), 1.5, 1.2, facecolor=SIDEBAR_YELLOW,
                           edgecolor="none", zorder=2))
ax.add_patch(plt.Rectangle((0.65, 0.3), 0.08, 12.5, facecolor=NUS_ORANGE,
                           edgecolor="none", zorder=2))

ax.text(2.0, 13.35, "TRACE — System Architecture", fontsize=22,
        color=WHITE, fontweight="bold", fontfamily="sans-serif", va="center", zorder=4)
ax.text(2.0, 12.95, "Multimodal Pattern Recognition for Screen Activity Classification",
        fontsize=12, color=LIGHT_GRAY, fontfamily="sans-serif", va="center", zorder=4)

# NUS logo placeholder
ax.text(19.0, 13.35, "NUS", fontsize=16, color=WHITE, fontweight="bold",
        fontfamily="sans-serif", ha="center", va="center", zorder=4)
ax.text(19.0, 13.0, "National University\nof Singapore", fontsize=6, color=WHITE,
        fontfamily="sans-serif", ha="center", va="center", zorder=4)

# Orange accent bar at bottom
ax.add_patch(plt.Rectangle((0, 0.15), 20, 0.08, facecolor=NUS_ORANGE,
                           edgecolor="none", zorder=2))
ax.text(0.5, 0.02, "© Copyright National University of Singapore. All Rights Reserved.",
        fontsize=6, color=WHITE, fontfamily="sans-serif", zorder=4)


# ═══════════════════════════════════════════════════════════════════════════
# ROW 1: Input Layer (top)
# ═══════════════════════════════════════════════════════════════════════════

draw_section_label(1.2, 12.2, "① INPUT")

draw_box(1.5, 11.2, 2.8, 0.8, NUS_ORANGE, "Screen Recording\n(MP4 / MOV / WebM)", 10)
draw_box(4.8, 11.2, 2.3, 0.8, MID_BLUE, "Video Decoder\n(OpenCV)", 9)
draw_box(7.6, 11.2, 2.3, 0.8, MID_BLUE, "Keyframe\nExtraction", 9)
draw_box(10.4, 11.2, 2.3, 0.8, MID_BLUE, "Action Log\nParser", 9)

draw_arrow(4.3, 11.6, 4.8, 11.6, NUS_ORANGE)
draw_arrow(7.1, 11.6, 7.6, 11.6, LIGHT_GRAY)
draw_arrow(9.9, 11.6, 10.4, 11.6, LIGHT_GRAY)

# ═══════════════════════════════════════════════════════════════════════════
# ROW 2: Feature Extraction Pipeline
# ═══════════════════════════════════════════════════════════════════════════

draw_section_label(1.2, 10.4, "② FEATURE EXTRACTION")
draw_dashed_box(1.3, 7.6, 17.2, 2.6, NUS_ORANGE)

# 4 extractors
draw_box(1.6, 8.4, 3.8, 1.5, ACCENT_BLUE, "OCR Extractor\n─────────────\nEasyOCR + Tesseract\nTF-IDF Vectorization\n50 dimensions", 9)
draw_box(5.8, 8.4, 3.8, 1.5, NUS_ORANGE, "UI Detection\n─────────────\nYOLOv8 Nano\n12 UI Element Classes\n30 dimensions", 9)
draw_box(10.0, 8.4, 3.8, 1.5, ACCENT_PURPLE, "Visual Analyzer\n─────────────\nOpenCV Pipeline\nColor/Edge/Texture\n40 dimensions", 9)
draw_box(14.2, 8.4, 3.8, 1.5, ACCENT_GREEN, "Interaction\n─────────────\nAction Log Parser\n8 Action Types\n30 dimensions", 9)

# Arrows from input to extractors
for cx in [3.5, 7.7, 11.9, 16.1]:
    draw_arrow(cx, 11.2, cx, 9.9, LIGHT_GRAY, lw=1.5)

# ── Feature Assembly ──
draw_box(5.5, 7.7, 9.0, 0.55, DARK_CARD,
         "Feature Assembler  →  150-dim Concatenated Vector  [OCR:50 | UI:30 | Visual:40 | Interaction:30]",
         9, NUS_ORANGE)

# Arrows from extractors down to assembler
for cx in [3.5, 7.7, 11.9, 16.1]:
    draw_arrow(cx, 8.4, cx if cx < 14.5 else 14.5, 8.25, LIGHT_GRAY, lw=1)

# ═══════════════════════════════════════════════════════════════════════════
# ROW 3: Classification Engine (3 Tiers)
# ═══════════════════════════════════════════════════════════════════════════

draw_section_label(1.2, 7.0, "③ CLASSIFICATION ENGINE")
draw_dashed_box(1.3, 4.1, 17.2, 2.7, ACCENT_BLUE)

# Arrow from assembler to classification
draw_arrow(10.0, 7.7, 10.0, 6.8, NUS_ORANGE, lw=2.5)

# Tier 1
draw_box(1.6, 5.7, 5.3, 0.8, ACCENT_BLUE, "Tier 1 — Classical ML  (7 models)", 10)
tier1_models = "SVM  •  Naive Bayes  •  Decision Tree  •  Random Forest\nKNN  •  XGBoost  •  LightGBM"
draw_box(1.6, 4.3, 5.3, 1.3, LIGHT_BLUE, tier1_models, 8, LIGHT_GRAY, bold=False)

# Tier 2
draw_box(7.3, 5.7, 5.0, 0.8, ACCENT_PURPLE, "Tier 2 — Deep Learning  (4 models)", 10)
tier2_models = "MLP  •  CNN-1D\nLSTM  •  Transformer"
draw_box(7.3, 4.3, 5.0, 1.3, "#3D1F6F", tier2_models, 8, LIGHT_GRAY, bold=False)

# Tier 3
draw_box(12.7, 5.7, 5.3, 0.8, ACCENT_GREEN, "Tier 3 — Ensemble  (3 models)", 10)
tier3_models = "Voting Ensemble (Soft)\nStacking Classifier\nLate Fusion"
draw_box(12.7, 4.3, 5.3, 1.3, "#1A5C2E", tier3_models, 8, LIGHT_GRAY, bold=False)

# ═══════════════════════════════════════════════════════════════════════════
# ROW 4: Output & Results
# ═══════════════════════════════════════════════════════════════════════════

draw_section_label(1.2, 3.6, "④ OUTPUT")

draw_arrow(10.0, 4.3, 10.0, 3.4, NUS_ORANGE, lw=2.5)

draw_box(3.5, 2.5, 3.5, 0.7, NUS_ORANGE, "Activity Label\n(10 Classes)", 10)
draw_box(7.5, 2.5, 3.5, 0.7, ACCENT_BLUE, "Confidence Scores\n(per model)", 10)
draw_box(11.5, 2.5, 3.5, 0.7, ACCENT_GREEN, "Model Comparison\n(Ranked Table)", 10)

# ═══════════════════════════════════════════════════════════════════════════
# ROW 5: Infrastructure Layer
# ═══════════════════════════════════════════════════════════════════════════

draw_section_label(1.2, 1.9, "⑤ INFRASTRUCTURE")
draw_dashed_box(1.3, 0.4, 17.2, 1.45, ACCENT_GREEN)

draw_box(1.6, 0.6, 4.0, 1.0, ACCENT_BLUE,
         "Frontend\n─────────\nReact + TypeScript\nVite  •  Port 5173", 8)
draw_box(6.0, 0.6, 4.0, 1.0, NUS_ORANGE,
         "Backend API\n─────────\nFastAPI + Uvicorn\nPyTorch  •  Port 8000", 8)
draw_box(10.4, 0.6, 4.0, 1.0, ACCENT_GREEN,
         "Database\n─────────\nPostgreSQL 16\npgvector  •  Port 5434", 8)
draw_box(14.8, 0.6, 3.5, 1.0, ACCENT_PURPLE,
         "DevOps\n─────────\nDocker Compose\nTerraform • AWS EC2", 8)

# Arrows between infra
draw_arrow(5.6, 1.1, 6.0, 1.1, LIGHT_GRAY)
draw_arrow(10.0, 1.1, 10.4, 1.1, LIGHT_GRAY)
draw_arrow(14.4, 1.1, 14.8, 1.1, LIGHT_GRAY)


# ═══════════════════════════════════════════════════════════════════════════
# Save
# ═══════════════════════════════════════════════════════════════════════════

plt.tight_layout(pad=0.5)
out = "/Users/muneeswaranm/Projects/PRS/PatternRecognSystem-Video2Text/presentation/ScreenSense_SystemArchitecture.png"
fig.savefig(out, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor())
plt.close()
print(f"Saved: {out}")
