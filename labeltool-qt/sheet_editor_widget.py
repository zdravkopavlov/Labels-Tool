# sheet_editor_widget.py

import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
    QSpinBox, QCheckBox, QPushButton, QFileDialog, QGraphicsView,
    QGraphicsScene, QComboBox, QMessageBox
)
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPen, QColor, QPainterPath, QBrush, QFont, QPainter
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog

# ── Config & Fonts Setup ────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
os.makedirs(CONFIG_DIR, exist_ok=True)
SETTINGS_PATH = os.path.join(CONFIG_DIR, "settings.json")

FONTS_DIR = os.path.join(BASE_DIR, "fonts")
os.makedirs(FONTS_DIR, exist_ok=True)
_font_files = [f for f in os.listdir(FONTS_DIR) if f.lower().endswith('.ttf')]
FONTS_LIST  = [os.path.splitext(f)[0] for f in _font_files]


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
        s = sheet_settings
        label_w     = s.get("label_width_mm", 63.5)
        label_h     = s.get("label_height_mm", 38.1)
        margin_top  = s.get("margin_top_mm", 10)
        margin_left = s.get("margin_left_mm", 10)
        row_gap     = s.get("row_gap_mm", 0)
        col_gap     = s.get("col_gap_mm", 2.5)
        rows        = s.get("rows", 7)
        cols        = s.get("cols", 3)

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


class SheetEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sheet Setup Editor")
        self.setMinimumSize(900, 700)

        main = QVBoxLayout(self)
        layout = QHBoxLayout()
        main.addLayout(layout)

        # ── Left: controls ─────────────────────────────────────────────
        left = QVBoxLayout()
        layout.addLayout(left, 0)

        # Label size
        left.addWidget(QLabel("<b>Label size</b>"))
        for label_text, attr in [("Width:", "in_w"), ("Height:", "in_h")]:
            hl = QHBoxLayout()
            hl.addWidget(QLabel(label_text))
            setattr(self, attr, QLineEdit())
            hl.addWidget(getattr(self, attr))
            hl.addWidget(QLabel("mm"))
            left.addLayout(hl)

        # Margins
        left.addSpacing(14)
        left.addWidget(QLabel("<b>Margins</b>"))
        for label_text, attr in [
            ("Top:", "in_mt"), ("Left:", "in_ml"),
            ("Row gap:", "in_rg"), ("Col gap:", "in_cg")
        ]:
            hl = QHBoxLayout()
            hl.addWidget(QLabel(label_text))
            setattr(self, attr, QLineEdit())
            hl.addWidget(getattr(self, attr))
            hl.addWidget(QLabel("mm"))
            left.addLayout(hl)

        # Rows & Columns
        left.addSpacing(14)
        left.addWidget(QLabel("<b>Rows & Columns</b>"))
        for label_text, attr in [("Rows:", "in_rows"), ("Cols:", "in_cols")]:
            hl = QHBoxLayout()
            hl.addWidget(QLabel(label_text))
            spin = QSpinBox()
            spin.setRange(1, 99)
            setattr(self, attr, spin)
            hl.addWidget(spin)
            left.addLayout(hl)

        # Fonts & Styles
        left.addSpacing(18)
        left.addWidget(QLabel("<b>Fonts & Styles</b>"))
        for tag in ("name", "type", "price"):
            hl = QHBoxLayout()
            hl.addWidget(QLabel(f"{tag.capitalize()} font:"))
            combo = QComboBox()
            combo.addItems(FONTS_LIST)
            setattr(self, f"{tag}_font_combo", combo)
            hl.addWidget(combo)

            size = QSpinBox()
            size.setRange(6, 72)
            setattr(self, f"{tag}_font_size", size)
            hl.addWidget(size)
            hl.addWidget(QLabel("pt"))

            bold = QCheckBox("B")
            setattr(self, f"{tag}_bold", bold)
            hl.addWidget(bold)

            italic = QCheckBox("I")
            setattr(self, f"{tag}_italic", italic)
            hl.addWidget(italic)

            left.addLayout(hl)

        left.addSpacing(18)
        self.save_btn  = QPushButton("Save Sheet Setup")
        self.load_btn  = QPushButton("Load Sheet Setup")
        self.print_btn = QPushButton("Print Grid")
        left.addWidget(self.save_btn)
        left.addWidget(self.load_btn)
        left.addWidget(self.print_btn)
        left.addStretch(1)

        # ── Right: preview ──────────────────────────────────────────────
        self.preview = SheetPreview()
        layout.addWidget(self.preview, 1)

        # Load or apply defaults
        if os.path.exists(SETTINGS_PATH):
            self._load_settings(SETTINGS_PATH, autobackup=True)
        else:
            self._apply_defaults()

        # Connect autosave on all inputs
        for w in (
            self.in_w, self.in_h, self.in_mt, self.in_ml,
            self.in_rg, self.in_cg, self.in_rows, self.in_cols,
            self.name_font_combo, self.name_font_size, self.name_bold, self.name_italic,
            self.type_font_combo, self.type_font_size, self.type_bold, self.type_italic,
            self.price_font_combo, self.price_font_size, self.price_bold, self.price_italic
        ):
            if hasattr(w, "textChanged"):
                w.textChanged.connect(self._autosave)
            elif hasattr(w, "valueChanged"):
                w.valueChanged.connect(self._autosave)
            elif hasattr(w, "currentIndexChanged"):
                w.currentIndexChanged.connect(self._autosave)
            elif hasattr(w, "stateChanged"):
                w.stateChanged.connect(self._autosave)

        self.save_btn.clicked.connect(lambda: self._load_settings(None, autobackup=False))
        self.load_btn.clicked.connect(lambda: self._load_settings(None, autobackup=False))
        self.print_btn.clicked.connect(self._print_grid)   # <-- Only here!

        # Initial preview
        self.preview.update_preview(self.get_settings())

    def _apply_defaults(self):
        defaults = {
            "label_width_mm": 63.5, "label_height_mm": 38.1,
            "margin_top_mm": 10, "margin_left_mm": 10,
            "row_gap_mm": 0, "col_gap_mm": 2.5,
            "rows": 7, "cols": 3,
            "name_font": FONTS_LIST[0] if FONTS_LIST else "",
            "name_size_pt": 11, "name_bold": True, "name_italic": False,
            "type_font": FONTS_LIST[0] if FONTS_LIST else "",
            "type_size_pt": 9, "type_bold": False, "type_italic": True,
            "price_font": FONTS_LIST[0] if FONTS_LIST else "",
            "price_size_pt": 11, "price_bold": True, "price_italic": False,
        }
        self._populate_from_settings(defaults)

    def _autosave(self):
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(self.get_settings(), f, indent=2)
        self.preview.update_preview(self.get_settings())

    def _populate_from_settings(self, s):
        self.in_w.setText(str(s.get("label_width_mm", 63.5)))
        self.in_h.setText(str(s.get("label_height_mm", 38.1)))
        self.in_mt.setText(str(s.get("margin_top_mm", 10)))
        self.in_ml.setText(str(s.get("margin_left_mm", 10)))
        self.in_rg.setText(str(s.get("row_gap_mm", 0)))
        self.in_cg.setText(str(s.get("col_gap_mm", 2.5)))
        self.in_rows.setValue(s.get("rows", 7))
        self.in_cols.setValue(s.get("cols", 3))
        for tag in ("name", "type", "price"):
            getattr(self, f"{tag}_font_combo").setCurrentText(s.get(f"{tag}_font", FONTS_LIST[0] if FONTS_LIST else ""))
            getattr(self, f"{tag}_font_size").setValue(s.get(f"{tag}_size_pt", 11 if tag!="type" else 9))
            getattr(self, f"{tag}_bold").setChecked(s.get(f"{tag}_bold", tag!="type"))
            getattr(self, f"{tag}_italic").setChecked(s.get(f"{tag}_italic", tag=="type"))

    def _load_settings(self, path=None, autobackup=False):
        if not path:
            path, _ = QFileDialog.getOpenFileName(self, "Load Sheet Setup", "", "JSON Files (*.json)")
            if not path:
                return
        try:
            with open(path, "r", encoding="utf-8") as f:
                settings = json.load(f)
            self._populate_from_settings(settings)
            if autobackup:
                with open(SETTINGS_PATH, "w", encoding="utf-8") as bf:
                    json.dump(settings, bf, indent=2)
            self.preview.update_preview(self.get_settings())
        except Exception:
            QMessageBox.warning(self, "Грешка", "Не можа да зареди настройките.")

    def get_settings(self):
        def parse(txt, fallback):
            try:
                return float(txt)
            except:
                return fallback

        base = {
            "label_width_mm":  parse(self.in_w.text(),     63.5),
            "label_height_mm": parse(self.in_h.text(),     38.1),
            "margin_top_mm":   parse(self.in_mt.text(),    10),
            "margin_left_mm":  parse(self.in_ml.text(),    10),
            "row_gap_mm":      parse(self.in_rg.text(),     0),
            "col_gap_mm":      parse(self.in_cg.text(),     2.5),
            "rows":            self.in_rows.value(),
            "cols":            self.in_cols.value(),
        }
        fonts = {}
        for tag in ("name", "type", "price"):
            fonts[f"{tag}_font"]    = getattr(self, f"{tag}_font_combo").currentText()
            fonts[f"{tag}_size_pt"] = getattr(self, f"{tag}_font_size").value()
            fonts[f"{tag}_bold"]    = getattr(self, f"{tag}_bold").isChecked()
            fonts[f"{tag}_italic"]  = getattr(self, f"{tag}_italic").isChecked()
        return {**base, **fonts}

    def _print_grid(self):
        """
        Print only the blue calibration grid (no labels).
        """
        from PyQt5.QtCore import QRectF
        from PyQt5.QtGui import QPen, QColor, QPainter
        from PyQt5.QtPrintSupport import QPrinter, QPrintDialog

        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPrinter.A4)
        dlg = QPrintDialog(printer, self)
        if dlg.exec_() != QPrintDialog.Accepted:
            return

        painter = QPainter(printer)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor("#1c80e9"))
        pen.setWidthF(1.0)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        mm_to_pt = lambda mm: mm * 72 / 25.4

        s = self.get_settings()
        lw = float(s["label_width_mm"])
        lh = float(s["label_height_mm"])
        mt = float(s["margin_top_mm"])
        ml = float(s["margin_left_mm"])
        rg = float(s["row_gap_mm"])
        cg = float(s["col_gap_mm"])
        rows = int(s["rows"])
        cols = int(s["cols"])

        factor = printer.resolution() / 72.0
        painter.scale(factor, factor)

        for r in range(rows):
            for c in range(cols):
                x = mm_to_pt(ml + c * (lw + cg))
                y = mm_to_pt(mt + r * (lh + rg))
                rect = QRectF(
                    x,
                    y,
                    mm_to_pt(lw),
                    mm_to_pt(lh)
                )
                painter.drawRoundedRect(rect, 8, 8)

        painter.end()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = SheetEditor()
    win.show()
    sys.exit(app.exec_())
