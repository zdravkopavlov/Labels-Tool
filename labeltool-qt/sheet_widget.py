# sheet_widget.py

import os
import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QScrollArea, QFileDialog,
    QShortcut, QMessageBox
)
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QKeySequence
from label_widget import LabelWidget
from printer_rl import export_to_pdf  # ReportLab exporter from above

# ─── CONFIG PATHS ─────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR    = os.path.join(BASE_DIR, "config")
os.makedirs(CONFIG_DIR, exist_ok=True)
SESSION_PATH  = os.path.join(CONFIG_DIR, "session.json")
SETTINGS_PATH = os.path.join(CONFIG_DIR, "settings.json")
# ──────────────────────────────────────────────────────────────────────────────

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

        # Load or fallback settings
        self.sheet_settings = get_sheet_settings_from_tabs(self)
        if os.path.exists(SETTINGS_PATH):
            try:
                self.sheet_settings = json.load(open(SETTINGS_PATH, "r", encoding="utf-8"))
            except:
                pass

        # Top toolbar
        self.layout = QVBoxLayout(self)
        toolbar = QHBoxLayout()
        self.layout.addLayout(toolbar)
        self.export_btn = QPushButton("Запази PDF")
        self.print_btn  = QPushButton("Печатай")
        toolbar.addWidget(self.export_btn)
        toolbar.addWidget(self.print_btn)
        toolbar.addStretch(1)
        self.export_btn.clicked.connect(self.export_pdf)
        self.print_btn.clicked.connect(self.print_labels)

        # Scroll area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.layout.addWidget(self.scroll)

        # Restore session
        self.labels = []
        self.selected_indexes = []
        self._load_session()

        # Build grid
        self._populate_grid()

        # Click-outside clears selection
        self.scroll.viewport().installEventFilter(self)

        # Copy/paste shortcuts
        QShortcut(QKeySequence("Ctrl+C"), self, activated=self.copy_selected)
        QShortcut(QKeySequence("Ctrl+V"), self, activated=self.paste_selected)

    def _populate_grid(self):
        # Remove old
        if self.scroll.widget():
            self.scroll.takeWidget().deleteLater()

        rows = int(self.sheet_settings["rows"])
        cols = int(self.sheet_settings["cols"])

        container = QWidget()
        vlay = QVBoxLayout(container)
        vlay.setContentsMargins(12,12,12,12)

        self.labels.clear()
        for r in range(rows):
            hl = QHBoxLayout()
            hl.setSpacing(int(self.sheet_settings["col_gap_mm"] * 0.8))
            for c in range(cols):
                lbl = LabelWidget()
                lbl.clicked.connect(self.on_label_clicked)
                lbl.changed.connect(self._save_session)
                self.labels.append(lbl)
                hl.addWidget(lbl)
            vlay.addLayout(hl)
            # no manual setMinimumHeight; let Qt size the container
        self.scroll.setWidget(container)
        self._update_selection()

    def on_label_clicked(self, label, event):
        idx = self.labels.index(label)
        if event.modifiers() & Qt.ControlModifier:
            if idx in self.selected_indexes:
                self.selected_indexes.remove(idx)
            else:
                self.selected_indexes.append(idx)
        elif event.modifiers() & Qt.ShiftModifier and self.selected_indexes:
            start = min(self.selected_indexes)
            for i in range(min(start, idx), max(start, idx)+1):
                if i not in self.selected_indexes:
                    self.selected_indexes.append(i)
        else:
            for i in self.selected_indexes:
                self.labels[i].set_selected(False)
            self.selected_indexes = [idx]
        self._update_selection()

    def _update_selection(self):
        for i, lbl in enumerate(self.labels):
            lbl.set_selected(i in self.selected_indexes)

    def _save_session(self):
        try:
            data = [l.get_export_data() for l in self.labels]
            with open(SESSION_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except:
            pass

    def _load_session(self):
        if not os.path.exists(SESSION_PATH):
            return
        try:
            data = json.load(open(SESSION_PATH, "r", encoding="utf-8"))
            total = int(self.sheet_settings["rows"]) * int(self.sheet_settings["cols"])
            self.labels = [LabelWidget() for _ in range(total)]
            for i, d in enumerate(data):
                if i < len(self.labels):
                    lbl = self.labels[i]
                    lbl.set_name(d.get("name",""))
                    lbl.set_type(d.get("type",""))
                    lbl.set_price(d.get("price_bgn",""))
                    lbl.set_price_eur(d.get("price_eur",""))
                    lbl.set_unit_eur_text(d.get("unit_eur",""))
                    lbl.set_logo(d.get("logo",False))
        except:
            self.labels = []

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
        self._save_session()

    def export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Запази PDF", "", "PDF Files (*.pdf)")
        if not path:
            return
        export_to_pdf(path,
                      self.sheet_settings,
                      self.labels,
                      show_logo=True,
                      logo_path="logo.png")
        QMessageBox.information(self, "Export Complete", f"PDF saved to:\n{path}")

    def print_labels(self):
        # just exports for now
        self.export_pdf()

    def eventFilter(self, obj, event):
        if obj == self.scroll.viewport() and event.type() == QEvent.MouseButtonPress:
            pos = event.pos()
            if not any(lbl.geometry().contains(lbl.parentWidget().mapFrom(self.scroll.viewport(), pos))
                       for lbl in self.labels):
                for i in self.selected_indexes:
                    self.labels[i].set_selected(False)
                self.selected_indexes = []
                return True
        return super().eventFilter(obj, event)
