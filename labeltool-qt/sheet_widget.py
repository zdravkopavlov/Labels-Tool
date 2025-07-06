import os
import json
from PyQt5.QtWidgets import (
    QApplication,
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea, QFileDialog, QShortcut
)
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QPainter, QFont, QFontMetrics, QKeySequence
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from label_widget import LabelWidget

# ─── CONFIG PATHS ─────────────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR   = os.path.join(BASE_DIR, "config")
os.makedirs(CONFIG_DIR, exist_ok=True)
SESSION_PATH = os.path.join(CONFIG_DIR, "session.json")
SETTINGS_PATH= os.path.join(CONFIG_DIR, "settings.json")
# ──────────────────────────────────────────────────────────────────────────────

def get_sheet_settings_from_tabs(self):
    p = self.parent()
    while p:
        if hasattr(p, "count"):
            for i in range(p.count()):
                tab = p.widget(i)
                if hasattr(tab, "get_settings"):
                    return tab.get_settings()
        p = p.parent()
    # fallback defaults
    return {
        "label_width_mm": 63.5,
        "label_height_mm": 38.1,
        "margin_top_mm": 10,
        "margin_left_mm": 10,
        "row_gap_mm": 0,
        "col_gap_mm": 2.0,
        "rows": 7,
        "cols": 3,
    }

class SheetWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Labels Tool")

        # Layout
        self.layout = QVBoxLayout(self)
        tl = QHBoxLayout(); self.layout.addLayout(tl)
        self.export_pdf_btn = QPushButton("Запази PDF"); tl.addWidget(self.export_pdf_btn)
        self.print_btn      = QPushButton("Печатай");  tl.addWidget(self.print_btn)
        tl.addStretch(1)
        self.export_pdf_btn.clicked.connect(self.export_pdf)
        self.print_btn.clicked.connect(self.print_labels)

        # Load sheet settings
        self.sheet_settings = get_sheet_settings_from_tabs(self)
        if os.path.exists(SETTINGS_PATH):
            try:
                self.sheet_settings = json.load(open(SETTINGS_PATH, "r", encoding="utf-8"))
            except:
                pass

        # Scroll area + grid
        self.labels_area = QScrollArea()
        self.labels_area.setWidgetResizable(True)
        self.layout.addWidget(self.labels_area)
        self.selected_indexes = []
        self.populate_grid()

        # Install event filter for blank-space clicks
        self.labels_area.viewport().installEventFilter(self)

        # Load label session
        if os.path.exists(SESSION_PATH):
            try:
                data = json.load(open(SESSION_PATH, "r", encoding="utf-8"))
                for i, item in enumerate(data):
                    if i < len(self.labels):
                        lbl = self.labels[i]
                        lbl.set_name(item["name"])
                        lbl.set_type(item["type"])
                        lbl.set_price(item["price_bgn"])
                        lbl.set_price_eur(item["price_eur"])
                        lbl.set_unit_eur_text(item["unit_eur"])
                        lbl.set_logo(item["logo"])
            except:
                pass

        # Global shortcuts
        self.copy_sc = QShortcut(QKeySequence("Ctrl+C"), self)
        self.copy_sc.setContext(Qt.ApplicationShortcut)
        self.copy_sc.activated.connect(self.copy_selected)
        self.paste_sc = QShortcut(QKeySequence("Ctrl+V"), self)
        self.paste_sc.setContext(Qt.ApplicationShortcut)
        self.paste_sc.activated.connect(self.paste_selected)

    def populate_grid(self):
        # Clear old widget
        if self.labels_area.widget():
            self.labels_area.takeWidget().deleteLater()

        self.labels = []
        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(12, 12, 12, 12)

        ls = self.sheet_settings
        rows, cols = ls["rows"], ls["cols"]
        for r in range(rows):
            hb = QHBoxLayout()
            hb.setSpacing(int(ls["col_gap_mm"] * 0.8))
            for c in range(cols):
                lbl = LabelWidget()
                lbl.setMinimumHeight(130)
                lbl.setMaximumHeight(120)
                lbl.clicked.connect(self.on_label_clicked)
                lbl.changed.connect(self._auto_save_session)
                self.labels.append(lbl)
                hb.addWidget(lbl)
            lay.addLayout(hb)
            if r < rows - 1:
                lay.addSpacing(int(ls["row_gap_mm"] * 0.8))

        container.setMinimumHeight(120 * rows)
        self.labels_area.setWidget(container)
        self.update_selection()

    def on_label_clicked(self, label, event):
        idx = self.labels.index(label)
        mods = QApplication.keyboardModifiers()
        if mods & Qt.ControlModifier:
            if idx in self.selected_indexes:
                self.selected_indexes.remove(idx)
            else:
                self.selected_indexes.append(idx)
        elif mods & Qt.ShiftModifier and self.selected_indexes:
            start = min(self.selected_indexes)
            end = idx
            for i in range(min(start, end), max(start, end) + 1):
                if i not in self.selected_indexes:
                    self.selected_indexes.append(i)
        else:
            # single select
            for i in self.selected_indexes:
                self.labels[i].set_selected(False)
            self.selected_indexes = [idx]
        self.update_selection()

    def update_selection(self):
        for i, lbl in enumerate(self.labels):
            lbl.set_selected(i in self.selected_indexes)

    def _auto_save_session(self):
        try:
            data = [l.get_export_data() for l in self.labels]
            with open(SESSION_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except:
            pass

    def copy_selected(self):
        if not self.selected_indexes:
            return
        self.labels[self.selected_indexes[0]]._copy()

    def paste_selected(self):
        data = getattr(LabelWidget, "_copied_content", None)
        if not data or not self.selected_indexes:
            return
        for idx in self.selected_indexes:
            lbl = self.labels[idx]
            lbl.name_edit.setText(data[0])
            lbl.subtype_edit.setText(data[1])
            lbl.price_bgn_edit.setText(data[2])
            lbl.price_eur_edit.setText(data[3])
            lbl.set_unit_eur(data[4])
        self._auto_save_session()

    def export_pdf(self):
        fn, _ = QFileDialog.getSaveFileName(self, "Export to PDF", "", "PDF Files (*.pdf)")
        if not fn:
            return
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFileName(fn)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setPageSize(printer.A4)
        painter = QPainter(printer)
        self._draw(painter, border_rects=True)
        painter.end()

    def print_labels(self):
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(printer.A4)
        if QPrintDialog(printer, self).exec_() != QPrintDialog.Accepted:
            return
        painter = QPainter(printer)
        self._draw(painter, border_rects=False)
        painter.end()

    def _draw(self, painter, border_rects):
        ls = self.sheet_settings
        mm2pt = lambda mm: mm * 72 / 25.4
        # compute scale to fit A4
        pr = painter.device()
        rect = pr.pageRect()
        scale = min(rect.width() / mm2pt(210), rect.height() / mm2pt(297))
        offx = (rect.width() - mm2pt(210) * scale) / 2
        offy = (rect.height() - mm2pt(297) * scale) / 2
        painter.translate(offx, offy)
        painter.scale(scale, scale)

        # dynamic font sizing
        label_h_pt = mm2pt(ls["label_height_mm"])
        base_pt = max(6, min(10, int(label_h_pt * 0.1)))

        idx = 0
        for r in range(ls["rows"]):
            for c in range(ls["cols"]):
                x = mm2pt(ls["margin_left_mm"] + c * (ls["label_width_mm"] + ls["col_gap_mm"]))
                y = mm2pt(ls["margin_top_mm"]  + r * (ls["label_height_mm"] + ls["row_gap_mm"]))
                w = mm2pt(ls["label_width_mm"])
                h = mm2pt(ls["label_height_mm"])

                if idx < len(self.labels):
                    data = self.labels[idx].get_export_data()
                    lines = []
                    if data["name"]:
                        lines.append((data["name"], QFont("Arial", base_pt, QFont.Bold)))
                    if data["type"]:
                        f = QFont("Arial", max(6, int(base_pt * 0.9))); f.setItalic(True)
                        lines.append((data["type"], f))
                    if data["price_bgn"]:
                        lines.append((f"{data['price_bgn']} лв.", QFont("Arial", base_pt)))
                    if data["price_eur"]:
                        lines.append((f"€{data['price_eur']}", QFont("Arial", base_pt)))
                    if data["unit_eur"]:
                        f = QFont("Arial", max(6, int(base_pt * 0.8))); f.setItalic(True)
                        lines.append((f"/ {data['unit_eur']}", f))

                    # center vertically
                    total_h = sum(QFontMetrics(f).height() for _, f in lines)
                    y0 = y + (h - total_h) / 2
                    for text, font in lines:
                        painter.setFont(font)
                        fm = QFontMetrics(font)
                        painter.drawText(int(x), int(y0), int(w), fm.height(), Qt.AlignCenter, text)
                        y0 += fm.height()
                idx += 1

    def eventFilter(self, obj, event):
        if obj == self.labels_area.viewport() and event.type() == QEvent.MouseButtonPress:
            pos = event.pos()
            if not any(lbl.geometry().contains(lbl.parentWidget().mapFrom(self.labels_area.viewport(), pos))
                       for lbl in self.labels):
                for i in self.selected_indexes:
                    self.labels[i].set_selected(False)
                self.selected_indexes = []
                return True
        return super().eventFilter(obj, event)
