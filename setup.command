#!/bin/bash

# Kumihan-Formatter - One-time Setup Script
# This script automatically sets up everything needed to use Kumihan-Formatter

echo ""
echo "=========================================="
echo " Kumihan-Formatter - 初回セットアップ"
echo "=========================================="
echo "必要な環境を自動でセットアップします"
echo "すぐにKumihan-Formatterを使用できるようになります。"
echo "=========================================="
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check Python version
echo "[1/4] Python インストールを確認中..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    REQUIRED_VERSION="3.9"
    
    # Version comparison
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
        PYTHON_CMD="python3"
        echo "[OK] Python が見つかりました: $PYTHON_VERSION"
    else
        echo "[エラー] Python $REQUIRED_VERSION 以上が必要です (現在: $PYTHON_VERSION)"
        echo ""
        echo "Python $REQUIRED_VERSION 以上をインストールしてください："
        echo "https://www.python.org/downloads/"
        echo ""
        echo "Python インストール後、再度このセットアップを実行してください。"
        echo ""
        read -p "何かキーを押して終了してください..."
        exit 1
    fi
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    REQUIRED_VERSION="3.9"
    
    # Version comparison
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
        PYTHON_CMD="python"
        echo "[OK] Python が見つかりました: $PYTHON_VERSION"
    else
        echo "[エラー] Python $REQUIRED_VERSION 以上が必要です (現在: $PYTHON_VERSION)"
        echo ""
        echo "Python $REQUIRED_VERSION 以上をインストールしてください："
        echo "https://www.python.org/downloads/"
        echo ""
        echo "Python インストール後、再度このセットアップを実行してください。"
        echo ""
        read -p "何かキーを押して終了してください..."
        exit 1
    fi
else
    echo "[エラー] Python が見つかりません"
    echo ""
    echo "Python 3.9 以上をインストールしてください："
    echo "https://www.python.org/downloads/"
    echo ""
    echo "Python インストール後、再度このセットアップを実行してください。"
    echo ""
    read -p "何かキーを押して終了してください..."
    exit 1
fi

# Create virtual environment
echo "[2/4] 仮想環境を作成中..."
if [ -d ".venv" ]; then
    echo "[OK] 仮想環境は既に存在します"
else
    if $PYTHON_CMD -m venv .venv; then
        echo "[OK] 仮想環境を作成しました"
    else
        echo "[エラー] 仮想環境の作成に失敗しました"
        echo ""
        read -p "何かキーを押して終了してください..."
        exit 1
    fi
fi

# Activate virtual environment
echo "[3/4] 仮想環境をアクティベート中..."
source .venv/bin/activate
if [ $? -ne 0 ]; then
    echo "[エラー] 仮想環境のアクティベートに失敗しました"
    echo ""
    read -p "何かキーを押して終了してください..."
    exit 1
else
    echo "[OK] 仮想環境をアクティベートしました"
fi

# Install dependencies
echo "[4/4] 依存関係をインストール中..."
echo "しばらくお待ちください..."
if python -m pip install -e ".[dev]" --quiet; then
    echo "[OK] 依存関係のインストールが完了しました"
else
    echo "[エラー] 依存関係のインストールに失敗しました"
    echo ""
    echo "インターネット接続を確認して、再度お試しください。"
    echo ""
    read -p "何かキーを押して終了してください..."
    exit 1
fi

echo ""
echo "=========================================="
echo " セットアップ完了！"
echo "=========================================="
echo ""

# セットアップ完了後の変換ツール自動起動オプション
echo "🎉 セットアップが完了しました！"
echo ""
echo "次のステップ:"
echo "  1. 変換ツールを起動"
echo "  2. .txtファイルをドラッグ&ドロップ"
echo "  3. HTMLファイルが生成されます"
echo ""
echo -n "📱 変換ツールを今すぐ起動しますか？ [y/N]: "
read choice
echo ""
if [[ "$choice" =~ ^[Yy]$ ]]; then
    echo "🚀 変換ツールを起動しています..."
    echo ""
    if [ -f "MAC/変換ツール.command" ]; then
        exec ./MAC/変換ツール.command
    else
        echo "❌ エラー: MAC/変換ツール.command が見つかりません"
        echo "手動で MAC/変換ツール.command をダブルクリックしてください"
        echo ""
        echo "何かキーを押して終了してください..."
        read -n 1
    fi
else
    echo "💡 後で使用する場合:"
    echo "   MAC/変換ツール.command をダブルクリックしてください"
    echo ""
    echo "何かキーを押して終了してください..."
    read -p " "
fi