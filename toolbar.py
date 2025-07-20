from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QComboBox, QToolButton, QButtonGroup,
    QGridLayout, QMenu, QColorDialog, QWidgetAction
)
from PyQt5.QtGui import QFont, QIcon, QColor
from PyQt5.QtCore import pyqtSignal, Qt
import os

PALETTE_COLORS = [
    "#ffffff", "#9F9F9F", "#575757", "#000000", "#E01300", "#00DD29", "#00A0FF",
]

def resource_path(relpath):
    folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
    p = os.path.join(folder, relpath)
    if os.path.exists(p):
        return p
    return relpath

class ToolbarWidget(QWidget):
    font_changed = pyqtSignal(str)
    size_changed = pyqtSignal(int)
    bold_changed = pyqtSignal(bool)
    italic_changed = pyqtSignal(bool)
    align_changed = pyqtSignal(int)
    font_color_changed = pyqtSignal(str)
    bg_color_changed = pyqtSignal(str)

    def __init__(self, font_list, parent=None):
        super().__init__(parent)
        self.font_list = font_list
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)

        # Font selector
        self.font_combo = QComboBox()
        self.font_combo.addItems(self.font_list)
        self.font_combo.currentTextChanged.connect(self.font_changed)
        layout.addWidget(self.font_combo)

        # Font size
        self.font_size_minus = QToolButton(); self.font_size_minus.setText("–")
        self.font_size_plus = QToolButton(); self.font_size_plus.setText("+")
        self.font_size_disp = QLabel("15")
        self.font_size_minus.clicked.connect(lambda: self._emit_size(-1))
        self.font_size_plus.clicked.connect(lambda: self._emit_size(+1))
        layout.addWidget(self.font_size_minus)
        layout.addWidget(self.font_size_disp)
        layout.addWidget(self.font_size_plus)

        # Bold/Italic
        self.bold_btn = QToolButton(); self.bold_btn.setText("B"); self.bold_btn.setCheckable(True)
        self.bold_btn.setStyleSheet("font-weight: bold;")
        self.bold_btn.toggled.connect(self.bold_changed)
        self.italic_btn = QToolButton(); self.italic_btn.setText("I"); self.italic_btn.setCheckable(True)
        self.italic_btn.setStyleSheet("font-style: italic;")
        self.italic_btn.toggled.connect(self.italic_changed)
        layout.addWidget(self.bold_btn)
        layout.addWidget(self.italic_btn)

        # Alignment buttons
        self.align_group = QButtonGroup(self)
        self.align_left = QToolButton(); self.align_left.setCheckable(True)
        self.align_left.setIcon(QIcon(resource_path("format_align_left.svg")))
        self.align_left.setToolTip("Подравняване вляво")
        self.align_center = QToolButton(); self.align_center.setCheckable(True)
        self.align_center.setIcon(QIcon(resource_path("format_align_center.svg")))
        self.align_center.setToolTip("Центрирано")
        self.align_right = QToolButton(); self.align_right.setCheckable(True)
        self.align_right.setIcon(QIcon(resource_path("format_align_right.svg")))
        self.align_right.setToolTip("Подравняване вдясно")
        self.align_group.addButton(self.align_left, Qt.AlignLeft)
        self.align_group.addButton(self.align_center, Qt.AlignCenter)
        self.align_group.addButton(self.align_right, Qt.AlignRight)
        self.align_left.toggled.connect(lambda checked: self._emit_align(Qt.AlignLeft, checked))
        self.align_center.toggled.connect(lambda checked: self._emit_align(Qt.AlignCenter, checked))
        self.align_right.toggled.connect(lambda checked: self._emit_align(Qt.AlignRight, checked))
        layout.addWidget(self.align_left)
        layout.addWidget(self.align_center)
        layout.addWidget(self.align_right)

        # Font color
        self.font_color_btn = QToolButton()
        self.font_color_btn.setFixedSize(26, 26)
        self.font_color_btn.setToolTip("Цвят на текста")
        self.font_color_btn.clicked.connect(self._show_font_color_palette)
        layout.addWidget(QLabel("Текст:"))
        layout.addWidget(self.font_color_btn)

        # BG color
        self.bg_color_btn = QToolButton()
        self.bg_color_btn.setFixedSize(26, 26)
        self.bg_color_btn.setToolTip("Цвят на фона")
        self.bg_color_btn.clicked.connect(self._show_bg_color_palette)
        layout.addWidget(QLabel("Фон:"))
        layout.addWidget(self.bg_color_btn)

        layout.addStretch(1)
        self.setLayout(layout)

    def _emit_size(self, delta):
        try:
            val = int(self.font_size_disp.text())
        except Exception:
            val = 12
        new_val = max(6, min(72, val + delta))
        self.font_size_disp.setText(str(new_val))
        self.size_changed.emit(new_val)

    def _emit_align(self, align, checked):
        if checked:
            self.align_changed.emit(align)

    def _show_font_color_palette(self):
        self._show_color_palette("font_color")

    def _show_bg_color_palette(self):
        self._show_color_palette("bg_color")

    def _show_color_palette(self, which):
        menu = QMenu(self)
        swatch_row = QWidget()
        layout = QGridLayout(swatch_row)
        layout.setSpacing(2)
        for i, color in enumerate(PALETTE_COLORS):
            btn = QToolButton()
            btn.setFixedSize(26, 26)
            btn.setStyleSheet(f"background:{color}; border:1.5px solid #888; border-radius:6px;")
            btn.clicked.connect(lambda _, c=color: self._color_selected(which, c))
            btn.clicked.connect(menu.close)
            layout.addWidget(btn, i // 7, i % 7)
        menu.setMinimumWidth(30 * len(PALETTE_COLORS))
        action = QWidgetAction(menu)
        action.setDefaultWidget(swatch_row)
        menu.addAction(action)
        if which == "font_color":
            menu.exec_(self.font_color_btn.mapToGlobal(self.font_color_btn.rect().bottomLeft()))
        else:
            menu.exec_(self.bg_color_btn.mapToGlobal(self.bg_color_btn.rect().bottomLeft()))

    def _color_selected(self, which, color):
        if which == "font_color":
            self.font_color_btn.setStyleSheet(f"background:{color}; border:2.5px solid #222; border-radius:4px;")
            self.font_color_changed.emit(color)
        else:
            self.bg_color_btn.setStyleSheet(f"background:{color}; border:2.5px solid #222; border-radius:4px;")
            self.bg_color_changed.emit(color)

    def set_toolbar_state(self, font=None, size=None, bold=None, italic=None, align=None, font_color=None, bg_color=None):
        # Safely set toolbar to match the selected field
        if font:
            self.font_combo.setCurrentText(font)
        if size:
            self.font_size_disp.setText(str(size))
        if bold is not None:
            self.bold_btn.setChecked(bold)
        if italic is not None:
            self.italic_btn.setChecked(italic)
        if align == Qt.AlignLeft:
            self.align_left.setChecked(True)
        elif align == Qt.AlignCenter:
            self.align_center.setChecked(True)
        elif align == Qt.AlignRight:
            self.align_right.setChecked(True)
        if font_color:
            self.font_color_btn.setStyleSheet(f"background:{font_color}; border:2.5px solid #222; border-radius:4px;")
        if bg_color:
            self.bg_color_btn.setStyleSheet(f"background:{bg_color}; border:2.5px solid #222; border-radius:4px;")

