import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSpinBox, QDoubleSpinBox, QCheckBox, QSizePolicy, QPushButton
)
from PyQt5.QtGui import QPainter, QColor, QPen, QFont
from PyQt5.QtCore import Qt

MM_TO_PX = 72 / 25.4  # 1 mm in points (typical printer/screen DPI)

class SheetPreview(QWidget):
    def __init__(self, params, toggles, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.params = params
        self.toggles = toggles
        self.setMinimumSize(800, 600)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def paintEvent(self, event):
        p = self.params
        t = self.toggles

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Calculate full sheet size in px for scaling/centering
        sheet_w_mm = (
            p['left_margin'] + p['cols'] * p['label_w'] + (p['cols'] - 1) * p['col_gap']
        )
        sheet_h_mm = (
            p['top_margin'] + p['rows'] * p['label_h'] + (p['rows'] - 1) * p['row_gap']
        )
        # Fit to window, keep aspect
        scale = min((w-60) / (sheet_w_mm * MM_TO_PX), (h-60) / (sheet_h_mm * MM_TO_PX))
        offset_x = (w - sheet_w_mm * MM_TO_PX * scale) / 2
        offset_y = (h - sheet_h_mm * MM_TO_PX * scale) / 2

        def mm_to_px(x_mm, y_mm):
            return (offset_x + x_mm * MM_TO_PX * scale, offset_y + y_mm * MM_TO_PX * scale)

        # Background
        painter.fillRect(0, 0, w, h, QColor("#f7f7f7"))

        # Draw rulers if needed
        if t['ruler']:
            self.draw_rulers(painter, sheet_w_mm, sheet_h_mm, offset_x, offset_y, scale)

        # Draw grid (labels)
        if t['grid'] or t['crosshairs']:
            for row in range(p['rows']):
                for col in range(p['cols']):
                    x_mm = p['left_margin'] + col * (p['label_w'] + p['col_gap'])
                    y_mm = p['top_margin'] + row * (p['label_h'] + p['row_gap'])
                    x, y = mm_to_px(x_mm, y_mm)
                    w_px = p['label_w'] * MM_TO_PX * scale
                    h_px = p['label_h'] * MM_TO_PX * scale
                    if t['grid']:
                        painter.setPen(QPen(QColor("#333333"), 2))
                        painter.drawRect(int(x), int(y), int(w_px), int(h_px))

        # ---- Revised Crosshairs Logic: only in the MIDDLE of the gaps ----
        if t['crosshairs']:
            ch_len = 14 * scale  # crosshair size in px
            pen = QPen(QColor("#bd2323"), 1.6)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)

            # Calculate centers of horizontal and vertical gaps
            # Horizontal gaps: between rows (i.e., after each row except the last)
            row_centers_mm = []
            for r in range(p['rows'] - 1):
                y1 = p['top_margin'] + (r + 1) * p['label_h'] + r * p['row_gap']
                y2 = y1 + p['row_gap']
                center_y = y1 + (y2 - y1) / 2 if p['row_gap'] > 0 else y1
                row_centers_mm.append(center_y)
            # Vertical gaps: between columns (i.e., after each column except the last)
            col_centers_mm = []
            for c in range(p['cols'] - 1):
                x1 = p['left_margin'] + (c + 1) * p['label_w'] + c * p['col_gap']
                x2 = x1 + p['col_gap']
                center_x = x1 + (x2 - x1) / 2 if p['col_gap'] > 0 else x1
                col_centers_mm.append(center_x)

            # Draw crosshairs at every intersection of row and column gap centers
            for y_mm in row_centers_mm:
                for x_mm in col_centers_mm:
                    x, y = mm_to_px(x_mm, y_mm)
                    painter.drawLine(int(x - ch_len/2), int(y), int(x + ch_len/2), int(y))
                    painter.drawLine(int(x), int(y - ch_len/2), int(x), int(y + ch_len/2))

            # Optionally: Also draw crosshairs at the center of every horizontal and vertical gap,
            # not just intersections (so in the middle of each gap).
            # Uncomment below to draw at centers of horizontal gaps (along each vertical "gap" line):
            # for x_mm in col_centers_mm:
            #     for row in range(p['rows']):
            #         y1 = p['top_margin'] + row * (p['label_h'] + p['row_gap'])
            #         y2 = y1 + p['label_h']
            #         center_y = (y1 + y2) / 2
            #         x, y = mm_to_px(x_mm, center_y)
            #         painter.drawLine(int(x - ch_len/2), int(y), int(x + ch_len/2), int(y))
            #         painter.drawLine(int(x), int(y - ch_len/2), int(x), int(y + ch_len/2))
            # for y_mm in row_centers_mm:
            #     for col in range(p['cols']):
            #         x1 = p['left_margin'] + col * (p['label_w'] + p['col_gap'])
            #         x2 = x1 + p['label_w']
            #         center_x = (x1 + x2) / 2
            #         x, y = mm_to_px(center_x, y_mm)
            #         painter.drawLine(int(x - ch_len/2), int(y), int(x + ch_len/2), int(y))
            #         painter.drawLine(int(x), int(y - ch_len/2), int(x), int(y + ch_len/2))

    def draw_rulers(self, painter, sheet_w_mm, sheet_h_mm, offset_x, offset_y, scale):
        font = QFont("Arial", 10)
        painter.setFont(font)
        # Top ruler (horizontal)
        for mm in range(0, int(sheet_w_mm)+1):
            x = offset_x + mm * MM_TO_PX * scale
            y0 = offset_y - 24
            y1 = offset_y
            # mm lines
            if mm % 10 == 0:
                painter.setPen(QPen(QColor("#222"), 2.5))
                painter.drawLine(int(x), int(y0), int(x), int(y1))
                # draw number
                painter.setPen(QColor("#232390"))
                painter.drawText(int(x+2), int(y0+12), f"{mm//10} см" if mm>0 else "")
            elif mm % 5 == 0:
                painter.setPen(QPen(QColor("#555"), 1.7))
                painter.drawLine(int(x), int(y0+7), int(x), int(y1))
            else:
                painter.setPen(QPen(QColor("#555"), 0.7))
                painter.drawLine(int(x), int(y0+15), int(x), int(y1))
        # Left ruler (vertical)
        for mm in range(0, int(sheet_h_mm)+1):
            y = offset_y + mm * MM_TO_PX * scale
            x0 = offset_x - 24
            x1 = offset_x
            if mm % 10 == 0:
                painter.setPen(QPen(QColor("#222"), 2.5))
                painter.drawLine(int(x0), int(y), int(x1), int(y))
                painter.setPen(QColor("#232390"))
                if mm > 0:
                    painter.drawText(int(x0+2), int(y-2), f"{mm//10} см")
            elif mm % 5 == 0:
                painter.setPen(QPen(QColor("#555"), 1.7))
                painter.drawLine(int(x0+7), int(y), int(x1), int(y))
            else:
                painter.setPen(QPen(QColor("#555"), 0.7))
                painter.drawLine(int(x0+15), int(y), int(x1), int(y))

class SheetEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Редактор на лист – Калибриране")
        self.params = {
            'rows': 3, 'cols': 3,
            'left_margin': 8.0, 'top_margin': 12.0,
            'label_w': 63.5, 'label_h': 38.1,
            'col_gap': 2.0, 'row_gap': 0.0,
        }
        self.toggles = {'grid': True, 'crosshairs': True, 'ruler': True}
        self.init_ui()

    def init_ui(self):
        main_h = QHBoxLayout(self)
        # Left panel: parameters
        controls = QVBoxLayout()
        controls.addWidget(QLabel("Параметри на листа", self, font=QFont("Arial", 12, QFont.Bold)))
        self.sp_rows = QSpinBox(self); self.sp_rows.setRange(1, 20); self.sp_rows.setValue(self.params['rows'])
        self.sp_cols = QSpinBox(self); self.sp_cols.setRange(1, 20); self.sp_cols.setValue(self.params['cols'])

        # For floats, use QDoubleSpinBox
        self.sp_left = QDoubleSpinBox(self); self.sp_left.setRange(0, 100); self.sp_left.setDecimals(2); self.sp_left.setSingleStep(0.1); self.sp_left.setValue(self.params['left_margin'])
        self.sp_top = QDoubleSpinBox(self); self.sp_top.setRange(0, 100); self.sp_top.setDecimals(2); self.sp_top.setSingleStep(0.1); self.sp_top.setValue(self.params['top_margin'])
        self.sp_w = QDoubleSpinBox(self); self.sp_w.setRange(1, 200); self.sp_w.setDecimals(2); self.sp_w.setSingleStep(0.1); self.sp_w.setValue(self.params['label_w'])
        self.sp_h = QDoubleSpinBox(self); self.sp_h.setRange(1, 200); self.sp_h.setDecimals(2); self.sp_h.setSingleStep(0.1); self.sp_h.setValue(self.params['label_h'])
        self.sp_cgap = QDoubleSpinBox(self); self.sp_cgap.setRange(0, 50); self.sp_cgap.setDecimals(2); self.sp_cgap.setSingleStep(0.1); self.sp_cgap.setValue(self.params['col_gap'])
        self.sp_rgap = QDoubleSpinBox(self); self.sp_rgap.setRange(0, 50); self.sp_rgap.setDecimals(2); self.sp_rgap.setSingleStep(0.1); self.sp_rgap.setValue(self.params['row_gap'])

        for label, box, key in [
            ("Брой редове", self.sp_rows, 'rows'),
            ("Брой колони", self.sp_cols, 'cols'),
            ("Ляво поле (mm)", self.sp_left, 'left_margin'),
            ("Горно поле (mm)", self.sp_top, 'top_margin'),
            ("Широчина (mm)", self.sp_w, 'label_w'),
            ("Височина (mm)", self.sp_h, 'label_h'),
            ("Хор. разстояние (mm)", self.sp_cgap, 'col_gap'),
            ("Вер. разстояние (mm)", self.sp_rgap, 'row_gap'),
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
        for chk, k in [
            (self.chk_grid, 'grid'), (self.chk_ch, 'crosshairs'), (self.chk_ruler, 'ruler')
        ]:
            chk.stateChanged.connect(lambda _, k=k: self.toggle_overlay(k))
            controls.addWidget(chk)
        controls.addSpacing(10)
        # Print button
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
        self.preview.update()

    def toggle_overlay(self, key):
        self.toggles[key] = getattr(self, f'chk_{key if key!="crosshairs" else "ch"}').isChecked()
        self.preview.update()

    def print_sheet(self):
        from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
        printer = QPrinter(QPrinter.HighResolution)
        dlg = QPrintDialog(printer, self)
        if dlg.exec_() == QPrintDialog.Accepted:
            painter = QPainter(printer)
            # Draw preview scaled to page rect
            page_rect = printer.pageRect()
            # Temporarily set preview size to page size
            old_size = self.preview.size()
            self.preview.resize(page_rect.width(), page_rect.height())
            self.preview.render(painter)
            self.preview.resize(old_size)  # restore size
            painter.end()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = SheetEditor()
    win.resize(1150, 780)
    win.show()
    sys.exit(app.exec_())
