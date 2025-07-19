import sys, os
from functools import partial
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QComboBox,
    QButtonGroup, QToolButton, QFrame, QSizePolicy, QGridLayout, QMenu, QColorDialog, QWidgetAction
)
from PyQt5.QtGui import QFont, QFontDatabase, QPainter, QPen, QColor, QIcon
from PyQt5.QtCore import Qt, pyqtSignal

MM_TO_PX = 72 / 25.4
PREVIEW_SCALE = 2
LABEL_W_MM, LABEL_H_MM = 63.5, 38.1
LABEL_W_PX, LABEL_H_PX = int(LABEL_W_MM * MM_TO_PX), int(LABEL_H_MM * MM_TO_PX)
PALETTE_COLORS = [
    "#ffffff", "#9F9F9F", "#575757", "#000000", "#E01300", "#00DD29", "#00A0FF",
]

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

class SheetLabel(QWidget):
    # ... (Unchanged, use your previous implementation) ...
    clicked = pyqtSignal(object, object)
    rightClicked = pyqtSignal(object, object)
    def __init__(self, idx, get_label, selected=False, scale=PREVIEW_SCALE):
        super().__init__()
        self.idx = idx
        self.get_label = get_label
        self.selected = selected
        self.scale = scale
        self.setFixedSize(int(LABEL_W_PX*scale+20), int(LABEL_H_PX*scale+20))
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
    def paintEvent(self, event):
        label = self.get_label()
        s = self.scale
        qp = QPainter(self)
        qp.setRenderHint(QPainter.Antialiasing)
        qp.setPen(QPen(QColor("#2c7ee9") if self.selected else QColor("#ffffff"), 2*s if self.selected else 1))

        qp.setBrush(QColor(label["main"]["bg_color"]))
        qp.drawRoundedRect(6*s, 6*s, LABEL_W_PX*s, LABEL_H_PX*s, 12*s, 12*s)
        margin = 16*s
        x0, y0 = 6*s+margin, 6*s+margin
        w, h = LABEL_W_PX*s-2*margin, LABEL_H_PX*s-2*margin
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
            rect = fm.boundingRect(0,0,w,h,field['align']|Qt.TextWordWrap,text)
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

class SelectionManager:
    # ... (Unchanged, use your previous implementation) ...
    def __init__(self, labels):
        self.labels = labels
        self.selected = []
        self.last_clicked = None
    def select_all(self):
        self.clear_selection()
        self.selected = list(range(len(self.labels)))
        for idx in self.selected: self.labels[idx].set_selected(True)
    def clear_selection(self):
        for idx in self.selected: self.labels[idx].set_selected(False)
        self.selected = []; self.last_clicked = None
    def handle_label_click(self, label, event):
        idx = label.idx
        mods = event.modifiers()
        if mods & Qt.ControlModifier:
            if idx in self.selected: self.selected.remove(idx); label.set_selected(False)
            else: self.selected.append(idx); label.set_selected(True)
            self.last_clicked = idx
        elif mods & Qt.ShiftModifier and self.last_clicked is not None:
            start, end = min(self.last_clicked, idx), max(self.last_clicked, idx)
            for i in range(start,end+1):
                if i not in self.selected: self.selected.append(i); self.labels[i].set_selected(True)
        else:
            self.clear_selection()
            self.selected = [idx]; label.set_selected(True); self.last_clicked = idx

