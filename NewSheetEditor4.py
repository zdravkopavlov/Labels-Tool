import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QSizePolicy, QPushButton, QFileDialog
)
from PyQt5.QtGui import QPainter, QColor, QPen, QFont
from PyQt5.QtCore import Qt

MM_TO_PX = 72 / 25.4  # 1 mm in points (typical printer/screen DPI)

def appdata_path():
    # Cross-platform appdata path
    from pathlib import Path
    return os.path.join(str(Path.home()), "AppData", "Roaming", "LabelTool")

def sheet_settings_path():
    return os.path.join(appdata_path(), "sheet_settings.json")

def ensure_appdata():
    os.makedirs(appdata_path(), exist_ok=True)

def save_sheet_settings(data):
    ensure_appdata()
    with open(sheet_settings_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_sheet_settings():
    try:
        with open(sheet_settings_path(), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

class SheetPreview(QWidget):
    def __init__(self, params, toggles, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.params = params
        self.toggles = toggles
        self.setMinimumSize(800, 600)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._print_mode = False

    def paintEvent(self, event):
        p = self.params
        t = self.toggles

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # ----------- OUTER (physical) PAGE AREA -----------
        page_w_mm = p['page_w']
        page_h_mm = p['page_h']

        # Hardware margins: all dimensions in mm
        hw_left = p['hw_left']
        hw_top = p['hw_top']
        hw_right = p['hw_right']
        hw_bottom = p['hw_bottom']

        # Usable area (printable)
        usable_x_mm = hw_left
        usable_y_mm = hw_top
        usable_w_mm = page_w_mm - hw_left - hw_right
        usable_h_mm = page_h_mm - hw_top - hw_bottom

        # Sheet margins (on sticker sheet)
        sheet_left = p['sheet_left']
        sheet_top = p['sheet_top']

        # Label area within usable area
        label_w = p['label_w']
        label_h = p['label_h']
        col_gap = p['col_gap']
        row_gap = p['row_gap']
        rows = p['rows']
        cols = p['cols']

        # Calculate the entire drawn sheet (incl. sticker margins)
        total_label_w = cols * label_w + (cols - 1) * col_gap
        total_label_h = rows * label_h + (rows - 1) * row_gap

        # Calculate area for drawing:
        # (All inside usable area, and respecting sticker sheet margins)
        draw_x_mm = usable_x_mm + sheet_left
        draw_y_mm = usable_y_mm + sheet_top
        draw_w_mm = total_label_w
        draw_h_mm = total_label_h

        # Fit usable (printable) area to widget, keep aspect ratio
        scale = min((w-40) / (usable_w_mm * MM_TO_PX), (h-40) / (usable_h_mm * MM_TO_PX))
        offset_x = (w - usable_w_mm * MM_TO_PX * scale) / 2
        offset_y = (h - usable_h_mm * MM_TO_PX * scale) / 2

        def mm_to_px(x_mm, y_mm):
            return (
                offset_x + (x_mm - usable_x_mm) * MM_TO_PX * scale,
                offset_y + (y_mm - usable_y_mm) * MM_TO_PX * scale,
            )

        # --------- BACKGROUND (Gray fill for calibration only) ----------
        if t['gray_base'] and (not self._print_mode or (self._print_mode and t['gray_base'])):
            # Only on preview, or if explicitly requested in print
            x0, y0 = mm_to_px(usable_x_mm, usable_y_mm)
            w_px = usable_w_mm * MM_TO_PX * scale
            h_px = usable_h_mm * MM_TO_PX * scale
            painter.fillRect(int(x0), int(y0), int(w_px), int(h_px), QColor("#dddddd"))

        else:
            # White for printing, white for preview if gray is not enabled
            x0, y0 = mm_to_px(usable_x_mm, usable_y_mm)
            w_px = usable_w_mm * MM_TO_PX * scale
            h_px = usable_h_mm * MM_TO_PX * scale
            painter.fillRect(int(x0), int(y0), int(w_px), int(h_px), Qt.white)

        # --------- SHEET BORDER (Gray or dashed) -------------
        if t['sheet_border']:
            x0, y0 = mm_to_px(usable_x_mm, usable_y_mm)
            w_px = usable_w_mm * MM_TO_PX * scale
            h_px = usable_h_mm * MM_TO_PX * scale
            pen = QPen(QColor("#888888"), 2)
            if not t['gray_base']:
                pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            painter.drawRect(int(x0), int(y0), int(w_px), int(h_px))

        # --------- RULERS (ticks only, no text) --------------
        if t['ruler']:
            painter.setPen(QPen(QColor("#444"), 1))
            # Top ruler
            for mm in range(0, int(usable_w_mm)+1):
                x = offset_x + mm * MM_TO_PX * scale
                y0 = offset_y - 14
                y1 = offset_y
                if mm % 10 == 0:
                    painter.drawLine(int(x), int(y0), int(x), int(y1))
                elif mm % 5 == 0:
                    painter.drawLine(int(x), int(y0+7), int(x), int(y1))
                else:
                    painter.drawLine(int(x), int(y0+10), int(x), int(y1))
            # Left ruler
            for mm in range(0, int(usable_h_mm)+1):
                y = offset_y + mm * MM_TO_PX * scale
                x0 = offset_x - 14
                x1 = offset_x
                if mm % 10 == 0:
                    painter.drawLine(int(x0), int(y), int(x1), int(y))
                elif mm % 5 == 0:
                    painter.drawLine(int(x0+7), int(y), int(x1), int(y))
                else:
                    painter.drawLine(int(x0+10), int(y), int(x1), int(y))

        # --------- LABEL GRID ---------------
        if t['grid'] or t['crosshairs']:
            for row in range(rows):
                for col in range(cols):
                    x_mm = draw_x_mm + col * (label_w + col_gap)
                    y_mm = draw_y_mm + row * (label_h + row_gap)
                    x, y = mm_to_px(x_mm, y_mm)
                    w_px = label_w * MM_TO_PX * scale
                    h_px = label_h * MM_TO_PX * scale
                    if t['grid']:
                        painter.setPen(QPen(QColor("#333333"), 2))
                        painter.drawRect(int(x), int(y), int(w_px), int(h_px))

        # ---- Crosshairs in column gaps only ----
        if t['crosshairs']:
            ch_len = 14 * scale  # crosshair size in px
            pen = QPen(QColor("#bd2323"), 1.6)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            # Calculate gap centers
            row_centers_mm = []
            for r in range(rows - 1):
                y1 = draw_y_mm + (r + 1) * label_h + r * row_gap
                y2 = y1 + row_gap
                center_y = y1 + (y2 - y1) / 2 if row_gap > 0 else y1
                row_centers_mm.append(center_y)
            col_centers_mm = []
            for c in range(cols - 1):
                x1 = draw_x_mm + (c + 1) * label_w + c * col_gap
                x2 = x1 + col_gap
                center_x = x1 + (x2 - x1) / 2 if col_gap > 0 else x1
                col_centers_mm.append(center_x)
            for y_mm in row_centers_mm:
                for x_mm in col_centers_mm:
                    x, y = mm_to_px(x_mm, y_mm)
                    painter.drawLine(int(x - ch_len/2), int(y), int(x + ch_len/2), int(y))
                    painter.drawLine(int(x), int(y - ch_len/2), int(x), int(y + ch_len/2))

    def set_print_mode(self, on):
        self._print_mode = on

class SheetEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Редактор на лист – Калибриране")
        self.params = self.default_params()
        self.toggles = {
            'gray_base': False,
            'sheet_border': True,
            'grid': True,
            'crosshairs': True,
            'ruler': True,
        }
        # Try to load settings
        loaded = load_sheet_settings()
        if loaded:
            self.params.update(loaded.get("params", {}))
            self.toggles.update(loaded.get("toggles", {}))
        self.init_ui()

    def default_params(self):
        # All values in mm
        return {
            # --- Printer hardware margins (mm) ---
            'hw_left': 4.0, 'hw_top': 5.0, 'hw_right': 4.0, 'hw_bottom': 6.0,
            # --- Physical sheet size (mm) ---
            'page_w': 210.0, 'page_h': 297.0,
            # --- Sticker sheet margins ---
            'sheet_left': 7.0, 'sheet_top': 15.0,
            # --- Label parameters ---
            'label_w': 63.5, 'label_h': 38.1,
            'col_gap': 3.0, 'row_gap': 0.0,
            'rows': 7, 'cols': 3,
        }

    def save_settings(self):
        save_sheet_settings({
            "params": self.params,
            "toggles": self.toggles,
        })

    def init_ui(self):
        main_h = QHBoxLayout(self)
        controls = QVBoxLayout()

        # --------- Printer HW Margins group ----------
        gb_hw = QGroupBox("Полеви ограничения на принтера (mm)")
        l_hw = QHBoxLayout(gb_hw)
        self.sp_hw_left = QDoubleSpinBox(self); self.sp_hw_left.setRange(0, 50); self.sp_hw_left.setDecimals(2); self.sp_hw_left.setValue(self.params['hw_left'])
        self.sp_hw_top = QDoubleSpinBox(self); self.sp_hw_top.setRange(0, 50); self.sp_hw_top.setDecimals(2); self.sp_hw_top.setValue(self.params['hw_top'])
        self.sp_hw_right = QDoubleSpinBox(self); self.sp_hw_right.setRange(0, 50); self.sp_hw_right.setDecimals(2); self.sp_hw_right.setValue(self.params['hw_right'])
        self.sp_hw_bottom = QDoubleSpinBox(self); self.sp_hw_bottom.setRange(0, 50); self.sp_hw_bottom.setDecimals(2); self.sp_hw_bottom.setValue(self.params['hw_bottom'])
        l_hw.addWidget(QLabel("Ляво")); l_hw.addWidget(self.sp_hw_left)
        l_hw.addWidget(QLabel("Горе")); l_hw.addWidget(self.sp_hw_top)
        l_hw.addWidget(QLabel("Дясно")); l_hw.addWidget(self.sp_hw_right)
        l_hw.addWidget(QLabel("Долу")); l_hw.addWidget(self.sp_hw_bottom)
        controls.addWidget(gb_hw)

        for box, key in [
            (self.sp_hw_left, 'hw_left'), (self.sp_hw_top, 'hw_top'),
            (self.sp_hw_right, 'hw_right'), (self.sp_hw_bottom, 'hw_bottom')
        ]:
            box.valueChanged.connect(lambda val, k=key: self.update_param(k, float(val)))

        # --------- Sticker Sheet Margins group ----------
        gb_sheet = QGroupBox("Полеви ограничения на стикерния лист (mm)")
        l_sheet = QHBoxLayout(gb_sheet)
        self.sp_sheet_left = QDoubleSpinBox(self); self.sp_sheet_left.setRange(0, 100); self.sp_sheet_left.setDecimals(2); self.sp_sheet_left.setValue(self.params['sheet_left'])
        self.sp_sheet_top = QDoubleSpinBox(self); self.sp_sheet_top.setRange(0, 100); self.sp_sheet_top.setDecimals(2); self.sp_sheet_top.setValue(self.params['sheet_top'])
        l_sheet.addWidget(QLabel("Ляво")); l_sheet.addWidget(self.sp_sheet_left)
        l_sheet.addWidget(QLabel("Горе")); l_sheet.addWidget(self.sp_sheet_top)
        controls.addWidget(gb_sheet)

        for box, key in [
            (self.sp_sheet_left, 'sheet_left'), (self.sp_sheet_top, 'sheet_top')
        ]:
            box.valueChanged.connect(lambda val, k=key: self.update_param(k, float(val)))

        # --------- Label Size & Gaps group ----------
        gb_labels = QGroupBox("Размери и разстояния на етикетите (mm)")
        l_labels = QHBoxLayout(gb_labels)
        self.sp_w = QDoubleSpinBox(self); self.sp_w.setRange(1, 200); self.sp_w.setDecimals(2); self.sp_w.setSingleStep(0.1); self.sp_w.setValue(self.params['label_w'])
        self.sp_h = QDoubleSpinBox(self); self.sp_h.setRange(1, 200); self.sp_h.setDecimals(2); self.sp_h.setSingleStep(0.1); self.sp_h.setValue(self.params['label_h'])
        self.sp_cgap = QDoubleSpinBox(self); self.sp_cgap.setRange(0, 50); self.sp_cgap.setDecimals(2); self.sp_cgap.setSingleStep(0.1); self.sp_cgap.setValue(self.params['col_gap'])
        self.sp_rgap = QDoubleSpinBox(self); self.sp_rgap.setRange(0, 50); self.sp_rgap.setDecimals(2); self.sp_rgap.setSingleStep(0.1); self.sp_rgap.setValue(self.params['row_gap'])
        l_labels.addWidget(QLabel("Широчина")); l_labels.addWidget(self.sp_w)
        l_labels.addWidget(QLabel("Височина")); l_labels.addWidget(self.sp_h)
        l_labels.addWidget(QLabel("Хор. разстояние")); l_labels.addWidget(self.sp_cgap)
        l_labels.addWidget(QLabel("Вер. разстояние")); l_labels.addWidget(self.sp_rgap)
        controls.addWidget(gb_labels)

        for box, key in [
            (self.sp_w, 'label_w'), (self.sp_h, 'label_h'),
            (self.sp_cgap, 'col_gap'), (self.sp_rgap, 'row_gap')
        ]:
            box.valueChanged.connect(lambda val, k=key: self.update_param(k, float(val)))

        # --------- Rows & Columns group ----------
        gb_rc = QGroupBox("Брой редове и колони")
        l_rc = QHBoxLayout(gb_rc)
        self.sp_rows = QSpinBox(self); self.sp_rows.setRange(1, 20); self.sp_rows.setValue(self.params['rows'])
        self.sp_cols = QSpinBox(self); self.sp_cols.setRange(1, 20); self.sp_cols.setValue(self.params['cols'])
        l_rc.addWidget(QLabel("Редове")); l_rc.addWidget(self.sp_rows)
        l_rc.addWidget(QLabel("Колони")); l_rc.addWidget(self.sp_cols)
        controls.addWidget(gb_rc)
        self.sp_rows.valueChanged.connect(lambda val: self.update_param('rows', int(val)))
        self.sp_cols.valueChanged.connect(lambda val: self.update_param('cols', int(val)))

        # --------- Visual Helpers group ----------
        gb_vis = QGroupBox("Визуални помощници")
        l_vis = QVBoxLayout(gb_vis)
        self.chk_gray = QCheckBox("Покажи сива основа"); self.chk_gray.setChecked(self.toggles['gray_base'])
        self.chk_border = QCheckBox("Покажи рамка на листа"); self.chk_border.setChecked(self.toggles['sheet_border'])
        self.chk_grid = QCheckBox("Показвай мрежата"); self.chk_grid.setChecked(self.toggles['grid'])
        self.chk_ch = QCheckBox("Показвай кръстчета"); self.chk_ch.setChecked(self.toggles['crosshairs'])
        self.chk_ruler = QCheckBox("Показвай линийка"); self.chk_ruler.setChecked(self.toggles['ruler'])
        for chk, k in [
            (self.chk_gray, 'gray_base'), (self.chk_border, 'sheet_border'),
            (self.chk_grid, 'grid'), (self.chk_ch, 'crosshairs'), (self.chk_ruler, 'ruler')
        ]:
            chk.stateChanged.connect(lambda _, k=k: self.toggle_overlay(k))
            l_vis.addWidget(chk)
        controls.addWidget(gb_vis)
        controls.addSpacing(10)

        # Print button
        self.btn_print = QPushButton("Печатай")
        self.btn_print.clicked.connect(self.print_sheet)
        controls.addWidget(self.btn_print)
        controls.addStretch(1)

        main_h.addLayout(controls, 0)
        self.preview = SheetPreview(self.params, self.toggles)
        main_h.addWidget(self.preview, 1)

    def update_param(self, key, value):
        self.params[key] = value
        self.preview.update()
        self.save_settings()

    def toggle_overlay(self, key):
        toggle_names = {
            "gray_base": "chk_gray",
            "sheet_border": "chk_border",
            "grid": "chk_grid",
            "crosshairs": "chk_ch",
            "ruler": "chk_ruler"
        }
        widget = getattr(self, toggle_names[key])
        self.toggles[key] = widget.isChecked()
        self.preview.update()
        self.save_settings()


    def print_sheet(self):
        from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
        printer = QPrinter(QPrinter.HighResolution)
        printer.setFullPage(True)
        dlg = QPrintDialog(printer, self)
        if dlg.exec_() == QPrintDialog.Accepted:
            self.preview.set_print_mode(True)
            painter = QPainter(printer)
            page_rect = printer.pageRect()
            # Resize preview to printable area
            old_size = self.preview.size()
            self.preview.resize(page_rect.width(), page_rect.height())
            self.preview.render(painter)
            self.preview.resize(old_size)
            painter.end()
            self.preview.set_print_mode(False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = SheetEditor()
    win.resize(1200, 850)
    win.show()
    sys.exit(app.exec_())
