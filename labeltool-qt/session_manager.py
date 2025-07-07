# session_manager.py

import os, json

class SessionManager:
    def __init__(self, grid, session_path: str):
        """
        grid: your GridWidget instance, which must emit `labelsChanged()` whenever
              ANY LabelWidget field is edited.
        session_path: e.g. "config/session.json"
        """
        self.grid = grid
        self.path = session_path

        # load on init
        if os.path.exists(self.path):
            self.load()

        # save on any change
        self.grid.labelsChanged.connect(self.save)

    def load(self):
        try:
            data = json.load(open(self.path, "r", encoding="utf-8"))
            for idx, lbl_data in enumerate(data):
                if idx < len(self.grid.labels):
                    lbl = self.grid.labels[idx]
                    lbl.set_name(lbl_data.get("name", ""))
                    lbl.set_type(lbl_data.get("type", ""))
                    lbl.set_price(lbl_data.get("price_bgn", ""))
                    lbl.set_price_eur(lbl_data.get("price_eur", ""))
                    lbl.set_unit_eur(lbl_data.get("unit_eur", ""))
                    lbl.set_logo(lbl_data.get("logo", False))
        except Exception:
            pass

    def save(self):
        try:
            data = [lbl.get_export_data() for lbl in self.grid.labels]
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
