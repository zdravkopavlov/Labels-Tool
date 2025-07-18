import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QSizePolicy, QPushButton, QComboBox
)
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QPainterPath
from PyQt5.QtCore import Qt

MM_TO_PX = 72 / 25.4  # for preview only

PAPER_SIZES = {
    "A4 International (210×297 мм)": (210.0, 297.0),
}

PREVIEW_PAD = 38  # px margin so nothing is ever cropped

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
    def __init__(self, params, toggles, get_paper_size, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.params = params
        self.toggles = toggles
        self.get_paper_size = get_paper_size
        self.setMinimumSize(800, 600)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._print_mode = False

    def paintEvent(self, event):
        p = self.params
        t = self.toggles
        paper_w_mm, paper_h_mm = self.get_paper_size()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Always leave margin (PREVIEW_PAD) so nothing is cropped
        scale = min((w - 2*PREVIEW_PAD) / (paper_w_mm * MM_TO_PX),
                    (h - 2*PREVIEW_PAD) / (paper_h_mm * MM_TO_PX))
        offset_x = (w - paper_w_mm * MM_TO_PX * scale) / 2
        offset_y = (h - paper_h_mm * MM_TO_PX * scale) / 2

        def mm_to_px(x_mm, y_mm):
            return (
                offset_x + x_mm * MM_TO_PX * scale,
                offset_y + y_mm * MM_TO_PX * scale,
            )

        # 1. Draw gray background for whole paper area (ground truth, not affected by margins)
        page_x, page_y = mm_to_px(0, 0)
        page_w = paper_w_mm * MM_TO_PX * scale
        page_h = paper_h_mm * MM_TO_PX * scale
        if t['gray_area']:
            painter.fillRect(int(page_x), int(page_y), int(page_w), int(page_h), QColor("#dddddd"))
        else:
            painter.fillRect(int(page_x), int(page_y), int(page_w), int(page_h), Qt.white)

        # 2. Draw A4 border (always, black line)
        painter.setPen(QPen(QColor("#000"), 2))
        painter.drawRect(int(page_x), int(page_y), int(page_w), int(page_h))

        # 3. Decorative ruler and paper labels, always inside border
        if t['show_ruler']:
            ruler_offset = 15
            painter.setPen(QPen(QColor("#999"), 2))
            # Top edge
            for mm in range(0, int(paper_w_mm)+1):
                x = page_x + mm * MM_TO_PX * scale
                if mm % 10 == 0:
                    painter.drawLine(int(x), int(page_y - ruler_offset), int(x), int(page_y))
                elif mm % 5 == 0:
                    painter.drawLine(int(x), int(page_y - ruler_offset//2), int(x), int(page_y))
                else:
                    painter.drawLine(int(x), int(page_y - ruler_offset//3), int(x), int(page_y))
            # Left edge
            for mm in range(0, int(paper_h_mm)+1):
                y = page_y + mm * MM_TO_PX * scale
                if mm % 10 == 0:
                    painter.drawLine(int(page_x - ruler_offset), int(y), int(page_x), int(y))
                elif mm % 5 == 0:
                    painter.drawLine(int(page_x - ruler_offset//2), int(y), int(page_x), int(y))
                else:
                    painter.drawLine(int(page_x - ruler_offset//3), int(y), int(page_x), int(y))
            # Right edge
            for mm in range(0, int(paper_h_mm)+1):
                y = page_y + mm * MM_TO_PX * scale
                if mm % 10 == 0:
                    painter.drawLine(int(page_x + page_w), int(y), int(page_x + page_w + ruler_offset), int(y))
            # Bottom edge
            for mm in range(0, int(paper_w_mm)+1):
                x = page_x + mm * MM_TO_PX * scale
                if mm % 10 == 0:
                    painter.drawLine(int(x), int(page_y + page_h), int(x), int(page_y + page_h + ruler_offset))

            # Labels, always visible and inside page border
            font = QFont("Arial", 20, QFont.Bold)
            painter.setFont(font)
            painter.setPen(QPen(QColor("#222"), 1))
            painter.drawText(int(page_x + 8), int(page_y + 30), "A4")
            font2 = QFont("Arial", 13, QFont.Normal)
            painter.setFont(font2)
            # Bottom center (210mm)
            painter.drawText(int(page_x + page_w/2 - 30), int(page_y + page_h + ruler_offset + 18), "210mm")
            # Right center (297mm), rotated, but shifted out further to the right
            painter.save()
            painter.translate(int(page_x + page_w + ruler_offset + 30), int(page_y + page_h/2 + 30))
            painter.rotate(-90)
            painter.drawText(0, 0, "297mm")
            painter.restore()

        # 4. Dashed HW margin rectangle (the only thing affected by margin settings)
        hw_left = p['hw_left']
        hw_top = p['hw_top']
        hw_right = p['hw_right']
        hw_bottom = p['hw_bottom']
        # HW margin (dashed) always measured from paper border
        printable_x = hw_left
        printable_y = hw_top
        printable_w = paper_w_mm - hw_left - hw_right
        printable_h = paper_h_mm - hw_top - hw_bottom
        px, py = mm_to_px(printable_x, printable_y)
        pw = printable_w * MM_TO_PX * scale
        ph = printable_h * MM_TO_PX * scale
        pen = QPen(QColor("#444"), 2, Qt.DashLine)
        if t['show_hw_margin']:
            painter.setPen(pen)
            painter.drawRect(int(px), int(py), int(pw), int(ph))

        # 5. Label grid and calibration squares INSIDE dashed rectangle (not double-offset)
        sheet_left = p['sheet_left']
        sheet_top = p['sheet_top']
        label_w = p['label_w']
        label_h = p['label_h']
        col_gap = p['col_gap']
        row_gap = p['row_gap']
        rows = p['rows']
        cols = p['cols']
        corner_radius = 2.5 if t['rounded'] else 0  # mm

        # -- This is the CRUCIAL FIX:
        # The label grid starts AT the dashed rectangle (HW margin),
        # PLUS sticker sheet margin. If sticker margin == 0, grid is flush.
        labelgrid_x = hw_left + sheet_left
        labelgrid_y = hw_top + sheet_top

        for row in range(rows):
            for col in range(cols):
                x_mm = labelgrid_x + col * (label_w + col_gap)
                y_mm = labelgrid_y + row * (label_h + row_gap)
                x, y = mm_to_px(x_mm, y_mm)
                w_label_px = label_w * MM_TO_PX * scale
                h_label_px = label_h * MM_TO_PX * scale
                if t['grid']:
                    painter.setPen(QPen(QColor("#333333"), 2))
                    if corner_radius > 0:
                        radius_px = corner_radius * MM_TO_PX * scale
                        path = QPainterPath()
                        path.addRoundedRect(x, y, w_label_px, h_label_px, radius_px, radius_px)
                        painter.drawPath(path)
                    else:
                        painter.drawRect(int(x), int(y), int(w_label_px), int(h_label_px))
                # Calibration square in label center
                if t['cal_square']:
                    sq_size_mm = 10.0
                    sq_size_px = sq_size_mm * MM_TO_PX * scale
                    cx = x + w_label_px / 2
                    cy = y + h_label_px / 2
                    left = cx - sq_size_px / 2
                    top = cy - sq_size_px / 2
                    painter.setPen(QPen(QColor("#111"), 2))
                    painter.drawRect(int(left), int(top), int(sq_size_px), int(sq_size_px))
                    # Crosshair
                    crosshair_len = sq_size_px * 0.7
                    painter.drawLine(int(cx - crosshair_len/2), int(cy), int(cx + crosshair_len/2), int(cy))
                    painter.drawLine(int(cx), int(cy - crosshair_len/2), int(cx), int(cy + crosshair_len/2))
                    # Only one horizontal label, above the square
                    font = QFont("Arial", 12, QFont.Normal)
                    painter.setFont(font)
                    painter.drawText(int(cx - 22), int(top - 5), "10 mm")

    def set_print_mode(self, on):
        self._print_mode = on

class SheetEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Редактор на лист – Калибриране")
        self.params = self.default_params()
        self.toggles = {
            'show_ruler': True,
            'gray_area': False,
            'show_hw_margin': True,
            'grid': True,
            'rounded': False,
            'cal_square': False,
        }
        self.paper_size = "A4 International (210×297 мм)"
        loaded = load_sheet_settings()
        if loaded:
            self.params.update(loaded.get("params", {}))
            self.toggles.update(loaded.get("toggles", {}))
            self.paper_size = loaded.get("paper_size", self.paper_size)
        self.init_ui()
        self.update_helper_labels()

    def default_params(self):
        return {
            'hw_left': 8.0, 'hw_top': 8.0, 'hw_right': 8.0, 'hw_bottom': 8.0,
            'sheet_left': 0.0, 'sheet_top': 0.0,
            'label_w': 63.5, 'label_h': 38.1,
            'col_gap': 2.0, 'row_gap': 0.0,
            'rows': 7, 'cols': 3,
        }

    def save_settings(self):
        save_sheet_settings({
            "params": self.params,
            "toggles": self.toggles,
            "paper_size": self.paper_size,
        })

    def update_helper_labels(self):
        offset_left = self.params['hw_left'] + self.params['sheet_left']
        offset_top = self.params['hw_top'] + self.params['sheet_top']
        self.lbl_left_offset.setText(f"Общо разстояние от ляв ръб до етикет: {offset_left:.1f} мм")
        self.lbl_top_offset.setText(f"Общо разстояние от горен ръб до етикет: {offset_top:.1f} мм")

    def get_paper_size(self):
        return PAPER_SIZES[self.paper_size]

    def init_ui(self):
        main_h = QHBoxLayout(self)
        controls = QVBoxLayout()

        # Paper size selection (future-proof)
        l_paper = QHBoxLayout()
        l_paper.addWidget(QLabel("Размер на листа:"))
        self.combo_paper = QComboBox()
        for name in PAPER_SIZES.keys():
            self.combo_paper.addItem(name)
        self.combo_paper.setCurrentText(self.paper_size)
        self.combo_paper.currentTextChanged.connect(self.paper_changed)
        l_paper.addWidget(self.combo_paper)
        controls.addLayout(l_paper)

        # Printer HW Margins group
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

        # --- Helper: offset left/top ---
        self.lbl_left_offset = QLabel()
        self.lbl_top_offset = QLabel()
        controls.addWidget(self.lbl_left_offset)
        controls.addWidget(self.lbl_top_offset)

        # Sticker Sheet Margins group
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

        # Label Size & Gaps group + rounded corners
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

        # Rounded corners in label group
        l_labels2 = QVBoxLayout()
        self.chk_rounded = QCheckBox("Заоблени ъгли на етикетите"); self.chk_rounded.setChecked(self.toggles['rounded'])
        self.chk_rounded.stateChanged.connect(lambda _: self.toggle_overlay('rounded'))
        l_labels2.addWidget(self.chk_rounded)
        l_labels.addLayout(l_labels2)

        # Rows & Columns group
        gb_rc = QGroupBox("Брой редове и колони")
        l_rc = QHBoxLayout(gb_rc)
        self.sp_rows = QSpinBox(self); self.sp_rows.setRange(1, 20); self.sp_rows.setValue(self.params['rows'])
        self.sp_cols = QSpinBox(self); self.sp_cols.setRange(1, 20); self.sp_cols.setValue(self.params['cols'])
        l_rc.addWidget(QLabel("Редове")); l_rc.addWidget(self.sp_rows)
        l_rc.addWidget(QLabel("Колони")); l_rc.addWidget(self.sp_cols)
        controls.addWidget(gb_rc)
        self.sp_rows.valueChanged.connect(lambda val: self.update_param('rows', int(val)))
        self.sp_cols.valueChanged.connect(lambda val: self.update_param('cols', int(val)))

        # Visual Helpers group (+ calibration square here)
        gb_vis = QGroupBox("Визуални помощници")
        l_vis = QVBoxLayout(gb_vis)
        self.chk_ruler = QCheckBox("Покажи линийка на екрана"); self.chk_ruler.setChecked(self.toggles['show_ruler'])
        self.chk_gray = QCheckBox("Покажи сива основа"); self.chk_gray.setChecked(self.toggles['gray_area'])
        self.chk_hwmargin = QCheckBox("Покажи рамка на принтера"); self.chk_hwmargin.setChecked(self.toggles['show_hw_margin'])
        self.chk_grid = QCheckBox("Показвай мрежата"); self.chk_grid.setChecked(self.toggles['grid'])
        self.chk_cal_square = QCheckBox("Покажи калибрационен квадрат"); self.chk_cal_square.setChecked(self.toggles['cal_square'])
        for chk, k in [
            (self.chk_ruler, 'show_ruler'),
            (self.chk_gray, 'gray_area'),
            (self.chk_hwmargin, 'show_hw_margin'),
            (self.chk_grid, 'grid'),
            (self.chk_cal_square, 'cal_square'),
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
        self.preview = SheetPreview(self.params, self.toggles, self.get_paper_size)
        main_h.addWidget(self.preview, 1)

    def update_param(self, key, value):
        self.params[key] = value
        self.preview.update()
        self.save_settings()
        self.update_helper_labels()

    def toggle_overlay(self, key):
        toggle_names = {
            "show_ruler": "chk_ruler",
            "gray_area": "chk_gray",
            "show_hw_margin": "chk_hwmargin",
            "grid": "chk_grid",
            "rounded": "chk_rounded",
            "cal_square": "chk_cal_square",
        }
        widget = getattr(self, toggle_names[key])
        self.toggles[key] = widget.isChecked()
        self.preview.update()
        self.save_settings()

    def paper_changed(self, val):
        self.paper_size = val
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

