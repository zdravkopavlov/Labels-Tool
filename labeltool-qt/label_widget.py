from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QLineEdit, QLabel, QMenu, QAction
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont, QPalette, QColor, QPixmap, QPainter, QPen
from currency_manager import CurrencyManager
from currency_manager import QObject
from context_menu import make_label_context_menu

PREDEFINED_UNITS = ["", "бр.", "м", "м²", "м³", "кг.", "л."]

class DashedUnderlineLabel(QLabel):
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        pen = QPen(QColor("#cccccc"))
        pen.setWidth(1)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        y = self.height()
        painter.drawLine(0, y, self.width(), y)
        painter.end()

class LabelWidget(QWidget):
    changed = pyqtSignal()
    clicked = pyqtSignal(object, object)
    _copied_content = None

    def __init__(self,
                 name="",
                 subtype="",
                 price_bgn="",
                 price_eur="",
                 unit_eur="",
                 show_logo=False,
                 parent=None):
        super().__init__(parent)
        self._selected = False
        self._hovered  = False
        self._show_logo = show_logo

        # -- Layout & sizing --
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 4, 0, 0)
        outer.setSpacing(8)
        self.setLayout(outer)
        self.setFixedSize(240, 120)

        # -- Logo placeholder --
        self.logo_label = QLabel()
        self.logo_label.setFixedSize(40, 40)
        pm = QPixmap(40, 40)
        pm.fill(QColor("#70bfff"))
        self.logo_label.setPixmap(pm)
        self.logo_label.setVisible(self._show_logo)
        outer.addWidget(self.logo_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)

        # -- Content stack --
        content = QWidget()
        vlay = QVBoxLayout(content)
        vlay.setSpacing(2)
        vlay.setContentsMargins(4, 4, 4, 4)
        outer.addWidget(content, stretch=1)

        borderless = "border: none; background: #eeeeee;"
        dashed = "border: 1px dashed #bbbbbb; background: #fff;"

        # Name
        self.name_edit = QLineEdit(name)
        self.name_edit.setFont(QFont("Arial", 16, QFont.Bold))
        self.name_edit.setPlaceholderText("Артикул")
        self.name_edit.setAlignment(Qt.AlignCenter)
        self._set_placeholder_bright(self.name_edit)
        self.name_edit.setStyleSheet(dashed)
        vlay.addWidget(self.name_edit)

        # Subtype
        self.subtype_edit = QLineEdit(subtype)
        f_italic = QFont("Arial", 12); f_italic.setItalic(True)
        self.subtype_edit.setFont(f_italic)
        self.subtype_edit.setPlaceholderText("(вид или марка)")
        self.subtype_edit.setAlignment(Qt.AlignCenter)
        self._set_placeholder_bright(self.subtype_edit)
        self.subtype_edit.setStyleSheet(dashed)
        vlay.addWidget(self.subtype_edit)

        # BGN price
        self.price_bgn_edit = QLineEdit(price_bgn)
        self.price_bgn_edit.setFont(QFont("Arial", 16, QFont.Bold))
        self._set_placeholder_bright(self.price_bgn_edit)
        self.price_bgn_edit.setAlignment(Qt.AlignCenter)
        self.price_bgn_edit.setStyleSheet(dashed)
        vlay.addWidget(self.price_bgn_edit)

        # EUR price
        self.price_eur_edit = QLineEdit(price_eur)
        self.price_eur_edit.setFont(QFont("Arial", 16, QFont.Bold))
        self._set_placeholder_bright(self.price_eur_edit)
        self.price_eur_edit.setAlignment(Qt.AlignCenter)
        self.price_eur_edit.setStyleSheet(dashed)
        vlay.addWidget(self.price_eur_edit)

        # Unit label
        self.unit_eur_label = DashedUnderlineLabel(self._format_unit(unit_eur))
        ufont = QFont("Arial", 10); ufont.setItalic(True)
        self.unit_eur_label.setFont(ufont)
        self.unit_eur_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.unit_eur_label.setStyleSheet("border: none; background: transparent; color: #555;")
        vlay.addWidget(self.unit_eur_label)

        # Context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        # Visual style
        self.update_style()

        # Hook change notifications
        for fld in (self.name_edit, self.subtype_edit,
                    self.price_bgn_edit, self.price_eur_edit):
            fld.textChanged.connect(self.changed.emit)

        self.currency_manager = CurrencyManager(
            bgn_edit=self.price_bgn_edit,
            eur_edit=self.price_eur_edit,
            rate=1.95583,
            convert_on="keystroke"
)

    def _set_placeholder_bright(self, w):
        pal = w.palette()
        pal.setColor(QPalette.PlaceholderText, QColor("#cccccc"))
        w.setPalette(pal)

    def _format_unit(self, u):
        u = (u or "").strip()
        return f"/ {u}" if u else ""

    def _show_context_menu(self, pos):
        sw = self.parent()
        while sw and not hasattr(sw, "selection"):
            sw = sw.parent()
        if not sw:
            return
        menu = make_label_context_menu(self, sw)
        menu.exec_(self.mapToGlobal(pos))

    def _copy(self):
        LabelWidget._copied_content = (
            self.name_edit.text(),
            self.subtype_edit.text(),
            self.price_bgn_edit.text(),
            self.price_eur_edit.text(),
            self.get_unit_eur()  # Always raw value!
        )

    def _paste(self):
        data = LabelWidget._copied_content
        if not data: return
        for txt, setter in (
            (data[0], self.set_name),
            (data[1], self.set_type),
            (data[2], self.set_price),
            (data[3], self.set_price_eur),
            (data[4], self.set_unit_eur_text)
        ):
            setter(txt)

    def clear_fields(self):
        for txt, setter in (
            ("", self.set_name),
            ("", self.set_type),
            ("", self.set_price),
            ("", self.set_price_eur),
            ("", self.set_unit_eur_text)
        ):
            setter(txt)

    def set_unit_eur(self, v):
        self.set_unit_eur_text(v)

    def set_logo(self, show: bool):
        self._show_logo = show
        self.logo_label.setVisible(show)
        self.update_style()

    def get_export_data(self):
        return {
            "name":        self.name_edit.text().strip(),
            "type":        self.subtype_edit.text().strip(),
            "price_bgn":   self.price_bgn_edit.text().replace(" лв.","").strip(),
            "price_eur":   self.price_eur_edit.text().lstrip("€").strip(),
            "unit_eur":    self.get_unit_eur().strip(),  # Always raw
            "logo":        self._show_logo,
        }

    def get_unit_eur(self):
        t = self.unit_eur_label.text().strip()
        # Remove a single leading "/ " if present
        return t[2:] if t.startswith("/ ") else t

    def set_name(self, v): self.name_edit.setText(v)
    def set_type(self, v): self.subtype_edit.setText(v)

    def set_price(self, v):
        v = str(v).strip()
        if v and not v.endswith(" лв."):
            v = v + " лв."
        self.price_bgn_edit.setText(v)

    def set_price_eur(self, v):
        v = str(v).strip()
        if v and not v.startswith("€"):
            v = "€" + v
        self.price_eur_edit.setText(v)

    def set_unit_eur_text(self, v):
        v = (v or "").strip()
        self.unit_eur_label.setText(self._format_unit(v))
        self.changed.emit()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit(self, e)
        super().mousePressEvent(e)

    def enterEvent(self, e):
        self._hovered = True
        self.update_style()
        super().enterEvent(e)
    def leaveEvent(self, e):
        self._hovered = False
        self.update_style()
        super().leaveEvent(e)

    def set_selected(self, sel: bool):
        self._selected = sel
        self.update_style()

    def update_style(self):
        border = "#006eff" if self._selected else "#888888"
        w = "3px" if (self._selected or self._hovered) else "1px"
        self.setStyleSheet(f"QWidget {{ background: #eeeeee; border: {w} solid {border}; border-radius: 7px; }}")
