import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QDoubleSpinBox, QPushButton, QSizePolicy
)
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtCore import Qt

MM_TO_PX = 72 / 25.4  # preview only
A4_W, A4_H = 210.0, 297.0

class SheetPreview(QWidget):
    def __init__(self, params, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.params = params
        self.setMinimumSize(800, 600)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.calibration_mode = False

    def paintEvent(self, event):
        p = self.params
        w = self.width()
        h = self.height()
        scale = min((w-40)/(A4_W*MM_TO_PX), (h-40)/(A4_H*MM_TO_PX))
        off_x = (w - A4_W*MM_TO_PX*scale)/2
        off_y = (h - A4_H*MM_TO_PX*scale)/2

        qp = QPainter(self)
        qp.setRenderHint(QPainter.Antialiasing)

        def mm_to_px(x, y):
            return (
                off_x + x*MM_TO_PX*scale,
                off_y + y*MM_TO_PX*scale
            )

        # Calibration print preview: fill full page with gray
        if self.calibration_mode:
            qp.fillRect(int(off_x), int(off_y),
                        int(A4_W*MM_TO_PX*scale), int(A4_H*MM_TO_PX*scale),
                        QColor("#dddddd"))
            return

        # 1. Draw the paper
        qp.fillRect(int(off_x), int(off_y),
                    int(A4_W*MM_TO_PX*scale), int(A4_H*MM_TO_PX*scale),
                    Qt.white)
        qp.setPen(QPen(Qt.black, 2))
        qp.drawRect(int(off_x), int(off_y),
                    int(A4_W*MM_TO_PX*scale), int(A4_H*MM_TO_PX*scale))

        # 2. Draw shaded unprintable margin
        l, t, r, b = [p[k] for k in ['m_left','m_top','m_right','m_bottom']]
        px_w = A4_W*MM_TO_PX*scale
        px_h = A4_H*MM_TO_PX*scale
        # Top
        qp.fillRect(int(off_x), int(off_y), int(px_w), int(t*MM_TO_PX*scale), QColor(180,180,180,60))
        # Bottom
        qp.fillRect(int(off_x), int(off_y+px_h-b*MM_TO_PX*scale), int(px_w), int(b*MM_TO_PX*scale), QColor(180,180,180,60))
        # Left
        qp.fillRect(int(off_x), int(off_y), int(l*MM_TO_PX*scale), int(px_h), QColor(180,180,180,60))
        # Right
        qp.fillRect(int(off_x+px_w-r*MM_TO_PX*scale), int(off_y), int(r*MM_TO_PX*scale), int(px_h), QColor(180,180,180,60))

        # 3. Dashed rectangle for the true printable area
        qp.setPen(QPen(Qt.darkGray, 2, Qt.DashLine))
        pa_x, pa_y = mm_to_px(l, t)
        pa_w = (A4_W-l-r)*MM_TO_PX*scale
        pa_h = (A4_H-t-b)*MM_TO_PX*scale
        qp.drawRect(int(pa_x), int(pa_y), int(pa_w), int(pa_h))

        # 4. Sticker margin "start" mark (red dot and text)
        sl, st = p['s_left'], p['s_top']
        mark_x, mark_y = mm_to_px(l+sl, t+st)
        qp.setPen(QPen(Qt.red, 3))
        qp.drawEllipse(int(mark_x)-4, int(mark_y)-4, 8, 8)
        qp.setPen(QPen(Qt.red, 1))
        qp.drawText(int(mark_x)+10, int(mark_y)+5, "Начало на стикерната зона")

    def set_calibration(self, mode):
        self.calibration_mode = mode
        self.update()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Минимален инструмент за калибрация на етикети")
        self.params = {
            'm_left': 5.0, 'm_top': 5.0, 'm_right': 5.0, 'm_bottom': 5.0,  # hardware
            's_left': 0.0, 's_top': 0.0                                    # sticker
        }
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        controls = QVBoxLayout()

        # Calibration print button
        btn_calib = QPushButton("Калибриращ печат (сив фон)")
        btn_calib.clicked.connect(self.on_calibration_print)
        controls.addWidget(btn_calib)

        # Printer margin group
        gb_hw = QGroupBox("Измерени граници на принтера (mm)")
        l_hw = QHBoxLayout()
        self.sp_ml = QDoubleSpinBox(); self.sp_ml.setRange(0,20); self.sp_ml.setValue(self.params['m_left'])
        self.sp_mt = QDoubleSpinBox(); self.sp_mt.setRange(0,20); self.sp_mt.setValue(self.params['m_top'])
        self.sp_mr = QDoubleSpinBox(); self.sp_mr.setRange(0,20); self.sp_mr.setValue(self.params['m_right'])
        self.sp_mb = QDoubleSpinBox(); self.sp_mb.setRange(0,20); self.sp_mb.setValue(self.params['m_bottom'])
        for spin, key, label in [
            (self.sp_ml, 'm_left', 'Ляво'), (self.sp_mt, 'm_top', 'Горе'),
            (self.sp_mr, 'm_right', 'Дясно'), (self.sp_mb, 'm_bottom', 'Долу')
        ]:
            spin.valueChanged.connect(lambda val, k=key: self.set_param(k, val))
            l_hw.addWidget(QLabel(label)); l_hw.addWidget(spin)
        gb_hw.setLayout(l_hw)
        controls.addWidget(gb_hw)

        # Sticker margin group
        gb_sticker = QGroupBox("Стикерен лист – допълнителен отстъп (mm)")
        l_sticker = QHBoxLayout()
        self.sp_sl = QDoubleSpinBox(); self.sp_sl.setRange(0,30); self.sp_sl.setValue(self.params['s_left'])
        self.sp_st = QDoubleSpinBox(); self.sp_st.setRange(0,30); self.sp_st.setValue(self.params['s_top'])
        for spin, key, label in [
            (self.sp_sl, 's_left', 'Ляво'), (self.sp_st, 's_top', 'Горе')
        ]:
            spin.valueChanged.connect(lambda val, k=key: self.set_param(k, val))
            l_sticker.addWidget(QLabel(label)); l_sticker.addWidget(spin)
        gb_sticker.setLayout(l_sticker)
        controls.addWidget(gb_sticker)

        # Print button
        btn_print = QPushButton("Печатай (WYSIWYG)")
        btn_print.clicked.connect(self.on_print_sheet)
        controls.addWidget(btn_print)
        controls.addStretch(1)

        # Preview
        self.preview = SheetPreview(self.params)
        layout.addLayout(controls, 0)
        layout.addWidget(self.preview, 1)

    def set_param(self, key, value):
        self.params[key] = float(value)
        self.preview.update()

    def on_calibration_print(self):
        from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
        printer = QPrinter(QPrinter.HighResolution)
        printer.setFullPage(True)
        dlg = QPrintDialog(printer, self)
        if dlg.exec_() == QPrintDialog.Accepted:
            painter = QPainter(printer)
            rect = printer.pageRect()
            painter.fillRect(rect, QColor("#dddddd"))  # Solid gray, no borders
            painter.end()

    def on_print_sheet(self):
        from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
        printer = QPrinter(QPrinter.HighResolution)
        printer.setFullPage(True)
        dlg = QPrintDialog(printer, self)
        if dlg.exec_() == QPrintDialog.Accepted:
            painter = QPainter(printer)
            rect = printer.pageRect()
            # Drawing as if (0,0) is top-left of printable area, DO NOT add hardware margins again!
            # Only use sticker offsets
            p = self.params
            printable_w_mm = A4_W - p['m_left'] - p['m_right']
            printable_h_mm = A4_H - p['m_top'] - p['m_bottom']
            scale_x = rect.width() / (printable_w_mm * MM_TO_PX)
            scale_y = rect.height() / (printable_h_mm * MM_TO_PX)
            scale = min(scale_x, scale_y)
            def mm_to_px(x_mm, y_mm):
                return x_mm * MM_TO_PX * scale, y_mm * MM_TO_PX * scale

            # Optional: fill background white
            painter.fillRect(rect, Qt.white)
            # Draw dashed rectangle for printable area (for calibration)
            painter.setPen(QPen(Qt.darkGray, 2, Qt.DashLine))
            painter.drawRect(0, 0, rect.width()-1, rect.height()-1)

            # Draw sticker margin start
            sl, st = p['s_left'], p['s_top']
            x, y = mm_to_px(sl, st)
            painter.setPen(QPen(Qt.red, 3))
            painter.drawEllipse(int(x)-4, int(y)-4, 8, 8)
            painter.setPen(QPen(Qt.red, 1))
            painter.drawText(int(x)+10, int(y)+5, "Начало на стикерната зона")
            painter.end()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.resize(1100, 800)
    win.show()
    sys.exit(app.exec_())
