"""NUS ISS PowerPoint template — shared colors, helpers, and slide layouts."""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor

# ── NUS ISS Official Colors ─────────────────────────────────────────────────

NUS_BLUE = RGBColor(0x00, 0x3D, 0x7C)
NUS_ORANGE = RGBColor(0xEF, 0x7C, 0x00)
SIDEBAR_YELLOW = RGBColor(0xFF, 0xE0, 0x33)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY = RGBColor(0xCC, 0xCC, 0xCC)
DARK_TEXT = RGBColor(0x2D, 0x2D, 0x2D)
SUBTLE_GRAY = RGBColor(0x99, 0x99, 0x99)

ACCENT_BLUE = RGBColor(0x00, 0x7A, 0xCC)
ACCENT_GREEN = RGBColor(0x28, 0xA7, 0x45)
ACCENT_PURPLE = RGBColor(0x6F, 0x42, 0xC1)
ACCENT_RED = RGBColor(0xCC, 0x22, 0x33)

LIGHT_BG = RGBColor(0xF8, 0xF9, 0xFA)
CARD_BG = RGBColor(0xF0, 0xF4, 0xF8)
LIGHT_BLUE_BG = RGBColor(0xE8, 0xF4, 0xFD)
LIGHT_GREEN_BG = RGBColor(0xE6, 0xF9, 0xED)
LIGHT_PURPLE_BG = RGBColor(0xF0, 0xEB, 0xF9)
LIGHT_ORANGE_BG = RGBColor(0xFE, 0xF3, 0xE2)
LIGHT_RED_BG = RGBColor(0xFD, 0xE8, 0xEA)

# Backwards-compatible aliases
DARK_BG = NUS_BLUE
ACCENT_ORANGE = NUS_ORANGE

SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)

COPYRIGHT_TEXT = "© Copyright National University of Singapore. All Rights Reserved."


# ── Presentation factory ────────────────────────────────────────────────────

def create_presentation():
    prs = Presentation()
    prs.slide_width = SLIDE_WIDTH
    prs.slide_height = SLIDE_HEIGHT
    return prs


# ── Low-level helpers ───────────────────────────────────────────────────────

def set_slide_bg(slide, color):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_textbox(slide, left, top, width, height, text, font_size=18,
                color=NUS_ORANGE, bold=False, alignment=PP_ALIGN.LEFT,
                font_name="Calibri"):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = font_name
    p.alignment = alignment
    return tf


def add_multiline_textbox(slide, left, top, width, height, lines,
                          font_size=16, color=NUS_ORANGE, bold=False,
                          alignment=PP_ALIGN.LEFT, spacing=Pt(6),
                          font_name="Calibri"):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, line_info in enumerate(lines):
        if isinstance(line_info, str):
            text, sz, clr, b = line_info, font_size, color, bold
        else:
            text = line_info.get("text", "")
            sz = line_info.get("size", font_size)
            clr = line_info.get("color", color)
            b = line_info.get("bold", bold)
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = text
        p.font.size = Pt(sz)
        p.font.color.rgb = clr
        p.font.bold = b
        p.font.name = font_name
        p.alignment = alignment
        p.space_after = spacing
    return tf


def add_bullet_list(slide, left, top, width, height, items, font_size=16,
                    color=NUS_ORANGE, spacing=Pt(8), bold_items=None):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = item
        p.font.size = Pt(font_size)
        p.font.color.rgb = color
        p.font.name = "Calibri"
        p.space_after = spacing
        p.level = 0
        if bold_items and i in bold_items:
            p.font.bold = True
    return tf


def add_rect(slide, left, top, width, height, fill_color, text="",
             font_size=14, font_color=WHITE, bold=False):
    shape = slide.shapes.add_shape(1, left, top, width, height)
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
    return shape


def add_rounded_rect(slide, left, top, width, height, fill_color, text="",
                     font_size=14, font_color=WHITE, bold=False):
    shape = slide.shapes.add_shape(5, left, top, width, height)
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


# ── NUS slide decorations ───────────────────────────────────────────────────

