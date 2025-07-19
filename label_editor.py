import sys, os
import json
from functools import partial

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QComboBox,
    QButtonGroup, QToolButton, QSizePolicy, QGridLayout, QMenu, QColorDialog, QWidgetAction, QScrollArea
)
from PyQt5.QtGui import QFont, QFontDatabase, QPainter, QPen, QColor, QIcon
from PyQt5.QtCore import Qt, pyqtSignal

from currency_manager import CurrencyManager
from session_manager import SessionManager

MM_TO_PX = 72 / 25.4
DEFAULT_PREVIEW_SCALE = 1
MIN_PREVIEW_SCALE = 0.5
MAX_GRID_HEIGHT = 1000  # px

def sheet_settings_path():
    from pathlib import Path
    return os.path.join(str(Path.home()), "AppData", "Roaming", "LabelTool", "sheet_settings.json")

def blank_label():
    return {
        "main":    {"text": "", "font": "Arial", "size": 15, "bold": False, "italic": False, "align": Qt.AlignCenter, "font_color": "#222", "bg_color": "#fff"},
        "second":  {"text": "", "font": "Arial", "size": 12, "bold": False, "italic": False, "align": Qt.AlignCenter, "font_color": "#222", "bg_color": "#fff"},
        "bgn":     {"text": "", "font": "Arial", "size": 16, "bold": True,  "italic": False, "align": Qt.AlignCenter, "font_color": "#222", "bg_color": "#fff"},
        "eur":     {"text": "", "font": "Arial", "size": 16, "bold": True,  "italic": False, "align": Qt.AlignCenter, "font_color": "#222", "bg_color": "#fff"},
    }

def resource_path(relpath):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relpath)
    return relpath

PALETTE_COLORS = [
    "#ffffff", "#9F9F9F", "#575757", "#000000", "#E01300", "#00DD29", "#00A0FF",
]

CONV_MODES = [
    ("BGN → EUR", "bgn_to_eur"),
    ("EUR → BGN", "eur_to_bgn"),
    ("BGN ⇄ EUR", "both"),
    ("Без конверсия", "manual"),
]

class SheetLabel(QWidget):
    clicked = pyqtSignal(object, object)
    rightClicked = pyqtSignal(object, object)
    def __init__(self, idx, get_label, selected=False, scale=1.0, label_w_px=1, label_h_px=1):
        super().__init__()
        self.idx = idx
        self.get_label = get_label
        self.selected = selected
        self.scale = scale
        self.label_w_px = label_w_px
        self.label_h_px = label_h_px
        self.setFixedSize(int(self.label_w_px*self.scale+20), int(self.label_h_px*self.scale+20))
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
    def set_selected(self, on=True):
        self.selected = on
        self.update()
    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self.clicked.emit(self, ev)
        elif ev.button() == Qt.RightButton:
            self.rightClicked.emit(self, ev)
    def update_label_size(self, label_w_px, label_h_px, scale):
        self.label_w_px = label_w_px
        self.label_h_px = label_h_px
        self.scale = scale
        self.setFixedSize(int(self.label_w_px*self.scale+20), int(self.label_h_px*self.scale+20))
        self.update()
    def paintEvent(self, event):
        label = self.get_label()
        s = self.scale
        w_px = self.label_w_px
        h_px = self.label_h_px
        qp = QPainter(self)
        qp.setRenderHint(QPainter.Antialiasing)
        qp.setPen(QPen(QColor("#2c7ee9") if self.selected else QColor("#ffffff"), 2*int(s) if self.selected else 1))
        qp.setBrush(QColor(label["main"]["bg_color"]))
        qp.drawRoundedRect(int(6*s), int(6*s), int(w_px*s), int(h_px*s), 12*s, 12*s)
        margin = int(16*s)
        x0, y0 = int(6*s+margin), int(6*s+margin)
        w, h = int(w_px*s-2*margin), int(h_px*s-2*margin)
        lines = []
        for key in ["main", "second", "bgn", "eur"]:
            fld = label[key]
            if fld["text"]:
                t = fld["text"]
                if key=="bgn": t += " лв."
                if key=="eur": t = "€"+t
                lines.append((t, fld))
        total_h, metrics = 0, []
        for text, field in lines:
            fnt = QFont(field['font'], int(field['size']*s))
            fnt.setBold(field['bold'])
            fnt.setItalic(field['italic'])
            qp.setFont(fnt)
            fm = qp.fontMetrics()
            rect = fm.boundingRect(0, 0, w, h, field['align']|Qt.TextWordWrap, text)
            metrics.append((rect.height(), field, text, fnt))
            total_h += rect.height()
        cy = y0 + (h-total_h)//2
        for hgt, field, text, fnt in metrics:
            qp.setFont(fnt)
            qp.setPen(QColor(field.get("font_color", "#222")))
            bg = field.get("bg_color","#fff")
            qp.setBrush(QColor(bg))
            rect = qp.boundingRect(x0, cy, w, hgt, field['align']|Qt.TextWordWrap, text)
            qp.fillRect(rect, QColor(bg))
            qp.drawText(rect, field['align']|Qt.TextWordWrap, text)
            cy += hgt

