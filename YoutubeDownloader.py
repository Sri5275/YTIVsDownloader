import sys
import os
import re
import shutil
import multiprocessing
from typing import Optional, Dict, Any, List, Tuple

import yt_dlp
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, 
    QVBoxLayout, QHBoxLayout, QComboBox, QProgressBar, 
    QFileDialog, QMessageBox, QCheckBox, QTabWidget, QTextEdit
)
from PyQt5.QtGui import QIcon, QFont

class VideoMetadataExtractor:
    """Utility class to extract video metadata."""
    @staticmethod
    def extract_video_info(url: str) -> Dict[str, Any]:
        """
        Extract metadata for a given video URL.
        
        Args:
            url (str): Video URL to extract information from
        
        Returns:
            Dict containing video metadata
        """
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skipdownload': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                
                return {
                    'title': info_dict.get('title', 'Unknown Title'),
                    'uploader': info_dict.get('uploader', 'Unknown Uploader'),
                    'duration': info_dict.get('duration', 0),
                    'view_count': info_dict.get('view_count', 0),
                    'formats': info_dict.get('formats', []),
                    'thumbnail': info_dict.get('thumbnail', '')
                }
        except Exception as e:
            return {'error': str(e)}

class VideoDownloaderThread(QThread):
    """Thread for handling video downloads with advanced features."""
    finished_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    speed_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(
        self, 
        url: str, 
        quality: str, 
        ffmpeg_location: Optional[str], 
        download_path: str,
        download_subtitles: bool = False,
        download_thumbnail: bool = False
    ):
        super().__init__()
        self.url = url
        self.quality = quality
        self.ffmpeg_location = ffmpeg_location
        self.download_path = download_path
        self.download_subtitles = download_subtitles
        self.download_thumbnail = download_thumbnail
        self.num_cores = max(1, multiprocessing.cpu_count() - 1)

    def _get_format_option(self) -> str:
        """Optimize format selection for faster downloads."""
        platforms = {
            "youtube.com": lambda: 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]' 
                if self.quality == "Best Available" 
                else f'bestvideo[height<={self.quality[:-1]}][ext=mp4]+bestaudio[ext=m4a]/best[height<={self.quality[:-1]}][ext=mp4]',
            "instagram.com": lambda: "best[ext=mp4]",
            "vimeo.com": lambda: "best[ext=mp4]",
            "facebook.com": lambda: "best[ext=mp4]"
        }

        for platform, format_func in platforms.items():
            if platform in self.url:
                return format_func()
        
        return "best[ext=mp4]"

    def run(self):
        """Main download and conversion process."""
        try:
            format_option = self._get_format_option()
            
            postprocessors = []

            # Modify the video conversion postprocessor
            postprocessors.append({
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4'
            })

            # Add subtitle download if requested
            if self.download_subtitles:
                postprocessors.append({
                    'key': 'FFmpegSubtitlesConvertor',
                    'format': 'srt'
                })

            ydl_opts: Dict[str, Any] = {
                'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
                'progress_hooks': [self._progress_hook],
                'format': format_option,
                'ffmpeg_location': self.ffmpeg_location,
                'concurrent_views': self.num_cores,
                'fragment_retries': 3,
                'retries': 3,
                'no_color': True,
                'no_warnings': True,
                'ignoreerrors': False,
                'postprocessors': postprocessors,
                'writesubtitles': self.download_subtitles,
                'socket_timeout': 30,
                'force_generic_extractor': True
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            
            self.finished_signal.emit("Video downloaded and converted successfully.")
        
        except Exception as e:
            self.error_signal.emit(f"Download error: {str(e)}")

    def _progress_hook(self, d: Dict[str, Any]):
        """Enhanced progress tracking with speed information."""
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes_estimate', d.get('total_bytes', 0))
            
            if total > 0:
                percentage = min(100, int((downloaded / total) * 100))
                self.progress_signal.emit(percentage)

            speed = d.get('speed', 0)
            if speed:
                speed_str = f"{speed/1024/1024:.2f} MB/s"
                self.speed_signal.emit(speed_str)

class VideoDownloaderApp(QWidget):
    """Main application window for video downloading."""
    QUALITY_OPTIONS = ["360p", "480p", "720p", "1080p", "Best Available"]
    RECENT_URLS_FILE = os.path.expanduser("~/.youtube_downloader_history.txt")
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._load_recent_urls()

    def _setup_ui(self):
        """Setup the main user interface."""
        self.setWindowTitle("YTIV's Advanced Video Downloader")
        self.setGeometry(100, 100, 600, 500)
        self._set_app_icon()

        main_layout = QVBoxLayout()

        # Tabs for different functionalities
        self.tab_widget = QTabWidget()
        
        # Download Tab
        download_tab = QWidget()
        download_layout = QVBoxLayout()

        # URL Input Section
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter video URL")
        url_input_btn = QPushButton("Fetch Info")
        url_input_btn.clicked.connect(self._fetch_video_info)
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(url_input_btn)
        download_layout.addLayout(url_layout)

        # Recent URLs Dropdown
        self.recent_urls_combo = QComboBox()
        self.recent_urls_combo.currentTextChanged.connect(self._set_url_from_recent)
        download_layout.addWidget(self.recent_urls_combo)

        # Quality Selection
        quality_layout = QHBoxLayout()
        quality_label = QLabel("Quality:")
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(self.QUALITY_OPTIONS)
        quality_layout.addWidget(quality_label)
        quality_layout.addWidget(self.quality_combo)
        download_layout.addLayout(quality_layout)

        # Additional Download Options
        options_layout = QHBoxLayout()
        self.subtitles_check = QCheckBox("Download Subtitles")
        self.thumbnail_check = QCheckBox("Download Thumbnail")
        options_layout.addWidget(self.subtitles_check)
        options_layout.addWidget(self.thumbnail_check)
        download_layout.addLayout(options_layout)

        # Download Folder Selection
        folder_layout = QHBoxLayout()
        self.folder_path_display = QLineEdit()
        self.folder_path_display.setReadOnly(True)
        folder_button = QPushButton("Select Folder")
        folder_button.clicked.connect(self._select_folder)
        folder_layout.addWidget(self.folder_path_display)
        folder_layout.addWidget(folder_button)
        download_layout.addLayout(folder_layout)

        # Download Button and Progress
        self.download_button = QPushButton("Download Video")
        self.download_button.clicked.connect(self._start_download)
        download_layout.addWidget(self.download_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        download_layout.addWidget(self.progress_bar)

        self.speed_label = QLabel("Download Speed: N/A")
        download_layout.addWidget(self.speed_label)

        download_tab.setLayout(download_layout)

        # Video Info Tab
        info_tab = QWidget()
        info_layout = QVBoxLayout()
        self.video_info_text = QTextEdit()
        self.video_info_text.setReadOnly(True)
        info_layout.addWidget(self.video_info_text)
        info_tab.setLayout(info_layout)

        # Add tabs
        self.tab_widget.addTab(download_tab, "Download")
        self.tab_widget.addTab(info_tab, "Video Info")

        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

        # Set default download path
        self._set_default_download_path()

    def _set_default_download_path(self):
        """Set default download path to user's Downloads folder."""
        self.download_path = os.path.expanduser("~/Downloads")
        self.folder_path_display.setText(self.download_path)

    def _fetch_video_info(self):
        """Fetch and display video metadata."""
        url = self.url_input.text().strip()
        if not url:
            self._show_message("Error", "Please enter a valid URL", QMessageBox.Critical)
            return

        # Extract video metadata
        info = VideoMetadataExtractor.extract_video_info(url)
        
        if 'error' in info:
            self._show_message("Error", info['error'], QMessageBox.Critical)
            return

        # Switch to Video Info tab
        self.tab_widget.setCurrentIndex(1)

        # Display video info
        info_text = f"""
        Title: {info['title']}
        Uploader: {info['uploader']}
        Duration: {info['duration']} seconds
        Views: {info['view_count']}
        """
        self.video_info_text.setText(info_text)

        # Add to recent URLs
        self._add_to_recent_urls(url)

    def _add_to_recent_urls(self, url: str):
        """Add URL to recent URLs list."""
        recent_urls = self._load_recent_urls()
        if url not in recent_urls:
            recent_urls.insert(0, url)
            recent_urls = recent_urls[:10]  # Keep last 10 URLs
            
            with open(self.RECENT_URLS_FILE, 'w') as f:
                f.write('\n'.join(recent_urls))
            
            self.recent_urls_combo.clear()
            self.recent_urls_combo.addItems(recent_urls)

    def _load_recent_urls(self) -> List[str]:
        """Load recent URLs from file."""
        try:
            with open(self.RECENT_URLS_FILE, 'r') as f:
                urls = [line.strip() for line in f.readlines() if line.strip()]
                self.recent_urls_combo.clear()
                self.recent_urls_combo.addItems(urls)
                return urls
        except FileNotFoundError:
            return []

    def _set_url_from_recent(self, url: str):
        """Set URL from recent URLs dropdown."""
        if url:
            self.url_input.setText(url)

    def _set_app_icon(self):
        """Set application icon."""
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "YoutubeDownloaderLogo.png")
            app_icon = QIcon(logo_path)
            self.setWindowIcon(app_icon)
        except Exception as e:
            print(f"Icon loading error: {e}")

    def _select_folder(self):
        """Open folder selection dialog."""
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder")
        if folder:
            self.download_path = folder
            self.folder_path_display.setText(folder)

    def _start_download(self):
        """Initiate video download process."""
        url = self.url_input.text().strip()
        
        if not url:
            self._show_message("Error", "Please enter a valid video URL", QMessageBox.Critical)
            return

        # Find FFmpeg
        ffmpeg_location = shutil.which("ffmpeg")
        if not ffmpeg_location:
            self._show_message(
                "FFmpeg Not Found", 
                "FFmpeg is required. Please install it.", 
                QMessageBox.Critical
            )
            return

        # Prepare download thread
        self.download_thread = VideoDownloaderThread(
            url=url,
            quality=self.quality_combo.currentText(),
            ffmpeg_location=ffmpeg_location,
            download_path=self.download_path,
            download_subtitles=self.subtitles_check.isChecked(),
            download_thumbnail=self.thumbnail_check.isChecked()
        )

        # Connect signals
        self.download_thread.finished_signal.connect(self._on_download_finished)
        self.download_thread.progress_signal.connect(self.progress_bar.setValue)
        self.download_thread.speed_signal.connect(self._update_speed)
        self.download_thread.error_signal.connect(self._on_download_error)

        # Start download
        self.download_thread.start()
        self.download_button.setEnabled(False)
        self.progress_bar.setValue(0)

    def _update_speed(self, speed: str):
        """Update download speed display."""
        self.speed_label.setText(f"Download Speed: {speed}")

    def _on_download_finished(self, message: str):
        """Handle successful download."""
        self._show_message("Download Complete", message, QMessageBox.Information)
        self.download_button.setEnabled(True)
        self.progress_bar.setValue(100)

    def _on_download_error(self, error: str):
        """Handle download errors."""
        self._show_message("Download Error", error, QMessageBox.Critical)
        self.download_button.setEnabled(True)

    def _show_message(self, title: str, message: str, icon: QMessageBox.Icon):
        """Display message box."""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(icon)
        msg_box.exec_()

def main():
    """Main application entry point."""
    # Create the application
    app = QApplication(sys.argv)
    
    # Set application-wide style
    app.setStyle('Fusion')  # Modern, cross-platform look
    app.setWindowIcon(QIcon("icon.ico"))
    # Create and show the main window

    window = VideoDownloaderApp()

    window.show()
    
    # Run the application event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

