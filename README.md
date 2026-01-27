# PDF to Audio Converter

A complete Windows tool that converts PDF documents to spoken audio using offline text-to-speech voices. Now includes both **command-line tools** and a **beautiful web interface**!

## 🌐 **NEW: Web Interface**

### Quick Start - Web Version
```powershell
# Start the web server
.\start_web_server.ps1

# Or use the batch file
start_web_server.bat

# Then open http://localhost:5000 in your browser
```

**Web Features:**
- 🎨 **Beautiful UI** - Modern, responsive design
- 📁 **Drag & Drop** - Easy file upload
- 🎛️ **Advanced Settings** - Voice selection, speed control, page ranges
- 📊 **Real-time Progress** - Live conversion status
- 🎵 **Format Options** - WAV or MP3 output
- 📱 **Mobile Friendly** - Works on phones and tablets

## 🚀 Command Line Quick Start

### 1. Setup (One-time)
```powershell
# Clone/download this project
cd E:\demo2

# Activate the virtual environment (already configured)
.\.venv\Scripts\Activate.ps1

# Packages are already installed: PyPDF2, pyttsx3, pydub, reportlab, Flask
```

### 2. Convert PDF to Audio

**Option A: Using Python directly**
```powershell
# Basic conversion
python src\pdf_to_audio.py --pdf document.pdf --out audio.wav

# With custom settings
python src\pdf_to_audio.py --pdf document.pdf --out audio.wav --rate 200 --voice 1

# Export as MP3 (requires FFmpeg)
python src\pdf_to_audio.py --pdf document.pdf --out audio.mp3 --rate 180 --voice 0
```

**Option B: Using PowerShell script**
```powershell
# Basic usage
.\pdf_to_audio.ps1 -PDF document.pdf -Output audio.wav

# Custom settings
.\pdf_to_audio.ps1 -PDF document.pdf -Output audio.mp3 -Rate 200 -Voice 1
```

**Option C: Using Batch file**
```batch
REM Basic usage
pdf_to_audio.bat document.pdf audio.wav

REM Custom settings
pdf_to_audio.bat document.pdf audio.wav 200 1
```

### 3. List Available Voices
```powershell
# Using Python
python src\pdf_to_audio.py --list-voices

# Using PowerShell
.\pdf_to_audio.ps1 -ListVoices

# Using Batch
pdf_to_audio.bat --list-voices
```

## 📋 Available Voices on Your System
- **[0]** Microsoft David Desktop - English (United States)
- **[1]** Microsoft Hazel Desktop - English (Great Britain) 
- **[2]** Microsoft Zira Desktop - English (United States)

## ⚙️ Parameters

| Parameter | Description | Default | Examples |
|-----------|-------------|---------|----------|
| `--pdf` | Input PDF file path | Required | `document.pdf` |
| `--out` | Output audio file (.wav/.mp3) | Required | `audio.wav`, `audio.mp3` |
| `--rate` | Speech rate (words per minute) | 180 | 150, 200, 250 |
| `--voice` | Voice index or 'default' | default | 0, 1, 2, default |
| `--start-page` | Start from page (1-based) | 1 | 5 |
| `--end-page` | End at page (1-based) | Last | 10 |

## 🎯 Examples with Sample PDF

We've included a `sample.pdf` for testing:

```powershell
# Convert sample PDF to WAV
python src\pdf_to_audio.py --pdf sample.pdf --out test_output.wav --voice 0

# Convert to MP3 with British voice
python src\pdf_to_audio.py --pdf sample.pdf --out test_output.mp3 --voice 1 --rate 200

# Convert specific pages only
python src\pdf_to_audio.py --pdf sample.pdf --out partial.wav --start-page 1 --end-page 1
```

## 📁 Project Structure

```
E:\demo2\
├── 🌐 WEB INTERFACE
│   ├── web_app.py              # Flask web application
│   ├── templates\
│   │   └── index.html          # Beautiful web UI
│   ├── start_web_server.ps1    # PowerShell web server starter
│   └── start_web_server.bat    # Batch web server starter
├── 🖥️ COMMAND LINE TOOLS
│   ├── src\
│   │   └── pdf_to_audio.py     # Main conversion script
│   ├── pdf_to_audio.ps1        # PowerShell wrapper script
│   └── pdf_to_audio.bat        # Batch wrapper script
├── 📄 SAMPLES & DOCS
│   ├── sample.pdf              # Sample PDF for testing
│   ├── create_sample_pdf.py    # Script to generate sample PDF
│   ├── requirements.txt        # Python dependencies
│   └── README.md              # This file
└── 🔧 GENERATED FILES
    ├── uploads\               # Temporary PDF uploads (web)
    ├── output\               # Generated audio files (web)
    ├── *.wav                 # Audio files from CLI
    └── .venv\               # Python virtual environment
```

## 🔧 Features

- ✅ **Offline Processing**: Uses Windows built-in TTS voices
- ✅ **Multiple Formats**: Export to WAV or MP3
- ✅ **Text Cleanup**: Removes hyphenation and layout artifacts
- ✅ **Page Selection**: Convert specific page ranges
- ✅ **Voice Options**: Choose from available Windows voices
- ✅ **Rate Control**: Adjust speech speed (WPM)
- ✅ **Easy Scripts**: PowerShell and Batch wrappers included

## 📋 Requirements

- **Windows OS** (for SAPI5 voices)
- **Python 3.7+** with virtual environment
- **Dependencies**: PyPDF2, pyttsx3, pydub
- **Optional**: FFmpeg (for MP3 export)

## 🎵 MP3 Export Setup

For MP3 export, install FFmpeg:

1. Download FFmpeg from https://ffmpeg.org/download.html
2. Extract to a folder (e.g., `C:\ffmpeg`)
3. Add `C:\ffmpeg\bin` to your system PATH
4. Restart your terminal

Or use chocolatey:
```powershell
choco install ffmpeg
```

## 🚨 Troubleshooting

**"No module named 'pyttsx3'"**
- Ensure virtual environment is activated: `.\.venv\Scripts\Activate.ps1`
- Reinstall packages: `pip install -r requirements.txt`

**MP3 export fails**
- Install FFmpeg and ensure it's in PATH
- Use WAV format as alternative: `--out output.wav`

**No text extracted**
- PDF might be image-based (scanned document)
- Try OCR tools first to make text searchable

## 🎯 Use Cases

- **Accessibility**: Make documents readable for visually impaired users
- **Multitasking**: Listen to documents while doing other tasks
- **Learning**: Audio learning for better retention
- **Commuting**: Convert articles/papers for mobile listening
- **Language Learning**: Hear pronunciation of text content

---

**Ready to convert your PDFs to audio!** 🎧
