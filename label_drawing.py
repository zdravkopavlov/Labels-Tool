# label_drawing.py

from PyQt5.QtGui import QFont, QColor, QTextCharFormat, QTextCursor, QTextDocument
from PyQt5.QtCore import Qt, QRectF

def html_escape(text):
    import html
    return html.escape(text or "")

def build_label_html(label_dict):
    """Build HTML for a label with per-line formatting."""
    lines = []
    for key in ["main", "second", "bgn", "eur"]:
        field = label_dict.get(key, {})
        text = html_escape(field.get("text", ""))
        if not text.strip():
            continue
        font = field.get("font", "Arial")
        size = field.get("size", 15)
        bold = "font-weight:bold;" if field.get("bold") else ""
        italic = "font-style:italic;" if field.get("italic") else ""
        color = f"color:{field.get('font_color', '#222')};"
        bg_color = f"background-color:{field.get('bg_color', 'transparent')};"
        align = field.get("align", Qt.AlignCenter)
        align_str = "center"
        if align == Qt.AlignLeft:
            align_str = "left"
        elif align == Qt.AlignRight:
            align_str = "right"
        # Add units to price lines if needed
        if key == "bgn" and "лв" not in text:
            text = text + " лв."
        if key == "eur" and "€" not in text:
            text = "€" + text
        style = f"font-family:'{font}'; font-size:{size}pt; {bold}{italic}{color}{bg_color} text-align:{align_str};"
        html_line = f"<div style='{style}'>{text}</div>"
        lines.append(html_line)
    html_full = "<div>" + "\n".join(lines) + "</div>"
    return html_full

def draw_label_preview(painter, x, y, w, h, label_dict, scale=1.0):
    """Draw the label as preview using QTextDocument for accurate layout."""
    painter.save()
    # Draw rounded white background
    radius = int(12 * scale)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor("#fff"))
    painter.drawRoundedRect(x, y, w, h, radius, radius)
    # Draw border
    painter.setPen(QColor("#cccccc"))
    painter.setBrush(Qt.NoBrush)
    painter.drawRoundedRect(x, y, w, h, radius, radius)
    # Prepare text
    doc = QTextDocument()
    html = build_label_html(label_dict)
    doc.setHtml(html)
    doc.setTextWidth(w - int(8 * scale))  # Small margin
    # Vertically center
    height = doc.size().height()
    top = y + (h - height) / 2
    painter.translate(x + int(4 * scale), top)
    doc.drawContents(painter, QRectF(0, 0, w - int(8 * scale), height))
    painter.restore()

def draw_label_print(painter, x, y, w, h, label_dict, scale=1.0):
    """Draw the label for printing/export. Same as preview, but allows future print tweaks."""
    draw_label_preview(painter, x, y, w, h, label_dict, scale)

