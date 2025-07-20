from PyQt5.QtWidgets import QWidget, QGridLayout, QScrollArea, QVBoxLayout, QToolButton
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QColor, QFont

class SheetLabel(QWidget):
    clicked = pyqtSignal(object, object)
    rightClicked = pyqtSignal(object, object)
    def __init__(self, idx, get_label, selected=False, label_w_px=150, label_h_px=60):
        super().__init__()
        self.idx = idx
        self.get_label = get_label
        self.selected = selected
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumSize(label_w_px, label_h_px)
        self.setMaximumSize(label_w_px, label_h_px)
        self.setSizePolicy(QWidget.sizePolicy(self))

    def set_selected(self, on=True):
        self.selected = on
        self.update()

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self.clicked.emit(self, ev)
        elif ev.button() == Qt.RightButton:
            self.rightClicked.emit(self, ev)

    def paintEvent(self, event):
        label = self.get_label()
        qp = QPainter(self)
        qp.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(3,3,-3,-3)
        qp.setPen(QPen(QColor("#2c7ee9") if self.selected else QColor("#cccccc"), 2 if self.selected else 1))
        qp.setBrush(QColor(label["main"]["bg_color"]))
        qp.drawRoundedRect(rect, 12, 12)

        # Draw text fields centered
        margin = 12
        x0, y0 = rect.x() + margin, rect.y() + margin
        w, h = rect.width() - 2*margin, rect.height() - 2*margin
        lines = []
        for key in ["main", "second", "bgn", "eur"]:
            fld = label[key]
            t = fld["text"]
            if key=="bgn":
                t = t.replace(" лв.", "").replace("лв.", "").strip()
                if t: t += " лв."
            if key=="eur":
                t = t.replace("€", "").strip()
                if t: t = "€" + t
            if t:
                lines.append((t, fld))
        total_h, metrics = 0, []
        for text, field in lines:
            fnt = QFont(field['font'], int(field['size']))
            fnt.setBold(field['bold'])
            fnt.setItalic(field['italic'])
            qp.setFont(fnt)
            fm = qp.fontMetrics()
            rect_t = fm.boundingRect(0, 0, w, h, field['align']|Qt.TextWordWrap, text)
            metrics.append((rect_t.height(), field, text, fnt))
            total_h += rect_t.height()
        cy = y0 + (h - total_h) // 2
        for hgt, field, text, fnt in metrics:
            qp.setFont(fnt)
            qp.setPen(QColor(field.get("font_color", "#222")))
            rect_t = qp.fontMetrics().boundingRect(0, 0, w, hgt, field['align']|Qt.TextWordWrap, text)
            draw_rect = rect_t.translated(x0, cy)
            qp.drawText(draw_rect, field['align']|Qt.TextWordWrap, text)
            cy += hgt

class PreviewPaneWidget(QWidget):
    label_clicked = pyqtSignal(int, object)        # idx, event
    label_right_clicked = pyqtSignal(int, object)  # idx, event

    def __init__(self, labels, rows, cols, label_w_mm, label_h_mm, spacing_px=12, parent=None):
        super().__init__(parent)
        self.labels = labels
        self.rows = rows
        self.cols = cols
        self.label_w_mm = label_w_mm
        self.label_h_mm = label_h_mm
        self.spacing_px = spacing_px
        self.selected = [0] if labels else []
        self._setup_ui()

    def _setup_ui(self):
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(self.spacing_px)
        self.grid_layout.setContentsMargins(10,10,10,10)
        self.label_widgets = []
        self._rebuild_grid()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setWidget(self.grid_widget)
        self.scroll_area.setMinimumHeight(250)
        self.scroll_area.setSizePolicy(self.sizePolicy())
        vbox = QVBoxLayout(self)
        vbox.addWidget(self.scroll_area)
        self.setLayout(vbox)

    def compute_label_px(self):
        # Target label height in preview, e.g. 80 px, aspect for width
        target_h = 80
        aspect = self.label_w_mm / self.label_h_mm if self.label_h_mm else 1.0
        return int(target_h * aspect), int(target_h)

    def _rebuild_grid(self):
        # Remove old
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)
        self.label_widgets = []
        idx = 0
        label_w_px, label_h_px = self.compute_label_px()
        for i in range(self.rows):
            for j in range(self.cols):
                get_label = lambda idx=idx: self.labels[idx]
                lbl = SheetLabel(
                    idx, get_label, selected=(idx in self.selected),
                    label_w_px=label_w_px, label_h_px=label_h_px
                )
                lbl.clicked.connect(lambda label, ev, idx=idx: self.label_clicked.emit(idx, ev))
                lbl.rightClicked.connect(lambda label, ev, idx=idx: self.label_right_clicked.emit(idx, ev))
                self.grid_layout.addWidget(lbl, i, j)
                self.label_widgets.append(lbl)
                idx += 1
        total_w = self.cols * label_w_px + max(0, self.cols-1)*self.spacing_px + 20
        total_h = self.rows * label_h_px + max(0, self.rows-1)*self.spacing_px + 20
        self.grid_widget.setFixedSize(total_w, total_h)

    def update_labels(self, labels):
        self.labels = labels
        for idx, lbl in enumerate(self.label_widgets):
            lbl.update()

    def set_selected(self, idxs):
        self.selected = idxs
        for i, lbl in enumerate(self.label_widgets):
            lbl.set_selected(i in idxs)

    def update_calibration(self, rows, cols, label_w_mm, label_h_mm):
        self.rows = rows
        self.cols = cols
        self.label_w_mm = label_w_mm
        self.label_h_mm = label_h_mm
        self._rebuild_grid()

