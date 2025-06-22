#!/bin/bash

# Kumihan-Formatter - One-time Setup Script
# This script automatically sets up everything needed to use Kumihan-Formatter

echo ""
echo "=========================================="
echo " Kumihan-Formatter - Initial Setup"
echo "=========================================="
echo "This will automatically set up everything you need"
echo "to start using Kumihan-Formatter immediately."
echo "=========================================="
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check Python version
echo "[1/4] Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    REQUIRED_VERSION="3.9"
    
    # Version comparison
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
        PYTHON_CMD="python3"
        echo "[OK] Python found: $PYTHON_VERSION"
    else
        echo "[ERROR] Python $REQUIRED_VERSION or higher required (current: $PYTHON_VERSION)"
        echo ""
        echo "Please install Python $REQUIRED_VERSION or higher:"
        echo "https://www.python.org/downloads/"
        echo ""
        echo "After installing Python, run this setup again."
        echo ""
        read -p "Press any key to exit..."
        exit 1
    fi
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    REQUIRED_VERSION="3.9"
    
    # Version comparison
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
        PYTHON_CMD="python"
        echo "[OK] Python found: $PYTHON_VERSION"
    else
        echo "[ERROR] Python $REQUIRED_VERSION or higher required (current: $PYTHON_VERSION)"
        echo ""
        echo "Please install Python $REQUIRED_VERSION or higher:"
        echo "https://www.python.org/downloads/"
        echo ""
        echo "After installing Python, run this setup again."
        echo ""
        read -p "Press any key to exit..."
        exit 1
    fi
else
    echo "[ERROR] Python not found"
    echo ""
    echo "Please install Python 3.9 or higher:"
    echo "https://www.python.org/downloads/"
    echo ""
    echo "After installing Python, run this setup again."
    echo ""
    read -p "Press any key to exit..."
    exit 1
fi

# Create virtual environment
echo "[2/4] Creating virtual environment..."
if [ -d ".venv" ]; then
    echo "[OK] Virtual environment already exists"
else
    if $PYTHON_CMD -m venv .venv; then
        echo "[OK] Virtual environment created"
    else
        echo "[ERROR] Failed to create virtual environment"
        echo ""
        read -p "Press any key to exit..."
        exit 1
    fi
fi

# Activate virtual environment
echo "[3/4] Activating virtual environment..."
source .venv/bin/activate
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to activate virtual environment"
    echo ""
    read -p "Press any key to exit..."
    exit 1
else
    echo "[OK] Virtual environment activated"
fi

# Install dependencies
echo "[4/4] Installing dependencies..."
echo "This may take a moment..."
if python -m pip install -e ".[dev]" --quiet; then
    echo "[OK] Dependencies installed successfully"
else
    echo "[ERROR] Failed to install dependencies"
    echo ""
    echo "Please check your internet connection and try again."
    echo ""
    read -p "Press any key to exit..."
    exit 1
fi

echo ""
echo "=========================================="
echo " Setup Complete!"
echo "=========================================="
echo ""
echo "You can now use Kumihan-Formatter:"
echo ""
echo "For basic conversion:"
echo "  - Double-click: kumihan_convert.command"
echo "  - Drag and drop .txt files to convert"
echo ""
echo "To try examples:"
echo "  - Double-click: run_examples.command"
echo "  - See generated samples in examples/output/"
echo ""
echo "For help:"
echo "  - Read: LAUNCH_GUIDE.md"
echo "  - Read: FIRST_RUN.md"
echo ""
echo "Press any key to exit..."
read -p ""