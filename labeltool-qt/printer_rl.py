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

def export_to_pdf(output_path, settings, labels, show_logo=False, logo_path=None):
    """
    Creates a PDF at output_path with all labels laid out using the unified label_render logic.
    """
    from label_render import draw_labels_grid
    canvas_obj = pdfcanvas.Canvas(output_path, pagesize=A4)
    label_dicts = [lbl.get_export_data() for lbl in labels]
    draw_labels_grid(
        backend="reportlab",
        device=canvas_obj,
        settings=settings,
        labels=label_dicts,
        logo_path=logo_path if show_logo else None,
    )
    canvas_obj.showPage()
    canvas_obj.save()
