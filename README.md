# 🎬 Ultimate Batch TS Joiner

An automated, hardware-accelerated GUI tool to join `.ts` video segments into high-quality `.mp4` files. Designed for processing large archives of fragmented recordings.

## 🚀 Key Features
- **Smart Gap Detection:** Automatically splits recordings into separate files if a time gap (e.g., 15 mins) is detected between segments.
- **Batch Queue:** Add multiple folders and let the app process them all overnight.
- **Hardware Acceleration:** Support for **NVIDIA (NVENC)**, **AMD (AMF)**, and **Intel (QuickSync)**.
- **H.264 & H.265:** Toggle between maximum speed (H.264) or maximum compression (H.265).
- **Dry Run:** Estimates total file size and checks disk space before you start.
- **Error Logging:** Automatically creates `conversion_log.txt` to track successes and failures.

## 🛠️ Installation & Requirements

### 1. FFmpeg (Required)
This app is a graphical interface for **FFmpeg**. You must have `ffmpeg.exe` and `ffprobe.exe` available on your system.
- Download from: [ffmpeg.org](https://ffmpeg.org/download.html)
- **Tip:** Place `ffmpeg.exe` and `ffprobe.exe` in the same folder as this application.

### 2. Running from Source
If you have Python installed:
1. Clone this repository.
2. Run `python ultimate_joiner.py`.

### 3. Building the EXE
To create your own standalone executable:
```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --icon="app_icon.ico" --name "Ultimate_TS_Joiner" ultimate_joiner.py