# bottom_toolbar_widget.py

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QCheckBox, QLabel, QComboBox, QSizePolicy

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
