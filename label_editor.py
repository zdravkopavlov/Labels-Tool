import sys, os, json
from functools import partial

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QComboBox,
    QButtonGroup, QToolButton, QGridLayout, QMenu, QColorDialog, QWidgetAction, QScrollArea,
    QFileDialog, QMessageBox, QSizePolicy, QSpacerItem
)
from PyQt5.QtGui import QFont, QFontDatabase, QIcon, QPainter, QPagedPaintDevice, QPdfWriter, QColor, QPen
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtCore import Qt, QSize, pyqtSignal

from currency_manager import CurrencyManager
from session_manager import SessionManager

MM_TO_PX = 72 / 25.4

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
    folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
    p = os.path.join(folder, relpath)
    if os.path.exists(p):
        return p
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
    def __init__(self, idx, get_label, selected=False, label_w_px=150, label_h_px=60):
        super().__init__()
        self.idx = idx
        self.get_label = get_label
        self.selected = selected
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumSize(label_w_px, label_h_px)
        self.setMaximumSize(label_w_px, label_h_px)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def set_selected(self, on=True):
        self.selected = on
        self.update()

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self.clicked.emit(self, ev)
        elif ev.button() == Qt.RightButton:
            self.rightClicked.emit(self, ev)

    def paintEvent(self, event):
        label = self.get_label()
        qp = QPainter(self)
        qp.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(3,3,-3,-3)
        qp.setPen(QPen(QColor("#2c7ee9") if self.selected else QColor("#cccccc"), 2 if self.selected else 1))
        qp.setBrush(QColor(label["main"]["bg_color"]))
        qp.drawRoundedRect(rect, 12, 12)

        # Draw text fields centered
        margin = 12
        x0, y0 = rect.x() + margin, rect.y() + margin
        w, h = rect.width() - 2*margin, rect.height() - 2*margin
        lines = []
        for key in ["main", "second", "bgn", "eur"]:
            fld = label[key]
            t = fld["text"]
            if key=="bgn":
                t = t.replace(" лв.", "").replace("лв.", "").strip()
                if t: t += " лв."
            if key=="eur":
                t = t.replace("€", "").strip()
                if t: t = "€" + t
            if t:
                lines.append((t, fld))
        total_h, metrics = 0, []
        for text, field in lines:
            fnt = QFont(field['font'], int(field['size']))
            fnt.setBold(field['bold'])
            fnt.setItalic(field['italic'])
            qp.setFont(fnt)
            fm = qp.fontMetrics()
            rect_t = fm.boundingRect(0, 0, w, h, field['align']|Qt.TextWordWrap, text)
            metrics.append((rect_t.height(), field, text, fnt))
            total_h += rect_t.height()
        cy = y0 + (h - total_h) // 2
        for hgt, field, text, fnt in metrics:
            qp.setFont(fnt)
            qp.setPen(QColor(field.get("font_color", "#222")))
            rect_t = qp.fontMetrics().boundingRect(0, 0, w, hgt, field['align']|Qt.TextWordWrap, text)
            draw_rect = rect_t.translated(x0, cy)
            qp.drawText(draw_rect, field['align']|Qt.TextWordWrap, text)
            cy += hgt
