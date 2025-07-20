import sys, os, json
from functools import partial

from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QMessageBox, QSizePolicy
)
from PyQt5.QtCore import Qt

from toolbar import ToolbarWidget
from left_pane import LeftPaneWidget
from preview_pane import PreviewPaneWidget

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

def load_sheet_settings():
    path = sheet_settings_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("params", {})
        except Exception:
            return {}
    return {}

class LabelSheetEditor(QWidget):
    def __init__(self, font_list):
        super().__init__()
        self.setWindowTitle("Строймаркет Цаков – Етикетен инструмент – Версия: 3.0.0")
        self.font_list = font_list

        # --- Calibration: set up grid, label aspect, etc. ---
        self.sheet_settings = load_sheet_settings()
        self.rows = self.sheet_settings.get('rows', 3)
        self.cols = self.sheet_settings.get('cols', 3)
        self.label_w_mm = self.sheet_settings.get('label_w', 63.5)
        self.label_h_mm = self.sheet_settings.get('label_h', 38.1)
        self.label_aspect = self.label_w_mm / self.label_h_mm if self.label_h_mm else 1.0

        self.labels = [blank_label() for _ in range(self.rows*self.cols)]
        self.selected = [0] if self.labels else []
        self.active_field = "main"

        # --- Main layout: left (toolbar + inputs), right (preview) ---
        main_h = QHBoxLayout(self)

        # --- LEFT PANE: Toolbar + Inputs ---
        left_panel = QVBoxLayout()
        self.toolbar = ToolbarWidget(font_list)
        left_panel.addWidget(self.toolbar)
        self.left_pane = LeftPaneWidget()
        left_panel.addWidget(self.left_pane)
        left_panel.addStretch(1)
        main_h.addLayout(left_panel, 0)

        # --- RIGHT PANE: Preview grid ---
        right_panel = QVBoxLayout()
        self.preview_pane = PreviewPaneWidget(
            labels=self.labels,
            rows=self.rows,
            cols=self.cols,
            label_w_mm=self.label_w_mm,
            label_h_mm=self.label_h_mm,
            spacing_px=12
        )
        right_panel.addWidget(QLabel("Кликни за да избереш. Кликни с десен бутон за меню."))
        right_panel.addWidget(self.preview_pane, stretch=1)
        main_h.addLayout(right_panel, 1)
        self.setLayout(main_h)

        # --- Managers (currency, session) ---
        self.currency_manager = CurrencyManager(
            self.left_pane.field_inputs['bgn'], self.left_pane.field_inputs['eur']
        )
        self.session_manager = SessionManager(self)

        # --- Currency: Connect signal for preview update ---
        self.currency_manager.price_converted.connect(self.on_converted_price)

        # --- FIELD FOCUS HANDLING (Toolbar/Field Sync) ---
        for key, widget in self.left_pane.field_inputs.items():
            widget.installEventFilter(self)

        # --- Signal wiring: TOOLBAR <-> EDITOR LOGIC ---
        self.toolbar.font_changed.connect(self.set_font_family)
        self.toolbar.size_changed.connect(self.set_font_size)
        self.toolbar.bold_changed.connect(self.set_bold)
        self.toolbar.italic_changed.connect(self.set_italic)
        self.toolbar.align_changed.connect(self.set_alignment)
        self.toolbar.font_color_changed.connect(lambda color: self.set_field_color("font_color", color))
        self.toolbar.bg_color_changed.connect(lambda color: self.set_field_color("bg_color", color))

        # --- Signal wiring: LEFT PANE <-> EDITOR LOGIC ---
        self.left_pane.text_changed.connect(self.on_field_edited)
        self.left_pane.conversion_changed.connect(self.currency_manager.set_mode)
        self.left_pane.print_clicked.connect(self.do_print)
        self.left_pane.pdf_clicked.connect(self.do_export_pdf)

        # --- Signal wiring: PREVIEW GRID <-> EDITOR LOGIC ---
        self.preview_pane.label_clicked.connect(self.on_label_clicked)
        self.preview_pane.label_right_clicked.connect(self.on_label_right_clicked)

        # --- Load last session (or init) ---
        self.session_manager.load_session()
        self.update_edit_panel_from_selection()
        self.ensure_at_least_one_selected()
        self.refresh_preview()

    def on_converted_price(self, which, value):
        for idx in self.selected:
            self.labels[idx][which]["text"] = value
        self.session_manager.save_session()
        self.refresh_preview()

    def eventFilter(self, obj, ev):
        if ev.type() == ev.FocusIn:
            for k, w in self.left_pane.field_inputs.items():
                if obj is w:
                    self.active_field = k
                    self.update_toolbar_from_field()
                    break
        return super().eventFilter(obj, ev)

    def on_label_clicked(self, idx, event):
        if event.modifiers() & Qt.ControlModifier:
            if idx in self.selected:
                if len(self.selected) > 1:
                    self.selected.remove(idx)
            else:
                self.selected.append(idx)
        elif event.modifiers() & Qt.ShiftModifier and self.selected:
            start, end = min(self.selected[0], idx), max(self.selected[0], idx)
            self.selected = list(range(start, end + 1))
        else:
            self.selected = [idx]
        self.ensure_at_least_one_selected()
        self.update_edit_panel_from_selection()
        self.session_manager.save_session()
        self.refresh_preview()

    def on_label_right_clicked(self, idx, event):
        from PyQt5.QtWidgets import QMenu
        menu = QMenu(self)
        copy_action = menu.addAction("Копирай Етикет")
        copystyle_action = menu.addAction("Копирай форматиране")
        paste_action = menu.addAction("Постави")
        action = menu.exec_(self.preview_pane.label_widgets[idx].mapToGlobal(event.pos()))
        sel = self.selected
        if action == copy_action:
            self.clipboard = {k: self.labels[idx][k].copy() for k in self.labels[idx]}
            self.clipboard_style = None
        elif action == copystyle_action:
            self.clipboard_style = {k: {kk: vv for kk, vv in self.labels[idx][k].items() if kk != "text"} for k in self.labels[idx]}
            self.clipboard = None
        elif action == paste_action:
            if hasattr(self, 'clipboard') and self.clipboard:
                for idx2 in sel:
                    for k in self.labels[idx2]:
                        self.labels[idx2][k] = self.clipboard[k].copy()
            elif hasattr(self, 'clipboard_style') and self.clipboard_style:
                for idx2 in sel:
                    for k in self.labels[idx2]:
                        for sk, vv in self.clipboard_style[k].items():
                            self.labels[idx2][k][sk] = vv
            self.update_edit_panel_from_selection()
        self.session_manager.save_session()
        self.refresh_preview()

    def ensure_at_least_one_selected(self):
        if not self.selected or self.selected[0] >= len(self.labels):
            self.selected = [0] if self.labels else []
        self.preview_pane.set_selected(self.selected)

    def refresh_preview(self):
        self.preview_pane.update_labels(self.labels)

    def update_edit_panel_from_selection(self):
        sel = self.selected
        if not sel:
            return
        main = self.labels[sel[0]]
        placeholders = {"main": "Основен текст", "second": "Втори ред", "bgn": "BGN", "eur": "EUR"}
        for key in self.left_pane.field_inputs:
            vals = [self.labels[idx][key]["text"] for idx in sel]
            placeholder = placeholders[key]
            w = self.left_pane.field_inputs[key]
            w.blockSignals(True)
            if all(v == vals[0] for v in vals):
                if hasattr(w, "setPlainText"):
                    w.setPlainText(vals[0])
                else:
                    w.setText(vals[0])
                w.setPlaceholderText(placeholder)
            else:
                if hasattr(w, "setPlainText"):
                    w.setPlainText("")
                else:
                    w.setText("")
                w.setPlaceholderText("——————разлики——————")
            w.blockSignals(False)
        self.update_toolbar_from_field()
    def update_toolbar_from_field(self):
        sel = self.selected
        if not sel:
            return
        key = self.active_field if hasattr(self, "active_field") else "main"
        vals = [self.labels[idx][key] for idx in sel]
        f = vals[0]
        fonts_same = all(v["font"] == f["font"] for v in vals)
        sizes_same = all(v["size"] == f["size"] for v in vals)
        bold_same = all(v["bold"] == f["bold"] for v in vals)
        italic_same = all(v["italic"] == f["italic"] for v in vals)
        align_same = all(v["align"] == f["align"] for v in vals)
        color_same = all(v["font_color"] == f["font_color"] for v in vals)
        bg_same = all(v["bg_color"] == f["bg_color"] for v in vals)
        self.toolbar.set_toolbar_state(
            font=f["font"] if fonts_same else None,
            size=f["size"] if sizes_same else None,
            bold=f["bold"] if bold_same else None,
            italic=f["italic"] if italic_same else None,
            align=f["align"] if align_same else None,
            font_color=f['font_color'] if color_same else None,
            bg_color=f['bg_color'] if bg_same else None,
        )

    def on_field_edited(self, key, value):
        sel = self.selected
        if not sel:
            return
        for idx in sel:
            self.labels[idx][key]["text"] = value
        self.session_manager.save_session()
        self.refresh_preview()

    def set_font_family(self, fontname):
        sel = self.selected
        if not sel:
            return
        k = self.active_field
        for idx in sel:
            self.labels[idx][k]["font"] = fontname
        self.update_toolbar_from_field()
        self.session_manager.save_session()
        self.refresh_preview()

    def set_font_size(self, size):
        sel = self.selected
        if not sel:
            return
        k = self.active_field
        for idx in sel:
            self.labels[idx][k]["size"] = size
        self.update_toolbar_from_field()
        self.session_manager.save_session()
        self.refresh_preview()

    def set_bold(self, checked):
        sel = self.selected
        if not sel:
            return
        k = self.active_field
        for idx in sel:
            self.labels[idx][k]["bold"] = checked
        self.update_toolbar_from_field()
        self.session_manager.save_session()
        self.refresh_preview()

    def set_italic(self, checked):
        sel = self.selected
        if not sel:
            return
        k = self.active_field
        for idx in sel:
            self.labels[idx][k]["italic"] = checked
        self.update_toolbar_from_field()
        self.session_manager.save_session()
        self.refresh_preview()

    def set_alignment(self, align_value):
        sel = self.selected
        if not sel:
            return
        k = self.active_field
        for idx in sel:
            self.labels[idx][k]["align"] = align_value
        self.update_toolbar_from_field()
        self.session_manager.save_session()
        self.refresh_preview()

    def set_field_color(self, prop, val):
        sel = self.selected
        if not sel:
            return
        k = self.active_field
        for idx in sel:
            self.labels[idx][k][prop] = val
        self.update_toolbar_from_field()
        self.session_manager.save_session()
        self.refresh_preview()

    def do_print(self):
        from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
        from PyQt5.QtGui import QPainter, QColor, QFont
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPrinter.A4)
        printer.setOrientation(QPrinter.Portrait)
        dialog = QPrintDialog(printer, self)
        if dialog.exec_() == QPrintDialog.Accepted:
            painter = QPainter(printer)
            self.render_sheet(painter, printer.resolution())
            painter.end()

    def do_export_pdf(self):
        from PyQt5.QtGui import QPagedPaintDevice, QPdfWriter, QPainter, QColor, QFont
        from PyQt5.QtWidgets import QFileDialog
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
        # MOST IMPORTANT: scaling factor
        scale_correction = settings.get('user_scale_factor', 1.0)

        px_per_mm = dpi / 25.4 * scale_correction
        sheet_w_px = int(sheet_w * px_per_mm)
        sheet_h_px = int(sheet_h * px_per_mm)
        label_w_px = int(label_w * px_per_mm)
        label_h_px = int(label_h * px_per_mm)
        margin_left_px = int(margin_left * px_per_mm)
        margin_top_px = int(margin_top * px_per_mm)
        spacing_x_px = int(spacing_x * px_per_mm)
        spacing_y_px = int(spacing_y * px_per_mm)

        qp.setRenderHint(qp.Antialiasing)
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
        from PyQt5.QtGui import QColor, QFont
        qp.save()
        qp.setPen(Qt.NoPen)
        qp.setBrush(QColor(label["main"]["bg_color"]))
        qp.drawRect(x, y, w, h)
        margin = int(12 * w / 150)
        x0, y0 = x + margin, y + margin
        ww, hh = w - 2 * margin, h - 2 * margin
        lines = []
        for key in ["main", "second", "bgn", "eur"]:
            fld = label[key]
            t = fld["text"]
            if key == "bgn":
                t = t.replace(" лв.", "").replace("лв.", "").strip()
                if t:
                    t += " лв."
            if key == "eur":
                t = t.replace("€", "").strip()
                if t:
                    t = "€" + t
            if t:
                lines.append((t, fld))
        total_h, metrics = 0, []
        for text, field in lines:
            fnt = QFont(field['font'], int(field['size']))
            fnt.setBold(field['bold'])
            fnt.setItalic(field['italic'])
            qp.setFont(fnt)
            fm = qp.fontMetrics()
            rect_t = fm.boundingRect(0, 0, ww, hh, field['align'] | Qt.TextWordWrap, text)
            metrics.append((rect_t.height(), field, text, fnt))
            total_h += rect_t.height()
        cy = y0 + (hh - total_h) // 2
        for hgt, field, text, fnt in metrics:
            qp.setFont(fnt)
            qp.setPen(QColor(field.get("font_color", "#222")))
            rect_t = qp.fontMetrics().boundingRect(0, 0, ww, hgt, field['align'] | Qt.TextWordWrap, text)
            draw_rect = rect_t.translated(x0, cy)
            qp.drawText(draw_rect, field['align'] | Qt.TextWordWrap, text)
            cy += hgt
        qp.restore()

    def reload_from_calibration(self):
        self.sheet_settings = load_sheet_settings()
        self.rows = self.sheet_settings.get('rows', 3)
        self.cols = self.sheet_settings.get('cols', 3)
        self.label_w_mm = self.sheet_settings.get('label_w', 63.5)
        self.label_h_mm = self.sheet_settings.get('label_h', 38.1)
        label_count = self.rows * self.cols
        if len(self.labels) < label_count:
            for _ in range(label_count - len(self.labels)):
                self.labels.append(blank_label())
        elif len(self.labels) > label_count:
            self.labels = self.labels[:label_count]
        self.selected = [min(self.selected[0], label_count - 1)] if self.selected and label_count else []
        self.preview_pane.update_calibration(self.rows, self.cols, self.label_w_mm, self.label_h_mm)
        self.refresh_preview()
        self.update_edit_panel_from_selection()
        self.ensure_at_least_one_selected()

if __name__ == "__main__":
    from PyQt5.QtGui import QFontDatabase
    FONT_DB = QFontDatabase()
    FONTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
    FONT_LIST = []
    if os.path.isdir(FONTS_DIR):
        for fname in os.listdir(FONTS_DIR):
            if fname.lower().endswith('.ttf'):
                family_id = FONT_DB.addApplicationFont(os.path.join(FONTS_DIR, fname))
                families = FONT_DB.applicationFontFamilies(family_id)
                if families:
                    FONT_LIST.extend(families)
    if not FONT_LIST:
        FONT_LIST = ["Arial"]
    app = QApplication(sys.argv)
    win = LabelSheetEditor(FONT_LIST)
    win.resize(1550, 1050)
    win.show()
    sys.exit(app.exec_())
