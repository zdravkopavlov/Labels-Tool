# bottom_toolbar_widget.py

import json
import os
import sys

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QCheckBox, QLabel, QComboBox, QSizePolicy

def get_config_path():
    # Same logic as sheet_editor_widget.py for compatibility
    try:
        base = sys._MEIPASS  # If running as PyInstaller bundle
    except AttributeError:
        base = os.path.dirname(os.path.abspath(__file__))
    config_dir = os.path.join(base, "config")
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "settings.json")

class BottomToolbarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Layout for the bottom toolbar
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(16)

        # Checkboxes
        self.chk_show_logo = QCheckBox("Покажи лого")
        self.chk_show_bgn = QCheckBox("Покажи BGN")
        self.chk_show_eur = QCheckBox("Покажи EUR")

        # Add checkboxes to toolbar
        layout.addWidget(self.chk_show_logo)
        layout.addWidget(self.chk_show_bgn)
        layout.addWidget(self.chk_show_eur)

        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(spacer)

        # Conversion method dropdown
        self.lbl_convert = QLabel("Метод за конверсия:")
        self.cmb_convert = QComboBox()
        self.cmb_convert.addItems([
            "BGN → EUR",
            "EUR → BGN",
            "BGN ⇄ EUR",
            "Ръчно (без конверсия)"
        ])

        layout.addWidget(self.lbl_convert)
        layout.addWidget(self.cmb_convert)

        # Set the main layout
        self.setLayout(layout)

    def save_settings(self, filename=None):
        # Use shared config path if not given
        if filename is None:
            filename = get_config_path()
        settings = {
            "show_logo": self.chk_show_logo.isChecked(),
            "show_bgn": self.chk_show_bgn.isChecked(),
            "show_eur": self.chk_show_eur.isChecked(),
            "conversion_mode": self.cmb_convert.currentIndex(),
        }
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)      

    def load_settings(self, filename=None):
        if filename is None:
            filename = get_config_path()
        if not os.path.exists(filename):
            return
        with open(filename, "r", encoding="utf-8") as f:
            settings = json.load(f)
        self.chk_show_logo.setChecked(settings.get("show_logo", False))
        self.chk_show_bgn.setChecked(settings.get("show_bgn", False))
        self.chk_show_eur.setChecked(settings.get("show_eur", False))
        self.cmb_convert.setCurrentIndex(settings.get("conversion_mode", 0))          
