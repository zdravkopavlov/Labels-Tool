from PyQt5.QtGui import QFont, QFontMetrics, QPixmap
from PyQt5.QtCore import Qt, QRectF
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
import os

# === VERTICAL SPACING (pixels, in pt units) ===
PADDING_TOP = 40
GAP_NAME_TYPE = -8
GAP_TYPE_PRICE = 14
GAP_BETWEEN_PRICES = -5
PADDING_BOTTOM_UNIT = 5
# ==============================================

# --- Register DejaVu Sans family for ReportLab ---
FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")
DEJAVU_FONTS = {
    "DejaVu Sans": "DejaVuSans.ttf",
    "DejaVu Sans-Bold": "DejaVuSans-Bold.ttf",
    "DejaVu Sans-Oblique": "DejaVuSans-Oblique.ttf",
    "DejaVu Sans-BoldOblique": "DejaVuSans-BoldOblique.ttf"
}
for name, fname in DEJAVU_FONTS.items():
    path = os.path.join(FONT_DIR, fname)
    if os.path.exists(path) and name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(name, path))

def get_reportlab_font_name(base_name, bold, italic):
    name = base_name
    if bold and italic:
        name += "-BoldOblique"
    elif bold:
        name += "-Bold"
    elif italic:
        name += "-Oblique"
    if name in pdfmetrics.getRegisteredFontNames():
        return name
    if base_name in pdfmetrics.getRegisteredFontNames():
        return base_name
    return "Helvetica"

