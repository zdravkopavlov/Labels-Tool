# session_manager.py

import os
import json

class SessionManager:
    """
    Handles saving/loading session to config/session.json next to the .py/.exe.
    For use with the new dict-based label list in LabelSheetEditor.
    """
    def __init__(self, sheet_widget, session_filename="session.json"):
        self.sheet_widget = sheet_widget
        # Get absolute config folder next to this file
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_dir = os.path.join(base_dir, "config")
        os.makedirs(config_dir, exist_ok=True)
        self.session_path = os.path.join(config_dir, session_filename)

    def save_session(self):
        """
        Save all label data to config/session.json
        """
        data = self.sheet_widget.labels  # list of dicts
        try:
            with open(self.session_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save session: {e}")

    def load_session(self):
        """
        Load all label data from config/session.json (if present).
        If fewer labels in session, fill with blanks. If more, trim.
        """
        if not os.path.exists(self.session_path):
            return
        try:
            with open(self.session_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Failed to load session file: {e}")
            return
        label_count = len(self.sheet_widget.labels)
        # Fill in loaded data, or blank if not present
        for idx in range(label_count):
            if idx < len(data):
                self.sheet_widget.labels[idx] = data[idx]
            else:
                # Fill missing with blank label
                from label_editor import blank_label
                self.sheet_widget.labels[idx] = blank_label()
