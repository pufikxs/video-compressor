import os
import subprocess

import requests
import shutil
import src.globals as g
import zipfile
from PyQt6.QtCore import QThread, pyqtSignal

# Update the FFmpeg URL to a Linux-compatible build
FFMPEG_DL = "https://github.com/Tyrrrz/FFmpegBin/releases/download/7.1/ffmpeg-linux-x64.zip"

class DownloadThread(QThread):
    update_log = pyqtSignal(str)
    update_progress = pyqtSignal(int)
    installed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def download_ffmpeg(self):
        print("Downloading FFmpeg...")
        bin_path = g.bin_dir
        file_path = os.path.join(bin_path, "ffmpeg.zip")
        response = requests.get(FFMPEG_DL, stream=True)

        if not response.ok:
            print(f"Download failed: {response.status_code}\n{response.text}")
            return

        print(f"Source: {FFMPEG_DL}")
        total_size = response.headers.get("content-length")

        with open(file_path, "wb") as f:
            if total_size is None:
                f.write(response.content)
            else:
                downloaded = 0
                total_size = int(total_size)

                for chunk in response.iter_content(chunk_size=4096):
                    downloaded += len(chunk)
                    f.write(chunk)
                    percentage = (downloaded / total_size) * 100
                    downloaded_mb = downloaded / (1024 * 1024)
                    total_mb = total_size / (1024 * 1024)
                    message = f"Downloading FFmpeg...\n{downloaded_mb:.1f} MB / {total_mb:.1f} MB"
                    self.update_log.emit(message)
                    self.update_progress.emit(int(percentage))

    def install_ffmpeg(self):
        print("Installing FFmpeg...")
        zip_path = os.path.join(g.bin_dir, "ffmpeg.zip")

        # Extract binaries
        with zipfile.ZipFile(zip_path, "r") as zip_file:
            zip_file.extractall(g.bin_dir)
        os.remove(zip_path)
        os.remove(os.path.join(g.bin_dir, "ffplay"))

        # Making them executable
        subprocess.run(['chmod', '+x', os.path.join(g.bin_dir, "ffmpeg")])
        subprocess.run(['chmod', '+x', os.path.join(g.bin_dir, "ffprobe")])

    def run(self):
        self.download_ffmpeg()
        self.install_ffmpeg()
        self.installed.emit()
