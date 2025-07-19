import sys
import os
import json
import printer
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QSizePolicy, QPushButton
)
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QPainterPath
from PyQt5.QtCore import Qt

MM_TO_PX = 72 / 25.4

def appdata_path():
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
        self.calibration_mode = False
        self.rendering_for_print = False # Flag to indicate if rendering is for print

    def set_calibration_mode(self, on):
        self.calibration_mode = on
        self.update()

    def paintEvent(self, event):
        p = self.params
        t = self.toggles
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        page_w_mm = p['page_w']
        page_h_mm = p['page_h']
        hw_left = p['hw_left']
        hw_top = p['hw_top']
        hw_right = p['hw_right']
        hw_bottom = p['hw_bottom']
        usable_x_mm = hw_left
        usable_y_mm = hw_top
        usable_w_mm = page_w_mm - hw_left - hw_right
        usable_h_mm = page_h_mm - hw_top - hw_bottom

        sheet_left = p['sheet_left']
        sheet_top = p['sheet_top']
        label_w = p['label_w']
        label_h = p['label_h']
        col_gap = p['col_gap']
        row_gap = p['row_gap']
        rows = p['rows']
        cols = p['cols']
        corner_radius = 2.5 if t['rounded'] else 0

        cal_square = t.get('cal_square', False)
        cal_square_size = 10.0

        total_label_w = cols * label_w + (cols - 1) * col_gap
        total_label_h = rows * label_h + (rows - 1) * row_gap
        draw_x_mm = usable_x_mm + sheet_left
        draw_y_mm = usable_y_mm + sheet_top

        # --- CRITICAL: Always center preview on screen, but use offset=0 when printing ---
        scale = min((w-40) / (page_w_mm * MM_TO_PX), (h-40) / (page_h_mm * MM_TO_PX))
        if getattr(self, 'rendering_for_print', False):
            offset_x = 0
            offset_y = 0
        else:
            offset_x = (w - page_w_mm * MM_TO_PX * scale) / 2
            offset_y = (h - page_h_mm * MM_TO_PX * scale) / 2

        def mm_to_px(x_mm, y_mm):
            return (
                offset_x + x_mm * MM_TO_PX * scale,
                offset_y + y_mm * MM_TO_PX * scale,
            )

        # CALIBRATION PRINT (solid gray)
        if self.calibration_mode:
            page_x, page_y = mm_to_px(0, 0)
            page_w = page_w_mm * MM_TO_PX * scale
            page_h = page_h_mm * MM_TO_PX * scale
            painter.fillRect(int(page_x), int(page_y), int(page_w), int(page_h), QColor("#dddddd"))
            return

        # --- Draw A4 background and border (should now align perfectly when printing) ---
        page_x, page_y = mm_to_px(0, 0)
        page_w = page_w_mm * MM_TO_PX * scale
        page_h = page_h_mm * MM_TO_PX * scale
        painter.fillRect(int(page_x), int(page_y), int(page_w), int(page_h), Qt.white)
        painter.setPen(QPen(QColor("#888888"), 2, Qt.DashLine))
        painter.drawRect(int(page_x), int(page_y), int(page_w), int(page_h))

        # HW margin rectangle (toggleable!)
        margin_x, margin_y = mm_to_px(hw_left, hw_top)
        margin_w = (page_w_mm - hw_left - hw_right) * MM_TO_PX * scale
        margin_h = (page_h_mm - hw_top - hw_bottom) * MM_TO_PX * scale
        if t.get('show_hw_margin', True):
            painter.setPen(QPen(QColor("#228"), 2, Qt.DashLine))
            painter.drawRect(int(margin_x), int(margin_y), int(margin_w), int(margin_h))

        # Ruler
        if t.get('ruler', True):
            painter.setPen(QPen(QColor("#444"), 2))
            for mm in range(0, int(page_w_mm)+1):
                x = page_x + mm * MM_TO_PX * scale
                y0r = page_y - 18
                y1r = page_y
                if mm % 10 == 0:
                    painter.drawLine(int(x), int(y0r), int(x), int(y1r))
                elif mm % 5 == 0:
                    painter.drawLine(int(x), int(y0r+7), int(x), int(y1r))
                else:
                    painter.drawLine(int(x), int(y0r+13), int(x), int(y1r))
            for mm in range(0, int(page_h_mm)+1):
                y = page_y + mm * MM_TO_PX * scale
                x0r = page_x - 18
                x1r = page_x
                if mm % 10 == 0:
                    painter.drawLine(int(x0r), int(y), int(x1r), int(y))
                elif mm % 5 == 0:
                    painter.drawLine(int(x0r+7), int(y), int(x1r), int(y))
                else:
                    painter.drawLine(int(x0r+13), int(y), int(x1r), int(y))

        # Draw label grid and calibration squares
        for row in range(rows):
            for col in range(cols):
                x_mm = draw_x_mm + col * (label_w + col_gap)
                y_mm = draw_y_mm + row * (label_h + row_gap)
                x, y = mm_to_px(x_mm, y_mm)
                w_label_px = label_w * MM_TO_PX * scale
                h_label_px = label_h * MM_TO_PX * scale

                if t.get('grid', True):
                    painter.setPen(QPen(QColor("#333333"), 2))
                    if corner_radius > 0:
                        radius_px = corner_radius * MM_TO_PX * scale
                        path = QPainterPath()
                        path.addRoundedRect(x, y, w_label_px, h_label_px, radius_px, radius_px)
                        painter.drawPath(path)
                    else:
                        painter.drawRect(int(x), int(y), int(w_label_px), int(h_label_px))

                if cal_square:
                    sq_size_px = cal_square_size * MM_TO_PX * scale
                    cx = x + w_label_px / 2
                    cy = y + h_label_px / 2
                    left = cx - sq_size_px / 2
                    top = cy - sq_size_px / 2
                    painter.setPen(QPen(QColor("#111"), 2))
                    painter.drawRect(int(left), int(top), int(sq_size_px), int(sq_size_px))
                    crosshair_len = sq_size_px * 0.7
                    painter.drawLine(int(cx - crosshair_len/2), int(cy), int(cx + crosshair_len/2), int(cy))
                    painter.drawLine(int(cx), int(cy - crosshair_len/2), int(cx), int(cy + crosshair_len/2))
                    font = QFont("Arial", 12, QFont.Normal)
                    painter.setFont(font)
                    painter.drawText(int(cx - 22), int(top - 5), "10 mm")

        # CROSSHAIRS (trusted, only this block added!)
        if t.get('crosshairs', True):
            ch_len = 14 * scale
            pen = QPen(QColor("#bd2323"), 1.6)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            row_centers_mm = []
            for r in range(rows - 1):
                y1 = draw_x_mm + (r + 1) * label_h + r * row_gap
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

class CalibrationTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Калибрация на печат и етикети")
        self.params = self.default_params()
        self.toggles = {
            'grid': True,
            'crosshairs': True,
            'ruler': True,
            'rounded': False,
            'cal_square': False,
            'show_hw_margin': True
        }
        loaded = load_sheet_settings()
        if loaded:
            self.params.update(loaded.get("params", {}))
            self.toggles.update(loaded.get("toggles", {}))
        self.init_ui()
        self.update_helper_labels()

    def default_params(self):
        return {
            'hw_left': 8.0, 'hw_top': 8.0, 'hw_right': 8.0, 'hw_bottom': 8.0,
            'page_w': 210.0, 'page_h': 297.0,
            'sheet_left': 0.0, 'sheet_top': 0.0,
            'label_w': 63.5, 'label_h': 38.1,
            'col_gap': 2.0, 'row_gap': 0.0,
            'rows': 7, 'cols': 3,
        }

    def save_settings(self):
        save_sheet_settings({
            "params": self.params,
            "toggles": self.toggles,
        })

    def update_helper_labels(self):
        offset_left = self.params['hw_left'] + self.params['sheet_left']
        offset_top = self.params['hw_top'] + self.params['sheet_top']
        self.lbl_left_offset.setText(f"Общо разстояние от ляв ръб до етикет: {offset_left:.1f} мм")
        self.lbl_top_offset.setText(f"Общо разстояние от горен ръб до етикет: {offset_top:.1f} мм")

    def init_ui(self):
        main_h = QHBoxLayout(self)
        controls = QVBoxLayout()

        self.btn_calib_print = QPushButton("Калибриращ печат (сив фон)")
        self.btn_calib_print.clicked.connect(self.print_calibration)
        controls.addWidget(self.btn_calib_print)
        self.btn_print = QPushButton("Печатай")
        self.btn_print.clicked.connect(self.print_sheet)
        controls.addWidget(self.btn_print)

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

        self.lbl_left_offset = QLabel()
        self.lbl_top_offset = QLabel()
        controls.addWidget(self.lbl_left_offset)
        controls.addWidget(self.lbl_top_offset)

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

        l_labels2 = QVBoxLayout()
        self.chk_rounded = QCheckBox("Заоблени ъгли на етикетите"); self.chk_rounded.setChecked(self.toggles['rounded'])
        self.chk_rounded.stateChanged.connect(lambda _: self.toggle_overlay('rounded'))
        l_labels2.addWidget(self.chk_rounded)
        l_labels.addLayout(l_labels2)

        gb_rc = QGroupBox("Брой редове и колони")
        l_rc = QHBoxLayout(gb_rc)
        self.sp_rows = QSpinBox(self); self.sp_rows.setRange(1, 20); self.sp_rows.setValue(self.params['rows'])
        self.sp_cols = QSpinBox(self); self.sp_cols.setRange(1, 20); self.sp_cols.setValue(self.params['cols'])
        l_rc.addWidget(QLabel("Редове")); l_rc.addWidget(self.sp_rows)
        l_rc.addWidget(QLabel("Колони")); l_rc.addWidget(self.sp_cols)
        controls.addWidget(gb_rc)
        self.sp_rows.valueChanged.connect(lambda val: self.update_param('rows', int(val)))
        self.sp_cols.valueChanged.connect(lambda val: self.update_param('cols', int(val)))

        gb_vis = QGroupBox("Визуални помощници")
        l_vis = QVBoxLayout(gb_vis)
        self.chk_ruler = QCheckBox("Покажи линийка на екрана"); self.chk_ruler.setChecked(self.toggles['ruler'])
        self.chk_grid = QCheckBox("Показвай мрежата"); self.chk_grid.setChecked(self.toggles['grid'])
        self.chk_cal_square = QCheckBox("Покажи калибрационен квадрат"); self.chk_cal_square.setChecked(self.toggles['cal_square'])
        self.chk_crosses = QCheckBox("Показвай кръстчета"); self.chk_crosses.setChecked(self.toggles['crosshairs'])
        self.chk_hw_margin = QCheckBox("Покажи рамка на принтера"); self.chk_hw_margin.setChecked(self.toggles['show_hw_margin'])
        for chk, k in [
            (self.chk_ruler, 'ruler'),
            (self.chk_grid, 'grid'),
            (self.chk_cal_square, 'cal_square'),
            (self.chk_crosses, 'crosshairs'),
            (self.chk_hw_margin, 'show_hw_margin'),
        ]:
            chk.stateChanged.connect(lambda _, k=k: self.toggle_overlay(k))
            l_vis.addWidget(chk)
        controls.addWidget(gb_vis)
        controls.addSpacing(10)

        controls.addStretch(1)

        main_h.addLayout(controls, 0)
        self.preview = SheetPreview(self.params, self.toggles)
        main_h.addWidget(self.preview, 1)

    def update_param(self, key, value):
        self.params[key] = value
        self.preview.update()
        self.save_settings()
        self.update_helper_labels()

    def toggle_overlay(self, key):
        toggle_names = {
            "ruler": "chk_ruler",
            "grid": "chk_grid",
            "rounded": "chk_rounded",
            "cal_square": "chk_cal_square",
            "crosshairs": "chk_crosses",
            "show_hw_margin": "chk_hw_margin",
        }
        widget = getattr(self, toggle_names[key])
        self.toggles[key] = widget.isChecked()
        self.preview.update()
        self.save_settings()

    def print_calibration(self):
        printer.print_calibration(self.params['page_w'], self.params['page_h'], self)

    def print_sheet(self):
        # Critical: set preview to "rendering_for_print" mode during print, then reset
        self.preview.rendering_for_print = True
        printer.print_sheet(self.preview, self)
        self.preview.rendering_for_print = False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = CalibrationTab()
    win.resize(1200, 850)
    win.show()
    sys.exit(app.exec_())
