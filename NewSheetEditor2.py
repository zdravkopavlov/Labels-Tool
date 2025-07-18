import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSpinBox, QDoubleSpinBox, QCheckBox, QSizePolicy, QPushButton
)
from PyQt5.QtGui import QPainter, QColor, QPen, QFont
from PyQt5.QtCore import Qt

MM_TO_PX = 72 / 25.4  # 1 mm in points (typical printer/screen DPI)

A4_WIDTH_MM = 210
A4_HEIGHT_MM = 297

def get_appdata_path():
    folder = os.path.join(os.getenv("APPDATA"), "LabelTool")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "sheet_settings.json")

def save_settings(params):
    try:
        path = get_appdata_path()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(params, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Could not save settings: {e}")

def load_settings():
    try:
        path = get_appdata_path()
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"Could not load settings: {e}")
    return None

class SheetPreview(QWidget):
    def __init__(self, params, toggles, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.params = params
        self.toggles = toggles
        self.setMinimumSize(840, 1200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def paintEvent(self, event):
        p = self.params
        t = self.toggles

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Calculate scale to fit A4 in the widget, with small margin
        margin_px = 16
        scale = min((w - 2*margin_px) / (A4_WIDTH_MM * MM_TO_PX),
                    (h - 2*margin_px) / (A4_HEIGHT_MM * MM_TO_PX))
        offset_x = margin_px
        offset_y = margin_px

        def mm_to_px(x_mm, y_mm):
            return (offset_x + x_mm * MM_TO_PX * scale, offset_y + y_mm * MM_TO_PX * scale)

        a4_w_px = A4_WIDTH_MM * MM_TO_PX * scale
        a4_h_px = A4_HEIGHT_MM * MM_TO_PX * scale

        # Optional: Fill A4 area with light gray for preview
        if t['gray_fill']:
            painter.fillRect(int(offset_x), int(offset_y), int(a4_w_px), int(a4_h_px), QColor("#ededed"))

        # Always draw A4 outline
        pen_a4 = QPen(QColor("#bbb"), 2)
        painter.setPen(pen_a4)
        painter.drawRect(int(offset_x), int(offset_y), int(a4_w_px), int(a4_h_px))

        # Optional: Sheet border (middle gray)
        if t['sheet_border']:
            pen_border = QPen(QColor("#808080"), 2.7)
            pen_border.setStyle(Qt.DashLine)
            painter.setPen(pen_border)
            painter.drawRect(int(offset_x), int(offset_y), int(a4_w_px), int(a4_h_px))

        # Draw rulers along top and left (no text)
        if t['ruler']:
            self.draw_rulers(painter, offset_x, offset_y, scale)

        # Draw grid of labels (with optional rounded corners)
        if t['grid'] or t['crosshairs']:
            rows = p['rows']
            cols = p['cols']
            for row in range(rows):
                for col in range(cols):
                    x_mm = p['left_margin'] + col * (p['label_w'] + p['col_gap'])
                    y_mm = p['top_margin'] + row * (p['label_h'] + p['row_gap'])
                    x, y = mm_to_px(x_mm, y_mm)
                    w_px = p['label_w'] * MM_TO_PX * scale
                    h_px = p['label_h'] * MM_TO_PX * scale
                    if t['grid']:
                        painter.setPen(QPen(QColor("#333333"), 2))
                        radius_px = p.get('corner_radius', 0) * MM_TO_PX * scale
                        if radius_px > 0:
                            painter.drawRoundedRect(int(x), int(y), int(w_px), int(h_px), radius_px, radius_px)
                        else:
                            painter.drawRect(int(x), int(y), int(w_px), int(h_px))

        # Crosshairs logic (centered in label gaps only)
        if t['crosshairs']:
            ch_len = 14 * scale  # crosshair size in px
            pen = QPen(QColor("#bd2323"), 1.6)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            # Centers of horizontal and vertical gaps
            row_centers_mm = []
            for r in range(p['rows'] - 1):
                y1 = p['top_margin'] + (r + 1) * p['label_h'] + r * p['row_gap']
                y2 = y1 + p['row_gap']
                center_y = y1 + (y2 - y1) / 2 if p['row_gap'] > 0 else y1
                row_centers_mm.append(center_y)
            col_centers_mm = []
            for c in range(p['cols'] - 1):
                x1 = p['left_margin'] + (c + 1) * p['label_w'] + c * p['col_gap']
                x2 = x1 + p['col_gap']
                center_x = x1 + (x2 - x1) / 2 if p['col_gap'] > 0 else x1
                col_centers_mm.append(center_x)
            for y_mm in row_centers_mm:
                for x_mm in col_centers_mm:
                    x, y = mm_to_px(x_mm, y_mm)
                    painter.drawLine(int(x - ch_len/2), int(y), int(x + ch_len/2), int(y))
                    painter.drawLine(int(x), int(y - ch_len/2), int(x), int(y + ch_len/2))

    def draw_rulers(self, painter, offset_x, offset_y, scale):
        # Top ruler (horizontal)
        painter.setPen(QPen(QColor("#666"), 1.4))
        for mm in range(0, A4_WIDTH_MM + 1):
            x = offset_x + mm * MM_TO_PX * scale
            y0 = offset_y
            y1 = offset_y - (10 if mm % 10 == 0 else 5)
            painter.drawLine(int(x), int(y0), int(x), int(y1))
        # Left ruler (vertical)
        for mm in range(0, A4_HEIGHT_MM + 1):
            y = offset_y + mm * MM_TO_PX * scale
            x0 = offset_x
            x1 = offset_x - (10 if mm % 10 == 0 else 5)
            painter.drawLine(int(x0), int(y), int(x1), int(y))

class SheetEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sheet Editor – Calibration (Листов редактор – Калибриране)")

        default_params = {
            'rows': 3, 'cols': 3,
            'left_margin': 8.0, 'top_margin': 12.0,
            'label_w': 63.5, 'label_h': 38.1,
            'col_gap': 2.0, 'row_gap': 0.0,
            'corner_radius': 3.0
        }
        loaded = load_settings()
        self.params = loaded if loaded else default_params

        self.toggles = {
            'grid': True,
            'crosshairs': True,
            'ruler': True,
            'gray_fill': False,
            'sheet_border': False
        }
        self.init_ui()

    def init_ui(self):
        main_h = QHBoxLayout(self)
        controls = QVBoxLayout()
        controls.addWidget(QLabel("Параметри на листа", self, font=QFont("Arial", 12, QFont.Bold)))
        self.sp_rows = QSpinBox(self); self.sp_rows.setRange(1, 20); self.sp_rows.setValue(self.params['rows'])
        self.sp_cols = QSpinBox(self); self.sp_cols.setRange(1, 20); self.sp_cols.setValue(self.params['cols'])

        self.sp_left = QDoubleSpinBox(self); self.sp_left.setRange(0, 100); self.sp_left.setDecimals(2); self.sp_left.setSingleStep(0.1); self.sp_left.setValue(self.params['left_margin'])
        self.sp_top = QDoubleSpinBox(self); self.sp_top.setRange(0, 100); self.sp_top.setDecimals(2); self.sp_top.setSingleStep(0.1); self.sp_top.setValue(self.params['top_margin'])
        self.sp_w = QDoubleSpinBox(self); self.sp_w.setRange(1, 200); self.sp_w.setDecimals(2); self.sp_w.setSingleStep(0.1); self.sp_w.setValue(self.params['label_w'])
        self.sp_h = QDoubleSpinBox(self); self.sp_h.setRange(1, 200); self.sp_h.setDecimals(2); self.sp_h.setSingleStep(0.1); self.sp_h.setValue(self.params['label_h'])
        self.sp_cgap = QDoubleSpinBox(self); self.sp_cgap.setRange(0, 50); self.sp_cgap.setDecimals(2); self.sp_cgap.setSingleStep(0.1); self.sp_cgap.setValue(self.params['col_gap'])
        self.sp_rgap = QDoubleSpinBox(self); self.sp_rgap.setRange(0, 50); self.sp_rgap.setDecimals(2); self.sp_rgap.setSingleStep(0.1); self.sp_rgap.setValue(self.params['row_gap'])
        self.sp_radius = QDoubleSpinBox(self); self.sp_radius.setRange(0, 25); self.sp_radius.setDecimals(1); self.sp_radius.setSingleStep(0.5); self.sp_radius.setValue(self.params.get('corner_radius', 3.0))

        for label, box, key in [
            ("Брой редове", self.sp_rows, 'rows'),
            ("Брой колони", self.sp_cols, 'cols'),
            ("Ляво поле (mm)", self.sp_left, 'left_margin'),
            ("Горно поле (mm)", self.sp_top, 'top_margin'),
            ("Широчина (mm)", self.sp_w, 'label_w'),
            ("Височина (mm)", self.sp_h, 'label_h'),
            ("Хор. разстояние (mm)", self.sp_cgap, 'col_gap'),
            ("Вер. разстояние (mm)", self.sp_rgap, 'row_gap'),
            ("Радиус (mm)", self.sp_radius, 'corner_radius'),
        ]:
            row = QHBoxLayout()
            row.addWidget(QLabel(label))
            row.addWidget(box)
            controls.addLayout(row)
            if isinstance(box, QDoubleSpinBox):
                box.valueChanged.connect(lambda val, k=key: self.update_param(k, float(val)))
            else:
                box.valueChanged.connect(lambda val, k=key: self.update_param(k, int(val)))

        controls.addSpacing(10)
        # Toggles
        self.chk_grid = QCheckBox("Показвай мрежата"); self.chk_grid.setChecked(self.toggles['grid'])
        self.chk_ch = QCheckBox("Показвай кръстчета"); self.chk_ch.setChecked(self.toggles['crosshairs'])
        self.chk_ruler = QCheckBox("Показвай линийка"); self.chk_ruler.setChecked(self.toggles['ruler'])
        self.chk_grayfill = QCheckBox("Сива основа (A4)"); self.chk_grayfill.setChecked(self.toggles['gray_fill'])
        self.chk_border = QCheckBox("Покажи рамка на листа"); self.chk_border.setChecked(self.toggles['sheet_border'])
        for chk, k in [
            (self.chk_grid, 'grid'), (self.chk_ch, 'crosshairs'), (self.chk_ruler, 'ruler'),
            (self.chk_grayfill, 'gray_fill'), (self.chk_border, 'sheet_border')
        ]:
            chk.stateChanged.connect(lambda _, k=k: self.toggle_overlay(k))
            controls.addWidget(chk)
        controls.addSpacing(10)
        self.btn_print = QPushButton("Печатай")
        self.btn_print.clicked.connect(self.print_sheet)
        controls.addWidget(self.btn_print)
        controls.addStretch(1)

        main_h.addLayout(controls, 0)

        # Sheet preview
        self.preview = SheetPreview(self.params, self.toggles)
        main_h.addWidget(self.preview, 1)

    def update_param(self, key, value):
        self.params[key] = value
        save_settings(self.params)
        self.preview.update()

    def toggle_overlay(self, key):
        btn_map = {
            'grid': self.chk_grid,
            'crosshairs': self.chk_ch,
            'ruler': self.chk_ruler,
            'gray_fill': self.chk_grayfill,
            'sheet_border': self.chk_border
        }
        self.toggles[key] = btn_map[key].isChecked()
        self.preview.update()

    def print_sheet(self):
        from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPaperSize(printer.A4)
        dlg = QPrintDialog(printer, self)
        if dlg.exec_() == QPrintDialog.Accepted:
            painter = QPainter(printer)
            # Calculate scaling for A4
            page_rect = printer.pageRect()
            scale = min(
                page_rect.width() / (A4_WIDTH_MM * MM_TO_PX),
                page_rect.height() / (A4_HEIGHT_MM * MM_TO_PX)
            )
            offset_x = 0
            offset_y = 0
            # White background
            painter.fillRect(page_rect, Qt.white)
            # Fake a widget size just for paint logic
            class Dummy:
                width = lambda self: page_rect.width()
                height = lambda self: page_rect.height()
            # Temporarily override preview's paintEvent
            prev_scale = self.preview.width(), self.preview.height()
            self.preview.resize(page_rect.width(), page_rect.height())
            # Set toggles as per current settings
            self.preview.paintEvent(
                type("event", (), {})()
            )
            self.preview.render(painter)
            self.preview.resize(*prev_scale)
            painter.end()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = SheetEditor()
    win.resize(1150, 1500)
    win.show()
    sys.exit(app.exec_())
