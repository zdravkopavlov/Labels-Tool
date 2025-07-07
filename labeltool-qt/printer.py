# printer.py

import os
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtGui import QPainter, QFont, QFontMetrics
from PyQt5.QtCore import Qt, QRectF

def mm_to_pt(mm: float) -> float:
    """Convert millimeters to printer points."""
    return mm * 72 / 25.4

def draw_labels(painter: QPainter, sheet_settings: dict, labels: list):
    """
    Draw all LabelWidget instances onto the QPainter using the given
    sheet_settings and list of labels.
    """
    ls = sheet_settings

    # 1) Scale to A4
    pr = painter.device()
    page_rect = pr.pageRect()
    scale = min(page_rect.width() / mm_to_pt(210),
                page_rect.height() / mm_to_pt(297))
    offset_x = (page_rect.width() - mm_to_pt(210) * scale) / 2
    offset_y = (page_rect.height() - mm_to_pt(297) * scale) / 2
    painter.translate(offset_x, offset_y)
    painter.scale(scale, scale)

    idx = 0
    for r in range(ls["rows"]):
        for c in range(ls["cols"]):
            # cell origin and size (in points)
            x = mm_to_pt(ls["margin_left_mm"] + c * (ls["label_width_mm"] + ls["col_gap_mm"]))
            y = mm_to_pt(ls["margin_top_mm"]  + r * (ls["label_height_mm"] + ls["row_gap_mm"]))
            w = mm_to_pt(ls["label_width_mm"])
            h = mm_to_pt(ls["label_height_mm"])

            if idx < len(labels):
                data = labels[idx].get_export_data()
                # collect non-empty lines
                lines = []
                if data["name"]:     lines.append(data["name"])
                if data["type"]:     lines.append(data["type"])
                if data["price_bgn"]:lines.append(f"{data['price_bgn']} лв.")
                if data["price_eur"]:lines.append(f"€{data['price_eur']}")
                if data["unit_eur"]: lines.append(f"/ {data['unit_eur']}")

                # divide cell height evenly
                count = max(1, len(lines))
                region_h = h / count

                for i, text in enumerate(lines):
                    # choose font size = 80% of region height
                    size_pt = int(region_h * 0.8)
                    size_pt = max(4, min(size_pt, 8))  # clamp 4–8 pt

                    if i == 0 and data["name"]:
                        font = QFont("Helvetica", size_pt, QFont.Bold)
                    elif i == 1 and data["type"]:
                        font = QFont("Helvetica", size_pt)
                        font.setItalic(True)
                    else:
                        font = QFont("Helvetica", size_pt)

                    painter.setFont(font)
                    # draw in the sub-rectangle for this line
                    rect = QRectF(x, y + i * region_h, w, region_h)
                    painter.drawText(rect, Qt.AlignCenter, text)
            idx += 1

def export_to_pdf(path: str, sheet_settings: dict, labels: list):
    """
    Export labels to a PDF at the given path.
    """
    printer = QPrinter(QPrinter.HighResolution)
    printer.setOutputFileName(path)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setPageSize(printer.A4)

    painter = QPainter(printer)
    draw_labels(painter, sheet_settings, labels)
    painter.end()

def print_to_printer(parent_widget, sheet_settings: dict, labels: list):
    """
    Show a print dialog and print labels if accepted.
    """
    printer = QPrinter(QPrinter.HighResolution)
    printer.setPageSize(printer.A4)
    dialog = QPrintDialog(printer, parent_widget)
    if dialog.exec_() != QPrintDialog.Accepted:
        return

    painter = QPainter(printer)
    draw_labels(painter, sheet_settings, labels)
    painter.end()
