# selection_manager.py

from PyQt5.QtCore import Qt

class SelectionManager:
    """
    Manages multi-label selection, label-click selection, always keeps at least one selected.
    Usage: 
      - selection = SelectionManager(label_widgets)
      - selection.handle_click(idx, modifiers)
    """
    def __init__(self, label_widgets):
        self.label_widgets = label_widgets
        self.selected = [0] if label_widgets else []

    def handle_click(self, idx, modifiers):
        if modifiers & Qt.ControlModifier:
            if idx in self.selected:
                if len(self.selected) > 1:
                    self.selected.remove(idx)
                    self.label_widgets[idx].set_selected(False)
            else:
                self.selected.append(idx)
                self.label_widgets[idx].set_selected(True)
        elif modifiers & Qt.ShiftModifier and self.selected:
            start, end = min(self.selected[0], idx), max(self.selected[0], idx)
            for i in range(start, end + 1):
                if i not in self.selected:
                    self.selected.append(i)
                    self.label_widgets[i].set_selected(True)
        else:
            for i, lbl in enumerate(self.label_widgets):
                lbl.set_selected(i == idx)
            self.selected = [idx]
        # Always keep at least one selected
        if not self.selected and self.label_widgets:
            self.selected = [0]
            self.label_widgets[0].set_selected(True)

    def get_selected(self):
        return self.selected.copy()

    def set_selected(self, idxs):
        # Deselect all first
        for i, lbl in enumerate(self.label_widgets):
            lbl.set_selected(i in idxs)
        self.selected = [i for i in idxs if i < len(self.label_widgets)]
        if not self.selected and self.label_widgets:
            self.selected = [0]
            self.label_widgets[0].set_selected(True)

    def ensure_valid(self):
        if not self.selected and self.label_widgets:
            self.selected = [0]
            self.label_widgets[0].set_selected(True)
        else:
            self.selected = [i for i in self.selected if i < len(self.label_widgets)]
