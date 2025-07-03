# main.py
import tkinter as tk
from tkinter import filedialog
import csv
from settings import load_settings
from ui import LabelPrinterApp

def export_csv(app):
    path = filedialog.asksaveasfilename(defaultextension=".csv",
                                        filetypes=[("CSV Files", "*.csv")])
    if not path:
        return
    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["name_main", "name_sub", "price_bgn", "unit", "copies"])
        for it in app.items:
            writer.writerow([
                it["name"].get(),
                it["sub"].get(),
                it["bgn"].get(),
                it["unit"].get(),
                it["copies"].get()
            ])

def import_csv(app):
    path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
    if not path:
        return
    app.clear_session()
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            app._add_item_with_data(row)
    # after loading all items, refresh and save session
    app.save_session_items()
    from settings import save_settings
    save_settings(app.settings)
    from preview import draw_preview
    draw_preview(app)

if __name__ == "__main__":
    root = tk.Tk()
    app = LabelPrinterApp(root, load_settings())

    menubar = tk.Menu(root)
    file_menu = tk.Menu(menubar, tearoff=0)
    file_menu.add_command(label="Запази...", command=lambda: export_csv(app))
    file_menu.add_command(label="Отвори",   command=lambda: import_csv(app))
    menubar.add_cascade(label="Файл", menu=file_menu)
    root.config(menu=menubar)

    root.mainloop()
