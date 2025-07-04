# preview.py – cached PDF-based preview (fit‐inside) with grid toggle.
from __future__ import annotations
import os
import hashlib
import subprocess
import tempfile
import tkinter as tk
from PIL import Image, ImageTk
from helpers import collect_labels
from printer import export_pdf, export_pdf_gridonly

PREVIEW_DPI = 72
# Adjust this path if your GhostScript exe lives elsewhere:
GS_EXE = os.path.join(os.path.dirname(__file__), "ghostscript", "gswin64c.exe")

_cache_sig: str | None = None
_cache_img: Image.Image | None = None

def reset_preview_cache():
    global _cache_sig, _cache_img
    _cache_sig = None
    _cache_img = None

def _sheet_png(app, dpi=PREVIEW_DPI) -> Image.Image:
    global _cache_sig, _cache_img
    labels = collect_labels(app)
    # fingerprint all relevant settings + data
    sig = hashlib.md5(repr((
        labels,
        app.start_offset.get(),
        app.left_margin.get(), app.top_margin.get(),
        app.row_correction.get(), app.col_gap.get(),
        app.chk_bgn.get(), app.chk_eur.get(),
        app.name_font_family.get(), app.name_font_size.get(),
        app.name_bold.get(), app.name_italic.get(),
        app.sub_font_family.get(), app.sub_font_size.get(),
        app.sub_bold.get(),  app.sub_italic.get(),
        app.price_font_family.get(), app.price_font_size.get(),
        app.price_bold.get(), app.price_italic.get(),
    )).encode()).hexdigest()

    # reuse cached image if nothing changed
    if sig == _cache_sig and _cache_img is not None:
        return _cache_img.copy()

    # otherwise regenerate PDF → PNG
    pdf_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name

    # ----------- KEY LOGIC ------------
    # If no labels and grid ON, export grid only!
    if not labels and getattr(app, "show_guides", None) and app.show_guides.get():
        export_pdf_gridonly(app, pdf_path)
    else:
        export_pdf(app, pdf_path)
    # ----------------------------------

    png_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name

    import sys
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NO_WINDOW

    subprocess.run([
        GS_EXE,
        "-dNOPAUSE","-dBATCH","-sDEVICE=png16m",
        f"-r{dpi}", f"-sOutputFile={png_path}", pdf_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, creationflags=creationflags)

    img = Image.open(png_path).convert("RGB")
    _cache_sig, _cache_img = sig, img.copy()

    os.unlink(pdf_path)
    os.unlink(png_path)
    return img


def draw_preview(app):
    cv: tk.Canvas = app.preview_canvas
    cw, ch = max(cv.winfo_width(), 10), max(cv.winfo_height(), 10)
    # too small to draw
    if cw < 50 or ch < 50:
        return

    # get the sheet as an Image
    img = _sheet_png(app)
    # scale it to fit
    scale = min(cw / img.width, ch / img.height)
    new_w, new_h = int(img.width * scale), int(img.height * scale)
    photo = ImageTk.PhotoImage(img.resize((new_w, new_h), Image.LANCZOS))

    # clear old preview, draw new
    cv.delete("all")
    ox, oy = (cw - new_w) // 2, (ch - new_h) // 2
    cv.create_image(ox, oy, anchor="nw", image=photo)
    cv.image = photo  # keep reference!

    # optionally overlay the preview grid (not needed for grid-only preview, but left in for overlays)
    if getattr(app, "show_guides", None) and app.show_guides.get():
        from labeltool.models import SheetTemplate
        t = SheetTemplate()
        dpi = PREVIEW_DPI
        # convert mm → pixels (after scaling)
        def mm(v): return int(v / 25.4 * dpi * scale)

        lm = mm(7.0 + app.left_margin.get())
        tm = mm(app.top_margin.get())
        w = mm(t.label_w_mm)
        h = mm(t.label_h_mm)
        gap_x = mm(t.label_w_mm + t.col_gap_mm + app.col_gap.get())
        core_y = t.label_h_mm + t.row_gap_mm
        rc = app.row_correction.get()

        for r in range(t.rows):
            y = mm(core_y * r + rc * r) + tm + oy
            for c in range(t.cols):
                x = lm + c * gap_x + ox
                cv.create_rectangle(x, y, x + w, y + h, outline="#666")
