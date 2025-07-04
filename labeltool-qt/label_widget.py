from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QLabel, QHBoxLayout
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFont

class LabelWidget(QWidget):
    changed = pyqtSignal()

    def __init__(self, name="", item_type="", price="", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 8, 10, 8)
        self.setLayout(layout)
        self.setFixedSize(167, 300)  # Sticker aspect

        # --- Item Name ---
        name_label = QLabel("Item Name:")
        name_label.setFont(QFont("Arial", 11, QFont.Bold))
        layout.addWidget(name_label)

        self.name_edit = QLineEdit(name)
        self.name_edit.setFont(QFont("Arial", 13))
        self.name_edit.setPlaceholderText("Type name...")
        layout.addWidget(self.name_edit)

        # --- Item Type ---
        type_label = QLabel("Type:")
        type_label.setFont(QFont("Arial", 10))
        layout.addWidget(type_label)

        self.type_edit = QLineEdit(item_type)
        self.type_edit.setFont(QFont("Arial", 11))
        self.type_edit.setPlaceholderText("Type...")
        layout.addWidget(self.type_edit)

        # --- Price ---
        price_layout = QHBoxLayout()
        price_label = QLabel("Price:")
        price_label.setFont(QFont("Arial", 10))
        self.price_edit = QLineEdit(price)
        self.price_edit.setFont(QFont("Arial", 11))
        self.price_edit.setPlaceholderText("0.00")
        self.price_edit.setMaximumWidth(60)
        price_layout.addWidget(price_label)
        price_layout.addWidget(self.price_edit)
        layout.addLayout(price_layout)

        # Connect changes
        self.name_edit.textChanged.connect(self.changed.emit)
        self.type_edit.textChanged.connect(self.changed.emit)
        self.price_edit.textChanged.connect(self.changed.emit)

        self.setStyleSheet(
            "background: #ffe082; border: 2px solid #ffa000; border-radius: 10px; margin: 4px;"
        )

    def get_name(self):
        return self.name_edit.text()

    def get_type(self):
        return self.type_edit.text()

    def get_price(self):
        return self.price_edit.text()
