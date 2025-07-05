import sys
from PyQt5.QtWidgets import QApplication, QTabWidget
from sheet_widget import SheetWidget
from sheet_editor_widget import SheetEditor

class MainWindow(QTabWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Labels Tool")
        self.resize(1200, 900)

        # Tab 1: Main label editor (SheetWidget)
        self.label_tab = SheetWidget()
        self.addTab(self.label_tab, "Labels Editor")

        # Tab 2: Sheet setup editor
        self.sheet_tab = SheetEditor()
        self.addTab(self.sheet_tab, "Sheet Setup")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