class LabelSheetEditor(QWidget):
    def __init__(self, font_list):
        super().__init__()
        self.setWindowTitle("Строймаркет Цаков - Етикетен редактор  ДЕМО ПРОТОТИП")
        self.resize(1450, 760)
        self.font_list = font_list
        self.labels = [blank_label() for _ in range(9)]
        self.clipboard = None
        self.clipboard_style = None
        main_h = QHBoxLayout(self)
        left_panel = QVBoxLayout()

        # --- TOOLBAR: Alignment icons and new color pickers ---
        tbar = QHBoxLayout()
        self.font_combo = QComboBox(); self.font_combo.addItems(font_list)
        self.font_size_minus = QToolButton(); self.font_size_minus.setText("–")
        self.font_size_plus = QToolButton(); self.font_size_plus.setText("+")
        self.font_size_disp = QLabel("15")
        self.bold_btn = QToolButton(); self.bold_btn.setText("B"); self.bold_btn.setCheckable(True)
        self.bold_btn.setStyleSheet("font-weight: bold;")
        self.italic_btn = QToolButton(); self.italic_btn.setText("I"); self.italic_btn.setCheckable(True)
        self.italic_btn.setStyleSheet("font-style: italic;")
        self.align_group = QButtonGroup(self)
        # --- Use SVG icons for alignment ---
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

        # Right: 3x3 label grid
        grid_panel = QVBoxLayout()
        grid_panel.addWidget(QLabel("  Кликни за да избереш. Кликни с десен бутон за меню."))
        self.grid = QGridLayout(); self.grid.setSpacing(18)
        self.label_widgets = []
        for i in range(3):
            for j in range(3):
                idx = i*3 + j
                get_label = lambda idx=idx: self.labels[idx]
                lbl = SheetLabel(idx, get_label, selected=False, scale=PREVIEW_SCALE)
                lbl.clicked.connect(self.on_label_clicked)
                lbl.rightClicked.connect(self.on_label_right_click)
                self.grid.addWidget(lbl, i, j)
                self.label_widgets.append(lbl)
        grid_panel.addLayout(self.grid)
        grid_panel.addStretch(1)
        main_h.addLayout(grid_panel, 1)

        # Selection manager
        self.selection_mgr = SelectionManager(self.label_widgets)
        self.selection_mgr.clear_selection()
        self.selection_mgr.selected = [0]
        self.label_widgets[0].set_selected(True)

        # Connect editors
        for key, widget in self.field_inputs.items():
            if isinstance(widget, QTextEdit):
                widget.textChanged.connect(self.on_editor_changed)
            else:
                widget.textChanged.connect(self.on_editor_changed)

        # --- TOOLBAR CONTROLS: connect to dedicated slots ---
        self.font_combo.currentTextChanged.connect(self.set_font_family)
        self.font_size_minus.clicked.connect(lambda: self.adjust_font_size(-1))
        self.font_size_plus.clicked.connect(lambda: self.adjust_font_size(+1))
        self.bold_btn.toggled.connect(self.set_bold)
        self.italic_btn.toggled.connect(self.set_italic)
        self.align_left.toggled.connect(lambda checked: self.set_alignment(Qt.AlignLeft) if checked else None)
        self.align_center.toggled.connect(lambda checked: self.set_alignment(Qt.AlignCenter) if checked else None)
        self.align_right.toggled.connect(lambda checked: self.set_alignment(Qt.AlignRight) if checked else None)

        # Track which field is "active" for style edits (default to main)
        self.active_field = "main"
        for key, widget in self.field_inputs.items():
            widget.installEventFilter(self)
        self.update_edit_panel_from_selection()

    # ========== COLOR PALETTE POPUPS AND DIALOGS ==========
    def show_font_color_palette(self):
        self.show_color_palette("font_color")
    def show_bg_color_palette(self):
        self.show_color_palette("bg_color")

    def show_color_palette(self, which):
        # Show a palette grid as a QMenu of swatches.
        menu = QMenu(self)
        swatch_row = QWidget()
        layout = QGridLayout(swatch_row)
        layout.setSpacing(2)
        for i, color in enumerate(PALETTE_COLORS):
            btn = QToolButton()
            btn.setFixedSize(30, 30)
            btn.setStyleSheet(f"background:{color}; border:1.5px solid #888; border-radius:6px;")
            btn.clicked.connect(partial(self.set_field_color, which, color))
            # On click: close menu after setting color.
            btn.clicked.connect(menu.close)
            layout.addWidget(btn, i//7, i%7)
        menu.setMinimumWidth(30*len(PALETTE_COLORS))
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

    # ========== REST OF YOUR LOGIC ==========

    def eventFilter(self, obj, ev):
        if ev.type() == ev.FocusIn:
            for k, w in self.field_inputs.items():
                if obj is w:
                    self.active_field = k
                    self.update_toolbar_from_field()
                    break
        return super().eventFilter(obj, ev)

    def on_label_clicked(self, label, event):
        self.selection_mgr.handle_label_click(label, event)
        self.update_edit_panel_from_selection()

    def on_label_right_click(self, label, event):
        idx = label.idx
        menu = QMenu(self)
        copy_action = menu.addAction("Копирай Етикет")
        copystyle_action = menu.addAction("Копирай форматиране")
        paste_action = menu.addAction("Постави")
        action = menu.exec_(label.mapToGlobal(event.pos()))
        sel = self.selection_mgr.selected
        if action == copy_action:
            self.clipboard = {k: self.labels[idx][k].copy() for k in self.labels[idx]}
            self.clipboard_style = None
        elif action == copystyle_action:
            self.clipboard_style = {k: {kk: vv for kk,vv in self.labels[idx][k].items() if kk!="text"} for k in self.labels[idx]}
            self.clipboard = None
        elif action == paste_action:
            if self.clipboard:
                for idx2 in sel:
                    for k in self.labels[idx2]:
                        self.labels[idx2][k] = self.clipboard[k].copy()
            elif self.clipboard_style:
                for idx2 in sel:
                    for k in self.labels[idx2]:
                        for sk,vv in self.clipboard_style[k].items():
                            self.labels[idx2][k][sk]=vv
            self.update_edit_panel_from_selection()
            for lbl in self.label_widgets: lbl.update()

    def update_edit_panel_from_selection(self):
        sel = self.selection_mgr.selected
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
        sel = self.selection_mgr.selected
        if not sel: return
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
        # Update color swatch buttons:
        self.font_color_btn.setStyleSheet(f"background:{f['font_color']}; border: 2.5px solid {'#222' if color_same else '#eee'}; border-radius: 4px;")
        self.bg_color_btn.setStyleSheet(f"background:{f['bg_color']}; border: 2.5px solid {'#222' if bg_same else '#eee'}; border-radius: 4px;")

    def on_editor_changed(self):
        sel = self.selection_mgr.selected
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

    # ----- SMART TOOLBAR UPDATERS -----
    def set_font_family(self, fontname):
        sel = self.selection_mgr.selected
        if not sel:
            return
        k = self.active_field
        for idx in sel:
            self.labels[idx][k]["font"] = fontname
        for lbl in self.label_widgets:
            lbl.update()
        self.update_toolbar_from_field()

    def set_font_size(self, size):
        sel = self.selection_mgr.selected
        if not sel:
            return
        k = self.active_field
        for idx in sel:
            self.labels[idx][k]["size"] = size
        for lbl in self.label_widgets:
            lbl.update()
        self.update_toolbar_from_field()

    def set_bold(self, checked):
        sel = self.selection_mgr.selected
        if not sel:
            return
        k = self.active_field
        for idx in sel:
            self.labels[idx][k]["bold"] = checked
        for lbl in self.label_widgets:
            lbl.update()
        self.update_toolbar_from_field()

    def set_italic(self, checked):
        sel = self.selection_mgr.selected
        if not sel:
            return
        k = self.active_field
        for idx in sel:
            self.labels[idx][k]["italic"] = checked
        for lbl in self.label_widgets:
            lbl.update()
        self.update_toolbar_from_field()

    def set_alignment(self, align_value):
        sel = self.selection_mgr.selected
        if not sel:
            return
        k = self.active_field
        for idx in sel:
            self.labels[idx][k]["align"] = align_value
        for lbl in self.label_widgets:
            lbl.update()
        self.update_toolbar_from_field()

    def adjust_font_size(self, delta):
        try:
            val = int(self.font_size_disp.text())
        except:
            val = 12
        new_val = max(6, min(72, val + delta))
        self.font_size_disp.setText(str(new_val))
        self.set_font_size(new_val)

    def set_field_color(self, prop, val):
        sel = self.selection_mgr.selected
        if not sel: return
        k = self.active_field
        for idx in sel:
            self.labels[idx][k][prop] = val
        for lbl in self.label_widgets: lbl.update()
        self.update_toolbar_from_field()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    FONT_DB = QFontDatabase()
    FONTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
    FONT_LIST = []
    for fname in os.listdir(FONTS_DIR):
        if fname.lower().endswith('.ttf'):
            family_id = FONT_DB.addApplicationFont(os.path.join(FONTS_DIR, fname))
            families = FONT_DB.applicationFontFamilies(family_id)
            if families: FONT_LIST.extend(families)
    if not FONT_LIST: FONT_LIST = ["Arial"]
    win = LabelSheetEditor(FONT_LIST)
    win.show()
    sys.exit(app.exec_())
