from PyQt5.QtWidgets import QWidget, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal, QRect
from PyQt5.QtGui import QColor, QPainter, QPen
import os
import json

# Import the label preview drawing function
from label_drawing import draw_label_preview

PREVIEW_LABEL_SCALE = 3.2  # Preview scale for UI
PREVIEW_LABEL_GAP = 5      # gap in px

def load_current_corner_radius():
    # Reads corner_radius from sheet_settings.json each time (no restart needed)
    try:
        appdata_path = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "LabelTool")
        sheet_settings_path = os.path.join(appdata_path, "sheet_settings.json")
        with open(sheet_settings_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        params = data.get("params", {})
        return float(params.get("corner_radius", 2.5))
    except Exception:
        return 2.5

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
        self.hovered_index = None  # <-- For hover effect

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

        # Get the latest radius from settings
        corner_radius = load_current_corner_radius()

        idx = 0
        for row in range(self.rows):
            for col in range(self.cols):
                if idx >= len(self.labels):
                    break
                x = left + col * (label_w_px + gap_px)
                y = top + row * (label_h_px + gap_px)
                # Draw selection highlight border
                if idx in self.selected:
                    qp.save()
                    qp.setPen(QPen(QColor(70, 130, 255), 3))
                    qp.setBrush(Qt.NoBrush)
                    qp.drawRoundedRect(x, y, label_w_px, label_h_px,
                                      corner_radius, corner_radius)
                    qp.restore()
                # Draw hover effect (AFTER selection so it's visible)
                if idx == self.hovered_index:
                    qp.save()
                    qp.setPen(QPen(QColor(130, 200, 255, 180), 4, Qt.DashLine))
                    qp.setBrush(Qt.NoBrush)
                    qp.drawRoundedRect(x, y, label_w_px, label_h_px,
                                      corner_radius, corner_radius)
                    qp.restore()
                # Draw the label itself
                draw_label_preview(qp, x, y, label_w_px, label_h_px, self.labels[idx],
                                  scale=PREVIEW_LABEL_SCALE, corner_radius=corner_radius)
                idx += 1

    def mouseMoveEvent(self, event):
        label_w_px = int(self.label_w_mm * PREVIEW_LABEL_SCALE)
        label_h_px = int(self.label_h_mm * PREVIEW_LABEL_SCALE)
        gap_px = self.gap
        total_w = self.cols * label_w_px + (self.cols - 1) * gap_px
        total_h = self.rows * label_h_px + (self.rows - 1) * gap_px
        avail_w = self.width()
        avail_h = self.height()
        left = (avail_w - total_w) // 2 if avail_w > total_w else 0
        top = (avail_h - total_h) // 2 if avail_h > total_h else 0

        old_hover = self.hovered_index
        idx = 0
        found = False
        for row in range(self.rows):
            for col in range(self.cols):
                if idx >= len(self.labels):
                    break
                x = left + col * (label_w_px + gap_px)
                y = top + row * (label_h_px + gap_px)
                rect = QRect(x, y, label_w_px, label_h_px)
                if rect.contains(event.pos()):
                    self.hovered_index = idx
                    found = True
                    break
                idx += 1
            if found:
                break
        else:
            self.hovered_index = None
        if self.hovered_index != old_hover:
            self.update()

    def leaveEvent(self, event):
        if self.hovered_index is not None:
            self.hovered_index = None
            self.update()

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
