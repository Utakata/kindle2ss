# Kindle2PDF Automation Tool

A modern, cross-platform GUI tool to automate capturing Kindle screens (or any ebook reader) and converting them into PDF.
Features automatic page turning, duplicate detection, and OCR integration via YomiToku.

## Features

- **Intuitive GUI**: Built with PySide6 (Qt) for a modern look.
- **Visual Selection**: Drag and drop to select the capture area.
- **Auto-Capture**: Automatically screenshots and turns pages.
- **Smart Stop**: Detects when the book ends (duplicate pages) and stops.
- **PDF Creation**: Merges captured images into a PDF.
- **Cropping**: Auto-remove header/footer from pages.
- **OCR Support**: (Experimental) Integration with YomiToku for Japanese OCR.

## Requirements

- Python 3.9+
- OS: Windows, Linux, or macOS

## Installation

1. Clone the repository.
   ```bash
   git clone <repo_url>
   cd <repo_dir>
   ```

2. Install dependencies.
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: `requirements.txt` should include: PySide6, pyautogui, mss, Pillow, yomitoku)*

## Usage

1. Run the application:
   ```bash
   python main.py
   ```

2. **Select Area**: Click "Select Area" and drag your mouse over the Kindle content area.
3. **Configure**:
   - Go to "Settings" to adjust page turn speed, key (Left/Right), and crop margins (header/footer removal).
4. **Start**: Click "Start Capture". The tool will focus the window and start capturing.
5. **PDF**: Once finished, go to the "PDF & OCR" tab and click "Create PDF".

## Settings Details

- **Capture Interval**: Time to wait between page turns (give the screen time to refresh).
- **Page Turn Key**: Key to press to turn the page (default: `left`).
- **Header/Footer Crop**: Pixels to remove from top/bottom to get a clean page.
- **Stop Condition**: Stops after seeing N duplicate images in a row.

## Disclaimer

Please respect copyright laws and terms of service of content providers. This tool is for personal backup use only.
