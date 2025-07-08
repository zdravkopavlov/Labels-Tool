import sys
import os
from PyQt5.QtWidgets import QApplication, QTabWidget
from sheet_widget import SheetWidget
from sheet_editor_widget import SheetEditor

from PyQt5.QtGui import QIcon

APP_VERSION = "2.0.0"

class MainWindow(QTabWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Строймаркет Цаков - Етикети - v{APP_VERSION}")
        self.setWindowIcon(QIcon(os.path.abspath("icon.ico")))
        self.resize(1000, 1000)

        # Tab 1: Main label editor (SheetWidget)
        self.label_tab = SheetWidget()
        self.addTab(self.label_tab, "Редактор на етикети")

        # Tab 2: Sheet setup editor
        self.sheet_tab = SheetEditor()
        self.addTab(self.sheet_tab, "Настройки на листа")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
