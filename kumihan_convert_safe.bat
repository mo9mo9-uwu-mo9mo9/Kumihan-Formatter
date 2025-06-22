@echo off
setlocal enabledelayedexpansion
rem Windows character encoding safe version
rem This script works with both UTF-8 and Shift-JIS environments

rem Try to set UTF-8 encoding, but don't fail if it doesn't work
chcp 65001 > nul 2>&1

title Kumihan-Formatter - Text to HTML Converter

echo.
echo ==========================================
echo  Kumihan-Formatter - Text to HTML Tool
echo ==========================================
echo Convert .txt files to beautiful HTML
echo Usage: Drag and drop .txt file to this window
echo First run will auto-setup environment
echo ==========================================
echo.

rem Check Python version
python --version > nul 2>&1
if errorlevel 1 (
    echo Error: Python not found
    echo.
    echo Please install Python 3.9 or higher:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
) else (
    rem Python version check (3.9+)
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    rem Get version numbers (e.g., 3.13.0 -> 3.13)
    for /f "tokens=1,2 delims=." %%a in ("!PYTHON_VERSION!") do (
        set MAJOR=%%a
        set MINOR=%%b
    )
    rem Version comparison (3.9+)
    if !MAJOR! lss 3 (
        echo Error: Python 3.9+ required (current: !PYTHON_VERSION!)
        echo.
        echo Please install Python 3.9 or higher:
        echo https://www.python.org/downloads/
        echo.
        pause
        exit /b 1
    ) else if !MAJOR! equ 3 (
        if !MINOR! lss 9 (
            echo Error: Python 3.9+ required (current: !PYTHON_VERSION!)
            echo.
            echo Please install Python 3.9 or higher:
            echo https://www.python.org/downloads/
            echo.
            pause
            exit /b 1
        )
    )
    echo OK: Python version !PYTHON_VERSION! (>= 3.9)
)

rem Check and activate virtual environment
set VENV_CREATED=0
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
    set PYTHON_CMD=python
) else (
    echo Virtual environment not found. Creating automatically...
    echo Running first-time setup...
    echo.
    
    rem Create virtual environment
    echo Creating virtual environment...
    python -m venv .venv
    if !errorlevel! equ 0 (
        echo OK: Virtual environment created
        set VENV_CREATED=1
    ) else (
        echo Error: Failed to create virtual environment
        echo.
        pause
        exit /b 1
    )
    
    rem Activate virtual environment
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
    set PYTHON_CMD=python
)

rem Display Python version
echo Python version:
%PYTHON_CMD% --version

rem Check and install dependencies
rem Force install if new virtual environment
if !VENV_CREATED! equ 1 (
    echo Installing dependencies to new virtual environment...
    echo Installing packages... (please wait)
    echo.
    
    %PYTHON_CMD% -m pip install -e ".[dev]" --quiet
    if !errorlevel! equ 0 (
        echo OK: Dependencies installed successfully
    ) else (
        echo Error: Failed to install dependencies
        echo.
        echo Please run manually:
        echo     .venv\Scripts\activate.bat
        echo     pip install -e ".[dev]"
        echo.
        pause
        exit /b 1
    )
) else (
    rem Check dependencies for existing environment
    echo Checking dependencies...
    %PYTHON_CMD% -c "import click, jinja2, rich" 2>nul
    if errorlevel 1 (
        echo Missing required libraries. Installing automatically...
        echo Installing packages... (please wait)
        echo.
        
        %PYTHON_CMD% -m pip install -e ".[dev]" --quiet
        if !errorlevel! equ 0 (
            echo OK: Dependencies installed successfully
        ) else (
            echo Error: Failed to install dependencies
            echo.
            echo Please run manually:
            echo     .venv\Scripts\activate.bat
            echo     pip install -e ".[dev]"
            echo.
            pause
            exit /b 1
        )
    ) else (
        echo OK: Dependencies verified
    )
)

rem Detect execution context and set output directory
set "SCRIPT_PATH=%~f0"
echo %SCRIPT_PATH% | findstr /i "Desktop" >nul
if %errorlevel%==0 (
    rem Executed from Desktop
    set "OUTPUT_DIR=%USERPROFILE%\Desktop\Kumihan_Output"
    echo Desktop execution detected
    echo Output: !OUTPUT_DIR!
    if not exist "!OUTPUT_DIR!" mkdir "!OUTPUT_DIR!"
) else (
    rem Executed from project directory
    set "OUTPUT_DIR=.\dist"
    echo Project execution detected
    echo Output: !OUTPUT_DIR!
)
echo.

rem Check if file was dropped (argument provided)
if "%~1"=="" goto interactive_mode

rem Drag & Drop mode
echo Processing file: %~nx1
echo.

rem Check file extension
if /i not "%~x1"==".txt" (
    echo Error: Only .txt files are supported
    echo   Provided file: %~nx1
    echo.
    pause
    exit /b 1
)

rem Check file existence
if not exist "%~1" (
    echo Error: File not found
    echo   File: %~1
    echo.
    pause
    exit /b 1
)

echo Starting conversion...
echo.

rem Execute conversion
%PYTHON_CMD% -m kumihan_formatter "%~1" -o "!OUTPUT_DIR!"
if errorlevel 1 (
    echo.
    echo Error occurred during conversion
    echo.
    pause
    exit /b 1
)

echo.
echo Conversion completed successfully!
echo Open output folder? [Y/N]
set /p choice="> "
if /i "%choice%"=="y" (
    explorer "!OUTPUT_DIR!"
)

echo.
echo Press any key to exit...
pause > nul
exit /b 0

:interactive_mode
rem Interactive mode
echo Usage:
echo   1. Drag and drop .txt file to this window
echo   2. Or enter file path directly
echo.

set /p input_file="Enter .txt file path: "

rem Input validation
if "%input_file%"=="" (
    echo Error: No file path entered
    echo.
    pause
    exit /b 1
)

rem Remove quotes
set input_file=%input_file:"=%

rem Check file existence
if not exist "%input_file%" (
    echo Error: File not found
    echo   File: %input_file%
    echo.
    pause
    exit /b 1
)

rem Check extension
for %%i in ("%input_file%") do set ext=%%~xi
if /i not "%ext%"==".txt" (
    echo Error: Only .txt files are supported
    echo   Provided file: %input_file%
    echo.
    pause
    exit /b 1
)

echo.
echo Starting conversion...
echo.

rem Execute conversion
%PYTHON_CMD% -m kumihan_formatter "%input_file%" -o "!OUTPUT_DIR!"
if errorlevel 1 (
    echo.
    echo Error occurred during conversion
    echo.
    pause
    exit /b 1
)

echo.
echo Conversion completed successfully!
echo Open output folder? [Y/N]
set /p choice="> "
if /i "%choice%"=="y" (
    explorer "!OUTPUT_DIR!"
)

echo.
echo Press any key to exit...
pause > nul