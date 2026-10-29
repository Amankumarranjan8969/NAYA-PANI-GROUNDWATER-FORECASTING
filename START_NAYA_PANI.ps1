# NAYA PANI - Groundwater Intelligence & 3D Digital Twin Platform
# Native PowerShell 1-Click Launcher

$Host.UI.RawUI.WindowTitle = "NAYA PANI - Groundwater Intelligence & 3D Digital Twin"
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "               NAYA PANI - GROUNDWATER DIGITAL TWIN PLATFORM" -ForegroundColor Cyan
Write-Host "         AI Forecasting, USGS MODFLOW 6 Physics & Photorealistic 3D Twin" -ForegroundColor Cyan
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $PSScriptRoot

# 1. Locate Python
$pythonExe = $null

if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonExe = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonExe = "py"
} else {
    $candidates = @(
        "$env:LocalAppData\Programs\Python\Python310\python.exe",
        "$env:LocalAppData\Programs\Python\Python311\python.exe",
        "$env:LocalAppData\Programs\Python\Python312\python.exe",
        "C:\Python310\python.exe",
        "C:\Python311\python.exe",
        "C:\Python312\python.exe",
        "C:\Program Files\Python310\python.exe",
        "C:\Program Files\Python311\python.exe",
        "C:\Program Files\Python312\python.exe"
    )
    foreach ($cand in $candidates) {
        if (Test-Path $cand) {
            $pythonExe = $cand
            break
        }
    }
}

if (-not $pythonExe) {
    Write-Host "[ERROR] Python was not found on this computer." -ForegroundColor Red
    Write-Host "Naya Pani requires Python 3.10, 3.11, or 3.12 to run."
    Write-Host ""
    $installChoice = Read-Host "Would you like to install official Python 3.10 automatically via winget? (Y/N)"
    if ($installChoice -eq "Y" -or $installChoice -eq "y") {
        Write-Host "Installing Python 3.10..." -ForegroundColor Yellow
        winget install Python.Python.3.10 --silent --accept-package-agreements --accept-source-agreements
        Write-Host "Python installed! Please run this script again." -ForegroundColor Green
        Read-Host "Press Enter to exit"
        exit 0
    }
    Start-Process "https://www.python.org/downloads/"
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[OK] Using Python: $pythonExe" -ForegroundColor Green
& $pythonExe --version
Write-Host ""

# 2. Virtual Environment Setup
$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "===============================================================================" -ForegroundColor Yellow
    Write-Host "[FIRST-TIME SETUP] Creating virtual environment (.venv)..." -ForegroundColor Yellow
    Write-Host "===============================================================================" -ForegroundColor Yellow
    & $pythonExe -m venv (Join-Path $PSScriptRoot ".venv")
    if (-not (Test-Path $venvPython)) {
        Write-Host "[ERROR] Could not create virtual environment." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "[OK] Virtual environment created successfully." -ForegroundColor Green
    Write-Host "Installing required platform libraries (takes ~1-3 minutes on first run)..." -ForegroundColor Cyan
    Write-Host ""

    & $venvPython -m pip install --upgrade pip setuptools wheel
    & $venvPython -m pip install -r (Join-Path $PSScriptRoot "requirements.txt")
    & $venvPython -m pip install fastapi uvicorn flopy requests
    Write-Host ""
    Write-Host "[SUCCESS] Platform installation completed!" -ForegroundColor Green
    Write-Host ""
}

# 3. Launch Platform
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "                STARTING NAYA PANI GROUNDWATER PLATFORM" -ForegroundColor Cyan
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "  * Main Streamlit Dashboard : http://localhost:8501"
Write-Host "  * Standalone 3D Twin View   : http://localhost:8501/app/static/twin_fullscreen.html"
Write-Host "  * FastAPI Microservices     : http://localhost:8080/docs"
Write-Host "  * Sample Datasets Available : ./sample_data/"
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Opening your browser automatically in 3 seconds..." -ForegroundColor Green
Write-Host "(Keep this terminal window open while using Naya Pani)"
Write-Host ""

# Start FastAPI in background if available
$apiScript = Join-Path $PSScriptRoot "api_service.py"
if (Test-Path $apiScript) {
    Start-Process -FilePath $venvPython -ArgumentList "-m", "uvicorn", "api_service:app", "--port", "8080", "--host", "127.0.0.1" -WindowStyle Minimized
}

# Auto-open browser
Start-Job -ScriptBlock {
    Start-Sleep -Seconds 3
    Start-Process "http://localhost:8501"
} | Out-Null

# Run Streamlit
& $venvPython -m streamlit run (Join-Path $PSScriptRoot "app.py") --server.port 8501 --server.headless false
