# label_render.py

from PyQt5.QtGui import QFont, QFontMetrics, QPixmap
from PyQt5.QtCore import Qt
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.utils import ImageReader


def get_reportlab_font_name(base_name, bold, italic):
    """
    Return a ReportLab-registered font name, or fall back to Helvetica.
    Checks for Bold, Oblique, and BoldOblique variants.
    """
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


def wrap_text_and_scale(fm: QFontMetrics, text: str, max_width: float):
    """
    For QPainter: wrap `text` into up to two lines, shrinking font if needed.
    Returns (wrapped_text, QFont).
    """
    qf = fm.font()
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
    """
    For ReportLab: wrap `text` into up to two lines, shrinking font if needed.
    Returns (wrapped_text, final_font_size).
    """
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
    """
    Draws your labels grid on either:
      • QPainter (backend="qtpainter")
      • ReportLab Canvas (backend="reportlab")
    """
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
            settings.get(f"{tag}_font", "Helvetica"),
            settings.get(f"{tag}_size_pt", 11 if tag != "type" else 9),
            settings.get(f"{tag}_bold", tag != "type"),
            settings.get(f"{tag}_italic", tag == "type")
        )

    logo_pixmap = QPixmap(logo_path) if (logo_path and backend == "qtpainter") else None

    for idx, data in enumerate(labels):
        row, col = divmod(idx, cols)
        x = mm_to_pt(ml + col * (lw + cg))
        w_pt = mm_to_pt(lw)
        h_pt = mm_to_pt(lh)

        # ――― Build lines using unified "price" tag for both currencies ―――
        lines = []
        if data.get("name"):       lines.append(("name", data["name"]))
        if data.get("type"):       lines.append(("type", data["type"]))
        if data.get("price_bgn"):  lines.append(("price", f"{data['price_bgn']} лв."))
        if data.get("price_eur"):  lines.append(("price", f"€{data['price_eur']}"))

        max_text_w = w_pt - (48 if data.get("logo") else 0) - 4
        font_objs, line_texts, line_heights = [], [], []

        for i, (tag, txt) in enumerate(lines):
            fam, sz_pt, bd, it = get_font(tag)
            if backend == "qtpainter":
                qf = QFont(fam, sz_pt)
                qf.setBold(bd); qf.setItalic(it)
                fm = QFontMetrics(qf)
                if i == 0:
                    wrapped, qf2 = wrap_text_and_scale(fm, txt, max_text_w)
                    font_objs.append(qf2)
                    line_texts.append(wrapped)
                    line_heights.append(QFontMetrics(qf2).height() * (wrapped.count("\n") + 1))
                else:
                    font_objs.append(qf)
                    line_texts.append(txt)
                    line_heights.append(fm.height())
            else:
                rl_name = get_reportlab_font_name(fam, bd, it)
                if i == 0:
                    wrapped, new_sz = wrap_text_and_scale_reportlab(rl_name, txt, sz_pt, max_text_w, device)
                    font_objs.append((rl_name, new_sz))
                    line_texts.append(wrapped)
                    line_heights.append(new_sz * 1.3 * (wrapped.count("\n") + 1))
                else:
                    font_objs.append((rl_name, sz_pt))
                    line_texts.append(txt)
                    line_heights.append(sz_pt * 1.3)

        total_h = sum(line_heights)

        # ――― PDF branch ―――
        if backend == "reportlab":
            page_h = device._pagesize[1]
            y0 = page_h - mm_to_pt(mt + row * (lh + rg) + lh)
            top_off = (h_pt - total_h) / 2
            margin = mm_to_pt(2)

            if data.get("logo") and logo_path:
                img = ImageReader(logo_path)
                logo_sz = mm_to_pt(11)
                device.drawImage(img,
                                 x+3,
                                 y0 + (h_pt-logo_sz)/2,
                                 width=logo_sz, height=logo_sz,
                                 preserveAspectRatio=True)
                tx = x + 3 + logo_sz + 6
            else:
                tx = x + 2

            curr_y = y0 + h_pt - margin - top_off
            for (fname, fsz), block in zip(font_objs, line_texts):
                device.setFont(fname, fsz)
                for ln in block.split("\n"):
                    w_txt = device.stringWidth(ln, fname, fsz)
                    xpos = tx if data.get("logo") else x + (w_pt - w_txt)/2
                    device.drawString(xpos, curr_y, ln)
                    curr_y -= (fsz * 1.3)
            continue  # skip QPainter

        # ――― QPainter branch ―――
        start_y = mm_to_pt(mt + row*(lh+rg)) + (h_pt - total_h)/2
        if data.get("logo") and logo_pixmap:
            logo_sz = mm_to_pt(11)
            logo_x = x + 3
            logo_y = start_y + (total_h - logo_sz)/2
            device.drawPixmap(int(logo_x), int(logo_y),
                              int(logo_sz), int(logo_sz),
                              logo_pixmap)
            tx = logo_x + logo_sz + 6
        else:
            tx = x + 2

        cy = start_y
        for qf, block in zip(font_objs, line_texts):
            device.setFont(qf)
            fm = QFontMetrics(qf)
            for ln in block.split("\n"):
                w_txt = fm.width(ln)
                xpos = tx if data.get("logo") else x + (w_pt - w_txt)/2
                device.drawText(int(xpos), int(cy + fm.ascent()), ln)
                cy += fm.height()
