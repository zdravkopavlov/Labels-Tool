# sheet_widget.py

import os
import csv
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QFileDialog, QMessageBox
)
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtGui import QPainter, QFont, QFontMetrics
from PyQt5.QtCore import pyqtSignal, Qt
from label_widget import LabelWidget
from toolbar_widget import ToolbarWidget
from session_manager import SessionManager
from selection_manager import SelectionManager
from clipboard_manager import ClipboardManager
from printer_rl import export_to_pdf

def get_sheet_settings_from_tabs(widget):
    p = widget.parent()
    while p:
        if hasattr(p, "count"):
            for i in range(p.count()):
                tab = p.widget(i)
                if hasattr(tab, "get_settings"):
                    return tab.get_settings()
        p = p.parent()
    return {
        "label_width_mm": 63.5, "label_height_mm": 38.1,
        "margin_top_mm": 10,   "margin_left_mm": 10,
        "row_gap_mm": 0,       "col_gap_mm": 2.0,
        "rows": 7,             "cols": 3,
    }

class SheetWidget(QWidget):
    labelsChanged = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Labels Tool")

        # ensure config folder
        base = os.path.dirname(os.path.abspath(__file__))
        cfg  = os.path.join(base, "config")
        os.makedirs(cfg, exist_ok=True)

        # main layout
        self.layout = QVBoxLayout(self)

        # toolbar
        self.toolbar = ToolbarWidget()
        self.layout.addWidget(self.toolbar)
        self.toolbar.selectAllRequested.connect(lambda: self.selection.select_all())
        self.toolbar.clearRequested.connect(self._confirm_and_clear)
        self.toolbar.saveSessionRequested.connect(self.save_session_csv)
        self.toolbar.loadSessionRequested.connect(self.load_session_csv)
        self.toolbar.printRequested.connect(self._print_to_printer)
        self.toolbar.exportRequested.connect(self.export_pdf)

        # scrollable grid
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.layout.addWidget(self.scroll)

        # build grid & managers
        self._populate_grid()
        self.session   = SessionManager(self)
        self.selection = SelectionManager(self, self.labels)
        self.clipboard = ClipboardManager(self, self.labels, self.selection)
        for lbl in self.labels:
            lbl.changed.connect(self.labelsChanged.emit)

    def _populate_grid(self):
        if self.scroll.widget():
            self.scroll.takeWidget().deleteLater()

        s = get_sheet_settings_from_tabs(self)
        rows, cols = int(s["rows"]), int(s["cols"])
        container = QWidget()
        vlay = QVBoxLayout(container)
        vlay.setContentsMargins(12, 12, 12, 12)

        self.labels = []
        for r in range(rows):
            hl = QHBoxLayout()
            hl.setSpacing(int(s["col_gap_mm"] * 0.8))
            for _ in range(cols):
                lbl = LabelWidget()
                self.labels.append(lbl)
                hl.addWidget(lbl)
            vlay.addLayout(hl)
            if r < rows - 1:
                vlay.addSpacing(int(s["row_gap_mm"] * 0.8))

        self.scroll.setWidget(container)
        self.labelsChanged.emit()

    def _confirm_and_clear(self):
        reply = QMessageBox.question(
            self, "Потвърждение",
            "Сигурни ли сте, че искате да изчистите избраните или всички етикети?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            sel = self.selection.selected
            targets = sel if sel else list(range(len(self.labels)))
            for i in targets:
                self.labels[i].clear_fields()
            self.labelsChanged.emit()

    def save_session_csv(self):
        fn, _ = QFileDialog.getSaveFileName(
            self, "Запази сесия (CSV)", "", "CSV Files (*.csv)"
        )
        if not fn:
            return
        try:
            with open(fn, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["name","type","price_bgn","price_eur","unit_eur","logo"])
                for lbl in self.labels:
                    d = lbl.get_export_data()
                    w.writerow([
                        d["name"], d["type"],
                        d["price_bgn"], d["price_eur"],
                        d["unit_eur"], d["logo"]
                    ])
            QMessageBox.information(self, "Запазено", f"CSV записан в:\n{fn}")
        except Exception as e:
            QMessageBox.warning(self, "Грешка", f"Не можа да запише CSV:\n{e}")

    def load_session_csv(self):
        fn, _ = QFileDialog.getOpenFileName(
            self, "Зареди сесия (CSV)", "", "CSV Files (*.csv)"
        )
        if not fn:
            return
        try:
            with open(fn, "r", newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            for i, entry in enumerate(rows):
                if i >= len(self.labels):
                    break
                lbl = self.labels[i]
                lbl.set_name(entry.get("name",""))
                lbl.set_type(entry.get("type",""))
                lbl.set_price(entry.get("price_bgn",""))
                lbl.set_price_eur(entry.get("price_eur",""))
                lbl.set_unit_eur_text(entry.get("unit_eur",""))
                lbl.set_logo(entry.get("logo","False") in ("True","true","1"))
            self.labelsChanged.emit()
            QMessageBox.information(self, "Заредено", f"Сесията е заредена от:\n{fn}")
        except Exception as e:
            QMessageBox.warning(self, "Грешка", f"Не можа да зареди CSV:\n{e}")

    def export_pdf(self):
        fn, _ = QFileDialog.getSaveFileName(
            self, "Запази PDF", "", "PDF Files (*.pdf>"
        )
        if not fn:
            return
        settings = get_sheet_settings_from_tabs(self)
        export_to_pdf(fn, settings, self.labels, show_logo=True, logo_path="logo.png")
        QMessageBox.information(self, "Export Complete", f"PDF saved to:\n{fn}")

    def _print_to_printer(self):
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPrinter.A4)
        dlg = QPrintDialog(printer, self)
        if dlg.exec_() != QPrintDialog.Accepted:
            return

        painter = QPainter(printer)
        self._draw_labels_on_painter(painter)
        painter.end()

    def _draw_labels_on_painter(self, painter):
        s = get_sheet_settings_from_tabs(self)
        lw = float(s["label_width_mm"])
        lh = float(s["label_height_mm"])
        mt = float(s["margin_top_mm"])
        ml = float(s["margin_left_mm"])
        rg = float(s["row_gap_mm"])
        cg = float(s["col_gap_mm"])
        rows, cols = int(s["rows"]), int(s["cols"])

        mm_to_pt = lambda mm: mm * 72 / 25.4
        pr = painter.device()
        page_rect = pr.pageRect()
        pw, ph = page_rect.width(), page_rect.height()
        aw, ah = mm_to_pt(210), mm_to_pt(297)
        scale = min(pw/aw, ph/ah)
        off_x = (pw - aw*scale)/2
        off_y = (ph - ah*scale)/2

        painter.translate(off_x, off_y)
        painter.scale(scale, scale)

        font_name = "Arial"
        for idx, lbl in enumerate(self.labels):
            r, c = divmod(idx, cols)
            x = mm_to_pt(ml + c*(lw+cg))
            y = mm_to_pt(mt + r*(lh+rg))
            w = mm_to_pt(lw)
            h = mm_to_pt(lh)

            data = lbl.get_export_data()
            block = []
            if data["name"]:
                f = QFont(font_name, 11, QFont.Bold)
                block.append((data["name"], f))
            if data["type"]:
                f = QFont(font_name, 9); f.setItalic(True)
                block.append((data["type"], f))
            if data["price_bgn"]:
                f = QFont(font_name, 11, QFont.Bold)
                block.append((f'{data["price_bgn"]} лв.', f))
            if data["price_eur"]:
                f = QFont(font_name, 11, QFont.Bold)
                block.append((f'€ {data["price_eur"]}', f))
            if data["unit_eur"]:
                f = QFont(font_name, 9); f.setItalic(True)
                block.append((f'/ {data["unit_eur"]}', f))

            total_h = sum(QFontMetrics(f).height() for _, f in block)
            y0 = y + (h - total_h)/2

            for text, f in block:
                painter.setFont(f)
                line_h = QFontMetrics(f).height()
                painter.drawText(int(x), int(y0), int(w), int(line_h),
                                 Qt.AlignCenter, text)
                y0 += line_h
