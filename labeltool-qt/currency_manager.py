# currency_manager.py

from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtGui import QFocusEvent

class CurrencyManager(QObject):
    """
    Two-way binds a BGN QLineEdit and an EUR QLineEdit.
    Handles:
      • real-time or on-finish conversion (configurable)
      • loop prevention
      • always-prefix € and always-suffix ' лв.'
    """
    def __init__(self,
                 bgn_edit: QLineEdit,
                 eur_edit: QLineEdit,
                 rate: float = 1.95583,
                 convert_on: str = "keystroke"  # or "focusout"
    ):
        super().__init__(bgn_edit.parent())
        self.bgn = bgn_edit
        self.eur = eur_edit
        self.rate = rate
        self.updating = False
        self.mode = convert_on

        # set placeholders
        self.bgn.setPlaceholderText("0.00 лв.")
        self.eur.setPlaceholderText("€0.00")

        # hook events
        if self.mode == "keystroke":
            self.bgn.textChanged.connect(self._on_bgn)
            self.eur.textChanged.connect(self._on_eur)
        else:
            self.bgn.editingFinished.connect(self._on_bgn)
            self.eur.editingFinished.connect(self._on_eur)

        # focus handlers to strip/add signs
        self.bgn.focusInEvent  = self._make_focusin(self.bgn,  suffix=" лв.", prefix="")
        self.bgn.focusOutEvent = self._make_focusout(self.bgn, suffix=" лв.", prefix="")
        self.eur.focusInEvent  = self._make_focusin(self.eur,  suffix="",     prefix="€")
        self.eur.focusOutEvent = self._make_focusout(self.eur, suffix="",     prefix="€")

    def _on_bgn(self, *_):
        if self.updating: return
        txt = self.bgn.text().replace(" лв.","").strip().replace(",",".")
        try:
            val = float(txt)
        except:
            return
        eur = val / self.rate
        self.updating = True
        self.eur.setText(f"{eur:.2f}")
        # Add the euro symbol after setting (simulate focus-out)
        txt_eur = self.eur.text().strip()
        if txt_eur and not txt_eur.startswith("€"):
            self.eur.setText(f"€{txt_eur}")
        self.updating = False

    def _on_eur(self, *_):
        if self.updating: return
        txt = self.eur.text().replace("€","").strip().replace(",",".")
        try:
            val = float(txt)
        except:
            return
        bgn = val * self.rate
        self.updating = True
        self.bgn.setText(f"{bgn:.2f}")
        # Add the BGN symbol after setting (simulate focus-out)
        txt_bgn = self.bgn.text().strip()
        if txt_bgn and not txt_bgn.endswith(" лв."):
            self.bgn.setText(f"{txt_bgn} лв.")
        self.updating = False

    def _make_focusin(self, fld, suffix="", prefix=""):
        def handler(evt: QFocusEvent):
            txt = fld.text().strip()
            if prefix and txt.startswith(prefix):
                txt = txt[len(prefix):]
            if suffix and txt.endswith(suffix):
                txt = txt[:-len(suffix)]
            fld.setText(txt)
            return QLineEdit.focusInEvent(fld, evt)
        return handler

    def _make_focusout(self, fld, suffix="", prefix=""):
        def handler(evt: QFocusEvent):
            txt = fld.text().strip()
            # strip any stray signs
            txt = txt.replace(" лв.","").replace("€","").strip()
            if txt:
                fld.setText(f"{prefix}{txt}{suffix}")
            return QLineEdit.focusOutEvent(fld, evt)
        return handler
