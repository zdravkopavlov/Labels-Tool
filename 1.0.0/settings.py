# settings.py
import json, sys
from pathlib import Path

def _app_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent

SETTINGS_FILE = _app_dir() / "settings.json"

DEFAULT_SETTINGS: dict[str, object] = {
    "top_margin_mm":     8.0,
    "row_correction_mm": 1.3,
    "left_margin_mm":   -5.0,
    "col_gap_mm":        0.0,

    "name_font_family":  "DejaVuSans",
    "name_font_size":     20,
    "name_bold":          True,
    "name_italic":        False,

    "sub_font_family":   "DejaVuSans",
    "sub_font_size":      16,
    "sub_bold":           False,
    "sub_italic":         True,

    "price_font_family": "DejaVuSans",
    "price_font_size":    23,
    "price_bold":         True,
    "price_italic":       False,

    "show_logo":  True,
    "show_bgn":   True,
    "show_eur":   True,
    "show_guides":True,

    "session_items": []
}

def load_settings() -> dict[str, object]:
    if SETTINGS_FILE.exists():
        try:
            with SETTINGS_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
            merged = DEFAULT_SETTINGS.copy()
            merged.update(data)
            return merged
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()

def save_settings(settings: dict[str, object]) -> None:
    clean = {k: settings.get(k, v) for k, v in DEFAULT_SETTINGS.items()}
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with SETTINGS_FILE.open("w", encoding="utf-8") as f:
        json.dump(clean, f, indent=4, ensure_ascii=False)
