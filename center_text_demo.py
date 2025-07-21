from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPainter, QColor, QFont
from PyQt5.QtCore import Qt
import sys

class CenterTextDemo(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Centered Text Block Demo")
        self.setGeometry(100, 100, 500, 400)

    def paintEvent(self, event):
        qp = QPainter(self)
        box_x, box_y, box_w, box_h = 70, 70, 360, 220

        # Draw box
        qp.setPen(QColor("#888"))
        qp.setBrush(QColor("#ffe"))
        qp.drawRect(box_x, box_y, box_w, box_h)

        # The "fields" we want to center as a block (simulate label fields)
        lines = [
            {"text": "Big Bold Product Name", "font": ("Arial", 18, True, False), "align": Qt.AlignCenter},
            {"text": "Smaller description wraps to next line if needed", "font": ("Arial", 12, False, False), "align": Qt.AlignCenter},
            {"text": "BGN: 123.45 лв.", "font": ("Arial", 16, True, False), "align": Qt.AlignRight},
            {"text": "€62.99", "font": ("Arial", 23, True, False), "align": Qt.AlignLeft},
        ]
        max_width = box_w - 20  # leave some padding inside box

        # Step 1: Word-wrap and measure every line as it will be drawn
        display_lines = []
        for line in lines:
            font = QFont(line["font"][0], line["font"][1])
            font.setBold(line["font"][2])
            font.setItalic(line["font"][3])
            qp.setFont(font)
            fm = qp.fontMetrics()
            # Basic word wrap: split at spaces to fit line
            words = line["text"].split()
            current = ""
            for word in words:
                test = (current + " " + word).strip()
                if fm.width(test) > max_width and current:
                    display_lines.append({
                        "text": current,
                        "font": font,
                        "metrics": fm,
                        "align": line["align"]
                    })
                    current = word
                else:
                    current = test
            if current:
                display_lines.append({
                    "text": current,
                    "font": font,
                    "metrics": fm,
                    "align": line["align"]
                })

        # Step 2: Compute block height
        total_height = sum(l["metrics"].height() for l in display_lines)
        block_top = box_y + (box_h - total_height) // 2

        # Step 3: Draw each line with correct alignment
        y = block_top
        for l in display_lines:
            qp.setFont(l["font"])
            text_width = l["metrics"].width(l["text"])
            # Horizontal alignment
            if l["align"] == Qt.AlignRight:
                x = box_x + box_w - 10 - text_width
            elif l["align"] == Qt.AlignLeft:
                x = box_x + 10
            else:  # Center
                x = box_x + (box_w - text_width) // 2
            # Draw baseline at y + ascent
            qp.setPen(QColor("#111"))
            qp.drawText(x, y + l["metrics"].ascent(), l["text"])
            y += l["metrics"].height()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = CenterTextDemo()
    w.show()
    sys.exit(app.exec_())