class LabelSheetEditor(QWidget):
    def __init__(self, font_list):
        super().__init__()
        self.setWindowTitle("Строймаркет Цаков - Етикетен редактор")
        self.font_list = font_list

        self.sheet_settings = self.load_sheet_settings()
        self.rows = self.sheet_settings.get('rows', 3)
        self.cols = self.sheet_settings.get('cols', 3)
        self.label_w = self.sheet_settings.get('label_w', 63.5)
        self.label_h = self.sheet_settings.get('label_h', 38.1)

        self.label_w_px = int(self.label_w * MM_TO_PX)
        self.label_h_px = int(self.label_h * MM_TO_PX)
        self.preview_scale = self.compute_preview_scale()
        self.labels = [blank_label() for _ in range(self.rows*self.cols)]
        self.clipboard = None
        self.clipboard_style = None
        self.session_manager = SessionManager(self)
        self.selected = [0] if self.labels else []
        self.active_field = "main"
        self.init_ui()
        self.session_manager.load_session()
        self.ensure_at_least_one_selected()

    def compute_preview_scale(self):
        total_label_height = self.rows * self.label_h_px + self.rows * 18
        scale = min(DEFAULT_PREVIEW_SCALE, MAX_GRID_HEIGHT / total_label_height)
        return max(MIN_PREVIEW_SCALE, scale)

    def load_sheet_settings(self):
        path = sheet_settings_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data.get("params", {})
            except Exception:
                return {}
        return {}

    def save_session(self):
        self.session_manager.save_session()

    def init_ui(self):
        main_h = QHBoxLayout(self)
        left_panel = QVBoxLayout()

        # --- TOOLBAR ---
        tbar = QHBoxLayout()
        self.font_combo = QComboBox(); self.font_combo.addItems(self.font_list)
        self.font_size_minus = QToolButton(); self.font_size_minus.setText("–")
        self.font_size_plus = QToolButton(); self.font_size_plus.setText("+")
        self.font_size_disp = QLabel("15")
        self.bold_btn = QToolButton(); self.bold_btn.setText("B"); self.bold_btn.setCheckable(True)
        self.bold_btn.setStyleSheet("font-weight: bold;")
        self.italic_btn = QToolButton(); self.italic_btn.setText("I"); self.italic_btn.setCheckable(True)
        self.italic_btn.setStyleSheet("font-style: italic;")
        self.align_group = QButtonGroup(self)
        self.align_left = QToolButton(); self.align_left.setCheckable(True)
        self.align_left.setIcon(QIcon(resource_path("resources/format_align_left.svg")))
        self.align_left.setToolTip("Подравняване вляво")
        self.align_center = QToolButton(); self.align_center.setCheckable(True)
        self.align_center.setIcon(QIcon(resource_path("resources/format_align_center.svg")))
        self.align_center.setToolTip("Центрирано")
        self.align_right = QToolButton(); self.align_right.setCheckable(True)
        self.align_right.setIcon(QIcon(resource_path("resources/format_align_right.svg")))
        self.align_right.setToolTip("Подравняване вдясно")
        self.align_group.addButton(self.align_left, Qt.AlignLeft)
        self.align_group.addButton(self.align_center, Qt.AlignCenter)
        self.align_group.addButton(self.align_right, Qt.AlignRight)

        for w in [self.font_combo, self.font_size_minus, self.font_size_disp, self.font_size_plus,
                  self.bold_btn, self.italic_btn, self.align_left, self.align_center, self.align_right]:
            tbar.addWidget(w)
        tbar.addStretch(1)

        # --- Currency conversion mode dropdown
        self.conv_mode_combo = QComboBox()
        for label, key in CONV_MODES:
            self.conv_mode_combo.addItem(label, key)
        self.conv_mode_combo.setCurrentIndex(0)
        self.conv_mode_combo.setToolTip("Режим на конвертиране BGN/EUR")
        tbar.addWidget(QLabel("Режим:"))
        tbar.addWidget(self.conv_mode_combo)

        # --- Color Swatch Buttons ---
        color_icon_size = 26
        self.font_color_btn = QToolButton()
        self.font_color_btn.setFixedSize(color_icon_size, color_icon_size)
        self.font_color_btn.setToolTip("Цвят на текста")
        self.font_color_btn.clicked.connect(self.show_font_color_palette)
        self.font_color_dialog_btn = QToolButton()
        self.font_color_dialog_btn.setText("...")
        self.font_color_dialog_btn.setFixedSize(26, 26)
        self.font_color_dialog_btn.setToolTip("Друг цвят...")
        self.font_color_dialog_btn.clicked.connect(self.choose_font_color_dialog)

        self.bg_color_btn = QToolButton()
        self.bg_color_btn.setFixedSize(color_icon_size, color_icon_size)
        self.bg_color_btn.setToolTip("Цвят на фона")
        self.bg_color_btn.clicked.connect(self.show_bg_color_palette)
        self.bg_color_dialog_btn = QToolButton()
        self.bg_color_dialog_btn.setText("...")
        self.bg_color_dialog_btn.setFixedSize(26, 26)
        self.bg_color_dialog_btn.setToolTip("Друг цвят...")
        self.bg_color_dialog_btn.clicked.connect(self.choose_bg_color_dialog)

        tbar.addWidget(QLabel("Текст:"))
        tbar.addWidget(self.font_color_btn)
        tbar.addWidget(self.font_color_dialog_btn)
        tbar.addSpacing(10)
        tbar.addWidget(QLabel("Фон:"))
        tbar.addWidget(self.bg_color_btn)
        tbar.addWidget(self.bg_color_dialog_btn)
        left_panel.addLayout(tbar)
        left_panel.addSpacing(10)

        # Field editors
        self.field_inputs = {}
        for key, lbl in [("main","Основен текст:"),("second","Втори ред:"),("bgn","Цена BGN:"),("eur","Цена EUR:")]:
            left_panel.addWidget(QLabel(lbl))
            if key in ("main","second"):
                w = QTextEdit(); w.setFont(QFont("Arial",16)); w.setFixedHeight(54)
            else:
                w = QLineEdit(); w.setFont(QFont("Arial",16))
            self.field_inputs[key] = w
            left_panel.addWidget(w)
        left_panel.addStretch(1)
        main_h.addLayout(left_panel, 0)

        # --- Label grid inside scroll area ---
        grid_panel = QVBoxLayout()
        grid_panel.addWidget(QLabel("  Кликни за да избереш. Кликни с десен бутон за меню."))

        self.grid_widget = QWidget()
        self.grid = QGridLayout(self.grid_widget)
        self.grid.setSpacing(18)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.grid_widget)
        grid_panel.addWidget(self.scroll_area)

        reload_btn = QToolButton()
        reload_btn.setText("Обнови от калибрация")
        reload_btn.clicked.connect(self.reload_from_calibration)
        grid_panel.addWidget(reload_btn)
        grid_panel.addStretch(1)
        main_h.addLayout(grid_panel, 1)

        self.build_label_grid()

        for key, widget in self.field_inputs.items():
            if isinstance(widget, QTextEdit):
                widget.textChanged.connect(self.on_editor_changed)
            else:
                widget.textChanged.connect(self.on_editor_changed)

        self.font_combo.currentTextChanged.connect(self.set_font_family)
        self.font_size_minus.clicked.connect(lambda: self.adjust_font_size(-1))
        self.font_size_plus.clicked.connect(lambda: self.adjust_font_size(+1))
        self.bold_btn.toggled.connect(self.set_bold)
        self.italic_btn.toggled.connect(self.set_italic)
        self.align_left.toggled.connect(lambda checked: self.set_alignment(Qt.AlignLeft) if checked else None)
        self.align_center.toggled.connect(lambda checked: self.set_alignment(Qt.AlignCenter) if checked else None)
        self.align_right.toggled.connect(lambda checked: self.set_alignment(Qt.AlignRight) if checked else None)

        for key, widget in self.field_inputs.items():
            widget.installEventFilter(self)
        self.update_edit_panel_from_selection()

        # --- Currency manager for BGN/EUR fields ---
        self.currency_manager = CurrencyManager(self.field_inputs['bgn'], self.field_inputs['eur'])

        # Set mode from session (if loaded)
        session_mode = getattr(self.session_manager, 'last_mode', None)
        mode = session_mode if session_mode else "bgn_to_eur"
        self.currency_manager.set_mode(mode)
        self.set_conv_dropdown(mode)

        self.conv_mode_combo.currentIndexChanged.connect(self.on_conv_mode_changed)

        # Force label update after any currency editingFinished
        self.field_inputs['bgn'].editingFinished.connect(self.update_edit_panel_from_selection)
        self.field_inputs['eur'].editingFinished.connect(self.update_edit_panel_from_selection)

    def set_conv_dropdown(self, mode):
        for i, (_, key) in enumerate(CONV_MODES):
            if key == mode:
                self.conv_mode_combo.setCurrentIndex(i)
                break

    def on_conv_mode_changed(self, idx):
        mode = self.conv_mode_combo.itemData(idx)
        self.currency_manager.set_mode(mode)
        self.save_session()  # persist mode with session

    def build_label_grid(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.label_widgets = []
        self.preview_scale = self.compute_preview_scale()
        idx = 0
        for i in range(self.rows):
            for j in range(self.cols):
                get_label = lambda idx=idx: self.labels[idx]
                lbl = SheetLabel(idx, get_label, selected=(idx in self.selected),
                                 scale=self.preview_scale, label_w_px=self.label_w_px, label_h_px=self.label_h_px)
                lbl.clicked.connect(self.on_label_clicked)
                lbl.rightClicked.connect(self.on_label_right_click)
                self.grid.addWidget(lbl, i, j)
                self.label_widgets.append(lbl)
                idx += 1
        self.ensure_at_least_one_selected()

    def reload_from_calibration(self):
        settings = self.load_sheet_settings()
        rows = settings.get('rows', 3)
        cols = settings.get('cols', 3)
        label_w = settings.get('label_w', 63.5)
        label_h = settings.get('label_h', 38.1)
        self.label_w_px = int(label_w * MM_TO_PX)
        self.label_h_px = int(label_h * MM_TO_PX)
        self.rows = rows
        self.cols = cols
        self.label_w = label_w
        self.label_h = label_h
        label_count = self.rows * self.cols
        if len(self.labels) < label_count:
            for _ in range(label_count - len(self.labels)):
                self.labels.append(blank_label())
        elif len(self.labels) > label_count:
            self.labels = self.labels[:label_count]
        self.selected = [min(self.selected[0], label_count - 1)] if self.selected and label_count else []
        self.build_label_grid()
        self.update_edit_panel_from_selection()
        self.save_session()

    def ensure_at_least_one_selected(self):
        if not self.selected or self.selected[0] >= len(self.label_widgets):
            self.selected = [0] if self.label_widgets else []
        for i, lbl in enumerate(self.label_widgets):
            lbl.set_selected(i in self.selected)

    def eventFilter(self, obj, ev):
        if ev.type() == ev.FocusIn:
            for k, w in self.field_inputs.items():
                if obj is w:
                    self.active_field = k
                    self.update_toolbar_from_field()
                    break
        return super().eventFilter(obj, ev)

    def on_label_clicked(self, label, event):
        idx = label.idx
        if event.modifiers() & Qt.ControlModifier:
            if idx in self.selected:
                if len(self.selected) > 1:
                    self.selected.remove(idx)
                    label.set_selected(False)
            else:
                self.selected.append(idx)
                label.set_selected(True)
        elif event.modifiers() & Qt.ShiftModifier and self.selected:
            start, end = min(self.selected[0], idx), max(self.selected[0], idx)
            for i in range(start, end+1):
                if i not in self.selected:
                    self.selected.append(i)
                    self.label_widgets[i].set_selected(True)
        else:
            for i, lbl in enumerate(self.label_widgets):
                lbl.set_selected(i == idx)
            self.selected = [idx]
        self.update_edit_panel_from_selection()
        self.save_session()

    def on_label_right_click(self, label, event):
        idx = label.idx
        menu = QMenu(self)
        copy_action = menu.addAction("Копирай Етикет")
        copystyle_action = menu.addAction("Копирай форматиране")
        paste_action = menu.addAction("Постави")
        action = menu.exec_(label.mapToGlobal(event.pos()))
        sel = self.selected
        if action == copy_action:
            self.clipboard = {k: self.labels[idx][k].copy() for k in self.labels[idx]}
            self.clipboard_style = None
        elif action == copystyle_action:
            self.clipboard_style = {k: {kk: vv for kk, vv in self.labels[idx][k].items() if kk != "text"} for k in self.labels[idx]}
            self.clipboard = None
        elif action == paste_action:
            if self.clipboard:
                for idx2 in sel:
                    for k in self.labels[idx2]:
                        self.labels[idx2][k] = self.clipboard[k].copy()
            elif self.clipboard_style:
                for idx2 in sel:
                    for k in self.labels[idx2]:
                        for sk, vv in self.clipboard_style[k].items():
                            self.labels[idx2][k][sk] = vv
            self.update_edit_panel_from_selection()
            for lbl in self.label_widgets:
                lbl.update()
        self.save_session()

    def update_edit_panel_from_selection(self):
        sel = self.selected
        if not sel:
            return
        main = self.labels[sel[0]]
        placeholders = {"main": "Основен текст", "second": "Втори ред", "bgn": "BGN", "eur": "EUR"}
        for key, widget in self.field_inputs.items():
            vals = [self.labels[idx][key]["text"] for idx in sel]
            placeholder = placeholders[key]
            widget.blockSignals(True)
            if all(v == vals[0] for v in vals):
                if isinstance(widget, QTextEdit):
                    widget.setPlainText(vals[0])
                else:
                    widget.setText(vals[0])
                widget.setPlaceholderText(placeholder)
            else:
                if isinstance(widget, QTextEdit):
                    widget.setPlainText("")
                else:
                    widget.setText("")
                widget.setPlaceholderText("——————разлики——————")
            widget.blockSignals(False)
        self.update_toolbar_from_field()

    def update_toolbar_from_field(self):
        sel = self.selected
        if not sel:
            return
        key = self.active_field
        vals = [self.labels[idx][key] for idx in sel]
        f = vals[0]
        fonts_same = all(v["font"] == f["font"] for v in vals)
        self.font_combo.blockSignals(True)
        self.font_combo.setCurrentText(f["font"] if fonts_same else "")
        self.font_combo.blockSignals(False)
        sizes_same = all(v["size"] == f["size"] for v in vals)
        self.font_size_disp.setText(str(f["size"]) if sizes_same else "")
        bold_same = all(v["bold"] == f["bold"] for v in vals)
        italic_same = all(v["italic"] == f["italic"] for v in vals)
        self.bold_btn.blockSignals(True)
        self.bold_btn.setChecked(f["bold"] if bold_same else False)
        self.bold_btn.blockSignals(False)
        self.italic_btn.blockSignals(True)
        self.italic_btn.setChecked(f["italic"] if italic_same else False)
        self.italic_btn.blockSignals(False)
        align_same = all(v["align"] == f["align"] for v in vals)
        if align_same:
            if f["align"] == Qt.AlignLeft:
                self.align_left.setChecked(True)
            elif f["align"] == Qt.AlignRight:
                self.align_right.setChecked(True)
            else:
                self.align_center.setChecked(True)
        else:
            self.align_left.setChecked(False)
            self.align_center.setChecked(False)
            self.align_right.setChecked(False)
        color_same = all(v["font_color"] == f["font_color"] for v in vals)
        bg_same = all(v["bg_color"] == f["bg_color"] for v in vals)
        self.font_color_btn.setStyleSheet(f"background:{f['font_color']}; border: 2.5px solid {'#222' if color_same else '#eee'}; border-radius: 4px;")
        self.bg_color_btn.setStyleSheet(f"background:{f['bg_color']}; border: 2.5px solid {'#222' if bg_same else '#eee'}; border-radius: 4px;")

    def on_editor_changed(self):
        sel = self.selected
        if not sel:
            return
        key = self.active_field
        widget = self.field_inputs[key]
        if isinstance(widget, QTextEdit):
            val = widget.toPlainText()
        else:
            val = widget.text()
        for idx in sel:
            self.labels[idx][key]["text"] = val
        for lbl in self.label_widgets:
            lbl.update()
        self.save_session()

    def set_font_family(self, fontname):
        sel = self.selected
        if not sel:
            return
        k = self.active_field
        for idx in sel:
            self.labels[idx][k]["font"] = fontname
        for lbl in self.label_widgets:
            lbl.update()
        self.update_toolbar_from_field()
        self.save_session()

    def set_font_size(self, size):
        sel = self.selected
        if not sel:
            return
        k = self.active_field
        for idx in sel:
            self.labels[idx][k]["size"] = size
        for lbl in self.label_widgets:
            lbl.update()
        self.update_toolbar_from_field()
        self.save_session()

    def set_bold(self, checked):
        sel = self.selected
        if not sel:
            return
        k = self.active_field
        for idx in sel:
            self.labels[idx][k]["bold"] = checked
        for lbl in self.label_widgets:
            lbl.update()
        self.update_toolbar_from_field()
        self.save_session()

    def set_italic(self, checked):
        sel = self.selected
        if not sel:
            return
        k = self.active_field
        for idx in sel:
            self.labels[idx][k]["italic"] = checked
        for lbl in self.label_widgets:
            lbl.update()
        self.update_toolbar_from_field()
        self.save_session()

    def set_alignment(self, align_value):
        sel = self.selected
        if not sel:
            return
        k = self.active_field
        for idx in sel:
            self.labels[idx][k]["align"] = align_value
        for lbl in self.label_widgets:
            lbl.update()
        self.update_toolbar_from_field()
        self.save_session()

    def adjust_font_size(self, delta):
        try:
            val = int(self.font_size_disp.text())
        except:
            val = 12
        new_val = max(6, min(72, val + delta))
        self.font_size_disp.setText(str(new_val))
        self.set_font_size(new_val)

    def set_field_color(self, prop, val):
        sel = self.selected
        if not sel:
            return
        k = self.active_field
        for idx in sel:
            self.labels[idx][k][prop] = val
        for lbl in self.label_widgets:
            lbl.update()
        self.update_toolbar_from_field()
        self.save_session()

    def show_font_color_palette(self):
        self.show_color_palette("font_color")

    def show_bg_color_palette(self):
        self.show_color_palette("bg_color")

    def show_color_palette(self, which):
        menu = QMenu(self)
        swatch_row = QWidget()
        layout = QGridLayout(swatch_row)
        layout.setSpacing(2)
        for i, color in enumerate(PALETTE_COLORS):
            btn = QToolButton()
            btn.setFixedSize(30, 30)
            btn.setStyleSheet(f"background:{color}; border:1.5px solid #888; border-radius:6px;")
            btn.clicked.connect(partial(self.set_field_color, which, color))
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

    def choose_font_color_dialog(self):
        color = QColorDialog.getColor(parent=self, title="Избери цвят на текста")
        if color.isValid():
            self.set_field_color("font_color", color.name())

    def choose_bg_color_dialog(self):
        color = QColorDialog.getColor(parent=self, title="Избери цвят на фона")
        if color.isValid():
            self.set_field_color("bg_color", color.name())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    FONT_DB = QFontDatabase()
    FONTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
    FONT_LIST = []
    for fname in os.listdir(FONTS_DIR):
        if fname.lower().endswith('.ttf'):
            family_id = FONT_DB.addApplicationFont(os.path.join(FONTS_DIR, fname))
            families = FONT_DB.applicationFontFamilies(family_id)
            if families:
                FONT_LIST.extend(families)
    if not FONT_LIST:
        FONT_LIST = ["Arial"]
    win = LabelSheetEditor(FONT_LIST)
    win.resize(1350, 1000)
    win.show()
    sys.exit(app.exec_())
