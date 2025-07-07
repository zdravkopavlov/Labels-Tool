# sheet_widget.py

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QFileDialog, QMessageBox
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPainter
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from label_widget import LabelWidget
from toolbar_widget import ToolbarWidget
from session_manager import SessionManager
from selection_manager import SelectionManager
from clipboard_manager import ClipboardManager
from printer_rl import export_to_pdf

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR  = os.path.join(BASE_DIR, "config")
os.makedirs(CONFIG_DIR, exist_ok=True)
SESSION_PATH = os.path.join(CONFIG_DIR, "session.json")

def get_sheet_settings_from_tabs(widget):
    parent = widget.parent()
    while parent:
        if hasattr(parent, "count"):
            for i in range(parent.count()):
                tab = parent.widget(i)
                if hasattr(tab, "get_settings"):
                    return tab.get_settings()
        parent = parent.parent()
    return {
        "label_width_mm": 63.5, "label_height_mm": 38.1,
        "margin_top_mm": 10,   "margin_left_mm": 10,
        "row_gap_mm": 0,       "col_gap_mm": 2.0,
        "rows": 7,             "cols": 3,
        "name_font": "Helvetica-Bold",    "name_size_pt": 11,
        "type_font": "Helvetica-Oblique", "type_size_pt": 9,
        "price_font": "Helvetica-Bold",   "price_size_pt": 11,
    }

class SheetWidget(QWidget):
    labelsChanged = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Labels Tool")
        self.layout = QVBoxLayout(self)

        # Toolbar
        self.toolbar = ToolbarWidget()
        self.layout.addWidget(self.toolbar)

        # Scroll area for labels
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.layout.addWidget(self.scroll)

        # Build label grid
        self._populate_grid()

        # SessionManager: use config/session.json right next to the .py
        self.session = SessionManager(self)  # Always uses config/session.json
        self.session.load_session()

        # Selection & Clipboard
        self.selection = SelectionManager(self, self.labels)
        self.clipboard = ClipboardManager(self, self.labels, self.selection)

        # Hook toolbar actions
        self.toolbar.selectAllRequested.connect(self.selection.select_all)
        self.toolbar.clearRequested.connect(self._confirm_and_clear)
        self.toolbar.saveSessionRequested.connect(self.save_session_csv)
        self.toolbar.loadSessionRequested.connect(self.load_session_csv)
        self.toolbar.printRequested.connect(self._print_to_printer)
        self.toolbar.exportRequested.connect(self.export_pdf)

        # Hand cursor & change notifications
        for lbl in self.labels:
            lbl.setCursor(Qt.PointingHandCursor)
            lbl.changed.connect(self.labelsChanged.emit)

        # ALWAYS SAVE SESSION on any label change
        self.labelsChanged.connect(self.session.save_session)

    def _populate_grid(self):
        if self.scroll.widget():
            self.scroll.takeWidget().deleteLater()

        s = get_sheet_settings_from_tabs(self)
        rows, cols = int(s["rows"]), int(s["cols"])

        container = QWidget()
        from PyQt5.QtWidgets import QHBoxLayout
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
            targets = self.selection.selected or list(range(len(self.labels)))
            for i in targets:
                self.labels[i].clear_fields()
            self.labelsChanged.emit()

    def export_pdf(self):
        fn, _ = QFileDialog.getSaveFileName(self, "Запази PDF", "", "PDF Files (*.pdf)")
        if not fn:
            return
        settings = get_sheet_settings_from_tabs(self)
        try:
            export_to_pdf(fn, settings, self.labels, show_logo=True, logo_path="logo.png")
        except PermissionError as e:
            QMessageBox.warning(
                self,
                "Грешка при запис на PDF",
                "Не може да запише PDF–а.\n"
                "Уверете се, че файлът не е отворен в друг прозорец.\n\n"
                f"{e}"
            )
            return
        QMessageBox.information(self, "Готово", f"PDF записан в:\n{fn}")

    def _print_to_printer(self):
        # 1) Create & configure the printer
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPrinter.A4)

        # 2) Show the print dialog
        dlg = QPrintDialog(printer, self)
        if dlg.exec_() != QPrintDialog.Accepted:
            return

        # 3) Begin painting
        painter = QPainter(printer)
        painter.setRenderHint(QPainter.Antialiasing)

        # 4) Scale so that 1pt (1/72") == 1 logical DPI unit
        factor = printer.logicalDpiX() / 72.0
        painter.scale(factor, factor)

        # 5) Draw the labels at point-based coordinates
        self._draw_labels_on_painter(painter)

        # 6) Finish
        painter.end()

    def _draw_labels_on_painter(self, painter):
        # pulls in the unified layout code
        from label_render import draw_labels_grid
        # get the sheet settings (your existing helper)
        s = get_sheet_settings_from_tabs(self)
        # collect all label data
        data = [lbl.get_export_data() for lbl in self.labels]
        # draw everything on the QPainter
        draw_labels_grid(
            backend="qtpainter",
            device=painter,
            settings=s,
            labels=data,
            logo_path="logo.png",  # or None if you don’t use logos
        )

    def save_session_csv(self):
        fn, _ = QFileDialog.getSaveFileName(self, "Запази сесия (CSV)", "", "CSV Files (*.csv)")
        if not fn:
            return
        try:
            with open(fn, "w", newline="", encoding="utf-8") as f:
                import csv
                w = csv.writer(f)
                w.writerow(["name", "type", "price_bgn", "price_eur", "unit_eur", "logo"])
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
        fn, _ = QFileDialog.getOpenFileName(self, "Зареди сесия (CSV)", "", "CSV Files (*.csv)")
        if not fn:
            return
        try:
            with open(fn, "r", newline="", encoding="utf-8") as f:
                import csv
                rows = list(csv.DictReader(f))
            for i, entry in enumerate(rows):
                if i >= len(self.labels):
                    break
                lbl = self.labels[i]
                lbl.set_name(entry.get("name", ""))
                lbl.set_type(entry.get("type", ""))
                lbl.set_price(entry.get("price_bgn", ""))
                lbl.set_price_eur(entry.get("price_eur", ""))
                lbl.set_unit_eur_text(entry.get("unit_eur", ""))
                lbl.set_logo(entry.get("logo", "False") in ("True", "true", "1"))
            self.labelsChanged.emit()
            QMessageBox.information(self, "Заредено", f"Сесията е заредена от:\n{fn}")
        except Exception as e:
            QMessageBox.warning(self, "Грешка", f"Не можа да зареди CSV:\n{e}")

    # For explicit save/load if ever needed (compat)
    def save_session(self):
        self.session.save_session()
    def load_session(self):
        self.session.load_session()
