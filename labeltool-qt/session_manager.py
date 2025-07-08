# session_manager.py

import os
import json

class SessionManager:
    """
    Handles saving/loading session to config/session.json next to the .py/.exe.
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
        data = [lbl.get_export_data() for lbl in self.sheet_widget.labels]
        try:
            with open(self.session_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save session: {e}")

    def load_session(self):
        """
        Load all label data from config/session.json (if present)
        """
        if not os.path.exists(self.session_path):
            return
        try:
            with open(self.session_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Failed to load session file: {e}")
            return

        # Read user-selected mode from settings if you save it; else, pick your default
        # If not available, just set to "bgn_to_eur" (safe default)
        try:
            with open(os.path.join(os.path.dirname(self.session_path), "settings.json"), "r", encoding="utf-8") as f:
                settings = json.load(f)
            current_mode = {
                0: "bgn_to_eur",
                1: "eur_to_bgn",
                2: "both",
                3: "manual"
            }.get(settings.get("conversion_mode", 0), "bgn_to_eur")
        except Exception:
            current_mode = "bgn_to_eur"

        for idx, item in enumerate(data):
            if idx >= len(self.sheet_widget.labels):
                break
            lbl = self.sheet_widget.labels[idx]
            # Block conversions before loading values
            if hasattr(lbl, "currency_manager"):
                lbl.currency_manager.set_conversion_mode("manual")

            lbl.set_name(item.get("name", ""))
            lbl.set_type(item.get("type", ""))
            lbl.set_price(item.get("price_bgn", ""))
            lbl.set_price_eur(item.get("price_eur", ""))
            lbl.set_unit_eur_text((item.get("unit_eur") or "").strip())
            lbl.set_logo(item.get("logo", False))

            # Restore user's preferred conversion mode
            if hasattr(lbl, "currency_manager"):
                lbl.currency_manager.set_conversion_mode(current_mode)

