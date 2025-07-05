import sys
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QSpinBox, QPushButton,
    QFileDialog, QGraphicsView, QGraphicsScene
)
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPen, QColor, QPainterPath, QBrush, QFont, QPainter
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog

class SheetPreview(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setBackgroundBrush(QColor("#eaeaea"))
        self.a4_w_mm, self.a4_h_mm = 210, 297

        self.setRenderHint(QPainter.Antialiasing)
        self.sheet_settings = {}

    def update_preview(self, sheet_settings):
        self.scene.clear()
        self.sheet_settings = sheet_settings
        a4_w, a4_h = self.a4_w_mm, self.a4_h_mm

        # Calculate scale to fit view
        margin = 20
        w = self.viewport().width() - 2*margin
        h = self.viewport().height() - 2*margin
        scale = min(w / a4_w, h / a4_h)
        offset_x = (self.viewport().width() - a4_w * scale) / 2
        offset_y = (self.viewport().height() - a4_h * scale) / 2

        # Draw A4 page
        paper = self.scene.addRect(offset_x, offset_y, a4_w*scale, a4_h*scale,
                                   QPen(Qt.black), QBrush(Qt.white))
        paper.setZValue(-1)

        # Extract settings
        label_w = sheet_settings.get("label_width_mm", 63.5)
        label_h = sheet_settings.get("label_height_mm", 38.1)
        margin_top = sheet_settings.get("margin_top_mm", 10)
        margin_left = sheet_settings.get("margin_left_mm", 10)
        row_gap = sheet_settings.get("row_gap_mm", 0)
        col_gap = sheet_settings.get("col_gap_mm", 2.5)
        rows = sheet_settings.get("rows", 7)
        cols = sheet_settings.get("cols", 3)

        # Draw labels
        pen = QPen(QColor("#1c80e9"))
        pen.setWidth(1)
        for r in range(rows):
            for c in range(cols):
                x = offset_x + (margin_left + c * (label_w + col_gap)) * scale
                y = offset_y + (margin_top + r * (label_h + row_gap)) * scale
                rect = QRectF(x, y, label_w * scale, label_h * scale)
                path = QPainterPath()
                path.addRoundedRect(rect, 8, 8)
                item = self.scene.addPath(path, pen)
                item.setZValue(1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.sheet_settings:
            self.update_preview(self.sheet_settings)

    def print_preview(self):
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPrinter.A4)
        dialog = QPrintDialog(printer, self)
        if dialog.exec_() != QPrintDialog.Accepted:
            return
        painter = QPainter(printer)

        # Get page rect in points
        page_rect = printer.pageRect()
        page_w_pt, page_h_pt = page_rect.width(), page_rect.height()
        a4_w_mm, a4_h_mm = self.a4_w_mm, self.a4_h_mm

        # MM to points
        mm_to_pt = lambda mm: mm * 72 / 25.4
        a4_w_pt = mm_to_pt(a4_w_mm)
        a4_h_pt = mm_to_pt(a4_h_mm)

        # Calculate scale to fill the printer's page
        scale_x = page_w_pt / a4_w_pt
        scale_y = page_h_pt / a4_h_pt
        scale = min(scale_x, scale_y)

        # Center the drawing
        offset_x = (page_w_pt - a4_w_pt * scale) / 2
        offset_y = (page_h_pt - a4_h_pt * scale) / 2

        painter.translate(offset_x, offset_y)
        painter.scale(scale, scale)

        # Draw label rectangles (now scaled for print)
        label_w = self.sheet_settings.get("label_width_mm", 63.5)
        label_h = self.sheet_settings.get("label_height_mm", 38.1)
        margin_top = self.sheet_settings.get("margin_top_mm", 10)
        margin_left = self.sheet_settings.get("margin_left_mm", 10)
        row_gap = self.sheet_settings.get("row_gap_mm", 0)
        col_gap = self.sheet_settings.get("col_gap_mm", 2.5)
        rows = self.sheet_settings.get("rows", 7)
        cols = self.sheet_settings.get("cols", 3)

        pen = QPen(Qt.black)
        pen.setWidth(1)
        painter.setPen(pen)

        for r in range(rows):
            for c in range(cols):
                x = mm_to_pt(margin_left + c * (label_w + col_gap))
                y = mm_to_pt(margin_top + r * (label_h + row_gap))
                w = mm_to_pt(label_w)
                h = mm_to_pt(label_h)
                path = QPainterPath()
                path.addRoundedRect(x, y, w, h, 8, 8)
                painter.drawPath(path)
        painter.end()

class SheetEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sheet Setup Editor (Prototype)")
        self.setMinimumSize(900, 700)
        main = QVBoxLayout(self)
        layout = QHBoxLayout()
        main.addLayout(layout)

        # Left: controls
        left = QVBoxLayout()
        layout.addLayout(left, 0)

        fontb = QFont("Arial", 10, QFont.Bold)
        # Label size
        left.addWidget(QLabel("<b>Label size</b>"))
        hl = QHBoxLayout()
        hl.addWidget(QLabel("Width:"))
        self.in_w = QLineEdit("63.5")
        hl.addWidget(self.in_w)
        hl.addWidget(QLabel("mm"))
        left.addLayout(hl)
        hl = QHBoxLayout()
        hl.addWidget(QLabel("Height:"))
        self.in_h = QLineEdit("38.1")
        hl.addWidget(self.in_h)
        hl.addWidget(QLabel("mm"))
        left.addLayout(hl)

        # Margins
        left.addSpacing(14)
        left.addWidget(QLabel("<b>Margins</b>"))
        hl = QHBoxLayout()
        hl.addWidget(QLabel("Top:"))
        self.in_mt = QLineEdit("10")
        hl.addWidget(self.in_mt)
        hl.addWidget(QLabel("mm"))
        left.addLayout(hl)
        hl = QHBoxLayout()
        hl.addWidget(QLabel("Left:"))
        self.in_ml = QLineEdit("10")
        hl.addWidget(self.in_ml)
        hl.addWidget(QLabel("mm"))
        left.addLayout(hl)
        hl = QHBoxLayout()
        hl.addWidget(QLabel("Row gap:"))
        self.in_rg = QLineEdit("0")
        hl.addWidget(self.in_rg)
        hl.addWidget(QLabel("mm"))
        left.addLayout(hl)
        hl = QHBoxLayout()
        hl.addWidget(QLabel("Col gap:"))
        self.in_cg = QLineEdit("2.5")
        hl.addWidget(self.in_cg)
        hl.addWidget(QLabel("mm"))
        left.addLayout(hl)

        # Rows and Columns
        left.addSpacing(14)
        left.addWidget(QLabel("<b>Rows & Columns</b>"))
        hl = QHBoxLayout()
        hl.addWidget(QLabel("Rows:"))
        self.in_rows = QSpinBox()
        self.in_rows.setRange(1, 99)
        self.in_rows.setValue(7)
        hl.addWidget(self.in_rows)
        left.addLayout(hl)
        hl = QHBoxLayout()
        hl.addWidget(QLabel("Cols:"))
        self.in_cols = QSpinBox()
        self.in_cols.setRange(1, 99)
        self.in_cols.setValue(3)
        hl.addWidget(self.in_cols)
        left.addLayout(hl)

        left.addSpacing(18)
        # Save/Load/Print buttons
        self.save_btn = QPushButton("Save Sheet Setup")
        self.load_btn = QPushButton("Load Sheet Setup")
        self.print_btn = QPushButton("Print Grid")
        left.addWidget(self.save_btn)
        left.addWidget(self.load_btn)
        left.addWidget(self.print_btn)
        left.addStretch(1)

        # Right: preview
        self.preview = SheetPreview()
        layout.addWidget(self.preview, 1)

        # Connections
        for widget in [
            self.in_w, self.in_h, self.in_mt, self.in_ml, self.in_rg, self.in_cg,
            self.in_rows, self.in_cols
        ]:
            if isinstance(widget, QLineEdit):
                widget.textChanged.connect(self.refresh)
            else:
                widget.valueChanged.connect(self.refresh)
        self.save_btn.clicked.connect(self.save_setup)
        self.load_btn.clicked.connect(self.load_setup)
        self.print_btn.clicked.connect(self.preview.print_preview)

        self.refresh()

    def get_settings(self):
        # Parse all fields safely
        def parse(val, fallback):
            try:
                return float(val)
            except Exception:
                return fallback
        return {
            "label_width_mm": parse(self.in_w.text(), 63.5),
            "label_height_mm": parse(self.in_h.text(), 38.1),
            "margin_top_mm": parse(self.in_mt.text(), 10),
            "margin_left_mm": parse(self.in_ml.text(), 10),
            "row_gap_mm": parse(self.in_rg.text(), 0),
            "col_gap_mm": parse(self.in_cg.text(), 2.5),
            "rows": int(self.in_rows.value()),
            "cols": int(self.in_cols.value()),
        }

    def refresh(self):
        self.preview.update_preview(self.get_settings())

    def save_setup(self):
        settings = self.get_settings()
        fn, _ = QFileDialog.getSaveFileName(self, "Save Sheet Setup", "", "JSON Files (*.json)")
        if fn:
            with open(fn, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)

    def load_setup(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Load Sheet Setup", "", "JSON Files (*.json)")
        if fn:
            with open(fn, "r", encoding="utf-8") as f:
                settings = json.load(f)
            self.in_w.setText(str(settings.get("label_width_mm", 63.5)))
            self.in_h.setText(str(settings.get("label_height_mm", 38.1)))
            self.in_mt.setText(str(settings.get("margin_top_mm", 10)))
            self.in_ml.setText(str(settings.get("margin_left_mm", 10)))
            self.in_rg.setText(str(settings.get("row_gap_mm", 0)))
            self.in_cg.setText(str(settings.get("col_gap_mm", 2.5)))
            self.in_rows.setValue(int(settings.get("rows", 7)))
            self.in_cols.setValue(int(settings.get("cols", 3)))
            self.refresh()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = SheetEditor()
    win.show()
    sys.exit(app.exec_())
