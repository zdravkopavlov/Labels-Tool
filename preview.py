# printer.py

import os
import sys

# Ensure this folder is on the import path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import platform
import subprocess
import tempfile
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# type: ignore so Pylance stops warning, but runtime will work
from labeltool.models import SheetTemplate         # type: ignore
from helpers import collect_labels                  # type: ignore
from tools.fonts import list_system_fonts           # type: ignore

# ───────── constants ───────────────────────────────────────────────────
BASE_DIR  = Path(__file__).resolve().parent
FONTS_DIR = BASE_DIR / "fonts"
TEMPLATE  = SheetTemplate()

NORMAL_GAP = 2
BIGGER_GAP = 12

# ───────── build font map ──────────────────────────────────────────────
SYSTEM_FONTS: dict[str, Path | None] = {}
_raw = list_system_fonts()
if isinstance(_raw, dict):
    for fam, p in _raw.items():
        SYSTEM_FONTS[fam.lower()] = Path(p) if p else None
else:
    for entry in _raw:
        try:
            fam, p = entry
        except Exception:
            fam, p = entry, None
        SYSTEM_FONTS[str(fam).lower()] = Path(p) if p else None

# bundled DejaVu fallback
for name, file in {
    "dejavu":              "DejaVuSans.ttf",
    "dejavu bold":         "DejaVuSans-Bold.ttf",
    "dejavu italic":       "DejaVuSans-Oblique.ttf",
    "dejavu bold italic":  "DejaVuSans-BoldOblique.ttf",
}.items():
    SYSTEM_FONTS.setdefault(name, FONTS_DIR / file)

def mm_to_pt(mm: float) -> float:
    return mm * 72.0 / 25.4

def _register_font(post_name: str, path: Path):
    if post_name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(post_name, str(path)))

def _font_for_style(family: str, bold: bool, italic: bool) -> str:
    key = family.lower()
    if bold and italic:
        key += " bold italic"
    elif bold:
        key += " bold"
    elif italic:
        key += " italic"

    path = SYSTEM_FONTS.get(key) or SYSTEM_FONTS.get(family.lower())
    if not path or not path.exists():
        key = (
            "dejavu bold italic" if (bold and italic)
            else "dejavu bold"        if bold
            else "dejavu italic"      if italic
            else "dejavu"
        )
        path = SYSTEM_FONTS[key]

    _register_font(key, path)
    return key

# ───────── draw one label ──────────────────────────────────────────────
def _draw_label(c: canvas.Canvas, lbl, x_pt: float, y_pt: float, app):
    W_pt = mm_to_pt(TEMPLATE.label_w_mm)
    H_pt = mm_to_pt(TEMPLATE.label_h_mm)

    def fit_text(txt: str, size: int, max_w: float,
                 fam: str, b: bool, i: bool) -> tuple[list[str], int]:
        face = _font_for_style(fam, b, i)
        s = size
        c.setFont(face, s)
        if c.stringWidth(txt) <= max_w:
            return [txt], s
        if " " in txt:
            a, rest = txt.split(" ", 1)
            if c.stringWidth(a) <= max_w and c.stringWidth(rest) <= max_w:
                return [a, rest], size
        while s > 6 and c.stringWidth(txt) > max_w:
            s -= 1
            c.setFont(face, s)
        return [txt], s

    lines: list[tuple[str,int,str,bool,bool,int]] = []
    has_sub = bool(lbl.name_sub.strip())
    max_w = W_pt - 4

    # Main name
    if lbl.name_main.strip():
        mains, ms = fit_text(
            lbl.name_main,
            app.name_font_size.get(),
            max_w,
            app.name_font_family.get(),
            app.name_bold.get(),
            app.name_italic.get()
        )
        gap = BIGGER_GAP if not has_sub else NORMAL_GAP
        for ln in mains:
            lines.append((ln, ms,
                          app.name_font_family.get(),
                          app.name_bold.get(),
                          app.name_italic.get(),
                          gap))

    # Subtitle
    if has_sub:
        subs, ss = fit_text(
            lbl.name_sub,
            app.sub_font_size.get(),
            max_w,
            app.sub_font_family.get(),
            app.sub_bold.get(),
            app.sub_italic.get()
        )
        for ln in subs:
            lines.append((ln, ss,
                          app.sub_font_family.get(),
                          app.sub_bold.get(),
                          app.sub_italic.get(),
                          BIGGER_GAP))

    # Prices
    if app.chk_bgn.get():
        lines.append((f"{lbl.price_bgn} лв. {lbl.unit}",
                      app.price_font_size.get(),
                      app.price_font_family.get(),
                      app.price_bold.get(),
                      app.price_italic.get(),
                      NORMAL_GAP))
    if app.chk_eur.get():
        lines.append((f"€{lbl.price_eur} {lbl.unit}",
                      app.price_font_size.get(),
                      app.price_font_family.get(),
                      app.price_bold.get(),
                      app.price_italic.get(),
                      NORMAL_GAP))

    total_h = sum(sz + gap for _, sz, *_, gap in lines) - lines[-1][5]
    cy = y_pt + H_pt - (H_pt - total_h) / 2

    for txt, sz, fam, bold, ital, gap in lines:
        face = _font_for_style(fam, bold, ital)
        cy -= sz
        c.setFont(face, sz)
        c.drawCentredString(x_pt + W_pt / 2, cy, txt)
        cy -= gap

