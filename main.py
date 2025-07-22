import sys
import os

from PyQt5.QtWidgets import QApplication, QTabWidget, QWidget, QVBoxLayout
from PyQt5.QtGui import QIcon

from version import VERSION

# Import your main widget classes from the respective modules
from label_editor import LabelSheetEditor

from sheet_calibration_utility import CalibrationTab

APP_NAME = "Строймаркет Цаков – Етикетен инструмент -"
WINDOW_TITLE = f"{APP_NAME} Версия: - {VERSION}"
ICON_FILE = os.path.join(os.path.dirname(__file__), "icon.ico")

def main():
    app = QApplication(sys.argv)

    # Main window as a QWidget containing tabs
    main_window = QWidget()
    main_window.setWindowTitle(WINDOW_TITLE)
    if os.path.exists(ICON_FILE):
        main_window.setWindowIcon(QIcon(ICON_FILE))

    layout = QVBoxLayout(main_window)
    tabs = QTabWidget()
    tabs.setTabPosition(QTabWidget.North)

    # Load font list (for label editor)
    from PyQt5.QtGui import QFontDatabase
    FONTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
    FONT_DB = QFontDatabase()
    FONT_LIST = []
    if os.path.isdir(FONTS_DIR):
        for fname in os.listdir(FONTS_DIR):
            if fname.lower().endswith('.ttf'):
                family_id = FONT_DB.addApplicationFont(os.path.join(FONTS_DIR, fname))
                families = FONT_DB.applicationFontFamilies(family_id)
                if families: FONT_LIST.extend(families)
    if not FONT_LIST:
        FONT_LIST = ["Arial"]
    label_editor = LabelSheetEditor(FONT_LIST)
    calibration = CalibrationTab()

    tabs.addTab(label_editor, "Редактор на етикети")
    tabs.addTab(calibration, "Калибриране")

    layout.addWidget(tabs)
    main_window.resize(1200, 1000)
    main_window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
