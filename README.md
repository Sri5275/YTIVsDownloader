# 📥 YTIVs Advanced Video Downloader

A **PyQt5-based** GUI application that allows you to download videos from **YouTube** and **Instagram** with advanced features and user-friendly interface.

## 🚀 Features  
- **Multi-Platform Support**
  - **YouTube Video Download** – Select custom quality (360p, 480p, 720p, 1080p, Best Available)
  - **Instagram Video Download** – Automatically fetches best available quality
  - **Other Platform Support** – Basic download for various video sources

- **Advanced Download Options**
  - Video quality selection
  - Subtitle download option
  - Thumbnail extraction
  - Recent URL history

- **Metadata Extraction**
  - View video details before downloading
  - See video title, uploader, duration, and view count

- **User Experience**
  - Modern, intuitive PyQt5 interface
  - Real-time download progress tracking
  - Download speed display
  - Folder selection
  - Error handling and user notifications

## 🖥️ Installation  

### 1️⃣ Clone the Repository  
```bash
git clone https://github.com/your-username/ytivs-video-downloader.git
cd ytivs-video-downloader
```

### 2️⃣ Install Dependencies  
```bash
pip install -r requirements.txt
```

### 3️⃣ Run the Application  
```bash
python main.py
```

## 🛠️ System Requirements  
- **Python 3.8+**
- **FFmpeg** (Must be installed and added to system PATH)
- **Operating Systems:** Windows, macOS, Linux

## 📦 Dependencies  
```bash
pip install yt-dlp PyQt5
```

### Optional Dependencies
- `ffmpeg` (for video conversion)

## 🎥 Application Workflow  
1. **Enter Video URL**
   - Supports YouTube, Instagram, and other platforms
   - Automatic URL validation

2. **Explore Video Metadata**
   - View video details in the Info tab
   - See title, uploader, duration, view count

3. **Customize Download**
   - Select video quality
   - Choose additional options (subtitles, thumbnails)
   - Pick download location

4. **Download**
   - Real-time progress tracking
   - Download speed display
   - Error handling for failed downloads

## 🌟 Key Highlights
- Concurrent video fragment downloading
- Multi-core video conversion
- Error-resilient download process
- Clean, modern UI design

## ⚠️ Responsible Use Disclaimer  
- This tool is for **educational purposes only**
- Respect copyright laws and platform terms of service
- Only download content you have rights to access

## 🤝 Contributing  
Contributions are welcome! 
- Fork the repository
- Create a feature branch
- Submit a pull request

## 📜 License  
MIT License

## 🔗 Additional Resources
- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp)
- [PyQt5 Guide](https://www.riverbankcomputing.com/static/Docs/PyQt5/)

---

**Happy Downloading! 🎉**