# ───────── grid for calibration ────────────────────────────────────────
def _draw_grid(c: canvas.Canvas, app):
    for r in range(TEMPLATE.rows):
        for col in range(TEMPLATE.cols):
            x_mm = 7 + app.left_margin.get() + \
                   col * (TEMPLATE.label_w_mm + TEMPLATE.col_gap_mm + app.col_gap.get())
            y_mm = app.top_margin.get() + \
                   r * (TEMPLATE.label_h_mm + TEMPLATE.row_gap_mm) + \
                   app.row_correction.get() * r
            c.rect(mm_to_pt(x_mm),
                   mm_to_pt(297 - y_mm - TEMPLATE.label_h_mm),
                   mm_to_pt(TEMPLATE.label_w_mm),
                   mm_to_pt(TEMPLATE.label_h_mm),
                   stroke=1, fill=0)

# ───────── export / print functions ────────────────────────────────────
def export_pdf(app, path: str | os.PathLike):
    c = canvas.Canvas(str(path), pagesize=A4)
    labels = collect_labels(app)
    offset = app.start_offset.get()
    for idx in range(TEMPLATE.rows * TEMPLATE.cols):
        if idx < offset or (idx - offset) >= len(labels):
            continue
        row, col = divmod(idx, TEMPLATE.cols)
        lbl = labels[idx - offset]
        x_mm = 7 + app.left_margin.get() + \
               col * (TEMPLATE.label_w_mm + TEMPLATE.col_gap_mm + app.col_gap.get())
        y_mm = app.top_margin.get() + \
               row * (TEMPLATE.label_h_mm + TEMPLATE.row_gap_mm) + \
               app.row_correction.get() * row
        _draw_label(c, lbl,
                    mm_to_pt(x_mm),
                    mm_to_pt(297 - y_mm - TEMPLATE.label_h_mm),
                    app)
    c.save()

def export_pdf_dialog(app):
    from tkinter import filedialog
    path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                        filetypes=[("PDF", "*.pdf")])
    if path:
        export_pdf(app, path)
        try:
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", path])
            else:
                subprocess.run(["xdg-open", path])
        except Exception:
            pass

def print_labels(app):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.close()
    export_pdf(app, tmp.name)
    try:
        if platform.system() == "Windows":
            os.startfile(tmp.name, "print")
        elif platform.system() == "Darwin":
            subprocess.run(["lp", tmp.name])
        else:
            subprocess.run(["lpr", tmp.name])
    except Exception as e:
        from tkinter import messagebox
        messagebox.showerror("Print error", str(e))

def print_alignment_grid(app):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.close()
    c = canvas.Canvas(tmp.name, pagesize=A4)
    _draw_grid(c, app)
    c.save()
    try:
        if platform.system() == "Windows":
            os.startfile(tmp.name, "print")
        elif platform.system() == "Darwin":
            subprocess.run(["lp", tmp.name])
        else:
            subprocess.run(["lpr", tmp.name])
    except Exception as e:
        from tkinter import messagebox
        messagebox.showerror("Print error", str(e))
