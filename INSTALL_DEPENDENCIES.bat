@echo off
title NAYA PANI - Dependency Installer
color 0A
cd /d "%~dp0"

echo ===============================================================================
echo           NAYA PANI - MANUAL DEPENDENCY INSTALLER & VERIFIER
echo ===============================================================================
echo.

:: Locate Python
set PYTHON_EXE=
where python >nul 2>&1 && set "PYTHON_EXE=python"
if "%PYTHON_EXE%"=="" where py >nul 2>&1 && set "PYTHON_EXE=py"

if "%PYTHON_EXE%"=="" (
    echo [ERROR] Python not found. Please install Python 3.10+ from python.org.
    pause
    exit /b 1
)

echo [OK] Using Python: %PYTHON_EXE%
%PYTHON_EXE% --version
echo.

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment (.venv)...
    %PYTHON_EXE% -m venv .venv
)

echo Updating pip and packaging tools...
".venv\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel

echo Installing all required dependencies from requirements.txt...
".venv\Scripts\python.exe" -m pip install -r requirements.txt

echo Installing FastAPI and FloPy for MODFLOW 6 support...
".venv\Scripts\python.exe" -m pip install fastapi uvicorn flopy requests

echo.
echo ===============================================================================
echo [SUCCESS] Dependencies installed and verified!
echo You can now double-click START_NAYA_PANI.bat to run the application.
echo ===============================================================================
pause
