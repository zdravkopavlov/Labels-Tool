# session_manager.py

import os
import json
from pathlib import Path
from PyQt5.QtWidgets import QFileDialog, QMessageBox

class SessionManager:
    """
    Handles saving/loading session to/from file.
    Now supports user-chosen path, session dialog, and saving currency mode.
    """
    def __init__(self, sheet_widget, session_filename="session.json"):
        self.sheet_widget = sheet_widget
        # Save sessions in <user>/AppData/Roaming/LabelTool/
        self._default_session_dir = os.path.join(str(Path.home()), "AppData", "Roaming", "LabelTool")
        os.makedirs(self._default_session_dir, exist_ok=True)
        self.session_path = os.path.join(self._default_session_dir, session_filename)
        self.last_mode = "bgn_to_eur"  # Default currency mode (string key)
    
    def save_session(self, to_file=None):
        """
        Save all label data and settings to session file.
        """
        data = {
            "labels": self.sheet_widget.labels,  # list of dicts
            "conversion_mode": self.sheet_widget.currency_manager.get_mode(),
        }
        path = to_file if to_file else self.session_path
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            if to_file:  # If user-initiated save
                QMessageBox.information(self.sheet_widget, "Успех", f"Сесията е запазена:\n{path}")
        except Exception as e:
            QMessageBox.warning(self.sheet_widget, "Грешка", f"Неуспешно записване на сесия:\n{e}")

    def load_session(self, from_file=None):
        """
        Load all label data and settings from session file (if present).
        """
        path = from_file if from_file else self.session_path
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            QMessageBox.warning(self.sheet_widget, "Грешка", f"Неуспешно зареждане на сесия:\n{e}")
            return
        # Restore labels
        label_count = len(self.sheet_widget.labels)
        data_labels = data.get("labels", [])
        for idx in range(label_count):
            if idx < len(data_labels):
                self.sheet_widget.labels[idx] = data_labels[idx]
            else:
                from label_editor import blank_label
                self.sheet_widget.labels[idx] = blank_label()
        # Restore currency conversion mode if present
        mode = data.get("conversion_mode", "bgn_to_eur")
        self.last_mode = mode
        # UI update is handled after load
        if from_file:
            QMessageBox.information(self.sheet_widget, "Успех", f"Сесията е заредена:\n{path}")

    def save_session_as(self):
        path, _ = QFileDialog.getSaveFileName(self.sheet_widget, "Запази сесия...", self._default_session_dir, "Сесии (*.json)")
        if path:
            self.save_session(to_file=path)
    
    def load_session_as(self):
        path, _ = QFileDialog.getOpenFileName(self.sheet_widget, "Зареди сесия...", self._default_session_dir, "Сесии (*.json)")
        if path:
            self.load_session(from_file=path)
            # UI: force reload after session load
            self.sheet_widget.update_edit_panel_from_selection()
            self.sheet_widget.build_label_grid()
