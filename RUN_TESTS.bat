@echo off
title NAYA PANI - System Verification Test Suite
color 0E
cd /d "%~dp0"

echo ===============================================================================
echo              NAYA PANI - SYSTEM INTEGRATION TEST SUITE
echo ===============================================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found. Please run START_NAYA_PANI.bat first!
    pause
    exit /b 1
)

echo Running test_digital_twin_and_rag.py...
echo.
".venv\Scripts\python.exe" test_digital_twin_and_rag.py

echo.
echo ===============================================================================
echo Test execution completed.
echo ===============================================================================
pause