def wrap_text_and_scale(qf: QFont, text: str, max_width: float):
    size = qf.pointSize()
    words = text.split()
    while size > 7:
        qf.setPointSize(size)
        fm = QFontMetrics(qf)
        lines = []
        curr = ""
        for w in words:
            test = (curr + " " + w).strip()
            if fm.width(test) > max_width and curr:
                lines.append(curr)
                curr = w
            else:
                curr = test
        if curr:
            lines.append(curr)
        if len(lines) <= 2 and all(fm.width(ln) <= max_width for ln in lines):
            return ("\n".join(lines), QFont(qf.family(), size, qf.weight(), qf.italic()))
        size -= 1
    avg = fm.averageCharWidth() or 1
    count = int(max_width // avg)
    return (text[:count] + "...", QFont(qf.family(), size))

def wrap_text_and_scale_reportlab(
    font_name: str,
    text: str,
    font_size: float,
    max_width: float,
    device
):
    words = text.split()
    sz = font_size
    while sz > 7:
        lines = []
        curr = ""
        for w in words:
            test = (curr + " " + w).strip()
            if device.stringWidth(test, font_name, sz) > max_width and curr:
                lines.append(curr)
                curr = w
            else:
                curr = test
        if curr:
            lines.append(curr)
        if len(lines) <= 2 and all(device.stringWidth(ln, font_name, sz) <= max_width for ln in lines):
            return ("\n".join(lines), sz)
        sz -= 1
    return (text[:15] + "...", sz)

def draw_labels_grid(
    backend: str,
    device,
    settings: dict,
    labels: list,
    logo_path: str = None,
):
    mm_to_pt = lambda mm: mm * 72 / 25.4

    lw = float(settings.get("label_width_mm", 63.5))
    lh = float(settings.get("label_height_mm", 38.1))
    mt = float(settings.get("margin_top_mm", 10))
    ml = float(settings.get("margin_left_mm", 10))
    rg = float(settings.get("row_gap_mm", 0))
    cg = float(settings.get("col_gap_mm", 2.0))
    rows = int(settings.get("rows", 7))
    cols = int(settings.get("cols", 3))

    def get_font(tag):
        return (
            settings.get(f"{tag}_font", "DejaVu Sans"),
            settings.get(f"{tag}_size_pt", 11 if tag != "type" else 9),
            settings.get(f"{tag}_bold", tag != "type"),
            settings.get(f"{tag}_italic", tag == "type")
        )

    logo_pixmap = QPixmap(logo_path) if logo_path and backend == "qtpainter" else None

    for idx, data in enumerate(labels):
        row, col = divmod(idx, cols)
        x = mm_to_pt(ml + col * (lw + cg))
        w_pt = mm_to_pt(lw)
        h_pt = mm_to_pt(lh)

        # --- Gather main fields with per-line tags ---
        main_lines = []
        if data.get("name"):
            main_lines.append(("name", data["name"]))
        if data.get("type"):
            main_lines.append(("type", data["type"]))
        if data.get("price_bgn"):
            main_lines.append(("price_bgn", f"{data['price_bgn']} лв."))
        if data.get("price_eur"):
            main_lines.append(("price_eur", f"€{data['price_eur']}"))

        unit = data.get("unit_eur", "").strip()
        has_unit = bool(unit)
        unit_str = f"/ {unit}" if has_unit else ""

        max_w = w_pt - (48 if data.get("logo") else 0) - 4

        # --- QPainter Branch ---
        if backend == "qtpainter":
            font_objs, txt_blocks, heights = [], [], []
            for i, (tag, txt) in enumerate(main_lines):
                if tag == "name":
                    fam, sz_pt, bd, it = get_font("name")
                elif tag == "type":
                    fam, sz_pt, bd, it = get_font("type")
                elif tag in ("price_bgn", "price_eur"):
                    fam, sz_pt, bd, it = get_font("price")
                else:
                    fam, sz_pt, bd, it = get_font("name")
                qf = QFont(fam, sz_pt)
                qf.setBold(bd)
                qf.setItalic(it)
                if i == 0:
                    wrapped, qf_final = wrap_text_and_scale(qf, txt, max_w)
                else:
                    wrapped, qf_final = txt, qf
                font_objs.append(qf_final)
                txt_blocks.append(wrapped)
                fm = QFontMetrics(qf_final)
                heights.append(fm.height() * (wrapped.count("\n") + 1))
            unit_font = QFont(settings.get("type_font", "DejaVu Sans"), 9)
            unit_font.setItalic(True)
            unit_fm = QFontMetrics(unit_font)
            unit_height = unit_fm.height()

            main_total_h = sum(heights)
            if len(main_lines) >= 2:
                main_total_h += GAP_NAME_TYPE
            if len(main_lines) >= 3:
                main_total_h += GAP_TYPE_PRICE
            if len(main_lines) == 4:
                main_total_h += GAP_BETWEEN_PRICES

            available_height = h_pt - unit_height - PADDING_BOTTOM_UNIT - PADDING_TOP
            sy = mm_to_pt(mt + row * (lh + rg)) + PADDING_TOP + (available_height - main_total_h) / 2

            if data.get("logo") and logo_pixmap:
                lg = mm_to_pt(11)
                lx = x + 3
                ly = sy + (main_total_h - lg) / 2
                device.drawPixmap(int(lx), int(ly), int(lg), int(lg), logo_pixmap)

            cy = sy
            for i, (qf, block) in enumerate(zip(font_objs, txt_blocks)):
                device.setFont(qf)
                fm = QFontMetrics(qf)
                for ln in block.split("\n"):
                    rect = QRectF(x, cy, w_pt, fm.height())
                    device.drawText(rect, Qt.AlignHCenter | Qt.AlignTop, ln)
                    cy += fm.height()
                if i == 0 and len(main_lines) > 1:
                    cy += GAP_NAME_TYPE
                if i == 1 and len(main_lines) > 2:
                    cy += GAP_TYPE_PRICE
                if i == 2 and len(main_lines) > 3:
                    cy += GAP_BETWEEN_PRICES

            if has_unit:
                device.setFont(unit_font)
                unit_rect = QRectF(
                    x,
                    mm_to_pt(mt + row * (lh + rg)) + h_pt - unit_height - PADDING_BOTTOM_UNIT,
                    w_pt,
                    unit_height + 2
                )
                device.drawText(unit_rect, Qt.AlignRight | Qt.AlignVCenter, unit_str)

            continue

        # --- ReportLab branch (PDF) ---
        font_objs, txt_blocks, heights = [], [], []
        for i, (tag, txt) in enumerate(main_lines):
            if tag == "name":
                fam, sz_pt, bd, it = get_font("name")
            elif tag == "type":
                fam, sz_pt, bd, it = get_font("type")
            elif tag in ("price_bgn", "price_eur"):
                fam, sz_pt, bd, it = get_font("price")
            else:
                fam, sz_pt, bd, it = get_font("name")
            rl_name = get_reportlab_font_name(fam, bd, it)
            if i == 0:
                wrapped, new_sz = wrap_text_and_scale_reportlab(
                    rl_name, txt, sz_pt, max_w, device
                )
                font_objs.append((rl_name, new_sz))
                txt_blocks.append(wrapped)
                heights.append(new_sz * 1.3 * (wrapped.count("\n") + 1))
            else:
                font_objs.append((rl_name, sz_pt))
                txt_blocks.append(txt)
                heights.append(sz_pt * 1.3)
        unit_font = get_font("type")
        unit_sz = 9
        unit_rl_name = get_reportlab_font_name(unit_font[0], False, True)
        unit_height = unit_sz * 1.2

        main_total_h = sum(heights)
        if len(main_lines) >= 2:
            main_total_h += GAP_NAME_TYPE
        if len(main_lines) >= 3:
            main_total_h += GAP_TYPE_PRICE
        if len(main_lines) == 4:
            main_total_h += GAP_BETWEEN_PRICES

        page_h = device._pagesize[1]
        y0 = page_h - mm_to_pt(mt + row * (lh + rg) + lh)
        available_height = h_pt - unit_height - PADDING_BOTTOM_UNIT - PADDING_TOP
        top_off = PADDING_TOP + (available_height - main_total_h) / 2

        margin = mm_to_pt(2)
        if data.get("logo") and logo_path:
            img = ImageReader(logo_path)
            lg = mm_to_pt(11)
            device.drawImage(img,
                             x + 3,
                             y0 + (h_pt - lg) / 2,
                             width=lg, height=lg,
                             preserveAspectRatio=True)
            tx = x + 3 + lg + 6
        else:
            tx = x + 2

        cy = y0 + h_pt - margin - top_off
        for (fn, fs), block, (tag, _) in zip(font_objs, txt_blocks, main_lines):
            device.setFont(fn, fs)
            for line in block.split("\n"):
                wtext = device.stringWidth(line, fn, fs)
                xpos = tx if data.get("logo") else x + (w_pt - wtext) / 2
                device.drawString(xpos, cy, line)
                cy -= fs * 1.3
            if tag == "name" and len(main_lines) > 1:
                cy -= GAP_NAME_TYPE
            if tag == "type" and len(main_lines) > 2:
                cy -= GAP_TYPE_PRICE
            if tag in ("price_bgn", "price_eur") and len(main_lines) > 3:
                cy -= GAP_BETWEEN_PRICES

        if has_unit:
            device.setFont(unit_rl_name, unit_sz)
            unit_y = y0 + unit_height + PADDING_BOTTOM_UNIT
            unit_x = x + w_pt - device.stringWidth(unit_str, unit_rl_name, unit_sz) - mm_to_pt(2)
            device.drawString(unit_x, y0 + unit_height + PADDING_BOTTOM_UNIT, unit_str)
