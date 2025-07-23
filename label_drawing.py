# label_drawing.py
from PyQt5.QtGui import QFont, QColor, QTextDocument, QTextCursor, QTextBlockFormat, QTextCharFormat
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtSvg import QSvgRenderer
import os

def build_label_document(label_dict, width_px, font_scale=1.0):
    doc = QTextDocument()
    doc.setDocumentMargin(0)  # REMOVE default margins for truer centering
    cursor = QTextCursor(doc)

    for key in ["main", "second", "bgn", "eur"]:
        field = label_dict.get(key, {})
        text = field.get("text", "")
        if not text.strip():
            continue

        if key == "bgn" and text and "лв" not in text:
            text = text + " лв."
        if key == "eur" and text and "€" not in text:
            text = "€" + text

        block_fmt = QTextBlockFormat()
        align = field.get("align", Qt.AlignCenter)
        if align == Qt.AlignLeft:
            block_fmt.setAlignment(Qt.AlignLeft)
        elif align == Qt.AlignRight:
            block_fmt.setAlignment(Qt.AlignRight)
        else:
            block_fmt.setAlignment(Qt.AlignCenter)
        block_fmt.setLineHeight(120, QTextBlockFormat.ProportionalHeight)

        char_fmt = QTextCharFormat()
        font_family = field.get("font", "Arial")
        base_size = field.get("size", 15)
        font_size = max(1, int(base_size * font_scale))
        font_weight = QFont.Bold if field.get("bold", False) else QFont.Normal
        font_italic = field.get("italic", False)
        font_color = QColor(field.get("font_color", "#222"))
        bg_color = QColor(field.get("bg_color", "#fff"))

        font = QFont(font_family, pointSize=font_size)
        font.setBold(field.get("bold", False))
        font.setItalic(font_italic)
        char_fmt.setFont(font)
        char_fmt.setForeground(font_color)
        char_fmt.setBackground(bg_color)

        cursor.insertBlock(block_fmt)
        cursor.insertText(text, char_fmt)

    doc.setTextWidth(width_px)
    return doc

def draw_logo(painter, x, y, w, h, logo_settings, scale=1.0):
    if not logo_settings or logo_settings.get("position", "без лого") == "без лого":
        return
    svg_path = os.path.join(os.path.dirname(__file__), "resources", "logo.svg")
    if not os.path.exists(svg_path):
        return
    renderer = QSvgRenderer(svg_path)
    size = logo_settings.get("size", 24) * scale
    opacity = logo_settings.get("opacity", 1.0)
    margin = 6 * scale

    if logo_settings.get("position") == "долу ляво":
        pos_x = x + margin
    else:
        pos_x = x + w - size - margin
    pos_y = y + h - size - margin

    painter.save()
    painter.setOpacity(opacity)
    renderer.render(painter, QRectF(pos_x, pos_y, size, size))
    painter.setOpacity(1.0)
    painter.restore()

def draw_label_print(painter, x, y, w, h, label_dict, font_scale=1.0, scale=1.0, corner_radius=2.5, margin=10):
    painter.save()
    radius = corner_radius
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor("#fff"))
    painter.drawRoundedRect(x, y, w, h, radius, radius)
    painter.setPen(QColor("#cccccc"))
    painter.setBrush(Qt.NoBrush)
    painter.drawRoundedRect(x, y, w, h, radius, radius)

    logo_settings = label_dict.get("logo", None)
    draw_logo(painter, x, y, w, h, logo_settings, scale=font_scale)

    margin_px = int(margin * scale)
    doc_width = w - 2 * margin_px
    doc = build_label_document(label_dict, doc_width, font_scale=font_scale)
    block_height = doc.size().height()
    top = y + (h - block_height) / 2
    painter.translate(x + margin_px, top)
    doc.drawContents(painter, QRectF(0, 0, doc_width, block_height))
    painter.restore()


def draw_label_preview(painter, x, y, w, h, label_dict, scale=1.0, corner_radius=2.5, selection_highlight=False):
    painter.save()
    radius = corner_radius
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor("#fff"))
    painter.drawRoundedRect(x, y, w, h, radius, radius)
    painter.setPen(QColor("#cccccc"))
    painter.setBrush(Qt.NoBrush)
    painter.drawRoundedRect(x, y, w, h, radius, radius)

    logo_settings = label_dict.get("logo", None)
    draw_logo(painter, x, y, w, h, logo_settings)

    margin = int(6 * scale)
    doc_width = w - 2 * margin
    doc = build_label_document(label_dict, doc_width, font_scale=1.0)
    block_height = doc.size().height()
    # --- Manually nudge up for visual centering (screen preview only)
    top = y + (h - block_height) / 2 - (1.5 * scale)   # Adjust this value as needed!
    painter.translate(x + margin, top)
    doc.drawContents(painter, QRectF(0, 0, doc_width, block_height))
    painter.restore()

