# selection_manager.py

from PyQt5.QtCore import QObject, Qt, QEvent, pyqtSignal

class SelectionManager(QObject):
    """
    Manages Ctrl/Shift click selection for a list of widgets.
    Emits selectionChanged(list_of_indexes).
    """
    selectionChanged = pyqtSignal(list)

    def __init__(self, parent_widget, label_widgets):
        super().__init__(parent_widget)
        self.parent = parent_widget
        self.labels = label_widgets
        self.selected = []

        for idx, lbl in enumerate(self.labels):
            lbl.clicked.connect(lambda _lbl, ev, i=idx: self._on_click(i, ev))

        self.parent.scroll.viewport().installEventFilter(self)

    def _on_click(self, idx, ev):
        mods = ev.modifiers()
        if mods & Qt.ControlModifier:
            if idx in self.selected:
                self.selected.remove(idx)
            else:
                self.selected.append(idx)

        elif mods & Qt.ShiftModifier and self.selected:
            start = min(self.selected)
            for i in range(min(start, idx), max(start, idx) + 1):
                if i not in self.selected:
                    self.selected.append(i)

        else:
            self.selected = [idx]

        self._apply()
        self.selectionChanged.emit(self.selected)

    def _apply(self):
        for i, lbl in enumerate(self.labels):
            lbl.set_selected(i in self.selected)

    def eventFilter(self, obj, ev):
        if obj == self.parent.scroll.viewport() and ev.type() == QEvent.MouseButtonPress:
            pos = ev.pos()
            if not any(lbl.geometry().contains(lbl.parentWidget().mapFrom(obj, pos))
                       for lbl in self.labels):
                self.selected = []
                self._apply()
                self.selectionChanged.emit(self.selected)
                return True
        return False

    # ── NEW PUBLIC METHODS ────────────────────────────────────────────────────
    def select_all(self):
        """Select every label."""
        self.selected = list(range(len(self.labels)))
        self._apply()
        self.selectionChanged.emit(self.selected)

    def clear_selection(self):
        """Unselect everything."""
        self.selected = []
        self._apply()
        self.selectionChanged.emit(self.selected)
