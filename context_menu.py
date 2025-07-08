# context_menu.py

from PyQt5.QtWidgets import QMenu, QAction

# avoid circular import—define units here
PREDEFINED_UNITS = [" ", "бр.", "м", "м²", "м³", "кг.", "л."]

def make_label_context_menu(label_widget, sheet_widget):
    """
    Builds a copy/paste/units/clear menu that:
      • If the clicked label is not in the current selection, acts only on that one.
      • If it is in the selection, Copy uses the first selected,
        and Paste/Clear applies to all selected labels.
    """
    sel    = sheet_widget.selection.selected
    idx    = sheet_widget.labels.index(label_widget)
    in_sel = idx in sel

    menu = QMenu(label_widget)
    # re-apply hover styling
    menu.setStyleSheet("""
        QMenu { background: #fff; color: #111; }
        QMenu::item:selected { background: #008cff; color: #fff; }
    """)

    # ── COPY ─────────────────────────────────────────────────────────────────
    copy_act = QAction("Копиране", menu)
    def do_copy():
        target = sel[0] if in_sel and sel else idx
        sheet_widget.labels[target]._copy()
    copy_act.triggered.connect(do_copy)
    menu.addAction(copy_act)

    # ── PASTE ────────────────────────────────────────────────────────────────
    paste_act = QAction("Поставяне", menu)
    def do_paste():
        targets = sel if in_sel and sel else [idx]
        for i in targets:
            sheet_widget.labels[i]._paste()
    paste_act.triggered.connect(do_paste)
    menu.addAction(paste_act)

    menu.addSeparator()

    # ── UNITS ───────────────────────────────────────────────────────────────
    for unit in PREDEFINED_UNITS:
        disp = f"/ {unit}" if unit else '""'
        uact = QAction(disp, menu)
        def make_unit_closure(u):
            def apply_unit():
                targets = sel if in_sel and sel else [idx]
                for i in targets:
                    sheet_widget.labels[i].set_unit_eur(u)
            return apply_unit
        uact.triggered.connect(make_unit_closure(unit))
        menu.addAction(uact)

    menu.addSeparator()

    # ── CLEAR ────────────────────────────────────────────────────────────────
    clear_act = QAction("Изчисти", menu)
    def do_clear():
        targets = sel if in_sel and sel else [idx]
        for i in targets:
            sheet_widget.labels[i].clear_fields()
    clear_act.triggered.connect(do_clear)
    menu.addAction(clear_act)

    return menu
