# ui.py

import os
import sys
import json
import tkinter as tk
from tkinter import ttk

# make sure local modules are found
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from settings import save_settings, load_settings
from preview import draw_preview
from tools.fonts import list_system_fonts

def _load_units() -> list[str]:
    base = getattr(sys, "_MEIPASS", os.path.dirname(__file__))
    path = os.path.join(base, "units.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return ["", "/ бр.", "/ м.", "/ кв. м.", "/ кг.", "/ Литър"]

UNIT_CHOICES = _load_units()

# try to list bundled fonts, fall back to system list
FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")
try:
    ttfs = [p for p in os.listdir(FONTS_DIR) if p.lower().endswith(".ttf")]
    FONT_CHOICES = sorted({
        os.path.splitext(p)[0]
            .replace("-", " ")
            .replace(" BoldOblique", " Bold Italic")
        for p in ttfs
    }) or ["DejaVuSans"]
except Exception:
    fc = list_system_fonts()
    FONT_CHOICES = sorted(fc.keys()) if isinstance(fc, dict) else list(fc) or ["DejaVuSans"]

class LabelPrinterApp:
    def __init__(self, root: tk.Tk, settings: dict):
        self.root, self.settings = root, settings
        root.title("Строймаркет Цаков – Етикети")

        # ─ Margins & Gaps ─────────────────────────────────────────────
        self.top_margin     = tk.DoubleVar(value=settings.get("top_margin_mm"))
        self.row_correction = tk.DoubleVar(value=settings.get("row_correction_mm"))
        self.left_margin    = tk.DoubleVar(value=settings.get("left_margin_mm"))
        self.col_gap        = tk.DoubleVar(value=settings.get("col_gap_mm", 0.0))

        # ─ Start Offset ───────────────────────────────────────────────
        self.start_offset_display = tk.IntVar(value=1)
        self.start_offset         = tk.IntVar(value=0)

        # ─ Font Settings ──────────────────────────────────────────────
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

        # ─ Checkboxes ──────────────────────────────────────────────────
        self.chk_logo    = tk.BooleanVar(value=settings.get("show_logo", True))
        self.chk_bgn     = tk.BooleanVar(value=settings.get("show_bgn", True))
        self.chk_eur     = tk.BooleanVar(value=settings.get("show_eur", True))
        self.show_guides = tk.BooleanVar(value=settings.get("show_guides", True))

        # ─ Internal items list ────────────────────────────────────────
        self.items: list[dict] = []

        # ─ Trace & redraw on any change ──────────────────────────────
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

        # build UI, load any saved session items, then draw preview
        self._build_ui()
        self.load_session_items()
        draw_preview(self)

    def _on_change(self):
        """Save settings + session, then redraw preview."""
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

    # ─ Session Persistence ────────────────────────────────────────────
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

    # ─ UI Construction ───────────────────────────────────────────────
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
        canvas.create_window((0,0), window=self.items_frame, anchor="nw")
        self.items_frame.bind("<Configure>",
                              lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

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

        for txt,var in [("Лого", self.chk_logo), 
                        ("Покажи лв.", self.chk_bgn), 
                        ("Покажи €", self.chk_eur)]:
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
        btm = ttk.Frame(self.root)
        btm.grid(row=1, column=0, columnspan=2, pady=10)
        import printer
        ttk.Button(btm, text="Печат",      command=lambda: printer.print_labels(self)).pack(side="left", padx=12)
        ttk.Button(btm, text="Запази PDF",  command=lambda: printer.export_pdf_dialog(self)).pack(side="left", padx=12)
        ttk.Button(btm, text="Калибриране", command=lambda: printer.print_alignment_grid(self)).pack(side="left", padx=50)

    # ─ Helper to build font rows ────────────────────────────────────────
    def _font_row(self, master, row, label, fam, size, bold, ital):
        ttk.Label(master, text=label).grid(row=row, column=0, sticky="w")
        ttk.Combobox(master, values=FONT_CHOICES, textvariable=fam,
                     width=20, state="readonly").grid(row=row, column=1, padx=2)
        ttk.Spinbox(master, from_=6, to=72, textvariable=size,
                    width=4).grid(row=row, column=2, padx=2)
        ttk.Checkbutton(master, text="B", variable=bold).grid(row=row, column=3, padx=2)
        ttk.Checkbutton(master, text="I", variable=ital).grid(row=row, column=4, padx=2)

    # ─ Helper for spinboxes ───────────────────────────────────────────
    def _spin(self, master, row, label, var, rng, inc):
        ttk.Label(master, text=label).grid(row=row, column=0, sticky="w")
        sp = ttk.Spinbox(master, from_=rng[0], to=rng[1], increment=inc,
                         textvariable=var, width=6, command=self._on_change)
        sp.grid(row=row, column=1, padx=4)
        sp.bind("<Return>", self._on_change)
        sp.bind("<FocusOut>", self._on_change)

    # ─ Add one item row ────────────────────────────────────────────────
    def _add_item(self):
        from helpers import BGN_TO_EUR
        frame = ttk.Frame(self.items_frame, padding=4, relief="solid")
        frame.pack(fill="x", pady=2)

        ent_name = ttk.Entry(frame, width=30)
        ent_sub  = ttk.Entry(frame, width=30)
        ent_bgn  = ttk.Entry(frame, width=10)
        lbl_eur  = ttk.Label(frame, text="0.00")
        cmb_unit = ttk.Combobox(frame, values=UNIT_CHOICES,
                                width=10, state="readonly")
        cmb_unit.set("")
        spin_copies = ttk.Spinbox(frame, from_=1, to=999, width=5)

        # layout
        ttk.Label(frame, text="Име").grid(row=0, column=0, sticky="w")
        ent_name.grid(row=0, column=1, columnspan=5, sticky="we", padx=2)
        ttk.Label(frame, text="Вид").grid(row=1, column=0, sticky="w")
        ent_sub.grid(row=1, column=1, columnspan=5, sticky="we", padx=2)
        ttk.Label(frame, text="лв.").grid(row=2, column=0, sticky="w")
        ent_bgn.grid(row=2, column=1, sticky="w", padx=2)
        ttk.Label(frame, text="€").grid(row=2, column=2, sticky="e")
        lbl_eur.grid(row=2, column=3, sticky="w")
        ttk.Label(frame, text="Ед.").grid(row=2, column=4, sticky="e")
        cmb_unit.grid(row=2, column=5, sticky="w")
        ttk.Label(frame, text="Копия").grid(row=3, column=0, sticky="w")
        spin_copies.grid(row=3, column=1, sticky="w", padx=2)

        btn_up     = ttk.Button(frame, text="▲", command=lambda f=frame: self._move_item(f, -1))
        btn_down   = ttk.Button(frame, text="▼", command=lambda f=frame: self._move_item(f,  1))
        btn_remove = ttk.Button(frame, text="🗑", command=lambda f=frame: self._remove_item(f))
        btn_up.grid   (row=3, column=2, padx=2)
        btn_down.grid (row=3, column=3, padx=2)
        btn_remove.grid(row=3, column=4, padx=4)

        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(3, weight=1)

        def _update_eur(*_):
            try:
                val = float(ent_bgn.get().replace(",", ".") or "0")
                eur = round(val * BGN_TO_EUR, 2)
                lbl_eur.config(text=f"{eur:.2f}")
            except:
                lbl_eur.config(text="0.00")
            self._on_change()

        for w in (ent_name, ent_sub, ent_bgn):
            w.bind("<KeyRelease>", _update_eur)
            w.bind("<FocusOut>",   _update_eur)
        spin_copies.config(command=lambda: self._on_change())
        cmb_unit.bind("<<ComboboxSelected>>", lambda *_: self._on_change())

        self.items.append({
            "frame": frame,
            "name":  ent_name,
            "sub":   ent_sub,
            "bgn":   ent_bgn,
            "eur":   lbl_eur,
            "unit":  cmb_unit,
            "copies":spin_copies
        })
        self._on_change()

    # ─ Move an item up/down ───────────────────────────────────────────
    def _move_item(self, frame, delta):
        try:
            idx = next(i for i,it in enumerate(self.items) if it["frame"] == frame)
        except StopIteration:
            return
        new = idx + delta
        if not (0 <= new < len(self.items)):
            return
        self.items[idx], self.items[new] = self.items[new], self.items[idx]
        for it in self.items:
            it["frame"].pack_forget()
            it["frame"].pack(fill="x", pady=2)
        self._on_change()

    # ─ Remove an item ────────────────────────────────────────────────
    def _remove_item(self, frame):
        self.items = [it for it in self.items if it["frame"] != frame]
        frame.destroy()
        self._on_change()
