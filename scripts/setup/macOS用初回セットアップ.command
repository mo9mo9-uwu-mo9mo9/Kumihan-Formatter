#!/bin/bash

# Kumihan-Formatter - One-time Setup Script
# This script automatically sets up everything needed to use Kumihan-Formatter

# ターミナルの設定とエンコーディング修正
export LANG=ja_JP.UTF-8
export LC_ALL=ja_JP.UTF-8
export PYTHONIOENCODING=utf-8

# macOSのターミナルエンコーディング設定
if [[ "$TERM_PROGRAM" == "Apple_Terminal" ]] || [[ -z "$TERM_PROGRAM" ]]; then
    export LESSCHARSET=utf-8
    # ターミナルのエンコーディングを明示的に設定
    printf '\033]1337;SetProfile=Default\007' 2>/dev/null || true
fi

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
    REQUIRED_VERSION="3.12"

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
    REQUIRED_VERSION="3.12"

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
    echo "Please install Python 3.12 or higher:"
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
echo "[完了] セットアップが完了しました！"
echo ""
echo "次のステップ:"
echo "  1. 変換ツールを起動"
echo "  2. .txtファイルをドラッグ&ドロップ"
echo "  3. HTMLファイルが生成されます"
echo ""
echo "次のステップを選択してください:"
echo "  Y: 変換ツールを今すぐ起動"
echo "  N: 後で使用（使用方法を表示）"
echo "  S: サンプルを確認（出力例を見る）"
echo ""
read -p "選択してください [Y/N/S]: " choice
if [[ "$choice" =~ ^[Yy]$ ]]; then
    echo ""
    echo " GUIアプリを使用してください"
    echo ""
    echo "📻 リリースページからGUIアプリをダウンロード:"
    echo "   https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/releases"
    echo ""
    echo "🔧 またはコマンドラインで:"
    echo "   python -m kumihan_formatter convert input.txt"
    echo ""
    read -p "Press any key to continue..."
elif [[ "$choice" =~ ^[Ss]$ ]]; then
    echo ""
    echo " サンプルを実行しています..."
    echo ""
    echo "🎆 サンプルを生成しています..."
    python -m kumihan_formatter sample
        echo ""
        echo "サンプル確認が完了しました！"
        echo ""
        read -p "今度は変換ツールを試しますか？ [Y/N]: " convert_choice
        if [[ "$convert_choice" =~ ^[Yy]$ ]]; then
            echo ""
            echo " 変換ツールを起動しています..."
            echo "💻 GUIアプリを使用してください:"
            echo "   https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/releases"
            echo ""
            echo "🔧 またはコマンドラインで:"
            echo "   python -m kumihan_formatter convert input.txt"
        fi
    else
        echo "[エラー] サンプルの生成に失敗しました"
        echo "手動で 'python -m kumihan_formatter sample' を実行してください"
    fi
    echo ""
    echo "Press any key to exit..."
    read -p ""
else
    echo ""
    echo "[ヒント] 後で使用する場合:"
    echo "   GUIアプリ: https://github.com/mo9mo9-uwu-mo9mo9/Kumihan-Formatter/releases"
    echo "   コマンドライン: python -m kumihan_formatter convert input.txt"
    echo ""
    echo "サンプルを確認する場合:"
    echo "   python -m kumihan_formatter sample"
    echo ""
    echo "Press any key to exit..."
    read -p ""
fi
