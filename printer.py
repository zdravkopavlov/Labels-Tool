# printer.py

from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtGui import QPainter, QColor

def print_calibration(page_w_mm, page_h_mm, parent=None):
    printer = QPrinter(QPrinter.HighResolution)
    printer.setFullPage(True)
    dlg = QPrintDialog(printer, parent)
    if dlg.exec_() == QPrintDialog.Accepted:
        painter = QPainter(printer)
        page_rect = printer.pageRect()
        painter.fillRect(page_rect, QColor("#dddddd"))
        painter.end()

def print_sheet(preview_widget, parent=None):
    printer = QPrinter(QPrinter.HighResolution)
    printer.setFullPage(True)
    dlg = QPrintDialog(printer, parent)
    if dlg.exec_() == QPrintDialog.Accepted:
        painter = QPainter(printer)
        page_rect = printer.pageRect()
        old_size = preview_widget.size()
        preview_widget.resize(page_rect.width(), page_rect.height())
        preview_widget.render(painter)
        preview_widget.resize(old_size)
        painter.end()

def print_custom(preview_widget, parent=None, before_paint=None, after_paint=None):
    """
    Advanced: Print preview_widget, running hooks before/after paint.
    - before_paint(preview_widget, painter) is called before .render()
    - after_paint(preview_widget, painter) is called after .render()
    """
    from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
    from PyQt5.QtGui import QPainter
    printer = QPrinter(QPrinter.HighResolution)
    printer.setFullPage(True)
    dlg = QPrintDialog(printer, parent)
    if dlg.exec_() == QPrintDialog.Accepted:
        painter = QPainter(printer)
        if before_paint:
            before_paint(preview_widget, painter)
        page_rect = printer.pageRect()
        old_size = preview_widget.size()
        preview_widget.resize(page_rect.width(), page_rect.height())
        preview_widget.render(painter)
        preview_widget.resize(old_size)
        if after_paint:
            after_paint(preview_widget, painter)
        painter.end()
