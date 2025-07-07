# toolbar_widget.py

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt5.QtCore import pyqtSignal

class ToolbarWidget(QWidget):
    # Emitted when the user clicks Print or Export
    printRequested  = pyqtSignal()
    exportRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        self.print_btn  = QPushButton("Печатай")
        self.export_btn = QPushButton("Запази PDF")
        layout.addWidget(self.print_btn)
        layout.addWidget(self.export_btn)
        layout.addStretch(1)

        self.print_btn.clicked.connect(self.printRequested.emit)
        self.export_btn.clicked.connect(self.exportRequested.emit)
