# sheet_widget.py

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QFileDialog, QMessageBox
)
from PyQt5.QtCore import pyqtSignal
from label_widget import LabelWidget
from toolbar_widget import ToolbarWidget
from session_manager import SessionManager
from selection_manager import SelectionManager
from clipboard_manager import ClipboardManager
from printer_rl import export_to_pdf

def get_sheet_settings_from_tabs(widget):
    """Traverse up to find a tab with get_settings(), else return defaults."""
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
        "margin_top_mm": 10,  "margin_left_mm": 10,
        "row_gap_mm": 0,      "col_gap_mm": 2.0,
        "rows": 7,            "cols": 3,
    }

class SheetWidget(QWidget):
    # Emitted whenever any LabelWidget.changed fires
    labelsChanged = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Labels Tool")

        # Ensure config folder exists
        os.makedirs("config", exist_ok=True)

        # Main layout
        self.layout = QVBoxLayout(self)

        # 1) Toolbar
        self.toolbar = ToolbarWidget()
        self.layout.addWidget(self.toolbar)
        self.toolbar.printRequested.connect(self.print_labels)
        self.toolbar.exportRequested.connect(self.export_pdf)

        # 2) Scrollable area for grid
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.layout.addWidget(self.scroll)

        # 3) Populate the grid of LabelWidgets
        self._populate_grid()

        # 4) Session manager (loads on init, saves on labelsChanged)
        self.session = SessionManager(
            grid=self,
            session_path=os.path.join("config", "session.json")
        )

        # 5) Selection manager (handles Ctrl/Shift-click)
        self.selection = SelectionManager(self, self.labels)

        # 6) Clipboard manager (handles Ctrl+C / Ctrl+V)
        self.clipboard = ClipboardManager(self, self.labels, self.selection)

        # Forward each label’s changed signal to labelsChanged
        for lbl in self.labels:
            lbl.changed.connect(self.labelsChanged.emit)

    def _populate_grid(self):
        """Builds the grid of LabelWidget instances based on sheet settings."""
        # Remove previous widget
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
            for c in range(cols):
                lbl = LabelWidget()
                self.labels.append(lbl)
                hl.addWidget(lbl)
            vlay.addLayout(hl)
            if r < rows - 1:
                vlay.addSpacing(int(s["row_gap_mm"] * 0.8))

        self.scroll.setWidget(container)
        # Emit once so SessionManager can save the empty/new grid
        self.labelsChanged.emit()

    def export_pdf(self):
        """Invoke the ReportLab exporter to save a PDF."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Запази PDF", "", "PDF Files (*.pdf)"
        )
        if not path:
            return
        settings = get_sheet_settings_from_tabs(self)
        export_to_pdf(
            path,
            settings,
            self.labels,
            show_logo=True,
            logo_path="logo.png"
        )
        QMessageBox.information(
            self, "Export Complete", f"PDF saved to:\n{path}"
        )

    def print_labels(self):
        """For now, alias to export_pdf; could launch a headless print job."""
        self.export_pdf()
