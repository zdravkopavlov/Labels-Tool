# currency_manager.py

from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtGui import QFocusEvent, QDoubleValidator

class CurrencyManager(QObject):
    """
    Two-way binds a BGN QLineEdit and an EUR QLineEdit.
    Handles:
      • configurable conversion direction: bgn→eur, eur→bgn, both, manual
      • never doubles the currency sign
      • conversion only on editingFinished (not on every keystroke)
      • accepts only numbers and decimal signs
    """
    MODES = {
        "bgn_to_eur": 0,
        "eur_to_bgn": 1,
        "both": 2,
        "manual": 3,
    }
    MODES_R = {v: k for k, v in MODES.items()}

    def __init__(self,
                 bgn_edit: QLineEdit,
                 eur_edit: QLineEdit,
                 rate: float = 1.95583,
                 mode: str = "bgn_to_eur"  # default
    ):
        super().__init__(bgn_edit.parent())
        self.bgn = bgn_edit
        self.eur = eur_edit
        self.rate = rate
        self.set_mode(mode)
        self.updating = False

        # Placeholders
        self.bgn.setPlaceholderText("0.00 лв.")
        self.eur.setPlaceholderText("€0.00")

        # Numeric input only (accepts comma and dot)
        validator = QDoubleValidator(0.0, 999999.99, 2)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.bgn.setValidator(validator)
        self.eur.setValidator(validator)

        # Connect events
        self._connect_events()

        # Focus handlers: add/remove signs only on focus out/in
        self.bgn.focusInEvent  = self._make_focusin(self.bgn,  suffix=" лв.", prefix="")
        self.bgn.focusOutEvent = self._make_focusout(self.bgn, suffix=" лв.", prefix="")
        self.eur.focusInEvent  = self._make_focusin(self.eur,  suffix="",     prefix="€")
        self.eur.focusOutEvent = self._make_focusout(self.eur, suffix="",     prefix="€")

    def set_mode(self, mode):
        """Set conversion mode and reconnect signals."""
        if isinstance(mode, int):  # For session restoration
            mode = self.MODES_R.get(mode, "bgn_to_eur")
        self.mode = mode
        self._connect_events()

    def _connect_events(self):
        """(Re)connects editingFinished based on mode."""
        try:
            self.bgn.editingFinished.disconnect(self._on_bgn)
        except Exception:
            pass
        try:
            self.eur.editingFinished.disconnect(self._on_eur)
        except Exception:
            pass
        if self.mode == "bgn_to_eur":
            self.bgn.editingFinished.connect(self._on_bgn)
        elif self.mode == "eur_to_bgn":
            self.eur.editingFinished.connect(self._on_eur)
        elif self.mode == "both":
            self.bgn.editingFinished.connect(self._on_bgn)
            self.eur.editingFinished.connect(self._on_eur)
        # Manual: don't connect

    def _on_bgn(self):
        if self.updating:
            return
        txt = self._strip(self.bgn.text())
        if txt == "":
            self._set_eur("")
            return
        try:
            val = float(txt.replace(",", "."))
        except Exception:
            return
        eur = val / self.rate
        self.updating = True
        self._set_eur(f"{eur:.2f}")
        self.updating = False

    def _on_eur(self):
        if self.updating:
            return
        txt = self._strip(self.eur.text())
        if txt == "":
            self._set_bgn("")
            return
        try:
            val = float(txt.replace(",", "."))
        except Exception:
            return
        bgn = val * self.rate
        self.updating = True
        self._set_bgn(f"{bgn:.2f}")
        self.updating = False

    def _set_bgn(self, value):
        value = self._strip(value)
        if value == "":
            self.bgn.setText("")
        else:
            self.bgn.setText(value)

    def _set_eur(self, value):
        value = self._strip(value)
        if value == "":
            self.eur.setText("")
        else:
            self.eur.setText(value)

    @staticmethod
    def _strip(val):
        """Remove all currency signs and spaces."""
        return (val.replace(" лв.", "")
                   .replace("лв.", "")
                   .replace("€", "")
                   .replace(" ", "")
                   .strip())

    def _make_focusin(self, fld, suffix="", prefix=""):
        def handler(evt: QFocusEvent):
            txt = self._strip(fld.text())
            fld.setText(txt)
            return QLineEdit.focusInEvent(fld, evt)
        return handler

    def _make_focusout(self, fld, suffix="", prefix=""):
        def handler(evt: QFocusEvent):
            txt = self._strip(fld.text())
            if txt:
                fld.setText(f"{prefix}{txt}{suffix}")
            else:
                fld.setText("")
            return QLineEdit.focusOutEvent(fld, evt)
        return handler

    def get_mode(self):
        return self.mode
