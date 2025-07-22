import sys
import os
import json
import requests

from left_pane import resource_path

from PyQt5.QtWidgets import (
    QApplication, QTabWidget, QWidget, QVBoxLayout, QDialog, QLabel, QTextEdit, QPushButton, QHBoxLayout, QMessageBox
)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt

from version import VERSION

from label_editor import LabelSheetEditor
from sheet_calibration_utility import CalibrationTab

APP_NAME = "Строймаркет Цаков – Редактор за етикети -"
WINDOW_TITLE = f"{APP_NAME} Версия: - {VERSION}"
ICON_FILE = os.path.join(os.path.dirname(__file__), "icon.ico")
GIT_RELEASE_URL = "https://raw.githubusercontent.com/zdravkopavlov/Labels-Tool/refs/heads/master/git_release.json"

# -- User config location (per user) --
def get_appdata_dir():
    from pathlib import Path
    appdata = os.getenv("APPDATA") or os.path.expanduser("~")
    confdir = os.path.join(appdata, "LabelTool")
    os.makedirs(confdir, exist_ok=True)
    return confdir

def load_user_config():
    path = os.path.join(get_appdata_dir(), "user_config.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_user_config(config):
    path = os.path.join(get_appdata_dir(), "user_config.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

# -- Check for updates (blocking HTTP, but can be threaded in the future) --
def fetch_latest_release_info():
    try:
        r = requests.get(GIT_RELEASE_URL, timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("Грешка при проверка за обновления:", e)
        return None

def compare_versions(current, latest):
    # Naive string-based version comparison (assumes "X.Y.Z" format)
    from packaging import version
    try:
        return version.parse(latest) > version.parse(current)
    except Exception:
        return latest != current

# -- The update dialog (Bulgarian only) --
class UpdateDialog(QDialog):
    def __init__(self, ver, changelog, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Налично е ново обновление")
        self.setFixedWidth(420)
        layout = QVBoxLayout(self)
        info = QLabel(f'<b>Налична е нова версия: <span style="color:#247fc3">{ver}</span></b>')
        info.setWordWrap(True)
        layout.addWidget(info)

        if changelog:
            lbl = QLabel("<b>Новостите в тази версия:</b>")
            layout.addWidget(lbl)
            txt = QTextEdit()
            txt.setReadOnly(True)
            txt.setFont(QFont("Arial", 11))
            txt.setText(changelog)
            txt.setMinimumHeight(90)
            layout.addWidget(txt)
        else:
            layout.addSpacing(8)

        layout.addSpacing(5)
        # Button row
        btn_row = QHBoxLayout()
        self.update_btn = QPushButton("Обнови сега")
        self.skip_btn = QPushButton("Пропусни тази версия")
        self.later_btn = QPushButton("Не сега")
        btn_row.addWidget(self.update_btn)
        btn_row.addWidget(self.skip_btn)
        btn_row.addWidget(self.later_btn)
        layout.addLayout(btn_row)

        self.update_btn.clicked.connect(self.accept)
        self.skip_btn.clicked.connect(lambda: self.done(2))
        self.later_btn.clicked.connect(lambda: self.done(3))
        self.setWindowModality(Qt.ApplicationModal)
        self.setMinimumHeight(260)
        self.setMaximumHeight(330)

# -- Main window and update check logic --
def main():
    app = QApplication(sys.argv)

    # Version check, config load
    config = load_user_config()
    skip_version = config.get("skip_version", "")
    release_info = fetch_latest_release_info()
    show_update = False
    update_url = ""
    latest_ver = ""
    changelog = ""

    if release_info:
        latest_ver = release_info.get("version", "")
        changelog = release_info.get("changelog", "")
        update_url = release_info.get("download_url", "")
        if latest_ver and compare_versions(VERSION, latest_ver) and skip_version != latest_ver:
            show_update = True

    # Main window setup
    main_window = QWidget()
    main_window.setWindowTitle(WINDOW_TITLE)
    if os.path.exists(ICON_FILE):
        main_window.setWindowIcon(QIcon(ICON_FILE))
    layout = QVBoxLayout(main_window)
    tabs = QTabWidget()
    tabs.setTabPosition(QTabWidget.North)

    # Fonts for label editor
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
    tabs.addTab(label_editor, "Редактор")
    tabs.addTab(calibration, "Калибриране")
    layout.addWidget(tabs)
    main_window.resize(1200, 1000)
    main_window.show()

    # Show update dialog after main window is visible, if needed
    if show_update and update_url:
        dlg = UpdateDialog(latest_ver, changelog, parent=main_window)
        result = dlg.exec_()
        if result == QDialog.Accepted:
            # User chose to update now
            try:
                exe_path = os.path.join(os.path.dirname(sys.argv[0]), "update_downloader.exe")
                if not os.path.isfile(exe_path):
                    QMessageBox.warning(main_window, "Грешка", "Файлът update_downloader.exe не е намерен в директорията на приложението.")
                else:
                    # Pass download_url as an argument to update_downloader
                    import subprocess
                    # On Windows, use startfile or subprocess with shell=True for .exe
                    subprocess.Popen([exe_path, update_url])
                    app.quit()
                    return
            except Exception as e:
                QMessageBox.critical(main_window, "Грешка", f"Неуспешно стартиране на обновителя:\n{e}")
        elif result == 2:  # Skip this version
            config["skip_version"] = latest_ver
            save_user_config(config)
        # If 'Не сега', do nothing (remind next time)

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
