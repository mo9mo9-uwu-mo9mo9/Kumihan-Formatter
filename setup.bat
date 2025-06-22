@echo off
setlocal enabledelayedexpansion
rem Kumihan-Formatter - One-time Setup Script
rem This script automatically sets up everything needed to use Kumihan-Formatter

rem Try to set UTF-8 encoding, but don't fail if it doesn't work
chcp 65001 > nul 2>&1

title Kumihan-Formatter - Initial Setup

echo.
echo ==========================================
echo  Kumihan-Formatter - Initial Setup
echo ==========================================
echo This will automatically set up everything you need
echo to start using Kumihan-Formatter immediately.
echo ==========================================
echo.

rem Check Git installation
echo [1/5] Checking Git installation...
git --version > nul 2>&1
if errorlevel 1 (
    echo [WARNING] Git not found
    echo.
    echo Git is recommended for updating Kumihan-Formatter.
    echo To install Git:
    echo   1. Visit: https://git-scm.com/downloads
    echo   2. Download and install Git for Windows
    echo   3. Restart this setup after installation
    echo.
    echo You can continue setup without Git, but updates will be manual.
    echo Continue anyway? [Y/N]
    set /p git_choice="> "
    if /i not "!git_choice!"=="y" (
        echo.
        echo Setup cancelled. Please install Git and run setup again.
        echo.
        pause
        exit /b 1
    )
    echo.
    echo [OK] Continuing without Git (manual updates only)
) else (
    for /f "tokens=3" %%i in ('git --version 2^>^&1') do set GIT_VERSION=%%i
    echo [OK] Git found: !GIT_VERSION!
)

rem Check Python version
echo [2/5] Checking Python installation...
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    echo.
    echo Please install Python 3.9 or higher:
    echo https://www.python.org/downloads/
    echo.
    echo After installing Python, run this setup again.
    echo.
    pause
    exit /b 1
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo [OK] Python found: !PYTHON_VERSION!
)

rem Create virtual environment
echo [3/5] Creating virtual environment...
if exist ".venv" (
    echo [OK] Virtual environment already exists
) else (
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        echo.
        pause
        exit /b 1
    ) else (
        echo [OK] Virtual environment created
    )
)

rem Activate virtual environment
echo [4/5] Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    echo.
    pause
    exit /b 1
) else (
    echo [OK] Virtual environment activated
)

rem Install dependencies
echo [5/5] Installing dependencies...
echo This may take a moment...
python -m pip install -e ".[dev]" --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    echo.
    echo Please check your internet connection and try again.
    echo.
    pause
    exit /b 1
) else (
    echo [OK] Dependencies installed successfully
)

echo.
echo ==========================================
echo  Setup Complete!
echo ==========================================
echo.
echo You can now use Kumihan-Formatter:
echo.
echo For basic conversion:
echo   - Double-click: kumihan_convert.bat
echo   - Drag and drop .txt files to convert
echo.
echo To try examples:
echo   - Double-click: run_examples.bat
echo   - See generated samples in examples/output/
echo.
echo For updates:
git --version > nul 2>&1
if errorlevel 1 (
    echo   - Manual download from GitHub required (Git not installed)
) else (
    echo   - Run: git pull origin main (to get latest updates)
)
echo.
echo For help:
echo   - Read: LAUNCH_GUIDE.md
echo   - Read: FIRST_RUN.md
echo.
echo Press any key to exit...
pause > nul