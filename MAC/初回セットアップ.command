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
if [ -d "../.venv" ]; then
    echo "[OK] Virtual environment already exists"
else
    if $PYTHON_CMD -m venv ../.venv; then
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
source ../.venv/bin/activate
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
if python -m pip install -e "../[dev]" --quiet; then
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
echo "🎉 セットアップが完了しました！"
echo ""
echo "次のステップ:"
echo "  1. 変換ツールを起動"
echo "  2. .txtファイルをドラッグ&ドロップ"
echo "  3. HTMLファイルが生成されます"
echo ""
read -p "📱 変換ツールを今すぐ起動しますか？ [Y/N]: " choice
if [[ "$choice" =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 変換ツールを起動しています..."
    if [ -f "変換ツール.command" ]; then
        open "変換ツール.command"
    else
        echo "[ERROR] 変換ツール.command が見つかりません"
        echo ""
        echo "手動で起動してください:"
        echo "  - Double-click: MAC/変換ツール.command"
        echo ""
        read -p "Press any key to exit..."
    fi
else
    echo ""
    echo "💡 後で使用する場合:"
    echo "   MAC/変換ツール.command をダブルクリック"
    echo ""
    echo "その他の使用方法:"
    echo ""
    echo "To try examples:"
    echo "  - Double-click: サンプル実行.command"
    echo "  - See generated samples in examples/output/"
    echo ""
    echo "For updates:"
    echo "  - Download latest version from GitHub releases"
    echo "  - Or visit: https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter"
    echo ""
    echo "For help:"
    echo "  - Read: docs/user/LAUNCH_GUIDE.md"
    echo "  - Read: docs/user/FIRST_RUN.md"
    echo ""
    echo "Press any key to exit..."
    read -p ""
fi