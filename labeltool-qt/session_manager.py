# session_manager.py

import os
import json
from PyQt5.QtCore import QObject

class SessionManager(QObject):
    """
    Persists and restores the grid’s LabelWidget data to config/session.json
    using an absolute path next to this module.
    """

    def __init__(self, grid, session_filename: str = "session.json"):
        super().__init__(grid)
        self.grid = grid

        # Compute an absolute config folder next to this file
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_dir = os.path.join(base_dir, "config")
        os.makedirs(config_dir, exist_ok=True)

        # Final path for session file
        self.session_path = os.path.join(config_dir, session_filename)

        # Load any existing session
        self._load()

        # Save whenever ANY label changes
        self.grid.labelsChanged.connect(self._save)

    def _load(self):
        """Read session.json and populate every label in the grid."""
        if not os.path.exists(self.session_path):
            return

        try:
            with open(self.session_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print("⚠️  Failed to load session:", e)
            return

        # Apply each entry to the corresponding label widget
        for i, entry in enumerate(data):
            if i >= len(self.grid.labels):
                break
            lbl = self.grid.labels[i]
            lbl.set_name(entry.get("name", ""))
            lbl.set_type(entry.get("type", ""))
            lbl.set_price(entry.get("price_bgn", ""))
            lbl.set_price_eur(entry.get("price_eur", ""))
            lbl.set_unit_eur_text(entry.get("unit_eur", ""))
            lbl.set_logo(entry.get("logo", False))

    def _save(self):
        """Serialize all label data into session.json."""
        # Gather export data for each label
        all_data = [lbl.get_export_data() for lbl in self.grid.labels]

        try:
            with open(self.session_path, "w", encoding="utf-8") as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("⚠️  Failed to save session:", e)
