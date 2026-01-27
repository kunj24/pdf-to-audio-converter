# PDF to Audio Converter - PowerShell Script
# Usage: .\pdf_to_audio.ps1 -PDF input.pdf -Output output.wav [-Rate 180] [-Voice 0]

param(
    [Parameter(Position=0)]
    [string]$PDF,
    
    [Parameter(Position=1)]
    [string]$Output,
    
    [int]$Rate = 180,
    
    [string]$Voice = "default",
    
    [switch]$ListVoices
)

$VenvPython = "E:\demo2\.venv\Scripts\python.exe"
$ScriptPath = "E:\demo2\src\pdf_to_audio.py"

# Check if we should list voices
if ($ListVoices) {
    Write-Host "Available voices:" -ForegroundColor Green
    & $VenvPython $ScriptPath --list-voices
    exit
}

# Show help if no parameters
if (-not $PDF -or -not $Output) {
    Write-Host @"
PDF to Audio Converter

Usage:
  .\pdf_to_audio.ps1 -PDF input.pdf -Output output.wav [-Rate 180] [-Voice 0]

Parameters:
  -PDF     : Input PDF file path
  -Output  : Output audio file (.wav or .mp3)
  -Rate    : Speech rate in words per minute (default: 180)
  -Voice   : Voice index (0, 1, 2...) or 'default'
  -ListVoices : List available voices and exit

Examples:
  .\pdf_to_audio.ps1 -PDF document.pdf -Output audio.wav
  .\pdf_to_audio.ps1 -PDF document.pdf -Output audio.mp3 -Rate 200 -Voice 1
  .\pdf_to_audio.ps1 -ListVoices

"@ -ForegroundColor Yellow
    exit
}

# Check if PDF exists
if (-not (Test-Path $PDF)) {
    Write-Host "ERROR: PDF file not found: $PDF" -ForegroundColor Red
    exit 1
}

Write-Host "Converting: $PDF to $Output" -ForegroundColor Green
Write-Host "Rate: $Rate WPM, Voice: $Voice" -ForegroundColor Cyan
Write-Host ""

# Run the conversion
$result = & $VenvPython $ScriptPath --pdf $PDF --out $Output --rate $Rate --voice $Voice

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "SUCCESS: Audio file created at $Output" -ForegroundColor Green
    
    # Show file size
    if (Test-Path $Output) {
        $size = (Get-Item $Output).Length
        $sizeKB = [math]::Round($size / 1KB, 1)
        Write-Host "File size: $sizeKB KB" -ForegroundColor Cyan
    }
} else {
    Write-Host ""
    Write-Host "ERROR: Conversion failed" -ForegroundColor Red
    exit 1
}