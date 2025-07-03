# helpers.py
from dataclasses import dataclass
import tkinter as tk
import tkinter.font as tkfont

PAD_NORMAL       = 2
PAD_BEFORE_PRICE = 400

@dataclass
class Label:
    name_main: str = ""
    name_sub:  str = ""
    price_bgn: str = ""
    price_eur: str = ""
    unit:      str = ""
    copies:    int = 1

BGN_TO_EUR = 1 / 1.95583

def collect_labels(app) -> list[Label]:
    labels=[]
    for it in getattr(app, "items", []):
        try: copies=max(1,int(it["copies"].get() or 1))
        except: copies=1
        nm=it["name"].get().strip()
        ns=it["sub"].get().strip()
        b=it["bgn"].get().strip()
        try: eur=round(float(b.replace(",",".") or "0")*BGN_TO_EUR,2)
        except: eur=0.0
        et=f"{eur:.2f}"
        it["eur"].config(text=et)
        u=it["unit"].get().strip()
        lbl=Label(nm,ns,b,et,u,copies)
        labels.extend([lbl]*copies)
    return labels

def _line_h(canvas:tk.Canvas,font_tuple)->int:
    f=tkfont.Font(root=canvas,font=font_tuple)
    return f.metrics("linespace")
