# ui.py

import os
import sys
import json
import tkinter as tk
from tkinter import ttk, messagebox

# Ensure local folder is on the import path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from settings import save_settings, load_settings
from preview import draw_preview
from tools.fonts import list_system_fonts

# CollapsiblePane widget for hiding/showing advanced controls
class CollapsiblePane(ttk.Frame):
    """A pane you can collapse or expand by clicking its header."""
    def __init__(self, parent, text="", *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self._expanded = tk.BooleanVar(value=False)
        self._button = ttk.Checkbutton(
            self, text=text, width=0,
            variable=self._expanded,
            command=self._toggle,
            style="Toolbutton"
        )
        self._button.pack(fill="x")
        self.container = ttk.Frame(self)
        # starts collapsed by default

    def _toggle(self):
        if self._expanded.get():
            self.container.pack(fill="both", expand=True, padx=5, pady=5)
        else:
            self.container.forget()


def _load_units() -> list[str]:
    base = getattr(sys, "_MEIPASS", os.path.dirname(__file__))
    path = os.path.join(base, "units.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return ["", "/ бр.", "/ м.", "/ кв. м.", "/ кг.", "/ Литър"]

UNIT_CHOICES = _load_units()

# Load available fonts
FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")
try:
    ttfs = [p for p in os.listdir(FONTS_DIR) if p.lower().endswith(".ttf")]
    FONT_CHOICES = sorted({
        os.path.splitext(p)[0].replace("-", " ").replace(" BoldOblique", " Bold Italic")
        for p in ttfs
    })
except Exception:
    fonts = list_system_fonts()
    FONT_CHOICES = sorted(fonts.keys()) if isinstance(fonts, dict) else list(fonts)

if not FONT_CHOICES:
    FONT_CHOICES = ["DejaVuSans"]


class LabelPrinterApp:
    def __init__(self, root: tk.Tk, settings: dict):
        self.root = root
        self.settings = settings
        root.title("Строймаркет Цаков – Етикети")

        # Variables
        self.top_margin     = tk.DoubleVar(value=settings.get("top_margin_mm", 0.0))
        self.left_margin    = tk.DoubleVar(value=settings.get("left_margin_mm", 0.0))
        self.row_correction = tk.DoubleVar(value=settings.get("row_correction_mm", 0.0))
        self.col_gap        = tk.DoubleVar(value=settings.get("col_gap_mm", 0.0))
        self.start_offset_display = tk.IntVar(value=settings.get("start_offset_display", 1))
        self.start_offset = tk.IntVar(value=self.start_offset_display.get() - 1)

        # Font vars
        self.name_font_family  = tk.StringVar(value=settings.get("name_font_family", FONT_CHOICES[0]))
        self.name_font_size    = tk.IntVar(value=settings.get("name_font_size", 12))
        self.name_bold         = tk.BooleanVar(value=settings.get("name_bold", False))
        self.name_italic       = tk.BooleanVar(value=settings.get("name_italic", False))
        self.sub_font_family   = tk.StringVar(value=settings.get("sub_font_family", FONT_CHOICES[0]))
        self.sub_font_size     = tk.IntVar(value=settings.get("sub_font_size", 10))
        self.sub_bold          = tk.BooleanVar(value=settings.get("sub_bold", False))
        self.sub_italic        = tk.BooleanVar(value=settings.get("sub_italic", False))
        self.price_font_family = tk.StringVar(value=settings.get("price_font_family", FONT_CHOICES[0]))
        self.price_font_size   = tk.IntVar(value=settings.get("price_font_size", 10))
        self.price_bold        = tk.BooleanVar(value=settings.get("price_bold", False))
        self.price_italic      = tk.BooleanVar(value=settings.get("price_italic", False))

        # Element checkboxes
        self.chk_logo    = tk.BooleanVar(value=settings.get("show_logo", True))
        self.chk_bgn     = tk.BooleanVar(value=settings.get("show_bgn", True))
        self.chk_eur     = tk.BooleanVar(value=settings.get("show_eur", True))
        self.show_guides = tk.BooleanVar(value=settings.get("show_guides", False))

        self.items: list[dict] = []

        # Trace vars
        trace_list = [
            self.top_margin, self.left_margin, self.row_correction, self.col_gap,
            self.start_offset_display,
            self.name_font_family, self.name_font_size, self.name_bold, self.name_italic,
            self.sub_font_family, self.sub_font_size, self.sub_bold, self.sub_italic,
            self.price_font_family, self.price_font_size, self.price_bold, self.price_italic,
            self.chk_logo, self.chk_bgn, self.chk_eur, self.show_guides
        ]
        for v in trace_list:
            v.trace_add("write", self._on_change)

        # Build UI
        self._build_ui()
        self.load_session_items()
        draw_preview(self)

    def _confirm_clear(self):
        if messagebox.askyesno(
            "Потвърждение",
            "Сигурни ли сте, че искате да изчистите всички артикули?"
        ):
            self.clear_session()

    def _on_change(self, *args):
        # Sync start offset
        self.start_offset.set(max(0, self.start_offset_display.get() - 1))
        # Save settings
        self.settings.update({
            "top_margin_mm": self.top_margin.get(),
            "left_margin_mm": self.left_margin.get(),
            "row_correction_mm": self.row_correction.get(),
            "col_gap_mm": self.col_gap.get(),
            "start_offset_display": self.start_offset_display.get(),
            "name_font_family": self.name_font_family.get(),
            "name_font_size": self.name_font_size.get(),
            "name_bold": self.name_bold.get(),
            "name_italic": self.name_italic.get(),
            "sub_font_family": self.sub_font_family.get(),
            "sub_font_size": self.sub_font_size.get(),
            "sub_bold": self.sub_bold.get(),
            "sub_italic": self.sub_italic.get(),
            "price_font_family": self.price_font_family.get(),
            "price_font_size": self.price_font_size.get(),
            "price_bold": self.price_bold.get(),
            "price_italic": self.price_italic.get(),
            "show_logo": self.chk_logo.get(),
            "show_bgn": self.chk_bgn.get(),
            "show_eur": self.chk_eur.get(),
            "show_guides": self.show_guides.get(),
        })
        self.save_session_items()
        save_settings(self.settings)
        # Preview redraw or clear
        if hasattr(self, 'preview_canvas'):
            if not self.items:
                self.preview_canvas.delete("all")
            else:
                draw_preview(self)

    def save_session_items(self):
        data = []
        for it in self.items:
            data.append({
                "name_main": it["name"].get(),
                "name_sub": it["sub"].get(),
                "price_bgn": it["bgn"].get(),
                "unit": it["unit"].get(),
                "copies": it["copies"].get()
            })
        self.settings["session_items"] = data

    def load_session_items(self):
        for row in self.settings.get("session_items", []):
            self._add_item_with_data(row)

    def _add_item_with_data(self, row):
        self._add_item()
        item = self.items[-1]
        item["name"].insert(0, row.get("name_main", ""))
        item["sub"].insert(0, row.get("name_sub", ""))
        item["bgn"].insert(0, row.get("price_bgn", ""))
        item["unit"].set(row.get("unit", ""))
        item["copies"].set(row.get("copies", 1))

    def clear_session(self):
        for it in self.items:
            it["frame"].destroy()
        self.items.clear()
        self._on_change()

    def _build_ui(self):
        # Configure root grid
        self.root.geometry("1450x900")
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=2)
        self.root.rowconfigure(0, weight=1)

        left = ttk.Frame(self.root, padding=10)
        left.grid(row=0, column=0, sticky="nsew")

        # Items list
        items_box = ttk.LabelFrame(left, text="Списък артикули")
        items_box.pack(fill="both", expand=True)
        canvas = tk.Canvas(items_box, height=300)
        scrollbar = ttk.Scrollbar(items_box, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.items_frame = ttk.Frame(canvas)
        canvas.create_window((0,0), window=self.items_frame, anchor="nw")
        self.items_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.bind(
            "<Enter>",
            lambda e: canvas.bind_all(
                "<MouseWheel>",
                lambda ev: canvas.yview_scroll(int(-1*(ev.delta/120)), "units")
            )
        )
        canvas.bind(
            "<Leave>",
            lambda e: canvas.unbind_all("<MouseWheel>")
        )

        # Add/Clear buttons
        btn_frame = ttk.Frame(left)
        btn_frame.pack(fill="x", pady=5)

        ttk.Button(
            btn_frame, text="Изчисти всички", command=self._confirm_clear
        ).grid(row=0, column=0, sticky="e", padx=5)
        ttk.Button(btn_frame, text="+ Добави етикет +", command=self._add_item).grid(
            row=0, column=1, sticky="w", padx=5
        )

        # Start offset
        off_frame = ttk.Frame(left)
        off_frame.pack(fill="x", pady=(0,6))
        ttk.Label(off_frame, text="Стартова позиция #: ").pack(side="left")
        spin_offset = ttk.Spinbox(
            off_frame, from_=1, to=999, width=4,
            textvariable=self.start_offset_display,
            command=self._on_change
        )
        spin_offset.pack(side="left")
        for ev in ("<Return>", "<FocusOut>", "<MouseWheel>"):
            spin_offset.bind(ev, self._on_change)

        # Collapsible Fonts
        cp_fonts = CollapsiblePane(left, text="Шрифтове")
        cp_fonts.pack(fill="x", pady=5)
        fonts_frame = ttk.Frame(cp_fonts.container)
        fonts_frame.pack(fill="x")
        self._font_row(fonts_frame, 0,
                       "Име", self.name_font_family, self.name_font_size,
                       self.name_bold, self.name_italic)
        self._font_row(fonts_frame, 1,
                       "Вид", self.sub_font_family, self.sub_font_size,
                       self.sub_bold, self.sub_italic)
        self._font_row(fonts_frame, 2,
                       "Цена", self.price_font_family, self.price_font_size,
                       self.price_bold, self.price_italic)

        # Collapsible Elements
        cp_elems = CollapsiblePane(left, text="Елементи")
        cp_elems.pack(fill="x", pady=5)
        elems = ttk.Frame(cp_elems.container)
        elems.pack(fill="x")
        ttk.Checkbutton(elems, text="Лого", variable=self.chk_logo).grid(
            row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Checkbutton(elems, text="Покажи лв.", variable=self.chk_bgn).grid(
            row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Checkbutton(elems, text="Покажи €", variable=self.chk_eur).grid(
            row=2, column=0, sticky="w", padx=5, pady=2)
        ttk.Checkbutton(elems, text="Водачи (preview grid)", variable=self.show_guides).grid(
            row=3, column=0, sticky="w", padx=5, pady=2)

        # Collapsible Calibration
        cp_cal = CollapsiblePane(left, text="Калибрация")
        cp_cal.pack(fill="x", pady=5)
        cal_frame = ttk.LabelFrame(cp_cal.container, text="Отместване (mm)")
        cal_frame.pack(fill="x")
        self._spin(cal_frame, 0, "Горе",     self.top_margin,     (-50,50), 0.1)
        self._spin(cal_frame, 1, "Ляво",       self.left_margin,    (-50,50), 0.1)
        self._spin(cal_frame, 2, "Редове",     self.row_correction, (-50,50), 0.1)
        self._spin(cal_frame, 3, "Колони",     self.col_gap,        (-50,50), 0.1)
        ttk.Button(
            cp_cal.container,
            text="Принтирай мрежа",
            command=lambda: __import__('printer').print_alignment_grid(self)
        ).pack(pady=5)

        # Preview panel
        right = ttk.Frame(self.root, padding=10)
        right.grid(row=0, column=1, sticky="nsew")
        ttk.Label(right, text="Преглед", font=("Arial",12,"bold")).pack(anchor="nw")
        self.preview_canvas = tk.Canvas(right, bg="white")
        self.preview_canvas.pack(fill="both", expand=True)
        self.preview_canvas.bind("<Configure>", lambda e: draw_preview(self))

        # Bottom buttons
        bottom = ttk.Frame(self.root)
        bottom.grid(row=1, column=0, columnspan=2, pady=10)
        ttk.Button(bottom, text="Печат", command=lambda: __import__('printer').print_labels(self)).pack(side="left", padx=12)
        ttk.Button(bottom, text="Запази PDF", command=lambda: __import__('printer').export_pdf_dialog(self)).pack(side="left", padx=12)

    def _font_row(self, master, row, label, fam, size, bold, ital):
        ttk.Label(master, text=label).grid(row=row, column=0, sticky="w")
        ttk.Combobox(master, values=FONT_CHOICES, textvariable=fam, width=20, state="readonly").grid(row=row, column=1, padx=2)
        ttk.Spinbox(master, from_=6, to=72, textvariable=size, width=4).grid(row=row, column=2, padx=2)
        ttk.Checkbutton(master, text="B", variable=bold).grid(row=row, column=3, padx=2)
        ttk.Checkbutton(master, text="I", variable=ital).grid(row=row, column=4, padx=2)

    def _spin(self, master, row, label, var, rng, inc):
        ttk.Label(master, text=label).grid(row=row, column=0, sticky="w")
        sp = ttk.Spinbox(master, from_=rng[0], to=rng[1], increment=inc, textvariable=var, width=6, command=self._on_change)
        sp.grid(row=row, column=1, padx=5, pady=2)
        for ev in ("<Return>", "<FocusOut>"):
            sp.bind(ev, self._on_change)

    def _add_item(self):
        from helpers import BGN_TO_EUR
        frame = ttk.Frame(self.items_frame, padding=4, relief="solid")
        frame.pack(fill="x", pady=2)

        ent_name = ttk.Entry(frame, width=30)
        ent_sub  = ttk.Entry(frame, width=30)
        ent_bgn  = ttk.Entry(frame, width=10)
        lbl_eur  = ttk.Label(frame, text="0.00")
        cmb_unit = ttk.Combobox(frame, values=UNIT_CHOICES, width=10, state="readonly")
        cmb_unit.set("")
        spin_copies = ttk.Spinbox(frame, from_=1, to=999, width=5)
        spin_copies.set("1")

        # Layout
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
        btn_up.grid(row=3, column=2, padx=2)
        btn_down.grid(row=3, column=3, padx=2)
        btn_remove.grid(row=3, column=4, padx=4)

        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(3, weight=1)

        def update_eur(*a):
            try:
                val = float(ent_bgn.get().replace(",", ".") or "0")
                eur = round(val * BGN_TO_EUR, 2)
                lbl_eur.config(text=f"{eur:.2f}")
            except:
                lbl_eur.config(text="0.00")
            self._on_change()

        ent_bgn.bind("<KeyRelease>", update_eur)
        ent_bgn.bind("<FocusOut>", update_eur)
        spin_copies.config(command=self._on_change)
        cmb_unit.bind("<<ComboboxSelected>>", lambda e: self._on_change())

        self.items.append({
            "frame": frame,
            "name": ent_name,
            "sub": ent_sub,
            "bgn": ent_bgn,
            "eur": lbl_eur,
            "unit": cmb_unit,
            "copies": spin_copies,
        })
        self._on_change()

    def _move_item(self, frame, delta):
        idx = next((i for i,it in enumerate(self.items) if it["frame"]==frame), None)
        if idx is None: return
        new = idx + delta
        if 0 <= new < len(self.items):
            self.items[idx], self.items[new] = self.items[new], self.items[idx]
            for it in self.items:
                it["frame"].pack_forget()
                it["frame"].pack(fill="x", pady=2)
            self._on_change()

    def _remove_item(self, frame):
        self.items = [it for it in self.items if it["frame"]!=frame]
        frame.destroy()
        self._on_change()
