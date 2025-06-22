#!/bin/bash

# macOS用 Kumihan-Formatter ランチャー
# ダブルクリックで実行可能

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

# ターミナルの設定
export LANG=ja_JP.UTF-8
export LC_ALL=ja_JP.UTF-8

# 色付き出力の設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo ""
echo "=========================================="
echo " Kumihan-Formatter - Text to HTML Converter"
echo "=========================================="
echo "Convert .txt files to beautiful HTML"
echo "Usage: Enter file path or drag and drop"
echo "First run will auto-setup environment"
echo "=========================================="
echo ""

# Check if setup has been completed
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}[WARNING] Setup not completed yet!${NC}"
    echo ""
    echo "Please run the setup first:"
    echo "  1. Double-click: setup.command"
    echo "  2. Wait for setup to complete"
    echo "  3. Then run this script again"
    echo ""
    echo "For help, see: LAUNCH_GUIDE.md"
    echo ""
    echo "Press any key to exit..."
    read -n 1
    exit 1
fi
echo -e "${GREEN}[OK] Setup detected, proceeding...${NC}"

# Pythonのバージョン確認
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ エラー: Python 3 が見つかりません${NC}"
    echo ""
    echo "Python 3.9 以上をインストールしてください："
    echo "https://www.python.org/downloads/"
    echo ""
    echo "何かキーを押して終了してください..."
    read -n 1
    exit 1
fi

# 仮想環境の確認とアクティベート
VENV_CREATED=0
if [ -d ".venv" ]; then
    echo -e "${BLUE}🔧 仮想環境をアクティベート中...${NC}"
    source .venv/bin/activate
    PYTHON_CMD="python"
else
    echo -e "${YELLOW}⚠️  仮想環境が見つかりません。自動で作成します...${NC}"
    echo -e "${BLUE}🏗️  初回セットアップを実行しています...${NC}"
    
    # 仮想環境を作成
    echo -e "${BLUE}📦 仮想環境を作成中...${NC}"
    if python3 -m venv .venv; then
        echo -e "${GREEN}✅ 仮想環境を作成しました${NC}"
        VENV_CREATED=1
    else
        echo -e "${RED}❌ エラー: 仮想環境の作成に失敗しました${NC}"
        echo ""
        echo "何かキーを押して終了してください..."
        read -n 1
        exit 1
    fi
    
    # 仮想環境をアクティベート
    echo -e "${BLUE}🔧 仮想環境をアクティベート中...${NC}"
    source .venv/bin/activate
    PYTHON_CMD="python"
fi

# Pythonのバージョンを表示
echo -e "${BLUE}🐍 Python バージョン:${NC}"
$PYTHON_CMD --version

# 依存関係の確認と自動インストール
# 仮想環境を新規作成した場合は必ずインストールを実行
if [ $VENV_CREATED -eq 1 ]; then
    echo -e "${BLUE}📚 新規仮想環境に依存関係をインストール中...${NC}"
    echo -e "${BLUE}⏳ パッケージをインストール中... (しばらくお待ちください)${NC}"
    
    if $PYTHON_CMD -m pip install -e ".[dev]" --quiet; then
        echo -e "${GREEN}✅ 依存関係のインストールが完了しました${NC}"
    else
        echo -e "${RED}❌ エラー: 依存関係のインストールに失敗しました${NC}"
        echo ""
        echo "手動で以下のコマンドを実行してください："
        echo -e "${CYAN}    source .venv/bin/activate${NC}"
        echo -e "${CYAN}    pip install -e \".[dev]\"${NC}"
        echo ""
        echo "何かキーを押して終了してください..."
        read -n 1
        exit 1
    fi
else
    # 既存の仮想環境の場合は依存関係を確認
    echo -e "${BLUE}🔍 依存関係を確認中...${NC}"
    if ! $PYTHON_CMD -c "import click, jinja2, rich" 2>/dev/null; then
        echo -e "${YELLOW}📚 必要なライブラリが不足しています。自動でインストールします...${NC}"
        echo -e "${BLUE}⏳ パッケージをインストール中... (しばらくお待ちください)${NC}"
        
        if $PYTHON_CMD -m pip install -e ".[dev]" --quiet; then
            echo -e "${GREEN}✅ 依存関係のインストールが完了しました${NC}"
        else
            echo -e "${RED}❌ エラー: 依存関係のインストールに失敗しました${NC}"
            echo ""
            echo "手動で以下のコマンドを実行してください："
            echo -e "${CYAN}    source .venv/bin/activate${NC}"
            echo -e "${CYAN}    pip install -e \".[dev]\"${NC}"
            echo ""
            echo "何かキーを押して終了してください..."
            read -n 1
            exit 1
        fi
    else
        echo -e "${GREEN}✅ 依存関係の確認完了${NC}"
    fi
