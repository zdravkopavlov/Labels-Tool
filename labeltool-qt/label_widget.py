from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QLabel, QMenu, QAction
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont, QPalette, QColor, QPixmap, QPainter, QPen

PREDEFINED_UNITS = [
    "", "бр.", "м", "м²", "м³", "кг.", "л."
]

class DashedUnderlineLabel(QLabel):
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        pen = QPen(QColor("#cccccc"))
        pen.setWidth(1)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        y = self.height() - 2
        painter.drawLine(0, y, self.width(), y)
        painter.end()

class LabelWidget(QWidget):
    changed = pyqtSignal()
    clicked = pyqtSignal(object, object)

    _copied_content = None

    def __init__(self, name="", subtype="", price_bgn="", price_eur="", unit_eur="", show_logo=False, parent=None):
        super().__init__(parent)
        self._selected = False
        self._hovered = False
        self._show_logo = show_logo

        self._bgn_suffix = " лв."
        self._eur_suffix = " €"

        outer_layout = QHBoxLayout()
        outer_layout.setContentsMargins(8, 14, 8, 8)
        outer_layout.setSpacing(8)
        self.setLayout(outer_layout)
        self.setFixedSize(240, 160)

        self.logo_label = QLabel()
        self.logo_label.setFixedSize(40, 40)
        logo_pixmap = QPixmap(40, 40)
        logo_pixmap.fill(QColor("#70bfff"))
        self.logo_label.setPixmap(logo_pixmap)
        self.logo_label.setVisible(self._show_logo)
        outer_layout.addWidget(self.logo_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(2)
        content_layout.setContentsMargins(4, 4, 4, 4)
        outer_layout.addWidget(content_widget, stretch=1)

        borderless = "border: none; background: #fff;"

        self.name_edit = QLineEdit(name)
        self.name_edit.setFont(QFont("Arial", 13, QFont.Bold))
        self.name_edit.setPlaceholderText("Артикул")
        self.name_edit.setAlignment(Qt.AlignCenter)
        self._set_placeholder_bright(self.name_edit)
        self.name_edit.setStyleSheet(borderless)
        content_layout.addWidget(self.name_edit)

        self.subtype_edit = QLineEdit(subtype)
        font_italic = QFont("Arial", 10)
        font_italic.setItalic(True)
        self.subtype_edit.setFont(font_italic)
        self.subtype_edit.setPlaceholderText("(вид или марка)")
        self.subtype_edit.setAlignment(Qt.AlignCenter)
        self._set_placeholder_bright(self.subtype_edit)
        self.subtype_edit.setStyleSheet(borderless)
        content_layout.addWidget(self.subtype_edit)

        self.price_bgn_edit = QLineEdit()
        self.price_bgn_edit.setFont(QFont("Arial", 14, QFont.Bold))
        self.price_bgn_edit.setPlaceholderText("0.00 лв.")
        self._set_placeholder_bright(self.price_bgn_edit)
        self.price_bgn_edit.setStyleSheet(borderless)
        self.price_bgn_edit.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.price_bgn_edit)

        self.price_eur_edit = QLineEdit()
        self.price_eur_edit.setFont(QFont("Arial", 14, QFont.Bold))
        self.price_eur_edit.setPlaceholderText("0.00 €")
        self._set_placeholder_bright(self.price_eur_edit)
        self.price_eur_edit.setStyleSheet(borderless)
        self.price_eur_edit.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.price_eur_edit)

        # ---- Units label: separate row, right-aligned, dashed underline only, NO border, NO color
        self.unit_eur_label = DashedUnderlineLabel(self._format_unit(unit_eur))
        unit_font = QFont("Arial", 10)
        unit_font.setItalic(True)
        self.unit_eur_label.setFont(unit_font)
        self.unit_eur_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.unit_eur_label.setStyleSheet("border: none; background: transparent; color: #555;")
        content_layout.addWidget(self.unit_eur_label)

        self.price_bgn_edit.focusInEvent = self._make_focusin_handler(self.price_bgn_edit, self._bgn_suffix)
        self.price_bgn_edit.focusOutEvent = self._make_focusout_handler(self.price_bgn_edit, self._bgn_suffix)
        self.price_eur_edit.focusInEvent = self._make_focusin_handler(self.price_eur_edit, self._eur_suffix)
        self.price_eur_edit.focusOutEvent = self._make_focusout_handler(self.price_eur_edit, self._eur_suffix)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        self.update_style()
        for field in [self.name_edit, self.subtype_edit, self.price_bgn_edit, self.price_eur_edit]:
            field.textChanged.connect(self.changed.emit)

    def _set_placeholder_bright(self, widget):
        pal = widget.palette()
        pal.setColor(QPalette.PlaceholderText, QColor("#cccccc"))
        widget.setPalette(pal)

    def _format_unit(self, unit):
        if unit and unit.strip():
            return f"/ {unit.strip()}"
        return ""

    def _make_focusin_handler(self, field, suffix):
        def handler(event):
            txt = field.text()
            if suffix and txt.endswith(suffix):
                field.setText(txt[:-len(suffix)])
            field.setAlignment(Qt.AlignCenter)
            QLineEdit.focusInEvent(field, event)
        return handler

    def _make_focusout_handler(self, field, suffix):
        def handler(event):
            txt = field.text().strip()
            if suffix and txt and not txt.endswith(suffix):
                txt = txt.replace(" лв.", "").replace(" €", "")
                field.setText(txt + suffix)
            field.setAlignment(Qt.AlignCenter)
            QLineEdit.focusOutEvent(field, event)
        return handler

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self, event)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        self._hovered = True
        self.setCursor(Qt.PointingHandCursor)
        self.update_style()

    def leaveEvent(self, event):
        self._hovered = False
        self.setCursor(Qt.ArrowCursor)
        self.update_style()

    def set_selected(self, sel):
        self._selected = sel
        self.update_style()

    def update_style(self):
        border = "#008cff" if self._selected else "#888888"
        border_w = "3px" if (self._selected or self._hovered) else "1px"
        self.setStyleSheet(
            f"QWidget {{ background: #ffffff; border: {border_w} solid {border}; border-radius: 7px; }}"
        )

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background: #fff; color: #111; }
            QMenu::item:selected { background: #008cff; color: #fff; }
        """)
        copy_act = QAction("Копиране", self)
        copy_act.triggered.connect(self._copy)
        menu.addAction(copy_act)
        paste_act = QAction("Поставяне", self)
        paste_act.triggered.connect(self._paste)
        menu.addAction(paste_act)
        menu.addSeparator()

        for unit in PREDEFINED_UNITS:
            display_unit = self._format_unit(unit) if unit else '""'
            act = QAction(display_unit, self)
            act.triggered.connect(lambda checked, u=unit: self.set_unit_eur_all(u))
            menu.addAction(act)
        menu.addSeparator()

        clear_act = QAction("Изчисти", self)
        clear_act.triggered.connect(self.clear_fields)
        menu.addAction(clear_act)
        menu.exec_(self.mapToGlobal(pos))

    def _copy(self):
        LabelWidget._copied_content = (
            self.name_edit.text(), self.subtype_edit.text(),
            self.price_bgn_edit.text(), self.price_eur_edit.text(),
            self.unit_eur_label.text()
        )

    def _paste(self):
        parent = self.parent()
        while parent and not hasattr(parent, 'labels'):
            parent = parent.parent()
        if parent and hasattr(parent, 'selected_indexes'):
            for idx in parent.selected_indexes:
                label = parent.labels[idx]
                if LabelWidget._copied_content:
                    name, subtype, price_bgn, price_eur, unit_eur = LabelWidget._copied_content
                    label.name_edit.setText(name)
                    label.subtype_edit.setText(subtype)
                    label.price_bgn_edit.setText(price_bgn)
                    label.price_eur_edit.setText(price_eur)
                    label.set_unit_eur(unit_eur)
        else:
            if LabelWidget._copied_content:
                name, subtype, price_bgn, price_eur, unit_eur = LabelWidget._copied_content
                self.name_edit.setText(name)
                self.subtype_edit.setText(subtype)
                self.price_bgn_edit.setText(price_bgn)
                self.price_eur_edit.setText(price_eur)
                self.set_unit_eur(unit_eur)

    def clear_fields(self):
        parent = self.parent()
        while parent and not hasattr(parent, 'labels'):
            parent = parent.parent()
        if parent and hasattr(parent, 'selected_indexes'):
            for idx in parent.selected_indexes:
                label = parent.labels[idx]
                label.name_edit.clear()
                label.subtype_edit.clear()
                label.price_bgn_edit.clear()
                label.price_eur_edit.clear()
                label.set_unit_eur("")
        else:
            self.name_edit.clear()
            self.subtype_edit.clear()
            self.price_bgn_edit.clear()
            self.price_eur_edit.clear()
            self.set_unit_eur("")

    def set_unit_eur(self, unit):
        self.unit_eur_label.setText(self._format_unit(unit))
        self.changed.emit()

    def set_unit_eur_all(self, unit):
        parent = self.parent()
        while parent and not hasattr(parent, 'labels'):
            parent = parent.parent()
        if parent and hasattr(parent, 'selected_indexes'):
            for idx in parent.selected_indexes:
                label = parent.labels[idx]
                label.set_unit_eur(unit)
        else:
            self.set_unit_eur(unit)

    def set_logo(self, show_logo: bool):
        self._show_logo = show_logo
        self.logo_label.setVisible(show_logo)
        self.update_style()

    def get_name(self):
        return self.name_edit.text()
    def set_name(self, value):
        self.name_edit.setText(value)
    def get_type(self):
        return self.subtype_edit.text()
    def set_type(self, value):
        self.subtype_edit.setText(value)
    def get_price(self):
        val = self.price_bgn_edit.text().strip()
        return val[:-len(self._bgn_suffix)] if val.endswith(self._bgn_suffix) else val
    def set_price(self, value):
        self.price_bgn_edit.setText(value)
    def get_price_eur(self):
        val = self.price_eur_edit.text().strip()
        return val[:-len(self._eur_suffix)] if val.endswith(self._eur_suffix) else val
    def set_price_eur(self, value):
        self.price_eur_edit.setText(value)
    def get_unit_eur(self):
        txt = self.unit_eur_label.text().strip()
        return txt[2:] if txt.startswith("/ ") else txt
    def set_unit_eur_text(self, value):
        self.set_unit_eur(value)
    def get_logo(self):
        return self._show_logo
    def get_export_data(self):
        return {
            "name": self.get_name(),
            "type": self.get_type(),
            "price_bgn": self.get_price(),
            "price_eur": self.get_price_eur(),
            "unit_eur": self.get_unit_eur(),
            "logo": self.get_logo(),
        }
