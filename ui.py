# ui.py

import os
import sys
import json
import tkinter as tk
from tkinter import ttk

# Ensure local folder on the import path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# type: ignore so Pylance won’t warn
from settings import save_settings, load_settings     # type: ignore
from preview import draw_preview
from tools.fonts import list_system_fonts            # type: ignore

def _load_units() -> list[str]:
    base = getattr(sys, "_MEIPASS", os.path.dirname(__file__))
    path = os.path.join(base, "units.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return ["", "/ бр.", "/ м.", "/ кв. м.", "/ кг.", "/ Литър"]

UNIT_CHOICES = _load_units()

# Fonts folder may be missing; fall back safely
FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")
try:
    ttfs = [p for p in os.listdir(FONTS_DIR) if p.lower().endswith(".ttf")]
    FONT_CHOICES = sorted({
        os.path.splitext(p)[0].replace("-", " ").replace(" BoldOblique", " Bold Italic")
        for p in ttfs
    }) or ["DejaVuSans"]
except Exception:
    FONT_CHOICES = sorted(list_system_fonts().keys()) or ["DejaVuSans"]

class LabelPrinterApp:
    def __init__(self, root: tk.Tk, settings: dict):
        self.root, self.settings = root, settings
        root.title("Строймаркет Цаков – Етикети")

        # Margins & gaps
        self.top_margin     = tk.DoubleVar(value=settings.get("top_margin_mm"))
        self.row_correction = tk.DoubleVar(value=settings.get("row_correction_mm"))
        self.left_margin    = tk.DoubleVar(value=settings.get("left_margin_mm"))
        self.col_gap        = tk.DoubleVar(value=settings.get("col_gap_mm", 0.0))

        # Start offset
        self.start_offset_display = tk.IntVar(value=1)
        self.start_offset         = tk.IntVar(value=0)

        # Font settings vars
        self.name_font_family  = tk.StringVar(value=settings.get("name_font_family"))
        self.name_font_size    = tk.IntVar(   value=settings.get("name_font_size"))
        self.name_bold         = tk.BooleanVar(value=settings.get("name_bold"))
        self.name_italic       = tk.BooleanVar(value=settings.get("name_italic"))

        self.sub_font_family   = tk.StringVar(value=settings.get("sub_font_family"))
        self.sub_font_size     = tk.IntVar(   value=settings.get("sub_font_size"))
        self.sub_bold          = tk.BooleanVar(value=settings.get("sub_bold"))
        self.sub_italic        = tk.BooleanVar(value=settings.get("sub_italic"))

        self.price_font_family = tk.StringVar(value=settings.get("price_font_family"))
        self.price_font_size   = tk.IntVar(   value=settings.get("price_font_size"))
        self.price_bold        = tk.BooleanVar(value=settings.get("price_bold"))
        self.price_italic      = tk.BooleanVar(value=settings.get("price_italic"))

        # Checkboxes
        self.chk_logo    = tk.BooleanVar(value=settings.get("show_logo", True))
        self.chk_bgn     = tk.BooleanVar(value=settings.get("show_bgn", True))
        self.chk_eur     = tk.BooleanVar(value=settings.get("show_eur", True))
        self.show_guides = tk.BooleanVar(value=settings.get("show_guides", True))

        # Internal items list
        self.items: list[dict] = []

        # Trace changes → save & redraw
        for var in (
            self.top_margin, self.row_correction,
            self.left_margin, self.col_gap,
            self.name_font_family, self.name_font_size,
            self.name_bold, self.name_italic,
            self.sub_font_family, self.sub_font_size,
            self.sub_bold, self.sub_italic,
            self.price_font_family, self.price_font_size,
            self.price_bold, self.price_italic,
            self.chk_logo, self.chk_bgn, self.chk_eur, self.show_guides
        ):
            var.trace_add("write", lambda *a: self._on_change())

        self._build_ui()
        self.load_session_items()
        draw_preview(self)

    def _on_change(self):
        # Persist settings + session, then redraw
        self.settings.update({
            "top_margin_mm":     self.top_margin.get(),
            "row_correction_mm": self.row_correction.get(),
            "left_margin_mm":    self.left_margin.get(),
            "col_gap_mm":        self.col_gap.get(),

            "name_font_family":  self.name_font_family.get(),
            "name_font_size":    self.name_font_size.get(),
            "name_bold":         self.name_bold.get(),
            "name_italic":       self.name_italic.get(),

            "sub_font_family":   self.sub_font_family.get(),
            "sub_font_size":     self.sub_font_size.get(),
            "sub_bold":          self.sub_bold.get(),
            "sub_italic":        self.sub_italic.get(),

            "price_font_family": self.price_font_family.get(),
            "price_font_size":   self.price_font_size.get(),
            "price_bold":        self.price_bold.get(),
            "price_italic":      self.price_italic.get(),

            "show_logo":   self.chk_logo.get(),
            "show_bgn":    self.chk_bgn.get(),
            "show_eur":    self.chk_eur.get(),
            "show_guides": self.show_guides.get(),
        })
        self.save_session_items()
        save_settings(self.settings)
        try:
            draw_preview(self)
        except Exception:
            pass

    def save_session_items(self):
        data = []
        for it in self.items:
            data.append({
                "name_main": it["name"].get(),
                "name_sub":  it["sub"].get(),
                "price_bgn": it["bgn"].get(),
                "unit":      it["unit"].get(),
                "copies":    it["copies"].get()
            })
        self.settings["session_items"] = data

    def load_session_items(self):
        for row in self.settings.get("session_items", []):
            self._add_item_with_data(row)

    def _add_item_with_data(self, row):
        self._add_item()
        it = self.items[-1]
        it["name"].insert(0, row.get("name_main", ""))
        it["sub"].insert(0, row.get("name_sub", ""))
        it["bgn"].insert(0, row.get("price_bgn", ""))
        it["unit"].set( row.get("unit",""))
        it["copies"].set(row.get("copies",1))

    def clear_session(self):
        for it in self.items:
            it["frame"].destroy()
        self.items.clear()
        self.save_session_items()
        save_settings(self.settings)
        try:
            draw_preview(self)
        except Exception:
            pass

    def _build_ui(self):
        self.root.geometry("1450x900")
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=2)
        self.root.rowconfigure(0, weight=1)

        # LEFT panel
        left = ttk.Frame(self.root, padding=10)
        left.grid(row=0, column=0, sticky="nsew")

        # Scrollable items list
        box = ttk.LabelFrame(left, text="Списък артикули")
        box.pack(fill="both", expand=True)
        canvas = tk.Canvas(box, height=300)
        scrollbar = ttk.Scrollbar(box, orient="vertical", command=canvas.yview)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)

        self.items_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=self.items_frame, anchor="nw")
        self.items_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        ttk.Button(left, text="+ Добави", command=self._add_item).pack(pady=4, anchor="w")
        ttk.Button(left, text="Изчисти", command=self.clear_session).pack(pady=4, anchor="w")

        # Fonts panel
        fonts = ttk.LabelFrame(left, text="Шрифтове")
        fonts.pack(fill="x", pady=5)
        self._font_row(fonts, 0, "Име",   self.name_font_family, self.name_font_size, self.name_bold, self.name_italic)
        self._font_row(fonts, 1, "Подзаг",self.sub_font_family,  self.sub_font_size,   self.sub_bold,  self.sub_italic)
        self._font_row(fonts, 2, "Цена",  self.price_font_family,self.price_font_size,self.price_bold,self.price_italic)

        # Offset & calibration
        off = ttk.Frame(left); off.pack(anchor="w", pady=(0,6))
        ttk.Label(off, text="Стартова позиция #: ").pack(side="left")
        spin_off = ttk.Spinbox(
            off, from_=1, to=21, width=4,
            textvariable=self.start_offset_display,
            command=self._on_change, validate="all"
        )
        spin_off.pack(side="left")
        for ev in ("<Return>","<FocusOut>","<MouseWheel>"):
            spin_off.bind(ev, self._on_change)

        mbox = ttk.LabelFrame(left, text="Отместване Калибрация (mm)")
        mbox.pack(fill="x", pady=5)
        self._spin(mbox, 0, "  Начало", self.top_margin,     (-50,50), 0.1)
        self._spin(mbox, 1, "  Ляво",   self.left_margin,    (-50,50), 0.1)
        self._spin(mbox, 2, "  Редове", self.row_correction, (-50,50), 0.1)
        self._spin(mbox, 3, "  Колони", self.col_gap,        (-50,50), 0.1)

        for txt,var in [("Лого", self.chk_logo), ("Покажи лв.", self.chk_bgn), ("Покажи €", self.chk_eur)]:
            ttk.Checkbutton(left, text=txt, variable=var).pack(anchor="w")
        ttk.Checkbutton(left, text="Водачи (preview grid)", variable=self.show_guides).pack(anchor="w")

        # RIGHT panel (preview)
        right = ttk.Frame(self.root, padding=10)
        right.grid(row=0, column=1, sticky="nsew")
        ttk.Label(right, text="Преглед", font=("Arial",12,"bold")).pack(anchor="nw")
        self.preview_canvas = tk.Canvas(right, bg="white")
        self.preview_canvas.pack(fill="both", expand=True)
        self.preview_canvas.bind("<Configure>", lambda e: draw_preview(self))

        # Bottom buttons
        btm = ttk.Frame(self.root); btm.grid(row=1, column=0, columnspan=2, pady=10)
        import printer
        ttk.Button(btm, text="Печат",      command=lambda: printer.print_labels(self)).pack(side="left",  padx=12)
        ttk.Button(btm, text="Запази PDF",  command=lambda: printer.export_pdf_dialog(self)).pack(side="left",  padx=12)
        ttk.Button(btm, text="Калибриране", command=lambda: printer.print_alignment_grid(self)).pack(side="left", padx=50)

    # Remaining helper methods (_font_row, _spin, _add_item, etc.) unchanged...
