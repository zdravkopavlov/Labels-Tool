# sheet_widget.py

import os
import tempfile
import webbrowser
import subprocess
import json

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QFileDialog,
    QMessageBox
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QGridLayout, QVBoxLayout
from label_widget import LabelWidget
from toolbar_widget import ToolbarWidget
from bottom_toolbar_widget import BottomToolbarWidget
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

        self.bottom_toolbar = BottomToolbarWidget()
        self.layout.addWidget(self.bottom_toolbar)
        self.bottom_toolbar.load_settings()
        self.bottom_toolbar.chk_show_logo.stateChanged.connect(lambda _: self.bottom_toolbar.save_settings())
        self.bottom_toolbar.chk_show_bgn.stateChanged.connect(lambda _: self.bottom_toolbar.save_settings())
        self.bottom_toolbar.chk_show_eur.stateChanged.connect(lambda _: self.bottom_toolbar.save_settings())
        self.bottom_toolbar.cmb_convert.currentIndexChanged.connect(lambda _: self.bottom_toolbar.save_settings())


        # Build label grid
        self._populate_grid()

        # SessionManager
        self.session = SessionManager(self)
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
        self.bottom_toolbar.cmb_convert.currentIndexChanged.connect(self.on_conversion_mode_changed)


        # Hand cursor & change notifications
        for lbl in self.labels:
            lbl.setCursor(Qt.PointingHandCursor)
            lbl.changed.connect(self.labelsChanged.emit)

        self.labelsChanged.connect(self.session.save_session)

    def on_conversion_mode_changed(self, index):
        if index == 0:
            mode = "bgn_to_eur"
        elif index == 1:
            mode = "eur_to_bgn"
        elif index == 2:
            mode = "both"
        else:
            mode = "manual"
        for lbl in getattr(self, 'labels', []):
            if hasattr(lbl, "currency_manager"):
                lbl.currency_manager.set_conversion_mode(mode)    

    def _populate_grid(self):
        if self.scroll.widget():
            self.scroll.takeWidget().deleteLater()

        s = get_sheet_settings_from_tabs(self)
        rows, cols = int(s["rows"]), int(s["cols"])

        grid_container = QWidget()
        grid = QGridLayout(grid_container)
        grid.setSpacing(4)
        grid.setContentsMargins(10, 10, 0, 0)

        self.labels = []
        for r in range(rows):
            for c in range(cols):
                lbl = LabelWidget()
                lbl.setSizePolicy(lbl.sizePolicy().Fixed, lbl.sizePolicy().Fixed)
                self.labels.append(lbl)
                grid.addWidget(lbl, r, c, alignment=Qt.AlignTop | Qt.AlignLeft)

        for r in range(rows):
            grid.setRowStretch(r, 0)
        for c in range(cols):
            grid.setColumnStretch(c, 0)

        # NEW: main container to hold grid, aligned to top/left
        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(grid_container, alignment=Qt.AlignTop | Qt.AlignLeft)
        # Optionally add a vertical spacer if you want a minimum scroll area

        self.scroll.setWidget(main_container)
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
        except Exception as e:
            QMessageBox.critical(self, "Error exporting PDF", f"Could not create PDF:\n{e}")
            return
        QMessageBox.information(self, "Готово", f"PDF записан в:\n{fn}")

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

    def _print_to_printer(self):
        """
        Fallback: generate a temp PDF and silently print to the default printer.
        """
        # 1) Create temp PDF
        fd, tmp_path = tempfile.mkstemp(prefix="labels_", suffix=".pdf")
        os.close(fd)
        settings = get_sheet_settings_from_tabs(self)
        try:
            export_to_pdf(tmp_path, settings, self.labels, show_logo=True, logo_path="logo.png")
        except Exception as e:
            QMessageBox.critical(self, "Error exporting PDF", f"Could not create PDF:\n{e}")
            return

        # 2) Send to default printer
        try:
            if os.name == "nt":
                # Windows: print silently
                os.startfile(tmp_path, "print")
            else:
                # macOS/Linux: use lpr
                subprocess.run(["lpr", tmp_path], check=True)
        except Exception:
            QMessageBox.warning(
                self,
                "Print failed",
                "PDF created, but automatic printing failed.\n"
                "Please open and print manually:\n" + tmp_path
            )

    # For compatibility
    def save_session(self):
        self.session.save_session()

    def load_session(self):
        self.session.load_session()
