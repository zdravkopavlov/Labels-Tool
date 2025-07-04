from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QPushButton, QFrame, QGridLayout, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtGui import QPainter, QFont
from label_widget import LabelWidget

class SheetWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        self.setLayout(outer)

        self.add_btn = QPushButton("Add label")
        self.add_btn.clicked.connect(self.add_label)
        outer.addWidget(self.add_btn)

        self.print_btn = QPushButton("Print Sheet (Export PDF)")
        self.print_btn.clicked.connect(self.print_sheet)
        outer.addWidget(self.print_btn)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        outer.addWidget(self.scroll)

        self.sheet_frame = QFrame()
        self.sheet_layout = QGridLayout(self.sheet_frame)
        self.sheet_layout.setContentsMargins(12, 12, 12, 12)
        self.sheet_layout.setSpacing(8)
        self.sheet_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.scroll.setWidget(self.sheet_frame)

        self.rows = 7
        self.cols = 3
        self.labels = []  # List of LabelWidget instances

        self.refresh_grid()

    def refresh_grid(self):
        # Clear the grid
        for i in reversed(range(self.sheet_layout.count())):
            widget = self.sheet_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        # Add labels to the grid, fill up to 21 slots with empty spaces
        for idx in range(self.rows * self.cols):
            if idx < len(self.labels):
                self.sheet_layout.addWidget(self.labels[idx], idx // self.cols, idx % self.cols)
            else:
                spacer = QWidget()
                spacer.setFixedSize(167, 100)  # match label widget size
                self.sheet_layout.addWidget(spacer, idx // self.cols, idx % self.cols)

    def add_label(self):
        if len(self.labels) < self.rows * self.cols:
            label = LabelWidget()
            label.changed.connect(self.label_changed)
            self.labels.append(label)
            self.refresh_grid()

    def label_changed(self):
        pass

    def print_sheet(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export PDF", "", "PDF Files (*.pdf)")
        if not path:
            return

        printer = QPrinter()
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(path)
        printer.setPageSize(printer.A4)

        # Sticker/grid setup
        label_w_mm = 63.5
        label_h_mm = 38.1
        cols, rows = self.cols, self.rows
        margin_left_mm = 10
        margin_top_mm = 10
        col_gap_mm = 2.5
        row_gap_mm = 0  # Adjust if needed

        mm_to_pt = lambda mm: mm * 72 / 25.4

        painter = QPainter(printer)
        font_name = "Arial"
        for idx in range(self.rows * self.cols):
            r, c = divmod(idx, cols)
            x = margin_left_mm + c * (label_w_mm + col_gap_mm)
            y = margin_top_mm + r * (label_h_mm + row_gap_mm)
            x_pt, y_pt = mm_to_pt(x), mm_to_pt(y)
            w_pt, h_pt = mm_to_pt(label_w_mm), mm_to_pt(label_h_mm)
            # Draw rectangle for the label
            painter.setPen(Qt.black)
            painter.setBrush(Qt.white)
            painter.drawRect(int(x_pt), int(y_pt), int(w_pt), int(h_pt))

            if idx < len(self.labels):
                label = self.labels[idx]
                margin_inside = mm_to_pt(2)
                text_x = x_pt + margin_inside
                text_y = y_pt + margin_inside + 18

                painter.setFont(QFont(font_name, 14, QFont.Bold))
                painter.drawText(
                    int(text_x), int(text_y), int(w_pt - 2 * margin_inside), 20,
                    Qt.AlignLeft, label.get_name()
                )
                painter.setFont(QFont(font_name, 10))
                painter.drawText(
                    int(text_x), int(text_y + 20), int(w_pt - 2 * margin_inside), 16,
                    Qt.AlignLeft, label.get_type()
                )
                painter.setFont(QFont(font_name, 11))
                painter.drawText(
                    int(text_x), int(text_y + 36), int(w_pt - 2 * margin_inside), 16,
                    Qt.AlignLeft, label.get_price()
                )

        painter.end()
