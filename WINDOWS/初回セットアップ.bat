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

rem Check Python version
echo [1/4] Checking Python installation...
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
echo [2/4] Creating virtual environment...
if exist "../.venv" (
    echo [OK] Virtual environment already exists
) else (
    python -m venv ../.venv
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
echo [3/4] Activating virtual environment...
call ..\.venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    echo.
    pause
    exit /b 1
) else (
    echo [OK] Virtual environment activated
)

rem Install dependencies
echo [4/4] Installing dependencies...
echo This may take a moment...
python -m pip install -e "../[dev]" --quiet
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
echo 🎉 セットアップが完了しました！
echo.
echo 次のステップ:
echo   1. 変換ツールを起動
echo   2. .txtファイルをドラッグ&ドロップ
echo   3. HTMLファイルが生成されます
echo.
set /p choice="📱 変換ツールを今すぐ起動しますか？ [Y/N]: "
if /i "%choice%"=="y" (
    echo.
    echo 🚀 変換ツールを起動しています...
    if exist "変換ツール.bat" (
        call "変換ツール.bat"
    ) else (
        echo [ERROR] 変換ツール.bat が見つかりません
        echo.
        echo 手動で起動してください:
        echo   - Double-click: 変換ツール.bat
        echo.
        pause
    )
) else (
    echo.
    echo 💡 後で使用する場合:
    echo    WINDOWS/変換ツール.bat をダブルクリック
    echo.
    echo その他の使用方法:
    echo.
    echo To try examples:
    echo   - Double-click: サンプル実行.bat
    echo   - See generated samples in examples/output/
    echo.
    echo For updates:
    echo   - Download latest version from GitHub releases
    echo   - Or visit: https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter
    echo.
    echo For help:
    echo   - Read: docs/user/LAUNCH_GUIDE.md
    echo   - Read: docs/user/FIRST_RUN.md
    echo.
    echo Press any key to exit...
    pause > nul
)