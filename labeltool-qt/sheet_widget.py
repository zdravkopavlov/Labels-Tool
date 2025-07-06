from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QPushButton, QGridLayout, QFileDialog, QApplication, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtGui import QPainter, QFont
from label_widget import LabelWidget

class ClickableFrame(QFrame):
    backgroundClicked = pyqtSignal()

    def mousePressEvent(self, event):
        if self.childAt(event.pos()) is None:
            self.backgroundClicked.emit()
        else:
            super().mousePressEvent(event)

class SheetWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        self.setLayout(outer)
        # Compact horizontal layout for print buttons
        btn_row = QHBoxLayout()
        self.print_btn = QPushButton("Запази PDF")
        self.print_btn.clicked.connect(self.print_sheet)
        btn_row.addWidget(self.print_btn)

        self.print_btn2 = QPushButton("Печатай")
        self.print_btn2.clicked.connect(self.print_exact_sheet)
        btn_row.addWidget(self.print_btn2)

        outer.addLayout(btn_row)


        

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        outer.addWidget(self.scroll)

        self.sheet_frame = ClickableFrame()
        self.sheet_frame.backgroundClicked.connect(self.clear_selection)
        self.sheet_layout = QGridLayout(self.sheet_frame)
        self.sheet_layout.setContentsMargins(12, 12, 12, 12)
        self.sheet_layout.setSpacing(8)
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

        self.installEventFilter(self)
        self.setFocusPolicy(Qt.StrongFocus)

    def handle_label_click(self, label, event):
        idx = self.labels.index(label)
        modifiers = QApplication.keyboardModifiers()
        if modifiers & Qt.ControlModifier:
            if idx in self.selected_indexes:
                self.selected_indexes.remove(idx)
            else:
                self.selected_indexes.add(idx)
            self.last_clicked = idx
        elif modifiers & Qt.ShiftModifier and self.last_clicked is not None:
            rng = range(min(self.last_clicked, idx), max(self.last_clicked, idx) + 1)
            self.selected_indexes.update(rng)
        else:
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
        if event.type() == event.KeyPress:
            self.keyPressEvent(event)
        return super().eventFilter(obj, event)

    def copy_selected_label(self):
        if not self.selected_indexes:
            return
        idx = next(iter(self.selected_indexes))
        label = self.labels[idx]
        label._copy()  # copies to LabelWidget._copied_content

    def paste_to_selected_labels(self):
        if not self.selected_indexes or not LabelWidget._copied_content:
            return
        for idx in self.selected_indexes:
            label = self.labels[idx]
            label._paste()

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
            data = label.get_export_data()
            r, c = divmod(idx, cols)
            x = margin_left_mm + c * (label_w_mm + col_gap_mm)
            y = margin_top_mm + r * (label_h_mm + row_gap_mm)
            x_pt, y_pt = mm_to_pt(x), mm_to_pt(y)
            w_pt, h_pt = mm_to_pt(label_w_mm), mm_to_pt(label_h_mm)

            if data["name"] or data["type"] or data["price_bgn"] or data["price_eur"]:
                margin_inside = mm_to_pt(2)
                align = Qt.AlignLeft if data["logo"] else Qt.AlignCenter
                text_x = x_pt + margin_inside
                text_y = y_pt + margin_inside + 18

                painter.setFont(QFont(font_name, 14, QFont.Bold))
                painter.drawText(
                    int(text_x), int(text_y), int(w_pt - 2 * margin_inside), 20,
                    align, data["name"]
                )
                painter.setFont(QFont(font_name, 10))
                painter.drawText(
                    int(text_x), int(text_y + 20), int(w_pt - 2 * margin_inside), 16,
                    align, data["type"]
                )
                # BGN (always with "лв.")
                painter.setFont(QFont(font_name, 13, QFont.Bold))
                bgn_line = (data["price_bgn"] + " лв.") if data["price_bgn"] else ""
                painter.drawText(
                    int(text_x), int(text_y + 38), int(w_pt - 2 * margin_inside), 18,
                    align, bgn_line
               )
 
                # EUR (always with "€" and unit if present, inline)
                eur_line = data["price_eur"]
                if eur_line:
                    eur_line += " €"
                    if data["unit_eur"]:
                        eur_line += " / " + data["unit_eur"]
                painter.setFont(QFont(font_name, 13, QFont.Bold))
                painter.drawText(
                    int(text_x), int(text_y + 56), int(w_pt - 2 * margin_inside), 18,
                    align, eur_line
                )

        painter.end()

    def print_exact_sheet(self):
        from PyQt5.QtPrintSupport import QPrinter
        from PyQt5.QtGui import QPainter, QFont
        from PyQt5.QtWidgets import QFileDialog
        from PyQt5.QtCore import Qt
        import json
        import os

        if not os.path.exists("3x7.json"):
            print("Missing layout. Please save a sheet setup first.")
            return

        with open("3x7.json", "r", encoding="utf-8") as f:
            settings = json.load(f)

        path, _ = QFileDialog.getSaveFileName(self, "Export PDF", "", "PDF Files (*.pdf)")
        if not path:
            return

        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(path)
        printer.setPageSize(QPrinter.A4)

        mm_to_pt = lambda mm: mm * 72 / 25.4
        a4_w_mm, a4_h_mm = 210, 297
        a4_w_pt = mm_to_pt(a4_w_mm)
        a4_h_pt = mm_to_pt(a4_h_mm)

        page_rect = printer.pageRect()
        page_w_pt, page_h_pt = page_rect.width(), page_rect.height()
        scale = min(page_w_pt / a4_w_pt, page_h_pt / a4_h_pt)
        offset_x = (page_w_pt - a4_w_pt * scale) / 2
        offset_y = (page_h_pt - a4_h_pt * scale) / 2

        painter = QPainter(printer)
        painter.translate(offset_x, offset_y)
        painter.scale(scale, scale)

        margin_left = settings.get("margin_left_mm", 10)
        margin_top = settings.get("margin_top_mm", 10)
        col_gap = settings.get("col_gap_mm", 2.5)
        row_gap = settings.get("row_gap_mm", 0)
        label_w = settings.get("label_width_mm", 63.5)
        label_h = settings.get("label_height_mm", 38.1)
        cols = settings.get("cols", 3)

        for idx, label in enumerate(self.labels):
            data = label.get_export_data()
            r, c = divmod(idx, cols)
            x = mm_to_pt(margin_left + c * (label_w + col_gap))
            y = mm_to_pt(margin_top + r * (label_h + row_gap))
            w = mm_to_pt(label_w)
            h = mm_to_pt(label_h)
            margin = mm_to_pt(2)
            align = Qt.AlignLeft if data["logo"] else Qt.AlignCenter
            tx, ty = x + margin, y + margin + 18

            painter.setFont(QFont("Arial", 14, QFont.Bold))
            painter.drawText(int(tx), int(ty), int(w - 2*margin), 20, align, data["name"])
            painter.setFont(QFont("Arial", 10))
            painter.drawText(int(tx), int(ty + 20), int(w - 2*margin), 16, align, data["type"])

            painter.setFont(QFont("Arial", 13, QFont.Bold))
            if data["price_bgn"]:
                painter.drawText(int(tx), int(ty + 38), int(w - 2*margin), 18, align, data["price_bgn"] + " лв.")

            if data["price_eur"]:
                eur = "€" + data["price_eur"]
                if data["unit_eur"]:
                    eur += " / " + data["unit_eur"]
                painter.drawText(int(tx), int(ty + 56), int(w - 2*margin), 18, align, eur)

        painter.end()


