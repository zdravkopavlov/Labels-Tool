import os
import json
from PyQt5.QtCore import QObject, QEvent, Qt

class SelectionManager(QObject):
    """
    Manages multi-label selection, label-click selection, and clearing on empty-space clicks.
    """
    def __init__(self, parent, labels):
        super().__init__(parent)
        self.parent = parent      # SheetWidget instance
        self.labels = labels      # list of LabelWidget
        self.selected = []        # indices of selected labels
        self.last_clicked = None  # for shift-range

        # Install event filter on the scroll area's viewport
        try:
            self.parent.scroll.viewport().installEventFilter(self)
        except Exception:
            pass

        # Connect each label's click signal
        for lbl in self.labels:
            lbl.clicked.connect(self.handle_label_click)
            # Ensure hand cursor on hover (LabelWidget.update_style already sets cursor)

    def select_all(self):
        """Selects every label in the sheet."""
        self.clear_selection()
        self.selected = list(range(len(self.labels)))
        for idx in self.selected:
            self.labels[idx].set_selected(True)

    def clear_selection(self):
        """Clears any current selection."""
        for idx in self.selected:
            self.labels[idx].set_selected(False)
        self.selected = []
        self.last_clicked = None

    def handle_label_click(self, label, event):
        """
        Handles Ctrl/Shift/regular clicks on a label to manage multi-selection.
        """
        try:
            idx = self.labels.index(label)
        except ValueError:
            return
        mods = event.modifiers()
        if mods & Qt.ControlModifier:
            # toggle
            if idx in self.selected:
                self.selected.remove(idx)
                label.set_selected(False)
            else:
                self.selected.append(idx)
                label.set_selected(True)
            self.last_clicked = idx
        elif mods & Qt.ShiftModifier and self.last_clicked is not None:
            # range select
            start = min(self.last_clicked, idx)
            end = max(self.last_clicked, idx)
            for i in range(start, end+1):
                if i not in self.selected:
                    self.selected.append(i)
                    self.labels[i].set_selected(True)
        else:
            # single select
            self.clear_selection()
            self.selected = [idx]
            label.set_selected(True)
            self.last_clicked = idx

    def eventFilter(self, obj, ev):
        """
        Intercept clicks on the scroll viewport: if the click hits empty space,
        clear the current selection. Safely ignore events when the widget has
        already been deleted.
        """
        try:
            if ev.type() == QEvent.MouseButtonPress and obj is self.parent.scroll.viewport():
                pos = ev.pos()
                # if click is on any label, do nothing
                for lbl in self.labels:
                    local = lbl.parentWidget().mapFrom(self.parent.scroll.viewport(), pos)
                    if lbl.geometry().contains(local):
                        return False
                # clicked on whitespace => clear
                self.clear_selection()
                return True
        except RuntimeError:
            # underlying C++ object deleted
            return False
        return super().eventFilter(obj, ev)
