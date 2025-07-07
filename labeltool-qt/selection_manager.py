# selection_manager.py

from PyQt5.QtCore import QObject, Qt, pyqtSignal

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

        # Listen to each label’s click signal
        for idx, lbl in enumerate(self.labels):
            lbl.clicked.connect(lambda _lbl, ev, i=idx: self._on_click(i, ev))

        # Clear on background clicks
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
            end   = idx
            for i in range(min(start,end), max(start,end)+1):
                if i not in self.selected:
                    self.selected.append(i)

        else:
            # single‐click
            self.selected = [idx]

        self._apply()
        self.selectionChanged.emit(self.selected)

    def _apply(self):
        # update widget highlighting
        for i, lbl in enumerate(self.labels):
            lbl.set_selected(i in self.selected)

    def eventFilter(self, obj, ev):
        from PyQt5.QtCore import QEvent
        if obj == self.parent.scroll.viewport() and ev.type() == QEvent.MouseButtonPress:
            pos = ev.pos()
            # if clicked outside any label
            if not any(lbl.geometry().contains(lbl.parentWidget()
                                                .mapFrom(obj, pos))
                       for lbl in self.labels):
                self.selected = []
                self._apply()
                self.selectionChanged.emit(self.selected)
                return True
        return False
