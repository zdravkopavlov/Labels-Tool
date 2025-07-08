# toolbar_widget.py

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt5.QtCore import pyqtSignal

class ToolbarWidget(QWidget):
    selectAllRequested   = pyqtSignal()
    clearRequested       = pyqtSignal()
    saveSessionRequested = pyqtSignal()
    loadSessionRequested = pyqtSignal()    # ← new
    printRequested       = pyqtSignal()
    exportRequested      = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        # ── left group ─────────────────────────────────────────────────────────
        self.select_all_btn    = QPushButton("Избери всички")
        self.clear_btn         = QPushButton(" 🗑️ Изчисти")
        self.save_sess_btn     = QPushButton(" 💾 Запази сесия...")
        self.load_sess_btn     = QPushButton(" 📂 Зареди сесия...")  # ← new

        for btn, sig in (
            (self.select_all_btn,   self.selectAllRequested),
            (self.clear_btn,         self.clearRequested),
            (self.save_sess_btn,     self.saveSessionRequested),
            (self.load_sess_btn,     self.loadSessionRequested),
        ):
            layout.addWidget(btn)
            btn.clicked.connect(sig.emit)

        # spacer
        layout.addStretch(1)

        # ── right group ───────────────────────────────────────────────────────
        self.print_btn    = QPushButton(" 🖨️ Печат")
        self.export_btn   = QPushButton(" 📄 Запази PDF")
        for btn, sig in (
            (self.print_btn,   self.printRequested),
            (self.export_btn,  self.exportRequested),
        ):
            layout.addWidget(btn)
            btn.clicked.connect(sig.emit)
