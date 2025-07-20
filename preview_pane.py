from PyQt5.QtWidgets import QWidget, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal, QRect
from PyQt5.QtGui import QColor, QPainter, QPen, QFont

PREVIEW_LABEL_SCALE = 3.0  # <-- Adjust this to make preview bigger/smaller
PREVIEW_LABEL_GAP = 5     # gap in px

class PreviewPaneWidget(QWidget):
    label_clicked = pyqtSignal(int, object)
    label_right_clicked = pyqtSignal(int, object)

    def __init__(self, labels, rows, cols, label_w_mm, label_h_mm, spacing_px=12, parent=None):
        super().__init__(parent)
        self.labels = labels
        self.rows = rows
        self.cols = cols
        self.label_w_mm = label_w_mm
        self.label_h_mm = label_h_mm
        self.gap = PREVIEW_LABEL_GAP
        self.selected = []
        self.setMinimumSize(600, 400)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)

    def update_labels(self, labels):
        self.labels = labels
        self.update()

    def set_selected(self, selected):
        self.selected = selected
        self.update()

    def update_calibration(self, rows, cols, label_w_mm, label_h_mm):
        self.rows = rows
        self.cols = cols
        self.label_w_mm = label_w_mm
        self.label_h_mm = label_h_mm
        self.update()

    def paintEvent(self, event):
        qp = QPainter(self)
        qp.setRenderHint(QPainter.Antialiasing)
        # Label size in px (using calibration × scale)
        label_w_px = int(self.label_w_mm * PREVIEW_LABEL_SCALE)
        label_h_px = int(self.label_h_mm * PREVIEW_LABEL_SCALE)
        gap_px = self.gap
        total_w = self.cols * label_w_px + (self.cols - 1) * gap_px
        total_h = self.rows * label_h_px + (self.rows - 1) * gap_px
        avail_w = self.width()
        avail_h = self.height()
        # Center the grid
        left = (avail_w - total_w) // 2 if avail_w > total_w else 0
        top = (avail_h - total_h) // 2 if avail_h > total_h else 0

        idx = 0
        for row in range(self.rows):
            for col in range(self.cols):
                if idx >= len(self.labels):
                    break
                x = left + col * (label_w_px + gap_px)
                y = top + row * (label_h_px + gap_px)
                self.draw_preview_label(qp, x, y, label_w_px, label_h_px, self.labels[idx], idx in self.selected)
                idx += 1

    def draw_preview_label(self, qp, x, y, w, h, label, is_selected):
        r = 16
        pen = QPen(QColor(70, 130, 255) if is_selected else QColor("#CCCCCC"), 2 if is_selected else 1)
        qp.setPen(pen)
        qp.setBrush(QColor("#FFFFFF"))
        qp.drawRoundedRect(x, y, w, h, r, r)
        margin = int(w * 0.08)
        x0, y0 = x + margin, y + margin
        ww, hh = w - 2 * margin, h - 2 * margin
        lines = []
        for key in ["main", "second", "bgn", "eur"]:
            fld = label[key]
            t = fld["text"]
            if key == "bgn":
                t = t.replace(" лв.", "").replace("лв.", "").strip()
                if t:
                    t += " лв."
            if key == "eur":
                t = t.replace("€", "").strip()
                if t:
                    t = "€" + t
            if t:
                lines.append((t, fld))
        total_h, metrics = 0, []
        for text, field in lines:
            fnt = QFont(field['font'], int(field['size']))
            fnt.setBold(field['bold'])
            fnt.setItalic(field['italic'])
            qp.setFont(fnt)
            fm = qp.fontMetrics()
            rect_t = fm.boundingRect(0, 0, ww, hh, field['align'] | Qt.TextWordWrap, text)
            metrics.append((rect_t.height(), field, text, fnt))
            total_h += rect_t.height()
        cy = y0 + (hh - total_h) // 2
        for hgt, field, text, fnt in metrics:
            qp.setFont(fnt)
            qp.setPen(QColor(field.get("font_color", "#222")))
            rect_t = qp.fontMetrics().boundingRect(0, 0, ww, hgt, field['align'] | Qt.TextWordWrap, text)
            draw_rect = rect_t.translated(x0, cy)
            qp.drawText(draw_rect, field['align'] | Qt.TextWordWrap, text)
            cy += hgt

    def mousePressEvent(self, event):
        if event.button() not in (Qt.LeftButton, Qt.RightButton):
            return
        label_w_px = int(self.label_w_mm * PREVIEW_LABEL_SCALE)
        label_h_px = int(self.label_h_mm * PREVIEW_LABEL_SCALE)
        gap_px = self.gap
        total_w = self.cols * label_w_px + (self.cols - 1) * gap_px
        total_h = self.rows * label_h_px + (self.rows - 1) * gap_px
        avail_w = self.width()
        avail_h = self.height()
        left = (avail_w - total_w) // 2 if avail_w > total_w else 0
        top = (avail_h - total_h) // 2 if avail_h > total_h else 0

        idx = 0
        for row in range(self.rows):
            for col in range(self.cols):
                if idx >= len(self.labels):
                    break
                x = left + col * (label_w_px + gap_px)
                y = top + row * (label_h_px + gap_px)
                rect = QRect(x, y, label_w_px, label_h_px)
                if rect.contains(event.pos()):
                    if event.button() == Qt.LeftButton:
                        self.label_clicked.emit(idx, event)
                    elif event.button() == Qt.RightButton:
                        self.label_right_clicked.emit(idx, event)
                    break
                idx += 1
