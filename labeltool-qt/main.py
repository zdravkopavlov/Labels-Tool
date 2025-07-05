import sys
from PyQt5.QtWidgets import QApplication
from sheet_widget import SheetWidget

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = SheetWidget()
    window.resize(800, 1200)
    window.show()
    sys.exit(app.exec_())
