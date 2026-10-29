@echo off
title NAYA PANI - Standalone Fullscreen 3D Digital Twin Viewer
color 03
cd /d "%~dp0"

echo ===============================================================================
echo         NAYA PANI - STANDALONE 3D HYDROLOGICAL DIGITAL TWIN VIEWER
echo ===============================================================================
echo.
echo Starting dedicated local asset server on port 8000...
echo.

set PYTHON_EXE=python
if exist ".venv\Scripts\python.exe" set "PYTHON_EXE=.venv\Scripts\python.exe"

start "" cmd /c "timeout /t 2 /nobreak >nul & start http://localhost:8000/static/twin_fullscreen.html"

%PYTHON_EXE% -m http.server 8000
pause
