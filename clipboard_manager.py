# clipboard_manager.py

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QShortcut
from PyQt5.QtGui import QKeySequence

class ClipboardManager(QObject):
    """
    Handles Ctrl+C / Ctrl+V copy-paste for a grid of label dicts,
    using a SelectionManager to know which labels are selected.
    """
    def __init__(self, parent_widget, labels, selection_manager, update_callback):
        super().__init__(parent_widget)
        self.labels = labels
        self.selection = selection_manager
        self.clipboard = None
        self.clipboard_style = None
        self.update_callback = update_callback

        # Register keyboard shortcuts
        QShortcut(QKeySequence("Ctrl+C"), parent_widget, activated=self.copy)
        QShortcut(QKeySequence("Ctrl+V"), parent_widget, activated=self.paste)

    def copy(self):
        idxs = self.selection.get_selected()
        if not idxs:
            return
        first = idxs[0]
        self.clipboard = {k: self.labels[first][k].copy() for k in self.labels[first]}
        self.clipboard_style = None

    def copy_style(self):
        idxs = self.selection.get_selected()
        if not idxs:
            return
        first = idxs[0]
        self.clipboard_style = {k: {kk: vv for kk, vv in self.labels[first][k].items() if kk != "text"} for k in self.labels[first]}
        self.clipboard = None

    def paste(self):
        idxs = self.selection.get_selected()
        if not idxs:
            return
        if self.clipboard:
            for idx in idxs:
                for k in self.labels[idx]:
                    self.labels[idx][k] = self.clipboard[k].copy()
        elif self.clipboard_style:
            for idx in idxs:
                for k in self.labels[idx]:
                    for sk, vv in self.clipboard_style[k].items():
                        self.labels[idx][k][sk] = vv
        self.update_callback()
