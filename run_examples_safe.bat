@echo off
setlocal enabledelayedexpansion
rem Windows character encoding safe version
rem This script works with both UTF-8 and Shift-JIS environments

rem Try to set UTF-8 encoding, but don't fail if it doesn't work
chcp 65001 > nul 2>&1

title Kumihan-Formatter - Sample Execution Script

echo.
echo ==========================================
echo  Kumihan-Formatter - Sample Batch Run
echo ==========================================
echo Convert all sample files to HTML
echo Output: examples/output/
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
)

rem Check virtual environment
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
    set PYTHON_CMD=python
) else (
    echo Virtual environment not found
    echo Please run kumihan_convert.bat first to complete setup
    echo.
    pause
    exit /b 1
)

rem Check dependencies
echo Checking dependencies...
%PYTHON_CMD% -c "import click, jinja2, rich" 2>nul
if errorlevel 1 (
    echo Error: Required libraries missing
    echo Please run kumihan_convert.bat first to complete setup
    echo.
    pause
    exit /b 1
)

echo OK: Environment verified
echo.

rem Prepare output directory
set "OUTPUT_BASE=examples\output"
if not exist "%OUTPUT_BASE%" mkdir "%OUTPUT_BASE%"

echo Starting sample conversion...
echo.

rem Sample 1: basic
echo [1/3] Basic sample (sample.txt)
set "OUTPUT_DIR=%OUTPUT_BASE%\basic"
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

%PYTHON_CMD% -m kumihan_formatter "examples\input\sample.txt" -o "%OUTPUT_DIR%" --no-preview
if errorlevel 1 (
    echo Error: Failed to convert basic sample
    goto error_end
) else (
    echo OK: Basic sample completed -> %OUTPUT_DIR%
)
echo.

rem Sample 2: advanced
echo [2/3] Advanced sample (comprehensive-sample.txt)
set "OUTPUT_DIR=%OUTPUT_BASE%\advanced"
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

%PYTHON_CMD% -m kumihan_formatter "examples\input\comprehensive-sample.txt" -o "%OUTPUT_DIR%" --no-preview
if errorlevel 1 (
    echo Error: Failed to convert advanced sample
    goto error_end
) else (
    echo OK: Advanced sample completed -> %OUTPUT_DIR%
)
echo.

rem Sample 3: showcase
echo [3/3] Feature showcase (--generate-sample)
set "OUTPUT_DIR=%OUTPUT_BASE%\showcase"
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

%PYTHON_CMD% -m kumihan_formatter --generate-sample -o "%OUTPUT_DIR%" --no-preview
if errorlevel 1 (
    echo Error: Failed to convert showcase sample
    goto error_end
) else (
    echo OK: Showcase sample completed -> %OUTPUT_DIR%
)
echo.

echo ==========================================
echo All samples converted successfully!
echo ==========================================
echo.
echo Generated files:
echo   examples\output\basic\        - Basic syntax samples
echo   examples\output\advanced\     - Advanced syntax samples
echo   examples\output\showcase\     - Feature showcase
echo.
echo Please check HTML files in your browser
echo.
echo Open output folder? [Y/N]
set /p choice="> "
if /i "%choice%"=="y" (
    explorer "%OUTPUT_BASE%"
)

echo.
echo Press any key to exit...
pause > nul
exit /b 0

:error_end
echo.
echo Troubleshooting:
echo   1. Run kumihan_convert.bat first to complete setup
echo   2. Check error messages and fix issues
echo   3. Refer to FIRST_RUN.md for help
echo.
pause
exit /b 1