from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit, QLineEdit, QComboBox, QToolButton, QHBoxLayout
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import pyqtSignal

CONV_MODES = [
    ("BGN → EUR", "bgn_to_eur"),
    ("EUR → BGN", "eur_to_bgn"),
    ("BGN ⇄ EUR", "both"),
    ("Без конверсия", "manual"),
]

class LeftPaneWidget(QWidget):
    # Signals for external logic to connect to
    text_changed = pyqtSignal(str, str)  # key, value
    conversion_changed = pyqtSignal(str)
    print_clicked = pyqtSignal()
    pdf_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # --- Input fields ---
        self.field_inputs = {}
        for key, lbl in [("main", "Основен текст:"), ("second", "Втори ред:"), ("bgn", "Цена BGN:"), ("eur", "Цена EUR:")]:
            layout.addWidget(QLabel(lbl))
            if key in ("main", "second"):
                w = QTextEdit()
                w.setFont(QFont("Arial", 16))
                w.setFixedHeight(54)
                w.textChanged.connect(lambda k=key, w=w: self.text_changed.emit(k, w.toPlainText()))
            else:
                w = QLineEdit()
                w.setFont(QFont("Arial", 16))
                w.textChanged.connect(lambda text, k=key: self.text_changed.emit(k, text))
            self.field_inputs[key] = w
            layout.addWidget(w)

        # --- Conversion mode dropdown ---
        layout.addSpacing(6)
        layout.addWidget(QLabel("Конвертиране на валута:"))
        self.conv_mode_combo = QComboBox()
        for label, key in CONV_MODES:
            self.conv_mode_combo.addItem(label, key)
        self.conv_mode_combo.setCurrentIndex(0)
        self.conv_mode_combo.setToolTip("Режим на конвертиране BGN/EUR")
        self.conv_mode_combo.currentIndexChanged.connect(self._on_conv_mode_changed)
        layout.addWidget(self.conv_mode_combo)

        layout.addStretch(1)

        # --- Print and PDF buttons at bottom left ---
        btn_row = QHBoxLayout()
        self.print_btn = QToolButton()
        self.print_btn.setText("Печат")
        self.print_btn.setFixedHeight(36)
        self.print_btn.clicked.connect(self.print_clicked.emit)

        self.pdf_btn = QToolButton()
        self.pdf_btn.setText("Запази PDF")
        self.pdf_btn.setFixedHeight(36)
        self.pdf_btn.clicked.connect(self.pdf_clicked.emit)

        btn_row.addWidget(self.print_btn)
        btn_row.addWidget(self.pdf_btn)
        layout.addLayout(btn_row)

        self.setLayout(layout)

    def _on_conv_mode_changed(self, idx):
        mode = self.conv_mode_combo.itemData(idx)
        self.conversion_changed.emit(mode)

    def set_field_value(self, key, value):
        w = self.field_inputs[key]
        if isinstance(w, QTextEdit):
            w.blockSignals(True)
            w.setPlainText(value)
            w.blockSignals(False)
        else:
            w.blockSignals(True)
            w.setText(value)
            w.blockSignals(False)

    def get_field_value(self, key):
        w = self.field_inputs[key]
        if isinstance(w, QTextEdit):
            return w.toPlainText()
        else:
            return w.text()

    def set_conversion_mode(self, mode_key):
        for i in range(self.conv_mode_combo.count()):
            if self.conv_mode_combo.itemData(i) == mode_key:
                self.conv_mode_combo.setCurrentIndex(i)
                break
