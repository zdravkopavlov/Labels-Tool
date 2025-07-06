import sys
import json
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QSpinBox, QPushButton,
    QFileDialog, QGraphicsView, QGraphicsScene
)
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPen, QColor, QPainterPath, QBrush, QFont, QPainter
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog

# ─── CONFIG SETUP ───────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
os.makedirs(CONFIG_DIR, exist_ok=True)
SETTINGS_PATH = os.path.join(CONFIG_DIR, "settings.json")
# ────────────────────────────────────────────────────────────────────────────────

class SheetPreview(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setBackgroundBrush(QColor("#eaeaea"))
        self.a4_w_mm, self.a4_h_mm = 210, 297
        self.setRenderHint(QPainter.Antialiasing)
        self.sheet_settings = {}

    def update_preview(self, sheet_settings):
        self.scene.clear()
        self.sheet_settings = sheet_settings
        a4_w, a4_h = self.a4_w_mm, self.a4_h_mm

        # Calculate scale to fit view
        margin = 20
        w = self.viewport().width() - 2*margin
        h = self.viewport().height() - 2*margin
        scale = min(w / a4_w, h / a4_h)
        offset_x = (self.viewport().width() - a4_w * scale) / 2
        offset_y = (self.viewport().height() - a4_h * scale) / 2

        # Draw A4 page
        paper = self.scene.addRect(offset_x, offset_y, a4_w*scale, a4_h*scale,
                                   QPen(Qt.black), QBrush(Qt.white))
        paper.setZValue(-1)

        # Draw labels
        pen = QPen(QColor("#1c80e9")); pen.setWidth(1)
        ls = sheet_settings
        for r in range(ls["rows"]):
            for c in range(ls["cols"]):
                x = offset_x + (ls["margin_left_mm"] + c*(ls["label_width_mm"]+ls["col_gap_mm"]))*scale
                y = offset_y + (ls["margin_top_mm"]  + r*(ls["label_height_mm"]+ls["row_gap_mm"]))*scale
                path = QPainterPath()
                path.addRoundedRect(QRectF(x,y, ls["label_width_mm"]*scale, ls["label_height_mm"]*scale), 8,8)
                item = self.scene.addPath(path, pen); item.setZValue(1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.sheet_settings:
            self.update_preview(self.sheet_settings)

    def print_preview(self):
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPrinter.A4)
        if QPrintDialog(printer, self).exec_() != QPrintDialog.Accepted:
            return
        painter = QPainter(printer)
        # same drawing as update_preview but on printer
        mm2pt = lambda mm: mm * 72/25.4
        scale = min(printer.pageRect().width()/mm2pt(self.a4_w_mm),
                    printer.pageRect().height()/mm2pt(self.a4_h_mm))
        painter.translate((printer.pageRect().width()-mm2pt(self.a4_w_mm)*scale)/2,
                          (printer.pageRect().height()-mm2pt(self.a4_h_mm)*scale)/2)
        painter.scale(scale, scale)
        ls = self.sheet_settings
        pen = QPen(Qt.black); pen.setWidth(1); painter.setPen(pen)
        for r in range(ls["rows"]):
            for c in range(ls["cols"]):
                x = mm2pt(ls["margin_left_mm"]+c*(ls["label_width_mm"]+ls["col_gap_mm"]))
                y = mm2pt(ls["margin_top_mm"] +r*(ls["label_height_mm"]+ls["row_gap_mm"]))
                path = QPainterPath(); path.addRoundedRect(x,y, mm2pt(ls["label_width_mm"]), mm2pt(ls["label_height_mm"]),8,8)
                painter.drawPath(path)
        painter.end()

class SheetEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sheet Setup Editor (Prototype)")
        self.setMinimumSize(900, 700)

        # Layout & Controls
        main = QVBoxLayout(self)
        layout = QHBoxLayout(); main.addLayout(layout)
        left = QVBoxLayout(); layout.addLayout(left,0)

        fontb = QFont("Arial",10,QFont.Bold)
        # Label size
        left.addWidget(QLabel("<b>Label size</b>"))
        for label,text_attr in [("Width:", "in_w"), ("Height:", "in_h")]:
            hl = QHBoxLayout(); hl.addWidget(QLabel(label))
            line = QLineEdit("63.5" if text_attr=="in_w" else "38.1"); setattr(self,text_attr,line)
            hl.addWidget(line); hl.addWidget(QLabel("mm")); left.addLayout(hl)
        # Margins
        left.addSpacing(14); left.addWidget(QLabel("<b>Margins</b>"))
        for label,text_attr in [("Top:","in_mt"),("Left:","in_ml"),("Row gap:","in_rg"),("Col gap:","in_cg")]:
            hl=QHBoxLayout(); hl.addWidget(QLabel(label))
            line=QLineEdit({"in_rg":"0","in_cg":"2.5"}.get(text_attr,"10")); setattr(self,text_attr,line)
            hl.addWidget(line); hl.addWidget(QLabel("mm")); left.addLayout(hl)
        # Rows & Cols
        left.addSpacing(14); left.addWidget(QLabel("<b>Rows & Columns</b>"))
        for label,attr,defv in [("Rows:","in_rows",7),("Cols:","in_cols",3)]:
            hl=QHBoxLayout(); hl.addWidget(QLabel(label))
            spin=QSpinBox(); spin.setRange(1,99); spin.setValue(defv)
            setattr(self,attr,spin); hl.addWidget(spin); left.addLayout(hl)
        left.addSpacing(18)
        # Buttons
        self.save_btn=QPushButton("Save Sheet Setup")
        self.load_btn=QPushButton("Load Sheet Setup")
        self.print_btn=QPushButton("Print Grid")
        for w in (self.save_btn,self.load_btn,self.print_btn): left.addWidget(w)
        left.addStretch(1)

        # Preview
        self.preview = SheetPreview(); layout.addWidget(self.preview,1)

        # Connections
        widgets = [self.in_w,self.in_h,self.in_mt,self.in_ml,self.in_rg,self.in_cg,self.in_rows,self.in_cols]
        for w in widgets:
            sig = w.textChanged if isinstance(w,QLineEdit) else w.valueChanged
            sig.connect(self.on_change)
        self.save_btn.clicked.connect(self.save_setup)
        self.load_btn.clicked.connect(self.load_setup)
        self.print_btn.clicked.connect(self.preview.print_preview)

        # Load & show
        self.load_config()
        self.on_change()

    def get_settings(self):
        def p(v,fb): 
            try: return float(v)
            except: return fb
        return {
            "label_width_mm": p(self.in_w.text(),63.5),
            "label_height_mm":p(self.in_h.text(),38.1),
            "margin_top_mm":p(self.in_mt.text(),10),
            "margin_left_mm":p(self.in_ml.text(),10),
            "row_gap_mm":p(self.in_rg.text(),0),
            "col_gap_mm":p(self.in_cg.text(),2.5),
            "rows":int(self.in_rows.value()),
            "cols":int(self.in_cols.value()),
        }

    def on_change(self):
        settings = self.get_settings()
        self.preview.update_preview(settings)
        # save to config
        with open(SETTINGS_PATH,"w",encoding="utf-8") as f:
            json.dump(settings,f,indent=2)

    def load_config(self):
        if os.path.exists(SETTINGS_PATH):
            try:
                with open(SETTINGS_PATH,"r",encoding="utf-8") as f:
                    settings = json.load(f)
                # apply
                self.in_w.setText(str(settings["label_width_mm"]))
                self.in_h.setText(str(settings["label_height_mm"]))
                self.in_mt.setText(str(settings["margin_top_mm"]))
                self.in_ml.setText(str(settings["margin_left_mm"]))
                self.in_rg.setText(str(settings["row_gap_mm"]))
                self.in_cg.setText(str(settings["col_gap_mm"]))
                self.in_rows.setValue(settings["rows"])
                self.in_cols.setValue(settings["cols"])
            except:
                pass

    def save_setup(self):
        fn,_ = QFileDialog.getSaveFileName(self,"Save Sheet Setup","","JSON Files (*.json)")
        if fn:
            json.dump(self.get_settings(),open(fn,"w",encoding="utf-8"),indent=2)

    def load_setup(self):
        fn,_ = QFileDialog.getOpenFileName(self,"Load Sheet Setup","","JSON Files (*.json)")
        if fn:
            cfg=json.load(open(fn,"r",encoding="utf-8"))
            # apply only, don't overwrite main config
            self.in_w.setText(str(cfg.get("label_width_mm",63.5)))
            self.in_h.setText(str(cfg.get("label_height_mm",38.1)))
            self.in_mt.setText(str(cfg.get("margin_top_mm",10)))
            self.in_ml.setText(str(cfg.get("margin_left_mm",10)))
            self.in_rg.setText(str(cfg.get("row_gap_mm",0)))
            self.in_cg.setText(str(cfg.get("col_gap_mm",2.5)))
            self.in_rows.setValue(cfg.get("rows",7))
            self.in_cols.setValue(cfg.get("cols",3))
            self.on_change()
