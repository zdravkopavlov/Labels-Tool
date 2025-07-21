# field_toolbar.py

import os
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, QSpinBox, QToolButton, QMenu, QColorDialog, QWidgetAction, QGridLayout
)
from PyQt5.QtGui import QFontDatabase, QIcon, QColor
from PyQt5.QtCore import Qt, pyqtSignal

RESOURCE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")

def icon(name):
    path = os.path.join(RESOURCE_PATH, name)
    return QIcon(path) if os.path.exists(path) else QIcon()

SWATCH_COLORS = [
    "#000000", "#575757", "#9F9F9F", "#FFFFFF",
    "#E01300", "#00DD29", "#00A0FF",
    "#FFF000", "#FF8800", "#B700FF", "#FF00D2", "#00D9D9",
    "#FFB6C1", "#A52A2A", "#228B22", "#8B0000"
]

class FieldToolbar(QWidget):
    style_changed = pyqtSignal(dict)

    def __init__(self, fonts=None, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        self.fonts = fonts or QFontDatabase().families()

        # Font family
        self.font_combo = QComboBox()
        self.font_combo.addItems(self.fonts)
        self.font_combo.setMaximumWidth(110)
        layout.addWidget(self.font_combo)

        # Font size
        self.font_size = QSpinBox()
        self.font_size.setRange(6, 100)
        self.font_size.setValue(15)
        self.font_size.setMaximumWidth(52)
        layout.addWidget(self.font_size)

        # Bold/italic
        self.bold_btn = QToolButton()
        self.bold_btn.setCheckable(True)
        self.bold_btn.setIcon(icon("format_bold.svg"))
        self.bold_btn.setToolTip("Удебелен")
        layout.addWidget(self.bold_btn)

        self.italic_btn = QToolButton()
        self.italic_btn.setCheckable(True)
        self.italic_btn.setIcon(icon("format_italic.svg"))
        self.italic_btn.setToolTip("Курсив")
        layout.addWidget(self.italic_btn)

        # Alignment
        self.align_left = QToolButton()
        self.align_left.setCheckable(True)
        self.align_left.setIcon(icon("format_align_left.svg"))
        self.align_left.setToolTip("Подравняване вляво")
        self.align_center = QToolButton()
        self.align_center.setCheckable(True)
        self.align_center.setIcon(icon("format_align_center.svg"))
        self.align_center.setToolTip("Центрирано")
        self.align_right = QToolButton()
        self.align_right.setCheckable(True)
        self.align_right.setIcon(icon("format_align_right.svg"))
        self.align_right.setToolTip("Подравняване вдясно")

        self.align_group = [self.align_left, self.align_center, self.align_right]
        layout.addWidget(self.align_left)
        layout.addWidget(self.align_center)
        layout.addWidget(self.align_right)

        # Text color button
        self.text_color_btn = QToolButton()
        self.text_color_btn.setIcon(icon("format_color_text.svg"))
        self.text_color_btn.setToolTip("Цвят на текста")
        layout.addWidget(self.text_color_btn)

        # Background color button
        self.bg_color_btn = QToolButton()
        self.bg_color_btn.setIcon(icon("format_ink_highlighter.svg"))
        self.bg_color_btn.setToolTip("Цвят на фона")
        layout.addWidget(self.bg_color_btn)

        layout.addStretch(1)
        self.setLayout(layout)

        # Store state
        self._state = {
            "font": self.font_combo.currentText(),
            "size": self.font_size.value(),
            "bold": self.bold_btn.isChecked(),
            "italic": self.italic_btn.isChecked(),
            "align": Qt.AlignLeft,
            "font_color": "#222",
            "bg_color": "#fff"
        }
        self._block_signals = False

        # Connect signals
        self.font_combo.currentTextChanged.connect(self._emit_style)
        self.font_size.valueChanged.connect(self._emit_style)
        self.bold_btn.toggled.connect(self._emit_style)
        self.italic_btn.toggled.connect(self._emit_style)
        self.align_left.clicked.connect(lambda: self._set_align(Qt.AlignLeft))
        self.align_center.clicked.connect(lambda: self._set_align(Qt.AlignCenter))
        self.align_right.clicked.connect(lambda: self._set_align(Qt.AlignRight))
        self.text_color_btn.clicked.connect(lambda: self._show_color_popup("font_color"))
        self.bg_color_btn.clicked.connect(lambda: self._show_color_popup("bg_color"))

        # Init alignment group (mutually exclusive)
        self._set_align(Qt.AlignLeft)

    def _set_align(self, align):
        for btn in self.align_group:
            btn.setChecked(False)
        if align == Qt.AlignLeft:
            self.align_left.setChecked(True)
        elif align == Qt.AlignCenter:
            self.align_center.setChecked(True)
        elif align == Qt.AlignRight:
            self.align_right.setChecked(True)
        self._state["align"] = align
        self._emit_style()

    def _emit_style(self):
        if self._block_signals:
            return
        self._state = {
            "font": self.font_combo.currentText(),
            "size": self.font_size.value(),
            "bold": self.bold_btn.isChecked(),
            "italic": self.italic_btn.isChecked(),
            "align": (
                Qt.AlignLeft if self.align_left.isChecked() else
                Qt.AlignCenter if self.align_center.isChecked() else
                Qt.AlignRight
            ),
            "font_color": self._state.get("font_color", "#222"),
            "bg_color": self._state.get("bg_color", "#fff")
        }
        self.style_changed.emit(self._state.copy())

    def _show_color_popup(self, which):
        menu = QMenu(self)
        swatch_row = QWidget()
        layout = QGridLayout(swatch_row)
        layout.setSpacing(2)
        for i, color in enumerate(SWATCH_COLORS):
            btn = QToolButton()
            btn.setFixedSize(22, 22)
            btn.setStyleSheet(f"background:{color}; border:1.5px solid #888; border-radius:6px;")
            btn.clicked.connect(lambda _, c=color: self._color_selected(which, c))
            btn.clicked.connect(menu.close)
            layout.addWidget(btn, i // 8, i % 8)
        # Add color picker button as last swatch
        pick_btn = QToolButton()
        pick_btn.setFixedSize(22, 22)
        pick_btn.setIcon(icon("color_picker.svg"))
        pick_btn.setToolTip("Избери цвят...")
        pick_btn.clicked.connect(lambda: self._choose_custom_color(which, menu))
        layout.addWidget(pick_btn, (len(SWATCH_COLORS)) // 8, (len(SWATCH_COLORS)) % 8)
        menu.setMinimumWidth(22 * 10)
        action = QWidgetAction(menu)
        action.setDefaultWidget(swatch_row)
        menu.addAction(action)
        btn = self.text_color_btn if which == "font_color" else self.bg_color_btn
        menu.exec_(btn.mapToGlobal(btn.rect().bottomLeft()))

    def _choose_custom_color(self, which, menu):
        dlg = QColorDialog(self)
        if dlg.exec_() == QColorDialog.Accepted:
            color = dlg.selectedColor().name()
            self._color_selected(which, color)
        menu.close()

    def _color_selected(self, which, color):
        self._state[which] = color
        self._emit_style()

    def set_toolbar_state(self, style: dict):
        self._block_signals = True
        if "font" in style:
            idx = self.font_combo.findText(style["font"])
            if idx != -1:
                self.font_combo.setCurrentIndex(idx)
        if "size" in style:
            self.font_size.setValue(style["size"])
        if "bold" in style:
            self.bold_btn.setChecked(style["bold"])
        if "italic" in style:
            self.italic_btn.setChecked(style["italic"])
        if "align" in style:
            self._set_align(style["align"])
        if "font_color" in style:
            self._state["font_color"] = style["font_color"]
        if "bg_color" in style:
            self._state["bg_color"] = style["bg_color"]
        self._block_signals = False

