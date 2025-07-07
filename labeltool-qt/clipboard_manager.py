# clipboard_manager.py

import os
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QShortcut
from PyQt5.QtGui import QKeySequence
from label_widget import LabelWidget

class ClipboardManager(QObject):
    """
    Handles global Ctrl+C / Ctrl+V copy-paste for a grid of LabelWidget instances,
    using a SelectionManager to know which labels are selected.
    """

    def __init__(self, parent_widget, labels, selection_manager):
        super().__init__(parent_widget)
        self.labels = labels
        self.selection = selection_manager

        # Register keyboard shortcuts
        QShortcut(QKeySequence("Ctrl+C"), parent_widget, activated=self.copy)
        QShortcut(QKeySequence("Ctrl+V"), parent_widget, activated=self.paste)

    def copy(self):
        """
        Copy the contents of the first selected label to the internal clipboard.
        """
        idxs = self.selection.selected
        if not idxs:
            return
        first = idxs[0]
        self.labels[first]._copy()  # stores data in LabelWidget._copied_content

    def paste(self):
        """
        Paste the internal clipboard data into all selected labels.
        """
        idxs = self.selection.selected
        if not idxs:
            return
        data = getattr(LabelWidget, "_copied_content", None)
        if not data:
            return

        # data is a tuple: (name, subtype, price_bgn, price_eur, unit_eur)
        name, subtype, price_bgn, price_eur, unit_eur = data

        for idx in idxs:
            lbl = self.labels[idx]
            lbl.set_name(name)
            lbl.set_type(subtype)
            lbl.set_price(price_bgn)
            lbl.set_price_eur(price_eur)
            lbl.set_unit_eur_text(unit_eur)