class LabelSheetEditor(QWidget):
    def __init__(self, font_list):
        super().__init__()
        self.setWindowTitle("Строймаркет Цаков – Етикетен инструмент – Версия: 3.0.0")
        self.font_list = font_list

        self.sheet_settings = self.load_sheet_settings()
        self.rows = self.sheet_settings.get('rows', 3)
        self.cols = self.sheet_settings.get('cols', 3)
        self.label_w = self.sheet_settings.get('label_w', 63.5)
        self.label_h = self.sheet_settings.get('label_h', 38.1)
        self.margin_top = self.sheet_settings.get('margin_top', 0)
        self.margin_left = self.sheet_settings.get('margin_left', 0)
        self.spacing_x = self.sheet_settings.get('spacing_x', 0)
        self.spacing_y = self.sheet_settings.get('spacing_y', 0)
        self.label_w_px = int(self.label_w * MM_TO_PX)
        self.label_h_px = int(self.label_h * MM_TO_PX)

        self.labels = [blank_label() for _ in range(self.rows*self.cols)]
        self.clipboard = None
        self.clipboard_style = None
        self.selected = [0] if self.labels else []
        self.active_field = "main"

        main_h = QHBoxLayout(self)
        left_panel = QVBoxLayout()

        # --- Styling toolbar (font, bold, etc) ---
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

        for w in [self.font_combo, self.font_size_minus, self.font_size_disp, self.font_size_plus,
                  self.bold_btn, self.italic_btn, self.align_left, self.align_center, self.align_right]:
            tbar.addWidget(w)
        tbar.addStretch(1)

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

        # --- Field editors ---
        self.field_inputs = {}
        for key, lbl in [("main","Основен текст:"),("second","Втори ред:"),("bgn","Цена BGN:"),("eur","Цена EUR:")]:
            left_panel.addWidget(QLabel(lbl))
            if key in ("main","second"):
                w = QTextEdit(); w.setFont(QFont("Arial",16)); w.setFixedHeight(54)
            else:
                w = QLineEdit(); w.setFont(QFont("Arial",16))
            self.field_inputs[key] = w
            left_panel.addWidget(w)

        # --- Conversion dropdown below price fields ---
        self.conv_mode_combo = QComboBox()
        for label, key in CONV_MODES:
            self.conv_mode_combo.addItem(label, key)
        self.conv_mode_combo.setCurrentIndex(0)
        self.conv_mode_combo.setToolTip("Режим на конвертиране BGN/EUR")
        left_panel.addSpacing(6)
        left_panel.addWidget(QLabel("Конвертиране на валута:"))
        left_panel.addWidget(self.conv_mode_combo)

        left_panel.addStretch(1)

        # --- Print and PDF buttons at bottom left ---
        btn_row = QHBoxLayout()
        self.print_btn = QToolButton()
        self.print_btn.setIcon(QIcon(resource_path("print_.svg")))
        self.print_btn.setText("Печат")
        self.print_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.print_btn.setFixedHeight(36)
        self.print_btn.setToolTip("Печат на етикетите")
        self.print_btn.clicked.connect(self.do_print)

        self.pdf_btn = QToolButton()
        self.pdf_btn.setIcon(QIcon(resource_path("export_as_pdf.svg")))
        self.pdf_btn.setText("Запази PDF")
        self.pdf_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.pdf_btn.setFixedHeight(36)
        self.pdf_btn.setToolTip("Експортиране като PDF")
        self.pdf_btn.clicked.connect(self.do_export_pdf)

        btn_row.addWidget(self.print_btn)
        btn_row.addWidget(self.pdf_btn)
        left_panel.addLayout(btn_row)
        main_h.addLayout(left_panel, 0)

        # --- Right pane: SESSION TOOLBAR + PREVIEW ---
        right_panel = QVBoxLayout()
        session_row = QHBoxLayout()
        self.save_sess_btn = QToolButton()
        self.save_sess_btn.setText("Запази сесия")
        self.save_sess_btn.setToolTip("Запис на сесията в отделен файл")
        self.save_sess_btn.clicked.connect(self.save_session_as)
        session_row.addWidget(self.save_sess_btn)

        self.load_sess_btn = QToolButton()
        self.load_sess_btn.setText("Зареди сесия")
        self.load_sess_btn.setToolTip("Зареждане на сесия от файл")
        self.load_sess_btn.clicked.connect(self.load_session_as)
        session_row.addWidget(self.load_sess_btn)
        session_row.addStretch(1)
        right_panel.addLayout(session_row)
        right_panel.addWidget(QLabel("  Кликни за да избереш. Кликни с десен бутон за меню."))

        # --- Scrollable grid for the label sheet preview ---
        # grid_widget is fixed-size, never stretches; scroll area expands
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(int(self.spacing_y * MM_TO_PX) if self.spacing_y else 10)
        self.grid_layout.setContentsMargins(10,10,10,10)
        self.label_widgets = []
        self.build_label_grid()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setWidget(self.grid_widget)
        self.scroll_area.setMinimumHeight(250)
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_panel.addWidget(self.scroll_area, stretch=1)

        # --- Floating refresh button (top-right of preview pane) ---
        # Add after the scroll area is created
        main_h.addLayout(right_panel, 1)
        self.setLayout(main_h)

        # Now add floating button
        self.refresh_btn = QToolButton(self)
        self.refresh_btn.setIcon(QIcon(resource_path("refresh.svg")))
        self.refresh_btn.setIconSize(QSize(36, 36))
        self.refresh_btn.setStyleSheet(
            "QToolButton { background: rgba(255,255,255,0.82); border-radius: 18px; border: 1px solid #b4b4b4; }"
            "QToolButton:hover { background: #e2f1ff; }"
        )
        self.refresh_btn.setToolTip("Обнови от калибрация")
        self.refresh_btn.clicked.connect(self.reload_from_calibration)
        self.refresh_btn.raise_()

        # Make sure button is always in top-right of preview (right of scroll area)
        self.resizeEvent(None)

        # --- Now managers (order matters!) ---
        self.currency_manager = CurrencyManager(self.field_inputs['bgn'], self.field_inputs['eur'])
        self.session_manager = SessionManager(self)

        # --- Signals, mode restore, etc ---
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

        session_mode = getattr(self.session_manager, 'last_mode', None)
        mode = session_mode if session_mode else "bgn_to_eur"
        self.currency_manager.set_mode(mode)
        self.set_conv_dropdown(mode)

        self.conv_mode_combo.currentIndexChanged.connect(self.on_conv_mode_changed)
        self.field_inputs['bgn'].editingFinished.connect(self.update_edit_panel_from_selection)
        self.field_inputs['eur'].editingFinished.connect(self.update_edit_panel_from_selection)
        self.session_manager.load_session()
        self.ensure_at_least_one_selected()

    def resizeEvent(self, event):
        # Position floating refresh_btn at top-right of preview pane
        if hasattr(self, 'refresh_btn') and hasattr(self, 'scroll_area'):
            sa = self.scroll_area
            btn = self.refresh_btn
            margin = 16
            x = sa.geometry().right() - btn.width() - margin
            y = sa.geometry().top() + margin
            btn.move(x, y)
        if event:
            super().resizeEvent(event)

    def build_label_grid(self):
        # Remove all widgets
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)
        self.label_widgets = []
        idx = 0
        for i in range(self.rows):
            for j in range(self.cols):
                get_label = lambda idx=idx: self.labels[idx]
                lbl = SheetLabel(
                    idx, get_label, selected=(idx in self.selected),
                    label_w_px=self.label_w_px, label_h_px=self.label_h_px
                )
                lbl.clicked.connect(self.on_label_clicked)
                lbl.rightClicked.connect(self.on_label_right_click)
                self.grid_layout.addWidget(lbl, i, j)
                self.label_widgets.append(lbl)
                idx += 1
        # Set fixed size for grid_widget based on calibration
        total_w = self.cols * self.label_w_px + max(0, self.cols-1) * (int(self.spacing_x * MM_TO_PX) if self.spacing_x else 10) + 20
        total_h = self.rows * self.label_h_px + max(0, self.rows-1) * (int(self.spacing_y * MM_TO_PX) if self.spacing_y else 10) + 20
        self.grid_widget.setFixedSize(total_w, total_h)
        self.update_selection()
    def update_selection(self):
        for i, lbl in enumerate(self.label_widgets):
            lbl.set_selected(i in self.selected)

    def set_conv_dropdown(self, mode):
        for i, (_, key) in enumerate(CONV_MODES):
            if key == mode:
                self.conv_mode_combo.setCurrentIndex(i)
                break

    def on_conv_mode_changed(self, idx):
        mode = self.conv_mode_combo.itemData(idx)
        self.currency_manager.set_mode(mode)
        self.save_session()

    def save_session(self):
        self.session_manager.save_session()
    def save_session_as(self):
        self.session_manager.save_session_as()
    def load_session_as(self):
        self.session_manager.load_session_as()
        self.set_conv_dropdown(self.session_manager.last_mode)
        self.currency_manager.set_mode(self.session_manager.last_mode)

    def reload_from_calibration(self):
        settings = self.load_sheet_settings()
        self.rows = settings.get('rows', 3)
        self.cols = settings.get('cols', 3)
        self.label_w = settings.get('label_w', 63.5)
        self.label_h = settings.get('label_h', 38.1)
        self.margin_top = settings.get('margin_top', 0)
        self.margin_left = settings.get('margin_left', 0)
        self.spacing_x = settings.get('spacing_x', 0)
        self.spacing_y = settings.get('spacing_y', 0)
        self.label_w_px = int(self.label_w * MM_TO_PX)
        self.label_h_px = int(self.label_h * MM_TO_PX)
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
        self.update_selection()

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
            else:
                self.selected.append(idx)
        elif event.modifiers() & Qt.ShiftModifier and self.selected:
            start, end = min(self.selected[0], idx), max(self.selected[0], idx)
            self.selected = list(range(start, end+1))
        else:
            self.selected = [idx]
        self.update_selection()
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
        self.save_session()
        self.update_selection()

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
        self.save_session()
        self.update_selection()

    def set_font_family(self, fontname):
        sel = self.selected
        if not sel:
            return
        k = self.active_field
        for idx in sel:
            self.labels[idx][k]["font"] = fontname
        self.update_toolbar_from_field()
        self.save_session()
        self.update_selection()

    def set_font_size(self, size):
        sel = self.selected
        if not sel:
            return
        k = self.active_field
        for idx in sel:
            self.labels[idx][k]["size"] = size
        self.update_toolbar_from_field()
        self.save_session()
        self.update_selection()

    def set_bold(self, checked):
        sel = self.selected
        if not sel:
            return
        k = self.active_field
        for idx in sel:
            self.labels[idx][k]["bold"] = checked
        self.update_toolbar_from_field()
        self.save_session()
        self.update_selection()

    def set_italic(self, checked):
        sel = self.selected
        if not sel:
            return
        k = self.active_field
        for idx in sel:
            self.labels[idx][k]["italic"] = checked
        self.update_toolbar_from_field()
        self.save_session()
        self.update_selection()

    def set_alignment(self, align_value):
        sel = self.selected
        if not sel:
            return
        k = self.active_field
        for idx in sel:
            self.labels[idx][k]["align"] = align_value
        self.update_toolbar_from_field()
        self.save_session()
        self.update_selection()

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
        self.update_toolbar_from_field()
        self.save_session()
        self.update_selection()

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

    def do_print(self):
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPrinter.A4)
        dialog = QPrintDialog(printer, self)
        if dialog.exec_() == QPrintDialog.Accepted:
            painter = QPainter(printer)
            self.render_sheet(painter, printer.resolution())
            painter.end()

    def do_export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Запази PDF", "", "PDF Files (*.pdf)")
        if not path:
            return
        pdf = QPdfWriter(path)
        pdf.setPageSize(QPagedPaintDevice.A4)
        pdf.setResolution(300)
        painter = QPainter(pdf)
        self.render_sheet(painter, 300)
        painter.end()
        QMessageBox.information(self, "Успех", "PDF файлът е запазен успешно.")

    def render_sheet(self, qp, dpi):
        # Read calibration
        settings = self.load_sheet_settings()
        rows = settings.get('rows', 3)
        cols = settings.get('cols', 3)
        label_w = settings.get('label_w', 63.5)
        label_h = settings.get('label_h', 38.1)
        margin_left = settings.get('margin_left', 0)
        margin_top = settings.get('margin_top', 0)
        spacing_x = settings.get('spacing_x', 0)
        spacing_y = settings.get('spacing_y', 0)
        sheet_w = settings.get('sheet_w', 210)
        sheet_h = settings.get('sheet_h', 297)

        px_per_mm = dpi / 25.4
        sheet_w_px = int(sheet_w * px_per_mm)
        sheet_h_px = int(sheet_h * px_per_mm)
        label_w_px = int(label_w * px_per_mm)
        label_h_px = int(label_h * px_per_mm)
        margin_left_px = int(margin_left * px_per_mm)
        margin_top_px = int(margin_top * px_per_mm)
        spacing_x_px = int(spacing_x * px_per_mm)
        spacing_y_px = int(spacing_y * px_per_mm)

        qp.setRenderHint(QPainter.Antialiasing)
        qp.setBrush(Qt.white)
        qp.setPen(Qt.NoPen)
        qp.drawRect(0, 0, sheet_w_px, sheet_h_px)

        idx = 0
        for row in range(rows):
            for col in range(cols):
                if idx >= len(self.labels):
                    break
                x = margin_left_px + col * (label_w_px + spacing_x_px)
                y = margin_top_px + row * (label_h_px + spacing_y_px)
                self.draw_label_print(qp, x, y, label_w_px, label_h_px, self.labels[idx])
                idx += 1

    def draw_label_print(self, qp, x, y, w, h, label):
        qp.save()
        qp.setPen(QPen(QColor("#2c7ee9"), 1))
        qp.setBrush(QColor(label["main"]["bg_color"]))
        qp.drawRoundedRect(x, y, w, h, 12, 12)
        margin = int(12)
        x0, y0 = x+margin, y+margin
        ww, hh = w-2*margin, h-2*margin
        lines = []
        for key in ["main", "second", "bgn", "eur"]:
            fld = label[key]
            t = fld["text"]
            if key=="bgn":
                t = t.replace(" лв.", "").replace("лв.", "").strip()
                if t: t += " лв."
            if key=="eur":
                t = t.replace("€", "").strip()
                if t: t = "€" + t
            if t:
                lines.append((t, fld))
        total_h, metrics = 0, []
        for text, field in lines:
            fnt = QFont(field['font'], int(field['size']))
            fnt.setBold(field['bold'])
            fnt.setItalic(field['italic'])
            qp.setFont(fnt)
            fm = qp.fontMetrics()
            rect_t = fm.boundingRect(0, 0, ww, hh, field['align']|Qt.TextWordWrap, text)
            metrics.append((rect_t.height(), field, text, fnt))
            total_h += rect_t.height()
        cy = y0 + (hh - total_h) // 2
        for hgt, field, text, fnt in metrics:
            qp.setFont(fnt)
            qp.setPen(QColor(field.get("font_color", "#222")))
            qp.drawText(x0, cy + hgt - 4, text)
            cy += hgt
        qp.restore()

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
    win.resize(1550, 1050)
    win.show()
    sys.exit(app.exec_())
