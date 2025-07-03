"""Robust tools/fonts.py – compatible with Python 3.7 – 3.12, matplotlib optional."""

import os, sys, glob, tkinter as tk
from typing import Optional, List
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

# -------------------------------------------------
# Locate a font file (TTF/OTF) for a family name
# -------------------------------------------------
def _find_font_path(family: str) -> Optional[str]:
    """Return a TTF/OTF path for *family* or None if not found."""
    # 1) Try matplotlib.font_manager if present
    try:
        import matplotlib.font_manager as fm
        return fm.findfont(family, fallback_to_default=False)
    except (ModuleNotFoundError, ValueError):
        pass

    # 2) Manual search
    family_key = family.lower().replace(" ", "")
    candidates: List[str] = []

    def _add_folder(path: str) -> None:
        if os.path.isdir(path):
            candidates.extend(glob.glob(os.path.join(path, "**", "*.tt[fo]"), recursive=True))

    if sys.platform.startswith("win"):
        _add_folder(os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts"))
    elif sys.platform == "darwin":
        for p in ("/System/Library/Fonts", "/Library/Fonts", os.path.expanduser("~/Library/Fonts")):
            _add_folder(p)
    else:  # Linux / BSD
        for p in ("/usr/share/fonts", "/usr/local/share/fonts", os.path.expanduser("~/.fonts")):
            _add_folder(p)

    for path in candidates:
        name_match = os.path.basename(path).lower().replace(" ", "")
        if family_key in name_match:
            return path
    return None

# -------------------------------------------------
# Public helpers
# -------------------------------------------------
def list_system_fonts() -> List[str]:
    """Return Tk‑reported font families (sorted)."""
    root = tk.Tk()
    root.withdraw()
    try:
        families = sorted(set(root.tk.call("font", "families")))
    finally:
        root.destroy()
    return families

def register_font_for_pdf(family: str) -> str:
    """Register *family* with ReportLab if possible, else return fallback name."""
    path = _find_font_path(family)
    if path and os.path.splitext(path)[1].lower() in (".ttf", ".otf"):
        try:
            if family not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(family, path))
            return family
        except Exception:
            pass  # fall back below

    fallback = "DejaVuSans"
    if fallback not in pdfmetrics.getRegisteredFontNames():
        fb_path = _find_font_path(fallback)
        if fb_path:
            try:
                pdfmetrics.registerFont(TTFont(fallback, fb_path))
            except Exception:
                pass
    return fallback
