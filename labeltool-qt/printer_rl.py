# printer_rl.py

import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from textwrap import wrap

# ─── FONT REGISTRATION ─────────────────────────────────────────────────────────
# Fonts are stored in the "fonts" subfolder
HERE      = os.path.dirname(__file__)
FONT_FILE = os.path.join(HERE, "fonts", "DejaVuSans.ttf")

if os.path.exists(FONT_FILE):
    try:
        pdfmetrics.registerFont(TTFont("CustomFont", FONT_FILE))
        FONT_NAME = "CustomFont"
    except Exception as e:
        print(f"⚠️  Could not register font at '{FONT_FILE}': {e}")
        print("    Falling back to built-in Helvetica (Cyrillic may not render).")
        FONT_NAME = "Helvetica"
else:
    print(f"⚠️  Font file not found at '{FONT_FILE}'.")
    print("    Please ensure DejaVuSans.ttf is in the fonts/ folder.")
    FONT_NAME = "Helvetica"
# ──────────────────────────────────────────────────────────────────────────────

def export_to_pdf(path: str,
                  sheet_settings: dict,
                  labels: list,
                  show_logo: bool = False,
                  logo_path: str = None):
    """
    Export labels to a PDF at `path`, drawing text (in FONT_NAME)
    and an optional logo for each label cell, according to sheet_settings.
    """
    c = canvas.Canvas(path, pagesize=A4)
    page_w_pt, page_h_pt = A4

    # sheet_settings values in millimeters; convert to points
    cell_w   = sheet_settings["label_width_mm"] * mm
    cell_h   = sheet_settings["label_height_mm"] * mm
    margin_l = sheet_settings["margin_left_mm"]  * mm
    margin_t = sheet_settings["margin_top_mm"]   * mm
    gap_x    = sheet_settings["col_gap_mm"]      * mm
    gap_y    = sheet_settings["row_gap_mm"]      * mm
    rows     = int(sheet_settings["rows"])
    cols     = int(sheet_settings["cols"])
    LOGO_RATIO = 0.20  # fraction of cell width reserved for logo

    # preload logo image if requested
    logo_img = None
    if show_logo and logo_path and os.path.exists(logo_path):
        logo_img = ImageReader(logo_path)

    for idx, lbl in enumerate(labels):
        data = lbl.get_export_data()
        r    = idx // cols
        cidx = idx % cols

        # compute bottom-left corner of this label cell
        x0 = margin_l + cidx * (cell_w + gap_x)
        y0 = page_h_pt - margin_t - (r+1)*(cell_h + gap_y) + gap_y

        # 1) Draw logo region
        if logo_img:
            lw = cell_w * LOGO_RATIO
            lh = cell_h - (4 * mm)
            c.drawImage(logo_img, x0, y0 + 2*mm, lw, lh,
                        preserveAspectRatio=True, mask="auto")

        # 2) Build text lines
        lines = []
        if data["name"]:
            # wrap the name if too long
            max_chars = int((cell_w * (1 - LOGO_RATIO) - 4*mm) / (6*mm)) * 2
            wrapped = wrap(data["name"], max_chars)
            lines.extend(wrapped or [data["name"]])
        if data["type"]:
            lines.append(data["type"])
        if data["price_bgn"]:
            lines.append(f"{data['price_bgn']} лв.")
        if data["price_eur"]:
            eur = data["price_eur"].lstrip("€ ").strip()
            lines.append(f"€{eur}")
        if data["unit_eur"]:
            lines.append(f"/ {data['unit_eur']}")

        # 3) Dynamic vertical spacing
        count   = max(1, len(lines))
        avail_h = cell_h - (4 * mm)
        step    = avail_h / (count + 1)

        for i, text in enumerate(lines):
            y_line = y0 + cell_h - (i+1) * step - 2*mm
            # font size ~80% of step height
            font_pt = int(step * 0.8 / mm * 72 / 25.4)
            font_pt = max(4, min(font_pt, 10))

            c.setFont(FONT_NAME, font_pt)

            # horizontal alignment: left if logo, centered otherwise
            if logo_img:
                txt_x = x0 + cell_w * LOGO_RATIO + 2*mm
                c.drawString(txt_x, y_line, text)
            else:
                txt_x = x0 + (cell_w / 2)
                c.drawCentredString(txt_x, y_line, text)

    c.showPage()
    c.save()
