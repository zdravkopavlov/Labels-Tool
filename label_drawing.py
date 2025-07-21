# label_drawing.py
from PyQt5.QtGui import QFont, QColor, QTextDocument, QTextCursor, QTextBlockFormat, QTextCharFormat
from PyQt5.QtCore import Qt, QRectF

def build_label_document(label_dict, width_px, font_scale=1.0):
    doc = QTextDocument()
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

def draw_label_preview(painter, x, y, w, h, label_dict, scale=1.0):
    painter.save()
    radius = int(12 * scale)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor("#fff"))
    painter.drawRoundedRect(x, y, w, h, radius, radius)
    painter.setPen(QColor("#cccccc"))
    painter.setBrush(Qt.NoBrush)
    painter.drawRoundedRect(x, y, w, h, radius, radius)
    margin = int(6 * scale)
    doc_width = w - 2 * margin
    doc = build_label_document(label_dict, doc_width, font_scale=1.0)
    block_height = doc.size().height()
    top = y + (h - block_height) / 2
    painter.translate(x + margin, top)
    doc.drawContents(painter, QRectF(0, 0, doc_width, block_height))
    painter.restore()

def draw_label_print(painter, x, y, w, h, label_dict, font_scale=1.0, scale=1.0):
    print("CALLED: draw_label_print, font_scale =", font_scale)  # Debug print!
    painter.save()
    radius = int(12 * scale)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor("#fff"))
    painter.drawRoundedRect(x, y, w, h, radius, radius)
    painter.setPen(QColor("#cccccc"))
    painter.setBrush(Qt.NoBrush)
    painter.drawRoundedRect(x, y, w, h, radius, radius)
    margin = int(6 * scale)
    doc_width = w - 2 * margin
    doc = build_label_document(label_dict, doc_width, font_scale=font_scale)
    block_height = doc.size().height()
    top = y + (h - block_height) / 2
    painter.translate(x + margin, top)
    doc.drawContents(painter, QRectF(0, 0, doc_width, block_height))
    painter.restore()
