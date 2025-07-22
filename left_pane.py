from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit, QLineEdit, QComboBox, QHBoxLayout, QPushButton, QSpinBox, QDoubleSpinBox
)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import pyqtSignal
from field_toolbar import FieldToolbar
import sys
import os

# --- Robust resource path for PyInstaller one-folder builds and dev mode ---
def resource_path(relative_path):
    # Works for both dev and PyInstaller one-folder
    if hasattr(sys, '_MEIPASS'):
        # Should only be used for one-file!
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.path.join(base_path, relative_path)

CONV_MODES = [
    ("BGN → EUR", "bgn_to_eur"),
    ("EUR → BGN", "eur_to_bgn"),
    ("BGN ⇄ EUR", "both"),
    ("Без конверсия", "manual"),
]

FIELD_CONFIG = [
    ("main",   "Основен текст:", True),
    ("second", "Втори ред:", True),
    ("bgn",    "Цена BGN:", False),
    ("eur",    "Цена EUR:", False),
]

class LeftPaneWidget(QWidget):
    # Signals for external logic to connect to
    text_changed = pyqtSignal(str, str)  # key, value
    style_changed = pyqtSignal(str, dict)  # key, style dict
    conversion_changed = pyqtSignal(str)
    print_clicked = pyqtSignal()
    pdf_clicked = pyqtSignal()
    logo_settings_changed = pyqtSignal(dict)  # for logo controls

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        self.field_inputs = {}
        self.field_toolbars = {}

        for key, lbl, is_multiline in FIELD_CONFIG:
            layout.addWidget(QLabel(lbl))
            # Input widget
            if is_multiline:
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
            # Per-field toolbar
            tb = FieldToolbar()
            tb.style_changed.connect(lambda style, k=key: self.style_changed.emit(k, style))
            self.field_toolbars[key] = tb
            layout.addWidget(tb)

        # --- Currency conversion section ---
        layout.addSpacing(6)
        layout.addWidget(QLabel("Конвертиране на валута:"))
        self.conv_mode_combo = QComboBox()
        for label, key in CONV_MODES:
            self.conv_mode_combo.addItem(label, key)
        self.conv_mode_combo.setCurrentIndex(0)
        self.conv_mode_combo.setToolTip("Режим на конвертиране BGN/EUR")
        self.conv_mode_combo.currentIndexChanged.connect(self._on_conv_mode_changed)
        layout.addWidget(self.conv_mode_combo)

        # --- Logo controls section ---
        layout.addSpacing(16)
        layout.addWidget(QLabel("Лого:"))
        logo_row = QHBoxLayout()
        logo_row.setSpacing(6)

        self.logo_position = QComboBox()
        self.logo_position.addItems(["без лого", "долу ляво", "долу дясно"])
        self.logo_position.currentIndexChanged.connect(self._emit_logo_settings)
        logo_row.addWidget(self.logo_position)

        self.logo_size = QSpinBox()
        self.logo_size.setRange(10, 128)
        self.logo_size.setValue(24)
        self.logo_size.setSingleStep(2)
        self.logo_size.valueChanged.connect(self._emit_logo_settings)
        logo_row.addWidget(self.logo_size)

        self.logo_opacity = QDoubleSpinBox()
        self.logo_opacity.setRange(0.05, 1.0)
        self.logo_opacity.setSingleStep(0.05)
        self.logo_opacity.setValue(1.0)
        self.logo_opacity.setDecimals(2)
        self.logo_opacity.valueChanged.connect(self._emit_logo_settings)
        logo_row.addWidget(self.logo_opacity)

        layout.addLayout(logo_row)

        # --- Add fixed space above the buttons ---
        layout.addSpacing(100)

        # Print and PDF buttons at bottom left
        btn_row = QHBoxLayout()
        # Use resource_path for icons!
        self.print_btn = QLabelBtn("Печат", QIcon(resource_path("resources/print_.svg")))
        self.print_btn.clicked.connect(self.print_clicked.emit)
        self.pdf_btn = QLabelBtn("Запази PDF", QIcon(resource_path("resources/export_as_pdf.svg")))
        self.pdf_btn.clicked.connect(self.pdf_clicked.emit)
        btn_row.addWidget(self.print_btn)
        btn_row.addWidget(self.pdf_btn)
        layout.addLayout(btn_row)

        self.setLayout(layout)

    def _emit_logo_settings(self):
        logo_dict = {
            "position": self.logo_position.currentText(),
            "size": self.logo_size.value(),
            "opacity": float(self.logo_opacity.value())
        }
        self.logo_settings_changed.emit(logo_dict)

    def _on_conv_mode_changed(self, idx):
        mode = self.conv_mode_combo.itemData(idx)
        self.conversion_changed.emit(mode)

    def set_field_value(self, key, value):
        w = self.field_inputs[key]
        if hasattr(w, "blockSignals"):
            w.blockSignals(True)
        if isinstance(w, QTextEdit):
            w.setPlainText(value)
        else:
            w.setText(value)
        if hasattr(w, "blockSignals"):
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

    def set_toolbar_state(self, key, style_dict):
        tb = self.field_toolbars.get(key)
        if tb:
            tb.set_toolbar_state(style_dict)

# --- Helper: QPushButton with Icon and text, to look like original ---
from PyQt5.QtWidgets import QPushButton
class QLabelBtn(QPushButton):
    def __init__(self, label, icon=QIcon(), parent=None):
        super().__init__(label, parent)
        if icon:
            self.setIcon(icon)
        self.setMinimumHeight(36)
        self.setMaximumWidth(120)
        self.setStyleSheet("font-size:15px; font-weight:bold;")
