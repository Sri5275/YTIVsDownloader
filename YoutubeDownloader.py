import sys
import os
import shutil
import yt_dlp
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QComboBox, QProgressBar, QFileDialog, QMessageBox
from PyQt5.QtGui import QIcon

class VideoDownloaderThread(QThread):
    finished_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)

    def __init__(self, url, quality, ffmpeg_location, download_path, parent=None):
        super().__init__(parent)
        self.url = url
        self.quality = quality
        self.ffmpeg_location = ffmpeg_location
        self.download_path = download_path

    def run(self):
        format_option = self.get_format_option(self.url, self.quality)
        
        ydl_opts = {
            'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
            'progress_hooks': [self.progress_hook],
            'format': format_option,
            'ffmpeg_location': self.ffmpeg_location,
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4'
            }]
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            self.finished_signal.emit("The video has been downloaded and converted successfully.")
        except Exception as e:
            self.finished_signal.emit(f"An error occurred: {str(e)}")

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes', 0)
            if total:
                percentage = (downloaded / total) * 100
                self.progress_signal.emit(int(percentage))

    def get_format_option(self, url, quality):
        if "instagram.com" in url:
            return "best"  # Always download best available for Instagram
        elif "youtube.com" in url or "youtu.be" in url:
            if quality == "Best Available":
                return 'bestvideo+bestaudio/best'
            else:
                return f'bestvideo[height<={quality[:-1]}]+bestaudio[ext=m4a]/best[height<={quality[:-1]}]'
        else:
            return "best"  # Default to best for unknown sources


class VideoDownloaderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Downloader")
        self.setGeometry(100, 100, 400, 300)

        logo_path = "F:\\Coding\\Python\\Youtube Downloader\\YoutubeDownloaderLogo.png"

        try:
            app_icon = QIcon(logo_path)
            self.setWindowIcon(app_icon)
        except Exception as e:
            print(f"Error loading icon: {e}")

        layout = QVBoxLayout()

        self.url_label = QLabel("Enter Video URL:")
        self.url_input = QLineEdit()

        self.quality_label = QLabel("Select Quality (YouTube only):")
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["360p", "480p", "720p", "1080p", "Best Available"])

        self.folder_label = QLabel("Select Download Folder:")
        self.folder_path_display = QLineEdit()
        self.folder_path_display.setReadOnly(True)
        self.folder_button = QPushButton("Select Folder")
        self.folder_button.clicked.connect(self.select_folder)

        self.download_button = QPushButton("Download Video")
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setRange(0, 100)

        layout.addWidget(self.url_label)
        layout.addWidget(self.url_input)
        layout.addWidget(self.quality_label)
        layout.addWidget(self.quality_combo)
        layout.addWidget(self.folder_label)
        layout.addWidget(self.folder_path_display)
        layout.addWidget(self.folder_button)
        layout.addWidget(self.download_button)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)
        self.download_path = os.getcwd()  # Default to current working directory
        self.folder_path_display.setText(self.download_path)

        self.download_button.clicked.connect(self.start_download)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder")
        if folder:
            self.download_path = folder
            self.folder_path_display.setText(folder)

    def start_download(self):
        url = self.url_input.text()
        quality = self.quality_combo.currentText()

        if not url:
            self.show_error_message("Error", "Please enter a valid video URL.")
            return

        ffmpeg_location = self.get_ffmpeg_location()
        if ffmpeg_location is None:
            return

        self.download_thread = VideoDownloaderThread(url, quality, ffmpeg_location, self.download_path)
        self.download_thread.finished_signal.connect(self.on_download_finished)
        self.download_thread.progress_signal.connect(self.update_progress)
        self.download_thread.start()

        self.download_button.setEnabled(False)
        self.progress_bar.setValue(0)

    def on_download_finished(self, message):
        self.show_success_message("Download Complete", message)
        self.download_button.setEnabled(True)

    def update_progress(self, percentage):
        self.progress_bar.setValue(percentage)

    def show_error_message(self, title, message):
        QMessageBox.critical(self, title, message)

    def show_success_message(self, title, message):
        QMessageBox.information(self, title, message)

    def get_ffmpeg_location(self):
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path:
            return ffmpeg_path
        else:
            self.show_error_message("FFmpeg Not Found", "FFmpeg is not installed or not in your system PATH.")
            return None


if __name__ == "__main__":
    app = QApplication(sys.argv)

    logo_path = "F:\\Coding\\Python\\Youtube Downloader\\YoutubeDownloaderLogo.png"

    try:
        app_icon = QIcon(logo_path)
        app.setWindowIcon(app_icon)
    except Exception as e:
        print(f"Error setting application icon: {e}")

    window = VideoDownloaderApp()
    window.show()
    sys.exit(app.exec_())