fi

# 実行コンテキストの検出と出力先の決定
SCRIPT_PATH="$(realpath "$0")"
CALLING_DIR="$(pwd)"
if [[ "$SCRIPT_PATH" == *"Desktop"* ]] || [[ "$CALLING_DIR" == *"Desktop"* ]] || [[ "${SCRIPT_PATH:-}" == *"Desktop"* ]]; then
    # デスクトップから実行された場合
    OUTPUT_DIR="$HOME/Desktop/Kumihan_Output"
    echo -e "${BLUE}🏠 デスクトップ実行を検出しました${NC}"
    echo -e "${BLUE}📁 出力先: $OUTPUT_DIR${NC}"
    mkdir -p "$OUTPUT_DIR"
else
    # プロジェクト内から実行された場合
    OUTPUT_DIR="./dist"
    echo -e "${BLUE}🔧 プロジェクト内実行を検出しました${NC}"
    echo -e "${BLUE}📁 出力先: $OUTPUT_DIR${NC}"
fi
echo ""

# 引数がある場合（ドラッグ&ドロップされた場合）
if [ $# -gt 0 ]; then
    input_file="$1"
    echo -e "${CYAN}📝 処理ファイル: $(basename "$input_file")${NC}"
    echo ""
    
    # ファイルの存在を確認
    if [ ! -f "$input_file" ]; then
        echo -e "${RED}❌ エラー: ファイルが見つかりません${NC}"
        echo "   ファイル: $input_file"
        echo ""
        echo "何かキーを押して終了してください..."
        read -n 1
        exit 1
    fi
    
    # ファイル拡張子をチェック
    if [[ ! "$input_file" =~ \.txt$ ]]; then
        echo -e "${RED}❌ エラー: .txt ファイルのみ対応しています${NC}"
        echo "   指定されたファイル: $(basename "$input_file")"
        echo ""
        echo "何かキーを押して終了してください..."
        read -n 1
        exit 1
    fi
    
    echo -e "${YELLOW}🔄 変換を開始します...${NC}"
    echo ""
    
    # 変換実行
    if $PYTHON_CMD -m kumihan_formatter "$input_file" -o "$OUTPUT_DIR"; then
        echo ""
        echo -e "${GREEN}✅ 変換が完了しました！${NC}"
        echo ""
        echo "📁 出力フォルダを開きますか？ [y/N]"
        read -n 1 choice
        echo ""
        if [[ "$choice" =~ ^[Yy]$ ]]; then
            open "$OUTPUT_DIR"
        fi
    else
        echo ""
        echo -e "${RED}❌ 変換中にエラーが発生しました${NC}"
        echo ""
    fi
    
    echo ""
    echo "何かキーを押して終了してください..."
    read -n 1
    exit 0
fi

# 対話モード
echo -e "${BLUE}🖱️ 使い方:${NC}"
echo "  1. この画面に .txt ファイルをドラッグ&ドロップ"
echo "  2. または、ファイルパスを直接入力"
echo ""

echo -n "📝 変換したい .txt ファイルのパス: "
read input_file

# 入力チェック
if [ -z "$input_file" ]; then
    echo -e "${RED}❌ ファイルパスが入力されていません${NC}"
    echo ""
    echo "何かキーを押して終了してください..."
    read -n 1
    exit 1
fi

# クォートを除去
input_file=$(echo "$input_file" | sed 's/^"//;s/"$//')

# ファイルの存在確認
if [ ! -f "$input_file" ]; then
    echo -e "${RED}❌ エラー: ファイルが見つかりません${NC}"
    echo "   ファイル: $input_file"
    echo ""
    echo "何かキーを押して終了してください..."
    read -n 1
    exit 1
fi

# 拡張子チェック
if [[ ! "$input_file" =~ \.txt$ ]]; then
    echo -e "${RED}❌ エラー: .txt ファイルのみ対応しています${NC}"
    echo "   指定されたファイル: $(basename "$input_file")"
    echo ""
    echo "何かキーを押して終了してください..."
    read -n 1
    exit 1
fi

echo ""
echo -e "${YELLOW}🔄 変換を開始します...${NC}"
echo ""

# 変換実行
if $PYTHON_CMD -m kumihan_formatter "$input_file" -o "$OUTPUT_DIR"; then
    echo ""
    echo -e "${GREEN}✅ 変換が完了しました！${NC}"
    echo ""
    echo "📁 出力フォルダを開きますか？ [y/N]"
    read -n 1 choice
    echo ""
    if [[ "$choice" =~ ^[Yy]$ ]]; then
        open "$OUTPUT_DIR"
    fi
else
    echo ""
    echo -e "${RED}❌ 変換中にエラーが発生しました${NC}"
    echo ""
fi

echo ""
echo "何かキーを押して終了してください..."
read -n 1