def add_nus_logo(slide):
    """White 'NUS' text placeholder in top-right corner."""
    add_textbox(slide, Inches(11.3), Inches(0.15), Inches(1.8), Inches(0.5),
                "NUS", font_size=24, color=WHITE, bold=True,
                alignment=PP_ALIGN.RIGHT, font_name="Arial")
    add_textbox(slide, Inches(11.3), Inches(0.5), Inches(1.8), Inches(0.35),
                "National University\nof Singapore", font_size=8, color=WHITE,
                bold=False, alignment=PP_ALIGN.RIGHT, font_name="Arial")


def add_nus_footer(slide):
    """Orange accent bar and copyright footer at the bottom."""
    add_rect(slide, Inches(0), Inches(6.75), SLIDE_WIDTH, Inches(0.06),
             NUS_ORANGE)
    add_textbox(slide, Inches(0.3), Inches(7.0), Inches(8), Inches(0.3),
                COPYRIGHT_TEXT, font_size=8, color=WHITE, bold=False,
                font_name="Calibri")


def add_sidebar_decoration(slide):
    """Yellow block (top-left) with orange vertical line — NUS content slide motif."""
    add_rect(slide, Inches(0), Inches(0), Inches(1.1), Inches(0.9),
             SIDEBAR_YELLOW)
    add_rect(slide, Inches(0.5), Inches(0.9), Inches(0.06), Inches(5.8),
             NUS_ORANGE)


# ── High-level slide builders ───────────────────────────────────────────────

def add_title_slide(prs, title, subtitle="", author="", affiliation="",
                    date_text=""):
    """NUS ISS title slide — navy blue background, centered white title."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, NUS_BLUE)
    add_nus_logo(slide)

    add_textbox(slide, Inches(1), Inches(1.8), Inches(11), Inches(1.5),
                title, font_size=44, color=WHITE, bold=True,
                alignment=PP_ALIGN.LEFT, font_name="Calibri")

    if subtitle:
        add_textbox(slide, Inches(1), Inches(3.5), Inches(11), Inches(1),
                    subtitle, font_size=22, color=WHITE,
                    alignment=PP_ALIGN.LEFT)

    if author:
        add_textbox(slide, Inches(1), Inches(4.8), Inches(11), Inches(0.5),
                    author, font_size=20, color=WHITE, bold=True,
                    alignment=PP_ALIGN.LEFT)

    if affiliation:
        add_textbox(slide, Inches(1), Inches(5.4), Inches(11), Inches(0.5),
                    affiliation, font_size=16, color=LIGHT_GRAY,
                    alignment=PP_ALIGN.LEFT)

    if date_text:
        add_textbox(slide, Inches(1), Inches(6.0), Inches(11), Inches(0.4),
                    date_text, font_size=14, color=LIGHT_GRAY,
                    alignment=PP_ALIGN.LEFT)

    add_nus_footer(slide)
    return slide


def add_content_slide(prs, title, subtitle=""):
    """NUS ISS content slide with sidebar decoration, logo, and footer."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, NUS_BLUE)
    add_sidebar_decoration(slide)
    add_nus_logo(slide)

    add_textbox(slide, Inches(1.3), Inches(0.1), Inches(9.5), Inches(0.7),
                title, font_size=32, color=WHITE, bold=True,
                font_name="Calibri")

    if subtitle:
        add_textbox(slide, Inches(1.3), Inches(0.65), Inches(9.5), Inches(0.5),
                    subtitle, font_size=20, color=WHITE, font_name="Calibri")

    add_nus_footer(slide)
    return slide


def add_section_slide(prs, title, subtitle=""):
    """Full-width section divider — no sidebar, centered text."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, NUS_BLUE)
    add_nus_logo(slide)

    add_textbox(slide, Inches(1), Inches(2.5), Inches(11), Inches(1.2),
                title, font_size=44, color=WHITE, bold=True,
                alignment=PP_ALIGN.CENTER)

    if subtitle:
        add_textbox(slide, Inches(1), Inches(3.8), Inches(11), Inches(0.8),
                    subtitle, font_size=22, color=NUS_ORANGE,
                    alignment=PP_ALIGN.CENTER)

    add_nus_footer(slide)
    return slide
