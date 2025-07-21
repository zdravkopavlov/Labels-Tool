import sys
import os
import json
import printer
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QSizePolicy, QPushButton, QComboBox
)
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QPainterPath, QIcon
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
        self.rendering_for_print = False

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

        # --- Scaling ---
        if getattr(self, 'rendering_for_print', False):
            scale = w / (page_w_mm * MM_TO_PX)
            scale *= p.get('user_scale_factor', 1.0)
            offset_x = 0
            offset_y = 0
        else:
            margin_px = 48  # you can tweak this value!
            scale = min(
                (w - 2*margin_px) / (page_w_mm * MM_TO_PX),
                (h - 2*margin_px) / (page_h_mm * MM_TO_PX)
            )
            scale *= p.get('user_scale_factor', 1.0)
            offset_x = (w - page_w_mm * MM_TO_PX * scale) / 2
            offset_y = (h - page_h_mm * MM_TO_PX * scale) / 2

        def mm_to_px(x_mm, y_mm):
            return (
                offset_x + x_mm * MM_TO_PX * scale,
                offset_y + y_mm * MM_TO_PX * scale,
            )

        # --- Calibration print (solid gray) ---
        if self.calibration_mode:
            page_x, page_y = mm_to_px(0, 0)
            page_w = page_w_mm * MM_TO_PX * scale
            page_h = page_h_mm * MM_TO_PX * scale
            painter.fillRect(int(page_x), int(page_y), int(page_w), int(page_h), QColor("#dddddd"))
            return

        # --- Draw ruler, A4 label, and dimensions OUTSIDE page border ---
        if t.get('ruler', True):
            ruler_font = QFont("Arial", 20, QFont.Bold)
            painter.setFont(ruler_font)
            # A4 label, top left, outside page border
            page_x, page_y = mm_to_px(0, 0)
            painter.setPen(QPen(QColor("#888"), 2))
            a4_label = "A4"
            painter.drawText(int(page_x) - 34, int(page_y) - 14, a4_label)
            # Draw 210mm at bottom center, 297mm at right center (outside page)
            dim_font = QFont("Arial", 11)
            painter.setFont(dim_font)
            page_x2, page_y2 = mm_to_px(page_w_mm, 0)
            # bottom (horizontal dimension)
            painter.drawText(
                int(page_x + (page_x2 - page_x) / 2) - 30,
                int(page_y + page_h_mm * MM_TO_PX * scale) + 28,
                "210mm"
            )
            # right (vertical dimension)
            painter.save()
            painter.translate(int(page_x2) + 12, int(page_y + (page_h_mm * MM_TO_PX * scale) / 2) + 30)
            painter.rotate(-90)
            painter.drawText(0, 10, "297mm")
            painter.restore()

            # Tick marks (just outside the main rectangle)
            painter.setPen(QPen(QColor("#aaa"), 1))
            # Top edge
            for mm in range(0, int(page_w_mm) + 1):
                x = page_x + mm * MM_TO_PX * scale
                if mm % 10 == 0:
                    painter.drawLine(int(x), int(page_y) - 18, int(x), int(page_y))
                elif mm % 5 == 0:
                    painter.drawLine(int(x), int(page_y) - 11, int(x), int(page_y))
                else:
                    painter.drawLine(int(x), int(page_y) - 5, int(x), int(page_y))
            # Left edge
            for mm in range(0, int(page_h_mm) + 1):
                y = page_y + mm * MM_TO_PX * scale
                if mm % 10 == 0:
                    painter.drawLine(int(page_x) - 18, int(y), int(page_x), int(y))
                elif mm % 5 == 0:
                    painter.drawLine(int(page_x) - 11, int(y), int(page_x), int(y))
                else:
                    painter.drawLine(int(page_x) - 5, int(y), int(page_x), int(y))

        # --- A4 page border ---
        page_x, page_y = mm_to_px(0, 0)
        page_w = page_w_mm * MM_TO_PX * scale
        page_h = page_h_mm * MM_TO_PX * scale
        painter.fillRect(int(page_x), int(page_y), int(page_w), int(page_h), Qt.white)
        painter.setPen(QPen(QColor("#aaaaaa"), 1, Qt.DashLine))
        painter.drawRect(int(page_x), int(page_y), int(page_w), int(page_h))

        # --- HW margin rectangle (toggleable visual) ---
        margin_x, margin_y = mm_to_px(hw_left, hw_top)
        margin_w = (page_w_mm - hw_left - hw_right) * MM_TO_PX * scale
        margin_h = (page_h_mm - hw_top - hw_bottom) * MM_TO_PX * scale
        if t.get('show_hw_margin', True):
            painter.setPen(QPen(QColor("#aaaaaa"), 1, Qt.DashLine))
            painter.drawRect(int(margin_x), int(margin_y), int(margin_w), int(margin_h))

        # --- Label grid and helpers ---
        if getattr(self, 'rendering_for_print', False):
            draw_x_mm = sheet_left
            draw_y_mm = sheet_top
        else:
            draw_x_mm = hw_left + sheet_left
            draw_y_mm = hw_top + sheet_top

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
                    if getattr(self, 'rendering_for_print', False):
                        font_size_pt = max(int(22 * (1/scale)), 12)
                    else:
                        font_size_pt = 12
                    font = QFont("Arial", font_size_pt, QFont.Normal)
                    painter.setFont(font)
                    painter.drawText(int(cx - sq_size_px / 2), int(top - 8), "10 mm")

        # --- Crosshairs ---
        if t.get('crosshairs', True):
            ch_len = 14 * scale
            pen = QPen(QColor("#bd2323"), 1.6)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
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

class CalibrationTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Редактор на лист – Калибриране")
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
        if "user_scale_factor" not in self.params:
            self.params["user_scale_factor"] = 1.0
        self.init_ui()
        self.update_helper_labels()
        loaded = load_sheet_settings()

    def default_params(self):
        return {
            'hw_left': 5.0, 'hw_top': 5.0, 'hw_right': 5.0, 'hw_bottom': 5.0,
            'page_w': 210.0, 'page_h': 297.0,
            'sheet_left': 1.0, 'sheet_top': 10.0,
            'label_w': 63.5, 'label_h': 38.1,
            'col_gap': 3.4, 'row_gap': 0.0,
            'rows': 7, 'cols': 3,
        }

    def save_settings(self):
        # Load any existing settings, or start with empty dict
        current = load_sheet_settings() or {}
        # Update just the keys you manage
        current["params"] = self.params
        current["toggles"] = self.toggles
        current["skip_hw_margin"] = self.chk_skip_hw_margin.isChecked()
        # Save all keys (including unknown extras)
        save_sheet_settings(current)

    def update_helper_labels(self):
        offset_left = self.params['hw_left'] + self.params['sheet_left']
        offset_top = self.params['hw_top'] + self.params['sheet_top']
        self.lbl_left_offset.setText(f"Общо разстояние от ляв ръб до етикет: {offset_left:.1f} мм")
        self.lbl_top_offset.setText(f"Общо разстояние от горен ръб до етикет: {offset_top:.1f} мм")

    def init_ui(self):
        main_h = QHBoxLayout(self)
        controls = QVBoxLayout()

        # 1. Paper size dropdown (future-proof, single option for now)
        self.cb_page_size = QComboBox()
        self.cb_page_size.addItem("A4 International (210x297mm)")
        self.cb_page_size.setCurrentIndex(0)
        self.cb_page_size.setMaximumWidth(260)
        controls.addWidget(self.cb_page_size)

        # Printer margin group
        gb_hw = QGroupBox("Полеви ограничения на принтера (mm)")
        l_hw = QHBoxLayout()
        l_hw.setSpacing(16)
        for label, key in [("Ляво:", 'hw_left'), ("Горе:", 'hw_top'), ("Дясно:", 'hw_right'), ("Долу:", 'hw_bottom')]:
            pair_layout = QHBoxLayout()
            pair_layout.setSpacing(4)
            lbl = QLabel(label)
            lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            spin = QDoubleSpinBox()
            spin.setRange(0, 50)
            spin.setDecimals(2)
            spin.setValue(self.params[key])
            spin.setMaximumWidth(70)
            spin.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            setattr(self, f"sp_{key}", spin)
            pair_layout.addWidget(lbl)
            pair_layout.addWidget(spin)
            l_hw.addLayout(pair_layout)
            spin.valueChanged.connect(lambda val, k=key: self.update_param(k, float(val)))
        gb_hw.setLayout(l_hw)
        controls.addWidget(gb_hw)

        # Sticker sheet margin group
        gb_sheet = QGroupBox("Полеви ограничения на стикерния лист (mm)")
        l_sheet = QHBoxLayout()
        l_sheet.setSpacing(16)
        for label, key in [("Ляво:", 'sheet_left'), ("Горе:", 'sheet_top')]:
            pair_layout = QHBoxLayout()
            pair_layout.setSpacing(4)
            lbl = QLabel(label)
            lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            spin = QDoubleSpinBox()
            spin.setRange(0, 100)
            spin.setDecimals(2)
            spin.setValue(self.params[key])
            spin.setMaximumWidth(70)
            spin.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            setattr(self, f"sp_{key}", spin)
            pair_layout.addWidget(lbl)
            pair_layout.addWidget(spin)
            l_sheet.addLayout(pair_layout)
            spin.valueChanged.connect(lambda val, k=key: self.update_param(k, float(val)))
        gb_sheet.setLayout(l_sheet)
        controls.addWidget(gb_sheet)

        # 4. Offset reporting labels
        self.lbl_left_offset = QLabel()
        self.lbl_top_offset = QLabel()
        controls.addWidget(self.lbl_left_offset)
        controls.addWidget(self.lbl_top_offset)

        # 5. Label size group ("Размер на етикета")
        gb_labels = QGroupBox("Размер на етикета (mm)")
        l_labels = QVBoxLayout(gb_labels)
        l_row1 = QHBoxLayout()
        self.sp_w = QDoubleSpinBox(); self.sp_w.setRange(1, 200); self.sp_w.setDecimals(2); self.sp_w.setSingleStep(0.1); self.sp_w.setValue(self.params['label_w']); self.sp_w.setMaximumWidth(80)
        self.sp_h = QDoubleSpinBox(); self.sp_h.setRange(1, 200); self.sp_h.setDecimals(2); self.sp_h.setSingleStep(0.1); self.sp_h.setValue(self.params['label_h']); self.sp_h.setMaximumWidth(80)
        l_row1.addWidget(QLabel("Широчина:")); l_row1.addWidget(self.sp_w)
        l_row1.addWidget(QLabel("Височина:")); l_row1.addWidget(self.sp_h)
        l_row1.addStretch(1)
        l_labels.addLayout(l_row1)
        self.chk_rounded = QCheckBox("Заоблени ъгли на етикетите"); self.chk_rounded.setChecked(self.toggles['rounded'])
        l_labels.addWidget(self.chk_rounded)
        self.sp_w.valueChanged.connect(lambda val: self.update_param('label_w', float(val)))
        self.sp_h.valueChanged.connect(lambda val: self.update_param('label_h', float(val)))
        self.chk_rounded.stateChanged.connect(lambda _: self.toggle_overlay('rounded'))
        controls.addWidget(gb_labels)

        # 6. Rows/cols/gaps group
        gb_rc = QGroupBox("Брой редове и колони")
        l_rc = QHBoxLayout(gb_rc)
        l_rc.setSpacing(8)
        self.sp_rows = QSpinBox(); self.sp_rows.setRange(1, 20); self.sp_rows.setValue(self.params['rows']); self.sp_rows.setMaximumWidth(60)
        self.sp_cols = QSpinBox(); self.sp_cols.setRange(1, 20); self.sp_cols.setValue(self.params['cols']); self.sp_cols.setMaximumWidth(60)
        self.sp_cgap = QDoubleSpinBox(); self.sp_cgap.setRange(0, 50); self.sp_cgap.setDecimals(2); self.sp_cgap.setSingleStep(0.1); self.sp_cgap.setValue(self.params['col_gap']); self.sp_cgap.setMaximumWidth(70)
        self.sp_rgap = QDoubleSpinBox(); self.sp_rgap.setRange(0, 50); self.sp_rgap.setDecimals(2); self.sp_rgap.setSingleStep(0.1); self.sp_rgap.setValue(self.params['row_gap']); self.sp_rgap.setMaximumWidth(70)
        l_rc.addWidget(QLabel("Редове:")); l_rc.addWidget(self.sp_rows)
        l_rc.addWidget(QLabel("Колони:")); l_rc.addWidget(self.sp_cols)
        l_rc.addWidget(QLabel("Междина колони:")); l_rc.addWidget(self.sp_cgap)
        l_rc.addWidget(QLabel("Междина редове:")); l_rc.addWidget(self.sp_rgap)
        l_rc.addStretch(1)
        self.sp_rows.valueChanged.connect(lambda val: self.update_param('rows', int(val)))
        self.sp_cols.valueChanged.connect(lambda val: self.update_param('cols', int(val)))
        self.sp_cgap.valueChanged.connect(lambda val: self.update_param('col_gap', float(val)))
        self.sp_rgap.valueChanged.connect(lambda val: self.update_param('row_gap', float(val)))
        controls.addWidget(gb_rc)

        # 7. Visual helpers group
        gb_vis = QGroupBox("Визуални помощници")
        l_vis = QVBoxLayout(gb_vis)
        self.chk_ruler = QCheckBox("Линийка"); self.chk_ruler.setChecked(self.toggles['ruler'])
        self.chk_hw_margin = QCheckBox("Рамка на принтера"); self.chk_hw_margin.setChecked(self.toggles['show_hw_margin'])
        self.chk_grid = QCheckBox("Етикети"); self.chk_grid.setChecked(self.toggles['grid'])
        self.chk_crosses = QCheckBox("Кръстчета"); self.chk_crosses.setChecked(self.toggles['crosshairs'])
        self.chk_cal_square = QCheckBox("Калибрационен квадрат (10мм)"); self.chk_cal_square.setChecked(self.toggles['cal_square'])
        l_vis.addWidget(self.chk_ruler)
        l_vis.addWidget(self.chk_hw_margin)
        l_vis.addWidget(self.chk_grid)
        l_vis.addWidget(self.chk_crosses)
        l_vis.addWidget(self.chk_cal_square)
        controls.addWidget(gb_vis)

        self.chk_ruler.stateChanged.connect(lambda _: self.toggle_overlay('ruler'))
        self.chk_hw_margin.stateChanged.connect(lambda _: self.toggle_overlay('show_hw_margin'))
        self.chk_grid.stateChanged.connect(lambda _: self.toggle_overlay('grid'))
        self.chk_crosses.stateChanged.connect(lambda _: self.toggle_overlay('crosshairs'))
        self.chk_cal_square.stateChanged.connect(lambda _: self.toggle_overlay('cal_square'))

        controls.addSpacing(12)

        # Correction group (expected/measured width and scaling)
        gb_corr = QGroupBox("Принтерна корекция (скалиране)")
        l_corr = QHBoxLayout(gb_corr)
        expected_width = self.params['cols'] * self.params['label_w'] + (self.params['cols']-1) * self.params['col_gap']
        self.sp_expected_w = QDoubleSpinBox()
        self.sp_expected_w.setRange(10, 400)
        self.sp_expected_w.setDecimals(2)
        self.sp_expected_w.setValue(expected_width)
        self.sp_expected_w.setMaximumWidth(90)
        self.sp_expected_w.setEnabled(False)
        lbl_exp = QLabel("Очаквана широчина (mm):")
        l_corr.addWidget(lbl_exp)
        l_corr.addWidget(self.sp_expected_w)
        self.sp_measured_w = QDoubleSpinBox()
        self.sp_measured_w.setRange(10, 400)
        self.sp_measured_w.setDecimals(2)
        self.sp_measured_w.setValue(expected_width)
        self.sp_measured_w.setMaximumWidth(90)
        lbl_meas = QLabel("Измерена широчина (mm):")
        l_corr.addWidget(lbl_meas)
        l_corr.addWidget(self.sp_measured_w)

        self.lbl_corr_factor = QLabel("Корекция: 100%")
        l_corr.addWidget(self.lbl_corr_factor)
        controls.addWidget(gb_corr)

        if "user_scale_factor" in self.params and self.params["user_scale_factor"] != 1.0:
            exp = self.sp_expected_w.value()
            factor = self.params["user_scale_factor"]
            self.sp_measured_w.setValue(exp / factor)
            self.lbl_corr_factor.setText(f"Корекция: {factor*100:.2f}%")

        help_note = QLabel(
            "<b>Съвет:</b> Измерете с линийка реалната широчина на отпечатаните етикети и я въведете тук.<br>"
            "Инструментът автоматично ще коригира мащаба на печата за максимална точност."
        )
        help_note.setWordWrap(True)
        help_note.setStyleSheet("color: #333; font-size:11px; padding-bottom: 6px;")
        controls.addWidget(help_note)

        # HW margin skip checkbox, correctly placed
        self.chk_skip_hw_margin = QCheckBox("Пропусни хардуерния марж при печат/PDF (за печат без бели полета)")
        self.chk_skip_hw_margin.setChecked(False)
        controls.addWidget(self.chk_skip_hw_margin)
        self.chk_skip_hw_margin.stateChanged.connect(lambda _: self.save_settings())

        def update_corr_factor():
            exp = self.sp_expected_w.value()
            meas = self.sp_measured_w.value()
            if meas > 0:
                factor = exp / meas
            else:
                factor = 1.0
            factor = max(0.95, min(1.05, factor))
            self.lbl_corr_factor.setText(f"Корекция: {factor*100:.2f}%")
            self.params['user_scale_factor'] = factor
            self.preview.update()
            self.save_settings()
        self.sp_measured_w.valueChanged.connect(update_corr_factor)
        self.update_corr_factor = update_corr_factor

        self.btn_calib_print = QPushButton("Калибриращ печат (сив фон)")
        self.btn_calib_print.setMaximumHeight(80)
        self.btn_calib_print.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "./resources/background.svg")))
        self.btn_calib_print.clicked.connect(self.print_calibration)

        self.btn_print = QPushButton("Печат – Визуални помощници")
        self.btn_print.setMaximumHeight(32)
        self.btn_print.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "./resources/guides.svg")))
        self.btn_print.clicked.connect(self.print_sheet)
        btns_h = QHBoxLayout()
        btns_h.addWidget(self.btn_calib_print)
        btns_h.addWidget(self.btn_print)
        controls.addLayout(btns_h)

        controls.addStretch(1)
        main_h.addLayout(controls, 0)

        preview_pad = QVBoxLayout()
        preview_pad.setContentsMargins(3, 3, 3, 3)
        self.preview = SheetPreview(self.params, self.toggles)
        preview_pad.addWidget(self.preview)
        main_h.addLayout(preview_pad, 1)

        loaded = load_sheet_settings()
        if loaded and "skip_hw_margin" in loaded:
            self.chk_skip_hw_margin.setChecked(loaded["skip_hw_margin"])

    def update_param(self, key, value):
        self.params[key] = value
        self.preview.update()
        self.save_settings()
        self.update_helper_labels()
        if hasattr(self, "sp_expected_w"):
            exp = self.params['cols'] * self.params['label_w'] + (self.params['cols']-1) * self.params['col_gap']
            self.sp_expected_w.setValue(exp)
            if abs(self.sp_measured_w.value() - self.sp_expected_w.value()) < 0.1:
                self.sp_measured_w.setValue(exp)
            self.update_corr_factor()

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
        self.preview.rendering_for_print = True
        printer.print_sheet(self.preview, self)
        self.preview.rendering_for_print = False

    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = CalibrationTab()
    win.resize(1200, 850)
    win.show()
    sys.exit(app.exec_())
