from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QLabel, QHBoxLayout, QGridLayout
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont, QPalette, QColor

class LabelWidget(QWidget):
    changed = pyqtSignal()
    clicked = pyqtSignal(object, object)  # self, event

    def __init__(self, name="", subtype="", price_bgn="", unit_bgn="/m²", price_eur="", unit_eur="/m²", parent=None):
        super().__init__(parent)
        self._selected = False
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(2)
        self.setLayout(main_layout)
        self.setFixedSize(167, 100)

        self.bg_widget = QWidget(self)
        self.bg_widget.setStyleSheet(
            """
            background: #ffffff;
            border: 1px solid #888888;
            border-radius: 6px;
            """
        )
        grid = QGridLayout()
        grid.setContentsMargins(6, 6, 6, 6)
        grid.setSpacing(2)
        self.bg_widget.setLayout(grid)
        main_layout.addWidget(self.bg_widget)

        # Utility for bright placeholder text
        def set_placeholder_bright(widget):
            pal = widget.palette()
            pal.setColor(QPalette.PlaceholderText, QColor("#dddddd"))
            widget.setPalette(pal)

        border_css = "border: 0.5px dashed #999999; border-radius: 4px;"

        # Title (large, bold)
        self.name_edit = QLineEdit(name)
        self.name_edit.setFont(QFont("Arial", 14, QFont.Bold))
        self.name_edit.setPlaceholderText("Артикул")
        self.name_edit.setAlignment(Qt.AlignCenter)
        self.name_edit.setStyleSheet(border_css)
        set_placeholder_bright(self.name_edit)
        grid.addWidget(self.name_edit, 0, 0, 1, 4)

        # Subtype/brand (italic, smaller)
        self.subtype_edit = QLineEdit(subtype)
        font_italic = QFont("Arial", 11)
        font_italic.setItalic(True)
        self.subtype_edit.setFont(font_italic)
        self.subtype_edit.setPlaceholderText("(вид или марка)")
        self.subtype_edit.setAlignment(Qt.AlignCenter)
        self.subtype_edit.setStyleSheet(border_css)
        set_placeholder_bright(self.subtype_edit)
        grid.addWidget(self.subtype_edit, 1, 0, 1, 4)

        # Price BGN row
        self.price_bgn_edit = QLineEdit(price_bgn)
        self.price_bgn_edit.setFont(QFont("Arial", 15, QFont.Bold))
        self.price_bgn_edit.setPlaceholderText("0.00лв.")
        self.price_bgn_edit.setAlignment(Qt.AlignRight)
        self.price_bgn_edit.setStyleSheet(border_css)
        set_placeholder_bright(self.price_bgn_edit)
        grid.addWidget(self.price_bgn_edit, 2, 0, 1, 2)

        self.unit_bgn_edit = QLineEdit(unit_bgn)
        self.unit_bgn_edit.setFont(QFont("Arial", 11))
        self.unit_bgn_edit.setPlaceholderText("/m²")
        self.unit_bgn_edit.setAlignment(Qt.AlignLeft)
        self.unit_bgn_edit.setStyleSheet(border_css)
        set_placeholder_bright(self.unit_bgn_edit)
        grid.addWidget(self.unit_bgn_edit, 2, 2, 1, 2)

        # Price EUR row
        self.price_eur_edit = QLineEdit(price_eur)
        self.price_eur_edit.setFont(QFont("Arial", 15, QFont.Bold))
        self.price_eur_edit.setPlaceholderText("€0.00")
        self.price_eur_edit.setAlignment(Qt.AlignRight)
        self.price_eur_edit.setStyleSheet(border_css)
        set_placeholder_bright(self.price_eur_edit)
        grid.addWidget(self.price_eur_edit, 3, 0, 1, 2)

        self.unit_eur_edit = QLineEdit(unit_eur)
        self.unit_eur_edit.setFont(QFont("Arial", 11))
        self.unit_eur_edit.setPlaceholderText("/m²")
        self.unit_eur_edit.setAlignment(Qt.AlignLeft)
        self.unit_eur_edit.setStyleSheet(border_css)
        set_placeholder_bright(self.unit_eur_edit)
        grid.addWidget(self.unit_eur_edit, 3, 2, 1, 2)

        grid.setRowStretch(4, 1)

        # Connect signals
        for edit in [self.name_edit, self.subtype_edit, self.price_bgn_edit, self.unit_bgn_edit, self.price_eur_edit, self.unit_eur_edit]:
            edit.textChanged.connect(self.changed.emit)

        self.update_style()

    def mousePressEvent(self, event):
        self.clicked.emit(self, event)

    def set_selected(self, sel):
        self._selected = sel
        self.update_style()

    def update_style(self):
        if self._selected:
            outline = "#008cff"
            outline_width = "3px"
        else:
            outline = "#888888"
            outline_width = "1px"
        self.bg_widget.setStyleSheet(
            f"""
            background: #ffffff;
            border: {outline_width} solid {outline};
            border-radius: 6px;
            """
        )

    def get_name(self):
        return self.name_edit.text()

    def set_name(self, value):
        self.name_edit.setText(value)

    def get_type(self):
        return self.subtype_edit.text()

    def set_type(self, value):
        self.subtype_edit.setText(value)

    def get_price(self):
        return self.price_bgn_edit.text()

    def set_price(self, value):
        self.price_bgn_edit.setText(value)

    def get_price_eur(self):
        return self.price_eur_edit.text()

    def set_price_eur(self, value):
        self.price_eur_edit.setText(value)

    def get_unit_bgn(self):
        return self.unit_bgn_edit.text()

    def set_unit_bgn(self, value):
        self.unit_bgn_edit.setText(value)

    def get_unit_eur(self):
        return self.unit_eur_edit.text()

    def set_unit_eur(self, value):
        self.unit_eur_edit.setText(value)
