# clipboard_manager.py

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QShortcut
from PyQt5.QtGui import QKeySequence

class ClipboardManager(QObject):
    """
    Handles Ctrl+C / Ctrl+V copy-paste for a grid of label dicts,
    using a SelectionManager to know which labels are selected.
    Now also supports copy/paste from context menu on hovered index.
    """
    def __init__(self, parent_widget, labels, selection_manager, update_callback):
        super().__init__(parent_widget)
        self.labels = labels
        self.selection = selection_manager
        self.clipboard = None
        self.clipboard_style = None
        self.last_copied_idx = None  # For UI context (optional)
        self.update_callback = update_callback

        # Register keyboard shortcuts
        QShortcut(QKeySequence("Ctrl+C"), parent_widget, activated=self.copy)
        QShortcut(QKeySequence("Ctrl+V"), parent_widget, activated=self.paste)

    # Copy first selected item (for keyboard shortcut)
    def copy(self):
        idxs = self.selection.get_selected()
        if not idxs:
            return
        self.copy_from_index(idxs[0])

    # Copy the full label (from a specific index, e.g. hovered for context menu)
    def copy_from_index(self, idx):
        if idx is None or idx < 0 or idx >= len(self.labels):
            return
        self.clipboard = {k: self.labels[idx][k].copy() for k in self.labels[idx]}
        self.clipboard_style = None
        self.last_copied_idx = idx

    # Copy style only (for keyboard shortcut)
    def copy_style(self):
        idxs = self.selection.get_selected()
        if not idxs:
            return
        self.copy_style_from_index(idxs[0])

    # Copy only style info from a specific index (for context menu)
    def copy_style_from_index(self, idx):
        if idx is None or idx < 0 or idx >= len(self.labels):
            return
        self.clipboard_style = {k: {kk: vv for kk, vv in self.labels[idx][k].items() if kk != "text"} for k in self.labels[idx]}
        self.clipboard = None
        self.last_copied_idx = idx

    # Paste to current selection (for keyboard shortcut)
    def paste(self):
        idxs = self.selection.get_selected()
        self.paste_to_indices(idxs)

    # Paste to a given list of indices (for context menu)
    def paste_to_indices(self, indices):
        if not indices:
            return
        if self.clipboard:
            for idx in indices:
                if 0 <= idx < len(self.labels):
                    for k in self.labels[idx]:
                        self.labels[idx][k] = self.clipboard[k].copy()
        elif self.clipboard_style:
            for idx in indices:
                if 0 <= idx < len(self.labels):
                    for k in self.labels[idx]:
                        for sk, vv in self.clipboard_style[k].items():
                            self.labels[idx][k][sk] = vv
        self.update_callback()

    def has_clipboard(self):
        return bool(self.clipboard) or bool(self.clipboard_style)
