@echo off
title JD Hub School Management System - Building...
color 0A

echo.
echo ============================================================
echo JD HUB ENTERPRISE SCHOOL MANAGEMENT SYSTEM
echo Build Script
echo Contact: 0754687597
echo ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed!
    echo Please install Python 3.8 or higher from https://python.org
    echo.
    pause
    exit /b 1
)

echo [1/4] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [2/4] Cleaning previous builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "__pycache__" rmdir /s /q "__pycache__"

echo.
echo [3/4] Building executable...
echo.

REM Build with PyInstaller
pyinstaller --name=JDHubSchoolManagement --onefile --windowed --noconfirm --clean app_launcher.py

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    echo.
    pause
    exit /b 1
)

echo.
echo [4/4] Build complete!
echo.

echo ============================================================
echo BUILD SUCCESSFUL!
echo ============================================================
echo.
echo Executable location: dist\JDHubSchoolManagement.exe
echo.
echo Need help? Contact JD Hub:
echo   Phone: 0754687597
echo   WhatsApp: +256 754687597
echo   Email: jdhubtech@gmail.com
echo.
echo ============================================================
echo.

pause
