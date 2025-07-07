# printer_rl.py

import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as pdfcanvas

# ── 1) Scan & register all .ttf in /fonts ─────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONTS_DIR = os.path.join(BASE_DIR, "fonts")
os.makedirs(FONTS_DIR, exist_ok=True)

_registered_fonts = []
for fname in os.listdir(FONTS_DIR):
    if fname.lower().endswith(".ttf"):
        font_path = os.path.join(FONTS_DIR, fname)
        font_name = os.path.splitext(fname)[0]
        try:
            pdfmetrics.registerFont(TTFont(font_name, font_path))
            _registered_fonts.append(font_name)
        except Exception as e:
            print(f"⚠️ Could not register font {fname}: {e}")

# ── 2) Export function ──────────────────────────────────────────────────────
def export_to_pdf(output_path, settings, labels, show_logo=False, logo_path=None):
    """
    Creates a PDF at output_path with all labels laid out.
    `settings` is your dict from Sheet Editor (including:
       label_width_mm, rows, cols,
       name_font, name_size_pt, type_font, type_size_pt, price_font, price_size_pt, etc.)
    `labels` is a list of objects with .get_export_data() returning:
       {name, type, price_bgn, price_eur, unit_eur, logo}
    """
    canvas_obj = pdfcanvas.Canvas(output_path, pagesize=A4)
    page_w, page_h = A4
    mm_to_pt = lambda mm: mm * 72 / 25.4

    # ── Layout settings
    lw = float(settings.get("label_width_mm", 63.5))
    lh = float(settings.get("label_height_mm", 38.1))
    mt = float(settings.get("margin_top_mm", 10))
    ml = float(settings.get("margin_left_mm", 10))
    rg = float(settings.get("row_gap_mm", 0))
    cg = float(settings.get("col_gap_mm", 2.0))
    rows = int(settings.get("rows", 7))
    cols = int(settings.get("cols", 3))

    # ── Helper to pick a registered font or fallback
    def pick_font(key, fallback):
        fn = settings.get(key, "")
        return fn if fn in pdfmetrics.getRegisteredFontNames() else fallback

    # ── Font settings with Helvetica fallbacks
    name_font  = pick_font("name_font",   "Helvetica-Bold")
    name_size  = settings.get("name_size_pt", 11)
    type_font  = pick_font("type_font",   "Helvetica-Oblique")
    type_size  = settings.get("type_size_pt", 9)
    price_font = pick_font("price_font",  "Helvetica-Bold")
    price_size = settings.get("price_size_pt", 11)

    # ── Draw each label
    for idx, lbl in enumerate(labels):
        data = lbl.get_export_data()
        row, col = divmod(idx, cols)

        # Convert mm to points
        x_pt = mm_to_pt(ml + col * (lw + cg))
        # ReportLab origin is bottom-left
        y_pt = page_h - mm_to_pt(mt + row * (lh + rg) + lh)

        # small inside margin
        margin = mm_to_pt(2)
        text_x = x_pt + margin
        # start just below top of the label
        curr_y = y_pt + lh - margin

        # helper to draw text
        def draw_line(text, font_name, font_size):
            if not text:
                return 0
            # ensure font_name is string
            if not isinstance(font_name, str):
                font_name = "Helvetica"
            canvas_obj.setFont(font_name, font_size)
            canvas_obj.drawString(text_x, curr_y, text)
            return font_size * 1.2

        # — Name —
        delta = draw_line(data.get("name", ""), name_font, name_size)
        curr_y -= delta
        # — Type —
        delta = draw_line(data.get("type", ""), type_font, type_size)
        curr_y -= delta
        # — Price BGN —
        if data.get("price_bgn"):
            text = f"{data['price_bgn']} лв."
            delta = draw_line(text, price_font, price_size)
            curr_y -= delta
        # — Price EUR —
        if data.get("price_eur"):
            text = f"€{data['price_eur']}"
            delta = draw_line(text, price_font, price_size)
            curr_y -= delta

    canvas_obj.showPage()
    canvas_obj.save()
