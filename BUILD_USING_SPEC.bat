@echo off
title JD Hub SMS - Building with Spec File...
color 0A
cls

echo.
echo   JD HUB SCHOOL MANAGEMENT SYSTEM
echo   Building with SPEC file...
echo.

REM Install packages
echo   Installing packages...
pip install flet pillow reportlab openpyxl python-dateutil qrcode pyautogui cryptography schedule plyer flask werkzeug requests pyinstaller -q

REM Clean
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

REM Build using spec file
echo   Building...
pyinstaller JDHubSchoolManagement.spec --noconfirm

if exist "dist\JDHubSchoolManagement\JDHubSchoolManagement.exe" (
    echo.
    echo   SUCCESS!
    echo   File: dist\JDHubSchoolManagement\JDHubSchoolManagement.exe
) else (
    echo.
    echo   FAILED! Try 1_CLICK_BUILD.bat instead.
)

pause
