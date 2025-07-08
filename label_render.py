from PyQt5.QtGui import QFont, QFontMetrics, QPixmap
from PyQt5.QtCore import Qt, QRectF
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
import os

# === VERTICAL SPACING (pixels, in pt units) ===
PADDING_TOP = 45
GAP_HEADER = -6        # between name and type, if both present
GAP_HEADER_PRICE = 15  # between header group and price group
GAP_PRICES = -5        # between BGN and EUR prices, if both present
PADDING_BOTTOM_UNIT = 5
# ==============================================

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
            return (lines, QFont(qf.family(), size, qf.weight(), qf.italic()))
        size -= 1
    avg = fm.averageCharWidth() or 1
    count = int(max_width // avg)
    return ([text[:count] + "..."], QFont(qf.family(), size))

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
            return (lines, sz)
        sz -= 1
    return ([text[:15] + "..."], sz)

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

        # === Build blocks: header and price ===

        NAME_FONT_REDUCTION_FACTOR = 0.8  # 80% if wraps

        header_blocks = []
        if data.get("name"):
            fam, sz_pt, bd, it = get_font("name")
            qf = QFont(fam, sz_pt)
            qf.setBold(bd)
            qf.setItalic(it)
            lines, qf_final = wrap_text_and_scale(qf, data["name"], w_pt - (48 if data.get("logo") else 0) - 4)
            # If name wraps, shrink font and re-wrap
            if len(lines) > 1:
                reduced_size = max(7, int(sz_pt * NAME_FONT_REDUCTION_FACTOR))
                qf_small = QFont(fam, reduced_size)
                qf_small.setBold(bd)
                qf_small.setItalic(it)
                lines, qf_final = wrap_text_and_scale(qf_small, data["name"], w_pt - (48 if data.get("logo") else 0) - 4)
            header_blocks.append(("name", lines, qf_final))
        if data.get("type"):
            fam, sz_pt, bd, it = get_font("type")
            qf = QFont(fam, sz_pt)
            qf.setBold(bd)
            qf.setItalic(it)
            lines = [data["type"]]
            header_blocks.append(("type", lines, qf))


        price_blocks = []
        if data.get("price_bgn"):
            fam, sz_pt, bd, it = get_font("price")
            qf = QFont(fam, sz_pt); qf.setBold(bd); qf.setItalic(it)
            lines = [f"{data['price_bgn']} лв."]
            price_blocks.append(("price_bgn", lines, qf))
        if data.get("price_eur"):
            fam, sz_pt, bd, it = get_font("price")
            qf = QFont(fam, sz_pt); qf.setBold(bd); qf.setItalic(it)
            lines = [f"€{data['price_eur']}"]
            price_blocks.append(("price_eur", lines, qf))

        unit = data.get("unit_eur", "").strip()
        has_unit = bool(unit)
        unit_str = f"/ {unit}" if has_unit else ""

        # === Calculate total height of all blocks + spacings ===
        unit_font = QFont(settings.get("type_font", "DejaVu Sans"), 9)
        unit_font.setItalic(True)
        unit_fm = QFontMetrics(unit_font)
        unit_height = unit_fm.height()

        heights = []

        # Header blocks (with tight gaps)
        for i, (tag, lines, qf) in enumerate(header_blocks):
            fm = QFontMetrics(qf)
            heights.append(fm.height() * len(lines))
            if i < len(header_blocks) - 1:
                heights.append(GAP_HEADER)

        # Gap between header and price group, if both present
        if header_blocks and price_blocks:
            heights.append(GAP_HEADER_PRICE)

        # Price blocks (with tight gaps)
        for i, (tag, lines, qf) in enumerate(price_blocks):
            fm = QFontMetrics(qf)
            heights.append(fm.height() * len(lines))
            if i < len(price_blocks) - 1:
                heights.append(GAP_PRICES)

        total_h = sum(h if isinstance(h, (int, float)) else 0 for h in heights)

        available_height = h_pt - unit_height - PADDING_BOTTOM_UNIT - PADDING_TOP
        sy = mm_to_pt(mt + row * (lh + rg)) + PADDING_TOP + (available_height - total_h) / 2

        # === QPainter branch ===
        if backend == "qtpainter":
            # Draw logo (if any)
            if data.get("logo") and logo_pixmap:
                lg = mm_to_pt(11)
                lx = x + 3
                ly = sy + (total_h - lg) / 2
                device.drawPixmap(int(lx), int(ly), int(lg), int(lg), logo_pixmap)

            cy = sy
            # Draw header blocks
            for i, (tag, lines, qf) in enumerate(header_blocks):
                device.setFont(qf)
                fm = QFontMetrics(qf)
                for ln in lines:
                    rect = QRectF(x, cy, w_pt, fm.height())
                    device.drawText(rect, Qt.AlignHCenter | Qt.AlignTop, ln)
                    cy += fm.height()
                if i < len(header_blocks) - 1:
                    cy += GAP_HEADER

            # Gap between header group and price group
            if header_blocks and price_blocks:
                cy += GAP_HEADER_PRICE

            # Draw price blocks
            for i, (tag, lines, qf) in enumerate(price_blocks):
                device.setFont(qf)
                fm = QFontMetrics(qf)
                for ln in lines:
                    rect = QRectF(x, cy, w_pt, fm.height())
                    device.drawText(rect, Qt.AlignHCenter | Qt.AlignTop, ln)
                    cy += fm.height()
                if i < len(price_blocks) - 1:
                    cy += GAP_PRICES

            # Draw unit, always at same place, right-aligned and small italic
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

        # === ReportLab (PDF) branch ===
        header_blocks_pdf = []
        if data.get("name"):
            fam, sz_pt, bd, it = get_font("name")
            rl_name = get_reportlab_font_name(fam, bd, it)
            lines, new_sz = wrap_text_and_scale_reportlab(
                rl_name, data["name"], sz_pt, w_pt - (48 if data.get("logo") else 0) - 4, device)
            # If wraps, shrink font and re-wrap
            if len(lines) > 1:
                reduced_sz = max(7, int(sz_pt * NAME_FONT_REDUCTION_FACTOR))
                lines, new_sz = wrap_text_and_scale_reportlab(
                    rl_name, data["name"], reduced_sz, w_pt - (48 if data.get("logo") else 0) - 4, device)
            header_blocks_pdf.append(("name", lines, (rl_name, new_sz)))
        if data.get("type"):
            fam, sz_pt, bd, it = get_font("type")
            rl_name = get_reportlab_font_name(fam, bd, it)
            header_blocks_pdf.append(("type", [data["type"]], (rl_name, sz_pt)))


        price_blocks_pdf = []
        if data.get("price_bgn"):
            fam, sz_pt, bd, it = get_font("price")
            rl_name = get_reportlab_font_name(fam, bd, it)
            price_blocks_pdf.append(("price_bgn", [f"{data['price_bgn']} лв."], (rl_name, sz_pt)))
        if data.get("price_eur"):
            fam, sz_pt, bd, it = get_font("price")
            rl_name = get_reportlab_font_name(fam, bd, it)
            price_blocks_pdf.append(("price_eur", [f"€{data['price_eur']}"], (rl_name, sz_pt)))

        unit_font_pdf = get_font("type")
        unit_sz = 9
        unit_rl_name = get_reportlab_font_name(unit_font_pdf[0], False, True)
        unit_height = unit_sz * 1.2

        heights_pdf = []
        for i, (tag, lines, (fn, fs)) in enumerate(header_blocks_pdf):
            heights_pdf.append(fs * 1.3 * len(lines))
            if i < len(header_blocks_pdf) - 1:
                heights_pdf.append(GAP_HEADER)
        if header_blocks_pdf and price_blocks_pdf:
            heights_pdf.append(GAP_HEADER_PRICE)
        for i, (tag, lines, (fn, fs)) in enumerate(price_blocks_pdf):
            heights_pdf.append(fs * 1.3 * len(lines))
            if i < len(price_blocks_pdf) - 1:
                heights_pdf.append(GAP_PRICES)

        total_h_pdf = sum(h if isinstance(h, (int, float)) else 0 for h in heights_pdf)
        page_h = device._pagesize[1]
        y0 = page_h - mm_to_pt(mt + row * (lh + rg) + lh)
        available_height = h_pt - unit_height - PADDING_BOTTOM_UNIT - PADDING_TOP
        top_off = PADDING_TOP + (available_height - total_h_pdf) / 2

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
        # Header blocks
        for i, (tag, lines, (fn, fs)) in enumerate(header_blocks_pdf):
            device.setFont(fn, fs)
            for ln in lines:
                wtext = device.stringWidth(ln, fn, fs)
                xpos = tx if data.get("logo") else x + (w_pt - wtext) / 2
                device.drawString(xpos, cy, ln)
                cy -= fs * 1.3
            if i < len(header_blocks_pdf) - 1:
                cy -= GAP_HEADER
        if header_blocks_pdf and price_blocks_pdf:
            cy -= GAP_HEADER_PRICE
        for i, (tag, lines, (fn, fs)) in enumerate(price_blocks_pdf):
            device.setFont(fn, fs)
            for ln in lines:
                wtext = device.stringWidth(ln, fn, fs)
                xpos = tx if data.get("logo") else x + (w_pt - wtext) / 2
                device.drawString(xpos, cy, ln)
                cy -= fs * 1.3
            if i < len(price_blocks_pdf) - 1:
                cy -= GAP_PRICES

        if has_unit:
            device.setFont(unit_rl_name, unit_sz)
            unit_y = y0 + unit_height + PADDING_BOTTOM_UNIT
            unit_x = x + w_pt - device.stringWidth(unit_str, unit_rl_name, unit_sz) - mm_to_pt(2)
            device.drawString(unit_x, y0 + unit_height + PADDING_BOTTOM_UNIT, unit_str)
