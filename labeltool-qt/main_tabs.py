import sys
from PyQt5.QtWidgets import QApplication, QTabWidget, QWidget, QLabel, QVBoxLayout

from sheet_editor_widget import SheetEditor

# --- Replace this with your actual main UI widget ---
class MainLabelWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>Your Main Label Tool Goes Here</h2>"))
        # You can insert your real label grid/editor here

class MainWindow(QTabWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Labels Tool")
        self.resize(1200, 900)

        # Tab 1: Main label editor
        self.label_tab = MainLabelWidget()
        self.addTab(self.label_tab, "Labels Editor")

        # Tab 2: Sheet setup editor
        self.sheet_tab = SheetEditor()
        self.addTab(self.sheet_tab, "Sheet Setup")

        # (Optional: add more tabs as needed)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
