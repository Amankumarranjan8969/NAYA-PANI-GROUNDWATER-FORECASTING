@echo off
setlocal enabledelayedexpansion

:: Restore System32 in case it was omitted from the user's PATH
set "PATH=%SystemRoot%\System32;%SystemRoot%;%SystemRoot%\System32\Wbem;%PATH%"

title NAYA PANI - Groundwater Intelligence and 3D Digital Twin Platform
color 0B

echo ===============================================================================
echo                NAYA PANI - GROUNDWATER DIGITAL TWIN PLATFORM
echo          AI Forecasting, USGS MODFLOW 6 Physics, and Photorealistic 3D Twin
echo ===============================================================================
echo.

cd /d "%~dp0"

:: 1. Locate Python
set "PYTHON_EXE="

where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PYTHON_EXE=python"
    goto :PYTHON_FOUND
)

where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PYTHON_EXE=py"
    goto :PYTHON_FOUND
)

for %%P in (
    "%LocalAppData%\Programs\Python\Python310\python.exe"
    "%LocalAppData%\Programs\Python\Python311\python.exe"
    "%LocalAppData%\Programs\Python\Python312\python.exe"
    "C:\Python310\python.exe"
    "C:\Python311\python.exe"
    "C:\Python312\python.exe"
    "C:\Program Files\Python310\python.exe"
    "C:\Program Files\Python311\python.exe"
    "C:\Program Files\Python312\python.exe"
) do (
    if exist "%%~P" (
        set "PYTHON_EXE=%%~P"
        goto :PYTHON_FOUND
    )
)

:PYTHON_NOT_FOUND
color 0C
echo [ERROR] Python was not found on this computer.
echo.
echo Naya Pani requires Python 3.10, 3.11, or 3.12 to run.
echo.
echo Would you like to install official Python 3.10 automatically via Windows winget?
set /p INSTALL_CHOICE="Install Python now? (Y/N): "
if /i "!INSTALL_CHOICE!"=="Y" (
    echo [INFO] Downloading and installing Python 3.10...
    winget install Python.Python.3.10 --silent --accept-package-agreements --accept-source-agreements
    if %ERRORLEVEL% equ 0 (
        echo [SUCCESS] Python installed. Please close and reopen this batch file.
        pause
        exit /b 0
    )
)
echo.
echo You can also download Python manually from: https://www.python.org/downloads/
echo IMPORTANT: During setup, make sure to check "Add Python to PATH".
echo.
start https://www.python.org/downloads/
pause
exit /b 1

:PYTHON_FOUND
echo [OK] Using Python: %PYTHON_EXE%
"%PYTHON_EXE%" --version
echo.

:: 2. Check Virtual Environment
if not exist ".venv\Scripts\python.exe" (
    echo ===============================================================================
    echo [FIRST-TIME SETUP] Creating virtual environment .venv ...
    echo ===============================================================================
    "%PYTHON_EXE%" -m venv .venv
    if not exist ".venv\Scripts\python.exe" (
        color 0C
        echo [ERROR] Could not create virtual environment. Please check permissions.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created successfully.
    echo.
    echo [INFO] Installing required platform libraries...
    echo This is a one-time setup and takes about 1-3 minutes.
    echo.
    ".venv\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel
    echo.
    echo [Step 1 of 3] Installing Core Platform libraries...
    ".venv\Scripts\python.exe" -m pip install streamlit pandas numpy scipy scikit-learn statsmodels plotly openpyxl python-docx argon2-cffi fastapi uvicorn requests
    echo.
    echo [Step 2 of 3] Installing Advanced Modeling packages...
    ".venv\Scripts\python.exe" -m pip install xgboost lightgbm catboost mrmr-selection flopy
    echo.
    echo [Step 3 of 3] Installing Deep Learning package...
    ".venv\Scripts\python.exe" -m pip install torch --extra-index-url https://download.pytorch.org/whl/cpu
    echo.
    echo [SUCCESS] Platform installation completed.
    echo ===============================================================================
    echo.
)

:: 3. Launch Platform and Auto-Open Browser
echo ===============================================================================
echo                STARTING NAYA PANI GROUNDWATER PLATFORM
echo ===============================================================================
echo  * Main Streamlit Dashboard : http://localhost:8501
echo  * Standalone 3D Twin View   : http://localhost:8501/app/static/twin_fullscreen.html
echo  * FastAPI Microservices     : http://localhost:8080/docs
echo  * Sample Datasets Available : ./sample_data/
echo ===============================================================================
echo.
echo Launching browser automatically in 4 seconds...
echo (Keep this terminal window open while using Naya Pani)
echo.

if exist "api_service.py" (
    start "Naya Pani Microservice API" /min ".venv\Scripts\python.exe" -m uvicorn api_service:app --port 8080 --host 127.0.0.1
)

start "" "%SystemRoot%\System32\cmd.exe" /c "timeout /t 4 /nobreak >nul & start http://localhost:8501"

".venv\Scripts\python.exe" -m streamlit run app.py --server.port 8501 --server.headless false

echo.
echo Application stopped.
pause
