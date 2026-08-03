@echo off
title JD Hub SMS - Building...
color 0A
cls

echo.
echo   =============================================================
echo.
echo   JD HUB SCHOOL MANAGEMENT SYSTEM
echo   Version 1.0.0
echo   Contact: 0754687597
echo.
echo   =============================================================
echo.

REM Find Python path
set PYTHON=
for %%i in (python.exe) do set PYTHON=%%~$PATH:i
if "%PYTHON%"=="" (
    for /f "tokens=2*" %%a in ('reg query "HKEY_CURRENT_USER\Software\Python\PythonCore\3.11\InstallPath" /ve 2^>nul') do set PYTHON=%%a\python.exe
    if exist "%PYTHON%" goto :found
    for /f "tokens=2*" %%a in ('reg query "HKEY_LOCAL_MACHINE\Software\Python\PythonCore\3.11\InstallPath" /ve 2^>nul') do set PYTHON=%%a\python.exe
    if exist "%PYTHON%" goto :found
    for /f "tokens=2*" %%a in ('reg query "HKEY_CURRENT_USER\Software\Python\PythonCore\3.10\InstallPath" /ve 2^>nul') do set PYTHON=%%a\python.exe
    if exist "%PYTHON%" goto :found
    for /f "tokens=2*" %%a in ('reg query "HKEY_LOCAL_MACHINE\Software\Python\PythonCore\3.10\InstallPath" /ve 2^>nul') do set PYTHON=%%a\python.exe
    if exist "%PYTHON%" goto :found
    goto :nopython
)

:found
echo   Found Python: %PYTHON%
echo.

echo   Step 1 of 4: Installing packages...
"%PYTHON%" -m pip install pyinstaller flet==0.86.0 pillow reportlab openpyxl python-dateutil qrcode cryptography schedule plyer flask werkzeug requests
if errorlevel 1 goto :piperror

echo.
echo   Step 2 of 4: Packages installed.
echo.

echo   Step 3 of 4: Building application...
echo   This takes 10-20 minutes. Please wait...
echo.
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

"%PYTHON%" -m PyInstaller --name=JDHubSchool --onefile --windowed --noconfirm --clean app_launcher.py
if errorlevel 1 goto :buildfail

echo.
echo   Step 4 of 4: Complete!
echo.

if exist "dist\JDHubSchool.exe" (
    color 0A
    echo.
    echo   =============================================================
    echo.
    echo   BUILD SUCCESSFUL!
    echo.
    echo   Your EXE is ready at:
    echo   dist\JDHubSchool.exe
    echo.
    echo   Double-click to run!
    echo.
    echo   =============================================================
    echo.
    echo   Support: JD Hub - 0754687597
    echo.
) else (
    goto :buildfail
)
goto :end

:nopython
color 0C
echo.
echo   =============================================================
echo.
echo   ERROR: Python NOT FOUND!
echo.
echo   Please install Python 3.11 from:
echo   https://www.python.org/downloads/
echo.
echo   IMPORTANT: Check "Add Python to PATH"
echo.
echo   =============================================================
echo.
goto :end

:piperror
color 0C
echo.
echo   =============================================================
echo.
echo   ERROR: Failed to install packages!
echo.
echo   Try running CMD as Administrator
echo   and run this again.
echo.
echo   =============================================================
echo.
goto :end

:buildfail
color 0C
echo.
echo   =============================================================
echo.
echo   BUILD FAILED!
echo.
echo   Contact JD Hub: 0754687597
echo   WhatsApp: +256 754687597
echo.
echo   =============================================================
echo.

:end
pause
