@echo off
echo Starting PDF to Audio Web Converter...
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Start the web server
echo Web server starting at http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

python web_app.py

pause