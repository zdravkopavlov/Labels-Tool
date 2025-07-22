import sys
import os
import requests
import tempfile
import threading

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QProgressBar, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject

# Default JSON URL (fallback, used only if not passed as argument)
DEFAULT_LATEST_JSON_URL = "https://raw.githubusercontent.com/zdravkopavlov/Labels-Tool/refs/heads/master/git_release.json"

class DownloadSignals(QObject):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

def run_installer_as_admin(installer_path):
    if sys.platform == "win32":
        try:
            import ctypes
            params = ''
            result = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", installer_path, params, None, 1
            )
            return result > 32
        except Exception as e:
            print(f"Error running as admin: {e}")
            return False
    else:
        return False

class UniversalDownloader(QWidget):
    def __init__(self, download_url=None, json_url=None):
        super().__init__()
        self.setWindowTitle("Update Installer")
        self.setFixedSize(430, 220)
        self.layout = QVBoxLayout(self)
        
        self.label = QLabel("Fetching update information...")
        self.label.setWordWrap(True)
        self.layout.addWidget(self.label)
        
        self.progress = QProgressBar(self)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.layout.addWidget(self.progress)
        
        self.button = QPushButton("Download and Install")
        self.button.setEnabled(False)
        self.button.clicked.connect(self.start_download)
        self.layout.addWidget(self.button)

        self.signals = DownloadSignals()
        self.signals.progress.connect(self.progress.setValue)
        self.signals.finished.connect(self.download_finished)
        self.signals.error.connect(self.download_error)

        self.downloading = False
        self.download_url = download_url

        # Start fetching release info only if download_url was not passed
        if not self.download_url:
            self.json_url = json_url or DEFAULT_LATEST_JSON_URL
            threading.Thread(target=self.fetch_latest_info, daemon=True).start()
        else:
            self.label.setText("Ready to download the new version.")
            self.button.setEnabled(True)

    def fetch_latest_info(self):
        try:
            r = requests.get(self.json_url, timeout=10)
            r.raise_for_status()
            info = r.json()
            url = info.get("download_url")
            ver = info.get("version", "")
            changelog = info.get("changelog", "")
            if url:
                self.download_url = url
                label_text = f"Ready to download version {ver}."
                if changelog:
                    label_text += f"\n\nWhat's new:\n{changelog}"
                self.label.setText(label_text)
                self.button.setEnabled(True)
            else:
                self.download_error("No download URL found in the update information!")
        except Exception as e:
            self.download_error(f"Failed to fetch update info: {e}")

    def start_download(self):
        if self.downloading or not self.download_url:
            return
        self.downloading = True
        self.button.setEnabled(False)
        threading.Thread(target=self.download_file, daemon=True).start()

    def download_file(self):
        url = self.download_url
        local_filename = os.path.basename(url)
        temp_dir = tempfile.gettempdir()
        dest_path = os.path.join(temp_dir, local_filename)
        try:
            with requests.get(url, stream=True, timeout=15) as r:
                r.raise_for_status()
                total_length = r.headers.get('content-length')
                dl = 0
                if total_length is None:
                    with open(dest_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    self.signals.progress.emit(100)
                else:
                    total_length = int(total_length)
                    with open(dest_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                dl += len(chunk)
                                percent = int(dl * 100 / total_length)
                                self.signals.progress.emit(percent)
            self.signals.finished.emit(dest_path)
        except Exception as e:
            self.signals.error.emit(str(e))

    def download_finished(self, dest_path):
        self.label.setText("Download finished. Launching the installer...")
        try:
            if run_installer_as_admin(dest_path):
                self.close()
            else:
                QMessageBox.warning(self, "Error", "Failed to start the installer as administrator.")
                self.button.setEnabled(True)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to start the installer:\n{e}")
            self.button.setEnabled(True)
        self.downloading = False

    def download_error(self, message):
        self.label.setText("Error!")
        QMessageBox.critical(self, "Download Error", f"{message}")
        self.button.setEnabled(False)
        self.downloading = False

if __name__ == "__main__":
    # Accept a download URL as first argument (for universal usage)
    download_url = None
    json_url = None
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg.lower().startswith("http"):
            if arg.lower().endswith(".exe"):
                download_url = arg
            elif arg.lower().endswith(".json"):
                json_url = arg
    app = QApplication(sys.argv)
    w = UniversalDownloader(download_url=download_url, json_url=json_url)
    w.show()
    sys.exit(app.exec_())
