from PyQt5.QtCore import QObject, QEvent, pyqtSignal
import re

class CurrencyManager(QObject):
    price_converted = pyqtSignal(str, str)  # which ("bgn" or "eur"), value (as string)

    BGN_TO_EUR = "bgn_to_eur"
    EUR_TO_BGN = "eur_to_bgn"
    BOTH = "both"
    MANUAL = "manual"

    def __init__(self, bgn_field, eur_field, parent=None):
        super().__init__(parent)
        self.bgn_field = bgn_field
        self.eur_field = eur_field
        self.mode = self.BGN_TO_EUR
        self.exchange_rate = 1.95583  # BGN to EUR

        self._last_clean = {"bgn": "", "eur": ""}

        # Set up event filter and handlers
        for field, which in ((self.bgn_field, "bgn"), (self.eur_field, "eur")):
            field.installEventFilter(self)
            field.textEdited.connect(lambda val, w=which: self._on_text_edited(w, val))
            field.editingFinished.connect(lambda w=which: self._on_editing_finished(w))
            field.focused = False  # For focus logic

    def set_mode(self, mode):
        if mode not in (self.BGN_TO_EUR, self.EUR_TO_BGN, self.BOTH, self.MANUAL):
            mode = self.BGN_TO_EUR
        self.mode = mode

    def get_mode(self):
        return self.mode

    def _strip_sign(self, text, which):
        t = text.strip().replace(" ", "")
        if which == "bgn":
            t = re.sub(r"лв\.?$", "", t, flags=re.IGNORECASE)
        elif which == "eur":
            t = t.replace("€", "")
        return t

    def _clean_input(self, text):
        t = text.replace(",", ".")
        t = re.sub(r"[^0-9.]", "", t)
        if t.count(".") > 1:
            first = t.find(".")
            t = t[:first+1] + t[first+1:].replace(".", "")
        return t

    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusIn:
            which = "bgn" if obj is self.bgn_field else "eur"
            obj.focused = True
            raw = obj.text()
            clean = self._clean_input(self._strip_sign(raw, which))
            obj.blockSignals(True)
            obj.setText(clean)
            obj.blockSignals(False)
            return False
        elif event.type() == QEvent.FocusOut:
            which = "bgn" if obj is self.bgn_field else "eur"
            obj.focused = False
            self._on_editing_finished(which)
            return False
        return super().eventFilter(obj, event)

    def _on_text_edited(self, which, val):
        clean = self._clean_input(self._strip_sign(val, which))
        self._last_clean[which] = clean

    def _on_editing_finished(self, which):
        field = self.bgn_field if which == "bgn" else self.eur_field
        val = field.text()
        clean = self._clean_input(self._strip_sign(val, which))
        value = float(clean) if clean else 0.0
        self._last_clean[which] = clean

        formatted = self._format_bgn(value) if which == "bgn" else self._format_eur(value)
        field.blockSignals(True)
        field.setText(formatted)
        field.blockSignals(False)

        # Conversion logic with signal
        if self.mode == self.BGN_TO_EUR and which == "bgn":
            eur_val = round(value / self.exchange_rate, 2)
            self._last_clean["eur"] = f"{eur_val:.2f}".rstrip("0").rstrip(".")
            eur_display = self._format_eur(eur_val) if eur_val else ""
            self.eur_field.blockSignals(True)
            self.eur_field.setText(eur_display)
            self.eur_field.blockSignals(False)
            self.price_converted.emit("eur", self._last_clean["eur"])
        elif self.mode == self.EUR_TO_BGN and which == "eur":
            bgn_val = round(value * self.exchange_rate, 2)
            self._last_clean["bgn"] = f"{bgn_val:.2f}".rstrip("0").rstrip(".")
            bgn_display = self._format_bgn(bgn_val) if bgn_val else ""
            self.bgn_field.blockSignals(True)
            self.bgn_field.setText(bgn_display)
            self.bgn_field.blockSignals(False)
            self.price_converted.emit("bgn", self._last_clean["bgn"])
        elif self.mode == self.BOTH:
            if which == "bgn":
                eur_val = round(value / self.exchange_rate, 2)
                self._last_clean["eur"] = f"{eur_val:.2f}".rstrip("0").rstrip(".")
                eur_display = self._format_eur(eur_val) if eur_val else ""
                self.eur_field.blockSignals(True)
                self.eur_field.setText(eur_display)
                self.eur_field.blockSignals(False)
                self.price_converted.emit("eur", self._last_clean["eur"])
            else:
                bgn_val = round(value * self.exchange_rate, 2)
                self._last_clean["bgn"] = f"{bgn_val:.2f}".rstrip("0").rstrip(".")
                bgn_display = self._format_bgn(bgn_val) if bgn_val else ""
                self.bgn_field.blockSignals(True)
                self.bgn_field.setText(bgn_display)
                self.bgn_field.blockSignals(False)
                self.price_converted.emit("bgn", self._last_clean["bgn"])
        # MANUAL: do nothing

    def _format_bgn(self, value):
        s = f"{value:.2f}".rstrip("0").rstrip(".")
        return f"{s} лв." if s else ""

    def _format_eur(self, value):
        s = f"{value:.2f}".rstrip("0").rstrip(".")
        return f"€{s}" if s else ""

    def get_clean_bgn(self):
        return self._last_clean["bgn"]

    def get_clean_eur(self):
        return self._last_clean["eur"]
