import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QComboBox, QButtonGroup, QToolButton, QFrame
)
from PyQt5.QtGui import QFont, QFontDatabase, QPainter, QPen, QColor
from PyQt5.QtCore import Qt

MM_TO_PX = 72 / 25.4

LABEL_W_MM = 63.5
LABEL_H_MM = 38.1
LABEL_W_PX = int(LABEL_W_MM * MM_TO_PX)
LABEL_H_PX = int(LABEL_H_MM * MM_TO_PX)

# Default font settings; will update later based on FONT_LIST
DEFAULTS = {
    "main":    {"font": "Arial", "size": 15, "bold": False, "italic": False, "align": Qt.AlignCenter},
    "second":  {"font": "Arial", "size": 12, "bold": False, "italic": False, "align": Qt.AlignCenter},
    "bgn":     {"font": "Arial", "size": 16, "bold": True,  "italic": False, "align": Qt.AlignCenter},
    "eur":     {"font": "Arial", "size": 16, "bold": True,  "italic": False, "align": Qt.AlignCenter},
}

class LabelFieldEdit(QTextEdit):
    def __init__(self, placeholder="", **kwargs):
        super().__init__(**kwargs)
        self.setPlaceholderText(placeholder)
        self.setFrameShape(QFrame.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setTabChangesFocus(True)
        self.setFont(QFont("Arial", 16))  # Bigger input text

class PriceFieldEdit(QLineEdit):
    def __init__(self, placeholder="", **kwargs):
        super().__init__(**kwargs)
        self.setPlaceholderText(placeholder)
        self.setFrame(False)
        self.setAlignment(Qt.AlignCenter)
        self.setMaxLength(16)
        self.setFont(QFont("Arial", 16))

class LabelPreview(QWidget):
    def __init__(self, state):
        super().__init__()
        self.state = state
        self.setFixedSize(LABEL_W_PX + 8, LABEL_H_PX + 8)

    def paintEvent(self, event):
        qp = QPainter(self)
        qp.setRenderHint(QPainter.Antialiasing)
        qp.setPen(QPen(QColor("#333"), 2))
        qp.setBrush(Qt.white)
        qp.drawRoundedRect(4, 4, LABEL_W_PX, LABEL_H_PX, 12, 12)
        margin = 16
        x0 = 4 + margin
        y0 = 4 + margin
        w = LABEL_W_PX - 2 * margin
        h = LABEL_H_PX - 2 * margin

        lines = []
        main = self.state['main']
        second = self.state['second']
        bgn = self.state['bgn']
        eur = self.state['eur']

        if main['text']:
            lines.extend([(main['text'], main)])
        if second['text']:
            lines.extend([(second['text'], second)])
        if bgn['text']:
            lines.append((f"{bgn['text']} лв.", bgn))
        if eur['text']:
            lines.append((f"€{eur['text']}", eur))

        total_h = 0
        metrics = []
        for text, field in lines:
            fnt = QFont(field['font'], field['size'])
            fnt.setBold(field['bold'])
            fnt.setItalic(field['italic'])
            qp.setFont(fnt)
            rect = qp.boundingRect(x0, 0, w, h, field['align'] | Qt.TextWordWrap, text)
            metrics.append((rect.height(), field, text))
            total_h += rect.height()

        cy = y0 + (h - total_h) // 2
        for idx, (height, field, text) in enumerate(metrics):
            fnt = QFont(field['font'], field['size'])
            fnt.setBold(field['bold'])
            fnt.setItalic(field['italic'])
            qp.setFont(fnt)
            rect = qp.boundingRect(x0, cy, w, height, field['align'] | Qt.TextWordWrap, text)
            qp.drawText(rect, field['align'] | Qt.TextWordWrap, text)
            cy += height

class LabelEditor(QWidget):
    def __init__(self, font_list):
        super().__init__()
        self.setWindowTitle("Label Editor Prototype")
        self.resize(700, 750)

        # Set global font for the UI (affects labels, combo, buttons)
        ui_font = QFont("Arial", 13)
        self.setFont(ui_font)

        # Update font defaults to selected font
        for tag in DEFAULTS:
            DEFAULTS[tag]["font"] = font_list[0]

        self.state = {
            'main':   {'text': '', **DEFAULTS['main']},
            'second': {'text': '', **DEFAULTS['second']},
            'bgn':    {'text': '', **DEFAULTS['bgn']},
            'eur':    {'text': '', **DEFAULTS['eur']},
        }
        self.active_field = 'main'

        # Toolbar
        tbar = QHBoxLayout()
        self.font_combo = QComboBox()
        self.font_combo.addItems(font_list)
        self.font_combo.setFont(QFont("Arial", 13))
        self.font_combo.setMinimumWidth(150)
        tbar.addWidget(self.font_combo)

        self.font_size_minus = QToolButton()
        self.font_size_minus.setText("–")
        self.font_size_minus.setFont(QFont("Arial", 15))
        self.font_size_minus.setMinimumWidth(32)
        self.font_size_plus = QToolButton()
        self.font_size_plus.setText("+")
        self.font_size_plus.setFont(QFont("Arial", 15))
        self.font_size_plus.setMinimumWidth(32)
        self.font_size_disp = QLabel(str(DEFAULTS['main']['size']))
        self.font_size_disp.setFont(QFont("Arial", 15))
        tbar.addWidget(self.font_size_minus)
        tbar.addWidget(self.font_size_disp)
        tbar.addWidget(self.font_size_plus)

        self.bold_btn = QToolButton()
        self.bold_btn.setText("B")
        self.bold_btn.setFont(QFont("Arial", 15, QFont.Bold))
        self.bold_btn.setCheckable(True)
        self.bold_btn.setStyleSheet("font-weight: bold;")
        self.italic_btn = QToolButton()
        self.italic_btn.setText("I")
        self.italic_btn.setFont(QFont("Arial", 15, QFont.Normal, italic=True))
        self.italic_btn.setCheckable(True)
        self.italic_btn.setStyleSheet("font-style: italic;")
        tbar.addWidget(self.bold_btn)
        tbar.addWidget(self.italic_btn)

        self.align_group = QButtonGroup(self)
        self.align_left = QToolButton()
        self.align_left.setText("L")
        self.align_left.setFont(QFont("Arial", 15))
        self.align_center = QToolButton()
        self.align_center.setText("C")
        self.align_center.setFont(QFont("Arial", 15))
        self.align_right = QToolButton()
        self.align_right.setText("R")
        self.align_right.setFont(QFont("Arial", 15))
        self.align_left.setCheckable(True)
        self.align_center.setCheckable(True)
        self.align_right.setCheckable(True)
        self.align_group.addButton(self.align_left, Qt.AlignLeft)
        self.align_group.addButton(self.align_center, Qt.AlignCenter)
        self.align_group.addButton(self.align_right, Qt.AlignRight)
        tbar.addWidget(self.align_left)
        tbar.addWidget(self.align_center)
        tbar.addWidget(self.align_right)
        tbar.addStretch(1)

        # Field editors
        fmain = LabelFieldEdit("Основен текст (много реда OK)")
        fsecond = LabelFieldEdit("Втори ред (по избор)")
        fprice_bgn = PriceFieldEdit("BGN")
        feur = PriceFieldEdit("EUR")

        # Preview widget
        self.preview = LabelPreview(self.state)

        # Layout
        v = QVBoxLayout(self)
        v.addLayout(tbar)
        v.addSpacing(12)
        lab = QLabel("Основен текст:")
        lab.setFont(QFont("Arial", 14))
        v.addWidget(lab)
        v.addWidget(fmain)
        lab = QLabel("Втори ред:")
        lab.setFont(QFont("Arial", 14))
        v.addWidget(lab)
        v.addWidget(fsecond)
        lab = QLabel("Цена BGN:")
        lab.setFont(QFont("Arial", 14))
        v.addWidget(lab)
        v.addWidget(fprice_bgn)
        lab = QLabel("Цена EUR:")
        lab.setFont(QFont("Arial", 14))
        v.addWidget(lab)
        v.addWidget(feur)
        v.addStretch(1)
        lab = QLabel("WYSIWYG Преглед:")
        lab.setFont(QFont("Arial", 15, QFont.Bold))
        v.addWidget(lab)
        v.addWidget(self.preview, alignment=Qt.AlignHCenter)

        self.fields = {
            "main": fmain,
            "second": fsecond,
            "bgn": fprice_bgn,
            "eur": feur,
        }

        # Field selection
        for name, widget in self.fields.items():
            widget.installEventFilter(self)
            if isinstance(widget, QTextEdit):
                widget.textChanged.connect(self.make_text_updater(name))
            elif isinstance(widget, QLineEdit):
                widget.textChanged.connect(self.make_text_updater(name))

        # Toolbar connections
        self.font_combo.currentTextChanged.connect(self.apply_toolbar)
        self.font_size_minus.clicked.connect(lambda: self.adjust_font_size(-1))
        self.font_size_plus.clicked.connect(lambda: self.adjust_font_size(+1))
        self.bold_btn.toggled.connect(lambda _: self.apply_toolbar())
        self.italic_btn.toggled.connect(lambda _: self.apply_toolbar())
        self.align_left.toggled.connect(lambda _: self.apply_toolbar())
        self.align_center.toggled.connect(lambda _: self.apply_toolbar())
        self.align_right.toggled.connect(lambda _: self.apply_toolbar())

        self.update_toolbar_from_field()

    def make_text_updater(self, field):
        def updater():
            if isinstance(self.fields[field], QTextEdit):
                txt = self.fields[field].toPlainText()
            else:
                txt = self.fields[field].text()
            self.state[field]['text'] = txt
            self.preview.update()
        return updater

    def eventFilter(self, obj, ev):
        for name, widget in self.fields.items():
            if obj is widget:
                if ev.type() == ev.FocusIn:
                    self.active_field = name
                    self.update_toolbar_from_field()
        return super().eventFilter(obj, ev)

    def update_toolbar_from_field(self):
        s = self.state[self.active_field]
        self.font_combo.setCurrentText(s['font'])
        self.font_size_disp.setText(str(s['size']))
        self.bold_btn.setChecked(s['bold'])
        self.italic_btn.setChecked(s['italic'])
        if s['align'] == Qt.AlignLeft:
            self.align_left.setChecked(True)
        elif s['align'] == Qt.AlignRight:
            self.align_right.setChecked(True)
        else:
            self.align_center.setChecked(True)

    def apply_toolbar(self):
        s = self.state[self.active_field]
        s['font'] = self.font_combo.currentText()
        try:
            s['size'] = int(self.font_size_disp.text())
        except:
            s['size'] = 12
        s['bold'] = self.bold_btn.isChecked()
        s['italic'] = self.italic_btn.isChecked()
        if self.align_left.isChecked():
            s['align'] = Qt.AlignLeft
        elif self.align_right.isChecked():
            s['align'] = Qt.AlignRight
        else:
            s['align'] = Qt.AlignCenter
        self.preview.update()

    def adjust_font_size(self, delta):
        val = int(self.font_size_disp.text())
        new_val = max(6, min(72, val + delta))
        self.font_size_disp.setText(str(new_val))
        self.apply_toolbar()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    FONT_DB = QFontDatabase()
    FONTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
    FONT_LIST = []
    for fname in os.listdir(FONTS_DIR):
        if fname.lower().endswith('.ttf'):
            family_id = FONT_DB.addApplicationFont(os.path.join(FONTS_DIR, fname))
            families = FONT_DB.applicationFontFamilies(family_id)
            if families:
                FONT_LIST.extend(families)
    if not FONT_LIST:
        FONT_LIST = ["Arial"]
    win = LabelEditor(font_list=FONT_LIST)
    win.show()
    sys.exit(app.exec_())
