"""Generate Video2Knowledge Video Segmentation presentation (NUS ISS template)."""
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

DARK_CARD = RGBColor(0x00, 0x2A, 0x55)

prs = create_presentation()


# ============================================================
# SLIDE 1: Title
# ============================================================
add_title_slide(
    prs,
    "How Video Segmentation Works",
    subtitle="Splitting continuous screen recordings into meaningful activity segments",
    author="Video2Knowledge  |  Pattern Recognition Systems",
)


# ============================================================
# SLIDE 2: The Problem
# ============================================================
slide = add_content_slide(prs, "The Problem")

add_textbox(slide, Inches(1.3), Inches(1.3), Inches(11), Inches(0.5),
            "A continuous video is just a stream of frames — we need to identify WHERE activities change",
            font_size=16, color=LIGHT_GRAY)

# --- Continuous video timeline ---
add_textbox(slide, Inches(1.3), Inches(1.9), Inches(5), Inches(0.4),
            "53-second continuous screen recording", font_size=14,
            color=NUS_ORANGE, bold=True)

# Full-width timeline bar representing continuous video
add_rounded_rect(slide, Inches(1.3), Inches(2.4), Inches(11.5), Inches(0.8),
                 DARK_CARD)
add_textbox(slide, Inches(1.3), Inches(2.5), Inches(11.5), Inches(0.6),
            "Frame 1  ...  Frame 30  ...  Frame 60  ...  Frame 450  ...  Frame 900  ...  Frame 1590",
            font_size=13, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

# Time markers under timeline
times_x = [Inches(1.3), Inches(3.8), Inches(6.3), Inches(8.8), Inches(11.8)]
times_t = ["0:00", "0:15", "0:30", "0:45", "0:53"]
for tx, tt in zip(times_x, times_t):
    add_textbox(slide, tx, Inches(3.3), Inches(1), Inches(0.25),
                tt, font_size=10, color=SUBTLE_GRAY)

# Challenge callout
add_rounded_rect(slide, Inches(1.3), Inches(4.0), Inches(11.5), Inches(1.2),
                 LIGHT_ORANGE_BG)
add_textbox(slide, Inches(1.7), Inches(4.1), Inches(10.8), Inches(0.4),
            "The Challenge", font_size=16, color=NUS_ORANGE, bold=True)
add_multiline_textbox(slide, Inches(1.7), Inches(4.5), Inches(10.8), Inches(0.6),
                      [
                          "Continuous stream of pixels   →   Need to find meaningful boundaries",
                          "No built-in chapter markers   →   Must infer from user actions",
                          "Multiple activities in one recording   →   Each needs separate analysis",
                      ], font_size=13, color=NUS_ORANGE, spacing=Pt(6))

# Visual: stream arrow to segments
add_rounded_rect(slide, Inches(1.3), Inches(5.6), Inches(5), Inches(1.2),
                 DARK_CARD,
                 "Continuous Stream\n1,590 frames @ 30fps",
                 font_size=14, font_color=LIGHT_GRAY, bold=True)

add_textbox(slide, Inches(6.3), Inches(5.9), Inches(0.8), Inches(0.5),
            "→", font_size=32, color=ACCENT_BLUE, alignment=PP_ALIGN.CENTER)

add_textbox(slide, Inches(6.8), Inches(5.8), Inches(1.2), Inches(0.8),
            "Find\nBoundaries", font_size=13, color=ACCENT_BLUE, bold=True,
            alignment=PP_ALIGN.CENTER)

add_textbox(slide, Inches(7.8), Inches(5.9), Inches(0.8), Inches(0.5),
            "→", font_size=32, color=ACCENT_BLUE, alignment=PP_ALIGN.CENTER)

# Small colored segment blocks
seg_colors = [ACCENT_BLUE, ACCENT_GREEN, NUS_ORANGE, ACCENT_PURPLE,
              ACCENT_BLUE, ACCENT_GREEN, NUS_ORANGE]
seg_x = Inches(8.5)
for i, sc in enumerate(seg_colors):
    add_rounded_rect(slide, seg_x, Inches(5.7), Inches(0.55), Inches(1.0),
                     sc, str(i + 1), font_size=11, font_color=WHITE, bold=True)
    seg_x += Inches(0.6)

add_textbox(slide, Inches(8.5), Inches(6.75), Inches(4.2), Inches(0.3),
            "7 meaningful segments", font_size=11, color=SUBTLE_GRAY,
            alignment=PP_ALIGN.CENTER)


# ============================================================
# SLIDE 3: How Segmentation Works
# ============================================================
slide = add_content_slide(prs, "How Segmentation Works")

# --- Left side: action_log.json ---
add_rounded_rect(slide, Inches(1.3), Inches(1.3), Inches(4.8), Inches(0.5),
                 ACCENT_BLUE, "action_log.json — Source of Timing",
                 font_size=14, font_color=WHITE, bold=True)

# Simulated JSON entries
add_rounded_rect(slide, Inches(1.3), Inches(1.9), Inches(4.8), Inches(4.3),
                 DARK_CARD)
json_lines = [
    '{ "action_type": "CLICK",   "timestamp": "0:00" }',
    '{ "action_type": "CLICK",   "timestamp": "0:03" }',
    '{ "action_type": "CLICK",   "timestamp": "0:07" }',
    '',
    '{ "action_type": "TYPING",  "timestamp": "0:16" }',
    '',
    '{ "action_type": "PRESS",   "timestamp": "0:25" }',
    '{ "action_type": "CLICK",   "timestamp": "0:29" }',
    '',
    '{ "action_type": "TYPING",  "timestamp": "0:35" }',
    '{ "action_type": "PRESS",   "timestamp": "0:53" }',
    '{ "action_type": "CLICK",   "timestamp": "0:58" }',
    '...',
]
add_multiline_textbox(slide, Inches(1.5), Inches(2.0), Inches(4.4), Inches(4.0),
                      json_lines, font_size=10, color=ACCENT_GREEN,
                      spacing=Pt(3), font_name="Courier New")

# Gap annotations overlaid on the JSON
add_rounded_rect(slide, Inches(4.4), Inches(2.95), Inches(1.5), Inches(0.3),
                 NUS_ORANGE, "← 9s gap", font_size=9,
                 font_color=WHITE, bold=True)
add_rounded_rect(slide, Inches(4.4), Inches(4.0), Inches(1.5), Inches(0.3),
                 NUS_ORANGE, "← 4s gap", font_size=9,
                 font_color=WHITE, bold=True)

# --- Right side: Timeline visualization ---
add_rounded_rect(slide, Inches(6.6), Inches(1.3), Inches(6.2), Inches(0.5),
                 ACCENT_PURPLE, "Timeline: Actions, Gaps, and Boundaries",
                 font_size=14, font_color=WHITE, bold=True)

# Timeline base line
add_rect(slide, Inches(6.8), Inches(2.4), Inches(5.7), Inches(0.06),
         SUBTLE_GRAY)

# Action markers on timeline
actions = [
    (0.0, "CLICK\n0:00"),
    (0.18, "CLICK\n0:03"),
    (0.43, "CLICK\n0:07"),
    (0.97, "TYPE\n0:16"),
    (1.52, "PRESS\n0:25"),
    (1.76, "CLICK\n0:29"),
    (2.13, "TYPE\n0:35"),
    (3.22, "PRESS\n0:53"),
    (3.52, "CLICK\n0:58"),
]
for offset, label in actions:
    ax = Inches(6.8 + offset * 1.6)
    # Vertical tick
    add_rect(slide, ax, Inches(2.2), Inches(0.04), Inches(0.35), ACCENT_BLUE)
    # Label
    add_textbox(slide, ax - Inches(0.3), Inches(2.55), Inches(0.7), Inches(0.4),
                label, font_size=7, color=NUS_ORANGE, alignment=PP_ALIGN.CENTER)

# Gap highlights (orange zones between segments)
gaps = [
    (Inches(6.8 + 0.43 * 1.6), Inches(6.8 + 0.97 * 1.6), "9s gap"),
    (Inches(6.8 + 1.76 * 1.6), Inches(6.8 + 2.13 * 1.6), "6s gap"),
    (Inches(6.8 + 3.22 * 1.6), Inches(6.8 + 3.52 * 1.6), "5s gap"),
]
for gx1, gx2, glabel in gaps:
    gw = gx2 - gx1
    add_rect(slide, gx1, Inches(2.15), gw, Inches(0.35),
             LIGHT_ORANGE_BG)
    add_textbox(slide, gx1, Inches(1.9), gw, Inches(0.25),
                glabel, font_size=8, color=NUS_ORANGE, bold=True,
                alignment=PP_ALIGN.CENTER)

# Segment boundary markers
boundary_xs = [
    Inches(6.8 + 0.43 * 1.6),
    Inches(6.8 + 0.97 * 1.6),
    Inches(6.8 + 1.76 * 1.6),
    Inches(6.8 + 3.22 * 1.6),
    Inches(6.8 + 3.52 * 1.6),
]
for bx in boundary_xs:
    add_rect(slide, bx, Inches(2.0), Inches(0.03), Inches(0.65),
             NUS_ORANGE)

# Segment labels under the timeline
seg_ranges = [
    (0.0, 0.43, "Seg 1"),
    (0.43, 0.97, "Seg 2"),
    (0.97, 1.76, "Seg 3"),
    (1.76, 3.22, "Seg 4"),
    (3.22, 3.52, "Seg 5"),
]
seg_label_colors = [ACCENT_BLUE, ACCENT_GREEN, NUS_ORANGE,
                    ACCENT_PURPLE, ACCENT_BLUE]
for i, (s, e, slabel) in enumerate(seg_ranges):
    sx = Inches(6.8 + s * 1.6)
    sw = Inches((e - s) * 1.6)
    add_rounded_rect(slide, sx, Inches(3.05), sw, Inches(0.25),
                     seg_label_colors[i], slabel, font_size=8,
                     font_color=WHITE, bold=True)

# Key insight box
add_rounded_rect(slide, Inches(6.6), Inches(3.6), Inches(6.2), Inches(0.7),
                 LIGHT_BLUE_BG)
add_textbox(slide, Inches(6.8), Inches(3.65), Inches(5.8), Inches(0.6),
            "When the gap between actions exceeds a threshold → new segment starts",
            font_size=15, color=ACCENT_BLUE, bold=True,
            alignment=PP_ALIGN.CENTER)

# Algorithm steps
add_textbox(slide, Inches(6.6), Inches(4.5), Inches(6.2), Inches(0.4),
            "Segmentation Algorithm", font_size=16, color=NUS_ORANGE, bold=True)

algo_steps = [
    "1.  Parse action_log.json → sort actions by timestamp",
    "2.  Compute time gaps between consecutive actions",
    "3.  If gap > threshold (e.g. 5 seconds) → mark a segment boundary",
    "4.  Group actions within each boundary into segments",
    "5.  Record start_time, end_time, and actions for each segment",
]
add_multiline_textbox(slide, Inches(6.8), Inches(4.9), Inches(5.8), Inches(1.5),
                      algo_steps, font_size=12, color=NUS_ORANGE, spacing=Pt(6))


# ============================================================
# SLIDE 4: Segmentation Result
# ============================================================
slide = add_content_slide(prs, "Segmentation Result")

add_textbox(slide, Inches(1.3), Inches(1.3), Inches(11), Inches(0.4),
            "7 segments extracted from a 1:47 screen recording",
            font_size=14, color=LIGHT_GRAY)

# --- Segment data ---
segments = [
    ("Seg 1", "0:00 – 0:07",  "Opening editor",    ACCENT_BLUE,   7),
    ("Seg 2", "0:07 – 0:16",  "Opening terminal",  ACCENT_GREEN,  9),
    ("Seg 3", "0:16 – 0:29",  "git pull",          NUS_ORANGE,    13),
    ("Seg 4", "0:29 – 0:58",  "npm install",       ACCENT_PURPLE, 29),
    ("Seg 5", "0:58 – 1:12",  "Open browser",      ACCENT_BLUE,   14),
    ("Seg 6", "1:12 – 1:35",  "Check localhost",   ACCENT_GREEN,  23),
    ("Seg 7", "1:35 – 1:47",  "Verify app",        NUS_ORANGE,    12),
]

total_secs = 107  # 1:47 in seconds
timeline_left = Inches(1.3)
timeline_width_in = 11.5
timeline_top = Inches(1.8)
timeline_height = Inches(0.9)

# Draw segment blocks on the timeline (proportional width)
for seg_name, time_range, activity, color, duration in segments:
    frac = duration / total_secs
    block_w = Inches(timeline_width_in * frac)
    add_rounded_rect(slide, timeline_left, timeline_top, block_w,
                     timeline_height, color,
                     f"{seg_name}\n{activity}", font_size=10,
                     font_color=WHITE, bold=True)
    # Time label under each block
    add_textbox(slide, timeline_left, timeline_top + timeline_height,
                block_w, Inches(0.25), time_range, font_size=8,
                color=SUBTLE_GRAY, alignment=PP_ALIGN.CENTER)
    timeline_left += block_w

# --- Detailed table ---
add_textbox(slide, Inches(1.3), Inches(3.2), Inches(5), Inches(0.4),
            "Segment Details", font_size=16, color=NUS_ORANGE, bold=True)

# Table header
header_y = Inches(3.6)
add_rounded_rect(slide, Inches(1.3), header_y, Inches(11.5), Inches(0.35),
                 ACCENT_BLUE)
col_positions = [Inches(1.4), Inches(2.5), Inches(4.5), Inches(7.0),
                 Inches(9.0), Inches(11.0)]
col_headers = ["Segment", "Time Range", "Activity", "Duration",
               "Keyframes", "Actions"]
for cx, ch in zip(col_positions, col_headers):
    add_textbox(slide, cx, header_y, Inches(1.8), Inches(0.35),
                ch, font_size=10, color=WHITE, bold=True)

# Table rows
keyframe_counts = [2, 3, 3, 4, 3, 4, 2]
action_counts = [3, 4, 5, 8, 4, 6, 3]
row_y = header_y + Inches(0.38)
for i, (seg_name, time_range, activity, color, duration) in enumerate(segments):
    # Alternating row bg
    row_bg = LIGHT_BG if i % 2 == 0 else CARD_BG
    add_rounded_rect(slide, Inches(1.3), row_y, Inches(11.5), Inches(0.32),
                     row_bg)
    # Color indicator
    add_rounded_rect(slide, Inches(1.35), row_y + Inches(0.06),
                     Inches(0.08), Inches(0.2), color)

    row_data = [
        seg_name, time_range, activity,
        f"{duration}s",
        f"{keyframe_counts[i]} frames",
        f"{action_counts[i]} actions",
    ]
    for cx, cd in zip(col_positions, row_data):
        add_textbox(slide, cx, row_y, Inches(1.8), Inches(0.32),
                    cd, font_size=10, color=NUS_ORANGE)
    row_y += Inches(0.34)

# Summary box
add_rounded_rect(slide, Inches(1.3), Inches(6.2), Inches(11.5), Inches(0.5),
                 LIGHT_GREEN_BG)
add_textbox(slide, Inches(1.5), Inches(6.23), Inches(11), Inches(0.4),
            "Each segment = a discrete unit of work with its own keyframes and actions, ready for independent feature extraction",
            font_size=14, color=ACCENT_GREEN, bold=True,
            alignment=PP_ALIGN.CENTER)


# ============================================================
# SLIDE 5: Keyframe Extraction
# ============================================================
slide = add_content_slide(prs, "Keyframe Extraction")

add_textbox(slide, Inches(1.3), Inches(1.3), Inches(11), Inches(0.4),
            "Keyframes are actual video frames extracted at action boundaries",
            font_size=16, color=LIGHT_GRAY)

# --- Segment 3 focus ---
add_rounded_rect(slide, Inches(1.3), Inches(1.8), Inches(11.5), Inches(0.5),
                 NUS_ORANGE, "Segment 3: git pull  (0:16 – 0:29)",
                 font_size=16, font_color=WHITE, bold=True)

# Three keyframe boxes
kf_data = [
    ("Keyframe @ 0:16", "Start of typing", "$ git pull origin ma|",
     "User begins typing\nthe git pull command"),
    ("Keyframe @ 0:20", "Mid-action", "$ git pull origin main\nremote: Enumerating...",
     "Command sent,\nwaiting for response"),
    ("Keyframe @ 0:28", "Command output", "$ git pull origin main\nAlready up to date.\n$",
     "Operation complete,\nprompt returned"),
]

kf_x = Inches(1.3)
for title, subtitle, terminal_text, desc in kf_data:
    # Keyframe card
    add_rounded_rect(slide, kf_x, Inches(2.5), Inches(3.6), Inches(2.8),
                     CARD_BG)
    add_textbox(slide, kf_x + Inches(0.1), Inches(2.55), Inches(3.4),
                Inches(0.3), title, font_size=12, color=NUS_ORANGE,
                bold=True, alignment=PP_ALIGN.CENTER)
    add_textbox(slide, kf_x + Inches(0.1), Inches(2.8), Inches(3.4),
                Inches(0.25), subtitle, font_size=10, color=SUBTLE_GRAY,
                alignment=PP_ALIGN.CENTER)
    # Simulated terminal
    add_rounded_rect(slide, kf_x + Inches(0.15), Inches(3.1), Inches(3.3),
                     Inches(1.3), DARK_CARD)
    add_multiline_textbox(slide, kf_x + Inches(0.3), Inches(3.2), Inches(3.0),
                          Inches(1.1), terminal_text.split("\n"), font_size=10,
                          color=ACCENT_GREEN, font_name="Courier New",
                          spacing=Pt(3))
    # Description
    add_textbox(slide, kf_x + Inches(0.1), Inches(4.5), Inches(3.4),
                Inches(0.6), desc, font_size=10, color=NUS_ORANGE,
                alignment=PP_ALIGN.CENTER)

    kf_x += Inches(3.8)

# OpenCV explanation
add_rounded_rect(slide, Inches(1.3), Inches(5.5), Inches(5.5), Inches(0.9),
                 LIGHT_BLUE_BG)
add_textbox(slide, Inches(1.5), Inches(5.55), Inches(5.1), Inches(0.3),
            "How OpenCV Extracts Keyframes", font_size=13, color=ACCENT_BLUE,
            bold=True)
add_multiline_textbox(slide, Inches(1.5), Inches(5.85), Inches(5.1), Inches(0.5),
                      [
                          "cv2.VideoCapture(video_path)  →  opens the video file",
                          "cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_ms)  →  seeks to exact time",
                          "cap.read()  →  captures frame as numpy array (H x W x 3)",
                      ], font_size=10, color=NUS_ORANGE, spacing=Pt(3))

# SegmentData structure
add_rounded_rect(slide, Inches(7.1), Inches(5.5), Inches(5.5), Inches(1.2),
                 DARK_CARD)
add_textbox(slide, Inches(7.3), Inches(5.55), Inches(5.1), Inches(0.3),
            "SegmentData object", font_size=12, color=ACCENT_GREEN, bold=True)
struct_lines = [
    "class SegmentData:",
    "    segment_id: int          # 3",
    "    start_time: float        # 16.0",
    "    end_time: float          # 29.0",
    "    keyframes: list[ndarray] # [frame@16s, frame@20s, frame@28s]",
    "    actions: list[Action]    # [TYPING, PRESS, CLICK, ...]",
    "    label: str               # assigned after classification",
]
add_multiline_textbox(slide, Inches(7.3), Inches(5.85), Inches(5.1), Inches(1.0),
                      struct_lines, font_size=9, color=ACCENT_GREEN,
                      font_name="Courier New", spacing=Pt(2))


# ============================================================
# SLIDE 6: From Segments to Features
# ============================================================
slide = add_content_slide(prs, "From Segments to Features")

add_textbox(slide, Inches(1.3), Inches(1.3), Inches(11), Inches(0.4),
            "Each segment becomes a data point for classification",
            font_size=16, color=LIGHT_GRAY)

# --- Left: Segment inputs ---
add_rounded_rect(slide, Inches(1.3), Inches(1.8), Inches(3.2), Inches(2.0),
                 CARD_BG)
add_textbox(slide, Inches(1.5), Inches(1.85), Inches(2.8), Inches(0.35),
            "Segment Inputs", font_size=14, color=NUS_ORANGE, bold=True,
            alignment=PP_ALIGN.CENTER)

# Keyframes input
add_rounded_rect(slide, Inches(1.5), Inches(2.3), Inches(2.8), Inches(0.5),
                 ACCENT_BLUE, "Keyframes (images)", font_size=12,
                 font_color=WHITE, bold=True)
add_textbox(slide, Inches(1.5), Inches(2.85), Inches(2.8), Inches(0.3),
            "numpy arrays (H x W x 3)", font_size=9, color=SUBTLE_GRAY,
            alignment=PP_ALIGN.CENTER)

# Actions input
add_rounded_rect(slide, Inches(1.5), Inches(3.2), Inches(2.8), Inches(0.5),
                 ACCENT_GREEN, "Actions (from log)", font_size=12,
                 font_color=WHITE, bold=True)

# --- Arrow to extractors ---
add_textbox(slide, Inches(4.4), Inches(2.7), Inches(0.5), Inches(0.5),
            "→", font_size=32, color=NUS_ORANGE, alignment=PP_ALIGN.CENTER)

# --- Center: 4 Extractors ---
extractor_data = [
    ("EasyOCR", "50 dims", ACCENT_BLUE, LIGHT_BLUE_BG,
     "Reads text from frames\nTF-IDF vectorization\n\"git pull origin main\""),
    ("YOLOv8", "30 dims", NUS_ORANGE, LIGHT_ORANGE_BG,
     "Detects UI elements\nterminal, tabs, sidebar\nLayout + complexity"),
    ("OpenCV", "40 dims", ACCENT_PURPLE, LIGHT_PURPLE_BG,
     "Color histograms\nEdge density, texture\nScene composition"),
    ("Interaction\nParser", "30 dims", ACCENT_GREEN, LIGHT_GREEN_BG,
     "Action frequencies\nTyping speed, clicks\nMouse + keyboard stats"),
]

ext_y = Inches(1.6)
for name, dims, color, bg_color, desc in extractor_data:
    add_rounded_rect(slide, Inches(5.0), ext_y, Inches(4.3), Inches(1.2),
                     bg_color)
    add_rounded_rect(slide, Inches(5.1), ext_y + Inches(0.08), Inches(1.6),
                     Inches(0.35), color, name, font_size=10,
                     font_color=WHITE, bold=True)
    add_rounded_rect(slide, Inches(6.8), ext_y + Inches(0.08), Inches(0.9),
                     Inches(0.35), color, dims, font_size=10,
                     font_color=WHITE, bold=True)
    add_multiline_textbox(slide, Inches(5.2), ext_y + Inches(0.5), Inches(4.0),
                          Inches(0.65), desc.split("\n"), font_size=9,
                          color=NUS_ORANGE, spacing=Pt(2))
    ext_y += Inches(1.3)

# Source labels (connecting keyframes/actions to extractors)
add_textbox(slide, Inches(4.5), Inches(1.8), Inches(0.5), Inches(0.4),
            "→", font_size=18, color=ACCENT_BLUE,
            alignment=PP_ALIGN.CENTER)
add_textbox(slide, Inches(4.5), Inches(3.1), Inches(0.5), Inches(0.4),
            "→", font_size=18, color=NUS_ORANGE,
            alignment=PP_ALIGN.CENTER)
add_textbox(slide, Inches(4.5), Inches(4.4), Inches(0.5), Inches(0.4),
            "→", font_size=18, color=ACCENT_PURPLE,
            alignment=PP_ALIGN.CENTER)

# --- Arrow to combined vector ---
add_textbox(slide, Inches(9.3), Inches(3.2), Inches(0.5), Inches(0.5),
            "→", font_size=32, color=NUS_ORANGE, alignment=PP_ALIGN.CENTER)

# --- Right: 150-dim vector ---
add_rounded_rect(slide, Inches(9.8), Inches(1.6), Inches(3.2), Inches(5.2),
                 DARK_CARD)
add_textbox(slide, Inches(9.9), Inches(1.7), Inches(3.0), Inches(0.4),
            "150-dim Feature Vector", font_size=14, color=WHITE, bold=True,
            alignment=PP_ALIGN.CENTER)
add_textbox(slide, Inches(9.9), Inches(2.05), Inches(3.0), Inches(0.3),
            "per segment", font_size=11, color=LIGHT_GRAY,
            alignment=PP_ALIGN.CENTER)

vector_parts = [
    ("[0–49]",   "OCR",      "50 dims", ACCENT_BLUE),
    ("[50–79]",  "UI",       "30 dims", NUS_ORANGE),
    ("[80–119]", "Visual",   "40 dims", ACCENT_PURPLE),
    ("[120–149]", "Interact", "30 dims", ACCENT_GREEN),
]

vy = Inches(2.5)
for idx, label, dims, color in vector_parts:
    add_rounded_rect(slide, Inches(10.0), vy, Inches(2.8), Inches(0.85),
                     color)
    add_textbox(slide, Inches(10.1), vy + Inches(0.05), Inches(1.5),
                Inches(0.3), f"{idx} {label}", font_size=11, color=WHITE,
                bold=True)
    add_textbox(slide, Inches(10.1), vy + Inches(0.35), Inches(2.6),
                Inches(0.3), dims, font_size=10,
                color=RGBColor(0xE0, 0xE0, 0xE0))
    vy += Inches(0.95)

# Bottom: classification pointer
add_rounded_rect(slide, Inches(10.0), Inches(6.3), Inches(2.8), Inches(0.4),
                 DARK_CARD,
                 "→ Fed to 14 classifiers", font_size=12,
                 font_color=LIGHT_GRAY, bold=True)

# Bottom summary
add_rounded_rect(slide, Inches(1.3), Inches(6.3), Inches(8.3), Inches(0.4),
                 LIGHT_GREEN_BG)
add_textbox(slide, Inches(1.5), Inches(6.33), Inches(7.9), Inches(0.35),
            "7 segments  ×  150 features  =  7 data points for classification  →  7 activity labels",
            font_size=14, color=ACCENT_GREEN, bold=True,
            alignment=PP_ALIGN.CENTER)


# ============================================================
# Save
# ============================================================
output_path = "/Users/muneeswaranm/Projects/PRS/PatternRecognSystem-Video2Text/presentation/Video2Knowledge_Segmentation.pptx"
prs.save(output_path)
print(f"Saved to: {output_path}")
print(f"Total slides: {len(prs.slides)}")
