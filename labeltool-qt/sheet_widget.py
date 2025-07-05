from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QPushButton, QGridLayout, QFileDialog, QApplication, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtGui import QPainter, QFont
from label_widget import LabelWidget

# --- ClickableFrame lets us catch clicks on the empty area of the grid ---
class ClickableFrame(QFrame):
    backgroundClicked = pyqtSignal()

    def mousePressEvent(self, event):
        # Only emit if click is not on a child widget (label)
        if self.childAt(event.pos()) is None:
            self.backgroundClicked.emit()
        else:
            super().mousePressEvent(event)

class SheetWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        self.setLayout(outer)

        self.print_btn = QPushButton("Print Sheet (Export PDF)")
        self.print_btn.clicked.connect(self.print_sheet)
        outer.addWidget(self.print_btn)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        outer.addWidget(self.scroll)

        # Use ClickableFrame to catch clicks on the grid background!
        self.sheet_frame = ClickableFrame()
        self.sheet_frame.backgroundClicked.connect(self.clear_selection)
        self.sheet_layout = QGridLayout(self.sheet_frame)
        # --- Where to change sheet/grid margin and spacing ---
        self.sheet_layout.setContentsMargins(12, 12, 12, 12)  # (L, T, R, B) around the whole grid
        self.sheet_layout.setSpacing(8)  # Space between labels
        self.sheet_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.scroll.setWidget(self.sheet_frame)

        self.rows = 7
        self.cols = 3

        # Always create all 21 label widgets
        self.labels = [LabelWidget() for _ in range(self.rows * self.cols)]
        for idx, label in enumerate(self.labels):
            self.sheet_layout.addWidget(label, idx // self.cols, idx % self.cols)
            label.clicked.connect(self.handle_label_click)

        # Multi-selection
        self.selected_indexes = set()
        self.last_clicked = None

        self.update_selection()

        # Clipboard for copy/paste
        self.copied_label_data = None

        # Enable key event filtering for Ctrl+C/V
        self.installEventFilter(self)
        self.setFocusPolicy(Qt.StrongFocus)

    def handle_label_click(self, label, event):
        idx = self.labels.index(label)
        modifiers = QApplication.keyboardModifiers()
        if modifiers & Qt.ControlModifier:
            # Ctrl+Click: Toggle selection
            if idx in self.selected_indexes:
                self.selected_indexes.remove(idx)
            else:
                self.selected_indexes.add(idx)
            self.last_clicked = idx
        elif modifiers & Qt.ShiftModifier and self.last_clicked is not None:
            # Shift+Click: Select range
            rng = range(min(self.last_clicked, idx), max(self.last_clicked, idx) + 1)
            self.selected_indexes.update(rng)
        else:
            # Single click: select only this
            self.selected_indexes = {idx}
            self.last_clicked = idx
        self.update_selection()

    def clear_selection(self):
        self.selected_indexes = set()
        self.last_clicked = None
        self.update_selection()

    def update_selection(self):
        for i, label in enumerate(self.labels):
            label.set_selected(i in self.selected_indexes)

    def keyPressEvent(self, event):
        if (event.modifiers() & Qt.ControlModifier) and event.key() == Qt.Key_C:
            self.copy_selected_label()
        elif (event.modifiers() & Qt.ControlModifier) and event.key() == Qt.Key_V:
            self.paste_to_selected_labels()
        else:
            super().keyPressEvent(event)

    def eventFilter(self, obj, event):
        # Forward key presses to keyPressEvent so Ctrl+C/V work even when label field is focused
        if event.type() == event.KeyPress:
            self.keyPressEvent(event)
        return super().eventFilter(obj, event)

    def copy_selected_label(self):
        if not self.selected_indexes:
            return
        # Copy the first selected label's data
        idx = next(iter(self.selected_indexes))
        label = self.labels[idx]
        self.copied_label_data = (
            label.get_name(),
            label.get_type(),
            label.get_price()
        )

    def paste_to_selected_labels(self):
        if not self.selected_indexes or not self.copied_label_data:
            return
        name, typ, price = self.copied_label_data
        for idx in self.selected_indexes:
            label = self.labels[idx]
            label.set_name(name)
            label.set_type(typ)
            label.set_price(price)

    def print_sheet(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export PDF", "", "PDF Files (*.pdf)")
        if not path:
            return

        printer = QPrinter()
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(path)
        printer.setPageSize(printer.A4)

        label_w_mm = 63.5
        label_h_mm = 38.1
        cols, rows = self.cols, self.rows
        margin_left_mm = 10
        margin_top_mm = 10
        col_gap_mm = 2.5
        row_gap_mm = 0

        mm_to_pt = lambda mm: mm * 72 / 25.4

        painter = QPainter(printer)
        font_name = "Arial"
        for idx, label in enumerate(self.labels):
            r, c = divmod(idx, cols)
            x = margin_left_mm + c * (label_w_mm + col_gap_mm)
            y = margin_top_mm + r * (label_h_mm + row_gap_mm)
            x_pt, y_pt = mm_to_pt(x), mm_to_pt(y)
            w_pt, h_pt = mm_to_pt(label_w_mm), mm_to_pt(label_h_mm)

            # Only draw text if there's anything entered:
            if label.get_name() or label.get_type() or label.get_price():
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
