import sys, os, json
from functools import partial

from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QMessageBox, QSizePolicy
)
from PyQt5.QtCore import Qt

from left_pane import LeftPaneWidget
from preview_pane import PreviewPaneWidget

from currency_manager import CurrencyManager
from session_manager import SessionManager

from label_drawing import draw_label_print

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
    print("Loading sheet settings from:", path)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data  # <-- Return the whole dict, not just data.get("params", {})
        except Exception:
            return {}
    return {}

class LabelSheetEditor(QWidget):
    def __init__(self, font_list):
        super().__init__()
        self.setWindowTitle("Строймаркет Цаков – Етикетен инструмент – Версия: 3.0.0")
        self.font_list = font_list

        self.sheet_settings = load_sheet_settings()
        params = self.sheet_settings.get('params', {})
        self.rows = params.get('rows', 3)
        self.cols = params.get('cols', 3)
        self.label_w_mm = params.get('label_w', 63.5)
        self.label_h_mm = params.get('label_h', 38.1)
        self.label_aspect = self.label_w_mm / self.label_h_mm if self.label_h_mm else 1.0

        self.labels = [blank_label() for _ in range(self.rows*self.cols)]
        self.selected = [0] if self.labels else []
        self.active_field = "main"

        self.debug_draw_boxes = False  # For developer debugging

        main_h = QHBoxLayout(self)

        # --- LEFT PANE ---
        left_panel = QVBoxLayout()
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

        # --- Managers ---
        self.currency_manager = CurrencyManager(
            self.left_pane.field_inputs['bgn'], self.left_pane.field_inputs['eur']
        )
        self.session_manager = SessionManager(self)

        # --- Currency: Connect signal for preview update ---
        self.currency_manager.price_converted.connect(self.on_converted_price)

        # --- Signal wiring: LEFT PANE <-> EDITOR LOGIC ---
        self.left_pane.text_changed.connect(self.on_field_edited)
        self.left_pane.style_changed.connect(self.on_field_style_changed)
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

    def on_field_edited(self, key, value):
        sel = self.selected
        if not sel:
            return
        for idx in sel:
            self.labels[idx][key]["text"] = value
        self.session_manager.save_session()
        self.refresh_preview()

    def on_field_style_changed(self, key, style):
        # Update style for all selected labels for this field
        sel = self.selected
        if not sel:
            return
        for idx in sel:
            for prop, val in style.items():
                self.labels[idx][key][prop] = val
        self.session_manager.save_session()
        self.refresh_preview()

    def eventFilter(self, obj, ev):
        # No toolbar anymore, but if you want to keep track of active_field for future use
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
        action = menu.exec_(self.preview_pane.mapToGlobal(event.pos()))
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
        # --- Also update each field toolbar to reflect selected label's style
        for key in self.left_pane.field_toolbars:
            style = self.labels[sel[0]][key]
            self.left_pane.set_toolbar_state(key, style)

    def do_print(self):
        from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
        from PyQt5.QtGui import QPainter
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPrinter.A4)
        printer.setOrientation(QPrinter.Portrait)
        dialog = QPrintDialog(printer, self)
        if dialog.exec_() == QPrintDialog.Accepted:
            painter = QPainter(printer)
            self.render_sheet(painter, printer.resolution())
            painter.end()

    def do_export_pdf(self):
        from PyQt5.QtGui import QPagedPaintDevice, QPdfWriter, QPainter
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
        settings = load_sheet_settings()
        params = settings.get("params", {})
        hw_left = float(params.get('hw_left', 0))
        hw_top = float(params.get('hw_top', 0))
        hw_right = float(params.get('hw_right', 0))
        hw_bottom = float(params.get('hw_bottom', 0))
        sheet_left = float(params.get('sheet_left', 0))
        sheet_top = float(params.get('sheet_top', 0))
        label_w = float(params.get('label_w', 63.5))
        label_h = float(params.get('label_h', 38.1))
        col_gap = float(params.get('col_gap', 0))
        row_gap = float(params.get('row_gap', 0))
        rows = int(params.get('rows', 3))
        cols = int(params.get('cols', 3))
        scale_correction = float(params.get('user_scale_factor', 1.0))
        page_w = float(params.get('page_w', 210))
        page_h = float(params.get('page_h', 297))

        skip_hw_margin = settings.get("skip_hw_margin", False)
        if skip_hw_margin:
            hw_left = hw_top = hw_right = hw_bottom = 0

        # Correct: always read font_scale_factor from the ROOT of settings!
        font_scale_factor = float(settings.get("font_scale_factor", 1.0))

        print("skip_hw_margin =", skip_hw_margin, "hw_left =", hw_left, "hw_top =", hw_top, "font_scale_factor =", font_scale_factor)

        px_per_mm = dpi / 25.4 * scale_correction
        page_w_px = round(page_w * px_per_mm)
        page_h_px = round(page_h * px_per_mm)

        qp.setRenderHint(qp.Antialiasing)
        qp.setBrush(Qt.white)
        qp.setPen(Qt.NoPen)
        qp.drawRect(0, 0, page_w_px, page_h_px)

        idx = 0
        for row in range(rows):
            for col in range(cols):
                if idx >= len(self.labels):
                    break
                x_mm = hw_left + sheet_left + col * (label_w + col_gap)
                y_mm = hw_top + sheet_top + row * (label_h + row_gap)
                x = round(x_mm * px_per_mm)
                y = round(y_mm * px_per_mm)
                w = round(label_w * px_per_mm)
                h = round(label_h * px_per_mm)
                if self.debug_draw_boxes:
                    from PyQt5.QtGui import QPen, QColor
                    qp.save()
                    qp.setPen(QPen(QColor("#FF3333"), 2, Qt.DashLine))
                    qp.setBrush(Qt.NoBrush)
                    qp.drawRect(x, y, w, h)
                    qp.restore()
                draw_label_print(qp, x, y, w, h, self.labels[idx], font_scale=font_scale_factor)
                idx += 1


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
