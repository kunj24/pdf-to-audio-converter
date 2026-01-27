@echo off
REM PDF to Audio Converter - Windows Batch Script
REM Usage: pdf_to_audio.bat input.pdf output.wav [rate] [voice]

setlocal

set VENV_PYTHON=E:\demo2\.venv\Scripts\python.exe
set SCRIPT_PATH=E:\demo2\src\pdf_to_audio.py

if "%~1"=="" (
    echo Usage: %0 input.pdf output.wav [rate] [voice]
    echo.
    echo Examples:
    echo   %0 document.pdf audio.wav
    echo   %0 document.pdf audio.wav 200 1
    echo   %0 document.pdf audio.mp3 180 0
    echo.
    echo To list available voices:
    echo   %0 --list-voices
    goto :eof
)

if "%~1"=="--list-voices" (
    "%VENV_PYTHON%" "%SCRIPT_PATH%" --list-voices
    goto :eof
)

set PDF_FILE=%~1
set OUTPUT_FILE=%~2
set RATE=%~3
set VOICE=%~4

if "%OUTPUT_FILE%"=="" set OUTPUT_FILE=output.wav
if "%RATE%"=="" set RATE=180
if "%VOICE%"=="" set VOICE=default

echo Converting: %PDF_FILE% to %OUTPUT_FILE%
echo Rate: %RATE% WPM, Voice: %VOICE%
echo.

"%VENV_PYTHON%" "%SCRIPT_PATH%" --pdf "%PDF_FILE%" --out "%OUTPUT_FILE%" --rate %RATE% --voice %VOICE%

if %ERRORLEVEL% == 0 (
    echo.
    echo SUCCESS: Audio file created at %OUTPUT_FILE%
) else (
    echo.
    echo ERROR: Conversion failed
)