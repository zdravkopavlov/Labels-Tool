import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel
from PyQt5.QtGui import QPainter, QPen, QFont
from PyQt5.QtCore import Qt
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog

MM_TO_PX = 72 / 25.4  # Not used for printing, but for preview if you want to add it later.

class CalibrationWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Калибрационен квадрат за принтер")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "Натиснете бутона, за да отпечатате калибрационен квадрат 10×10mm.\n"
            "Измерете го с линийка. Ако не е точно 10mm, трябва да коригирате скалата при печат."
        ))
        self.print_button = QPushButton("Печатай калибрационен квадрат")
        self.print_button.clicked.connect(self.print_calibration_square)
        layout.addWidget(self.print_button)
        layout.addStretch(1)
        self.setMinimumSize(400, 180)

    def print_calibration_square(self):
        printer = QPrinter(QPrinter.HighResolution)
        dlg = QPrintDialog(printer, self)
        if dlg.exec_() == QPrintDialog.Accepted:
            painter = QPainter(printer)
            page_rect = printer.pageRect()  # This is the *printable* area in pixels

            # Convert 10mm to printer pixels
            dpi_x = printer.resolution()
            dpi_y = printer.resolution()
            mm_to_inch = 1.0 / 25.4
            square_px_x = int(10 * mm_to_inch * dpi_x)
            square_px_y = int(10 * mm_to_inch * dpi_y)

            # Center square on the page
            cx = page_rect.x() + page_rect.width() // 2
            cy = page_rect.y() + page_rect.height() // 2
            left = cx - square_px_x // 2
            top = cy - square_px_y // 2

            # White background
            painter.fillRect(page_rect, Qt.white)

            # Bold square
            pen = QPen(Qt.black, 2)
            painter.setPen(pen)
            painter.drawRect(left, top, square_px_x, square_px_y)

            # Draw horizontal and vertical lines through the center of the square for easy measuring
            painter.drawLine(left - 40, cy, left + square_px_x + 40, cy)
            painter.drawLine(cx, top - 40, cx, top + square_px_y + 40)

            # Draw "10 mm" labels
            font = QFont("Arial", 18, QFont.Bold)
            painter.setFont(font)
            painter.drawText(left + square_px_x + 10, cy + 8, "10 mm")
            painter.drawText(cx - 25, top - 12, "10 mm")

            # Draw instruction in bottom corner
            small_font = QFont("Arial", 10)
            painter.setFont(small_font)
            painter.drawText(
                page_rect.x() + 40,
                page_rect.y() + page_rect.height() - 30,
                "Измерете с линийка. Ако квадратът не е 10мм, коригирайте мащаба в настройките."
            )
            painter.end()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = CalibrationWidget()
    win.show()
    sys.exit(app.exec_())
