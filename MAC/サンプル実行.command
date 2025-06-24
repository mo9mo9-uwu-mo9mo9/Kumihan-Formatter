#!/bin/bash

# macOS用 サンプル一括実行スクリプト
# ダブルクリックで実行可能

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

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

# 色付き出力の設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo ""
echo "=========================================="
echo " Kumihan-Formatter - Sample Batch Run"
echo "=========================================="
echo "Convert all sample files to HTML"
echo "Output: ../examples/output/"
echo "=========================================="
echo ""

# Check if setup has been completed
if [ ! -d "../.venv" ]; then
    echo -e "${YELLOW}[WARNING] Setup not completed yet!${NC}"
    echo ""
    echo "Please run the setup first:"
    echo "  1. Double-click: setup.command"
    echo "  2. Wait for setup to complete"
    echo "  3. Then run this script again"
    echo ""
    echo "For help, see: docs/user/LAUNCH_GUIDE.md"
    echo ""
    echo "Press any key to exit..."
    read -n 1
    exit 1
fi
echo -e "${GREEN}[OK] Setup detected, proceeding...${NC}"

# Pythonのバージョン確認
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[エラー] エラー: Python 3 が見つかりません${NC}"
    echo ""
    echo "Python 3.9 以上をインストールしてください："
    echo "https://www.python.org/downloads/"
    echo ""
    echo "何かキーを押して終了してください..."
    read -n 1
    exit 1
fi

# 仮想環境の確認
if [ -d "../.venv" ]; then
    echo -e "${BLUE}[設定] 仮想環境をアクティベート中...${NC}"
    source ../.venv/bin/activate
    PYTHON_CMD="python"
else
    echo -e "${RED}[警告]  仮想環境が見つかりません${NC}"
    echo -e "${YELLOW}[ヒント] kumihan_convert.command を先に実行してセットアップを完了してください${NC}"
    echo ""
    echo "何かキーを押して終了してください..."
    read -n 1
    exit 1
fi

# 依存関係の確認
echo -e "${BLUE}[検証] 依存関係を確認中...${NC}"
if ! $PYTHON_CMD -c "import click, jinja2, rich" 2>/dev/null; then
    echo -e "${RED}[エラー] エラー: 必要なライブラリが不足しています${NC}"
    echo -e "${YELLOW}[ヒント] kumihan_convert.command を先に実行してセットアップを完了してください${NC}"
    echo ""
    echo "何かキーを押して終了してください..."
    read -n 1
    exit 1
fi

echo -e "${GREEN}[完了] 環境確認完了${NC}"
echo ""

# 出力ディレクトリの準備
OUTPUT_BASE="../dist/samples"

# 既存ディレクトリのチェック
if [ -d "$OUTPUT_BASE" ] && [ "$(ls -A $OUTPUT_BASE)" ]; then
    echo -e "${YELLOW}[警告]  警告: 出力ディレクトリ内にファイルが存在します${NC}"
    echo -e "${YELLOW}   以下のファイルが上書きされます:${NC}"
    echo ""
    for file in "$OUTPUT_BASE"/*; do
        if [ -e "$file" ]; then
            echo -e "${YELLOW}     - $(basename "$file")${NC}"
        fi
    done
    echo ""
    echo -e "${CYAN}続行しますか？ [Y/n]: ${NC}"
    read -n 1 choice
    echo ""
    if [[ ! $choice =~ ^[Yy]$ ]] && [ ! -z "$choice" ]; then
        echo -e "${YELLOW}処理を中止しました${NC}"
        echo ""
        echo "何かキーを押して終了してください..."
        read -n 1
        exit 0
    fi
fi

mkdir -p "$OUTPUT_BASE"

echo -e "${CYAN}サンプル変換を開始します...${NC}"
echo -e "${CYAN}出力先: ../dist/samples/ (自動作成されます)${NC}"
echo ""

# 記法表示機能の選択を事前に確認
echo -e "${CYAN}記法と結果を並べて表示する機能があります${NC}"
echo -e "${CYAN}改行処理などの動作を実際に確認しながら記法を学習できます${NC}"
echo -n "この機能を使用しますか？ (Y/n): "
read -n 1 choice
echo ""
echo ""

# 選択に基づいてフラグを設定
if [[ $choice =~ ^[Yy]$ ]] || [ -z "$choice" ]; then
    SOURCE_TOGGLE_FLAG="--with-source-toggle"
    echo -e "${GREEN}記法表示機能を有効にして変換します${NC}"
else
    SOURCE_TOGGLE_FLAG=""
    echo -e "${YELLOW}記法表示機能なしで変換します${NC}"
fi
echo ""

# サンプル1: basic
echo -e "${BLUE}[1/3] 基本サンプル (02-basic.txt)${NC}"
OUTPUT_DIR="$OUTPUT_BASE/basic"
mkdir -p "$OUTPUT_DIR"

if $PYTHON_CMD -m kumihan_formatter convert "../examples/02-basic.txt" -o "$OUTPUT_DIR" --no-preview $SOURCE_TOGGLE_FLAG; then
    echo -e "${GREEN}basic サンプル完了 → $OUTPUT_DIR${NC}"
else
    echo -e "${RED}エラー: basic サンプルの変換に失敗${NC}"
    exit 1
fi
echo ""

# サンプル2: advanced
echo -e "${BLUE}[2/3] 高度なサンプル (03-comprehensive.txt)${NC}"
OUTPUT_DIR="$OUTPUT_BASE/advanced"
mkdir -p "$OUTPUT_DIR"

if $PYTHON_CMD -m kumihan_formatter convert "../examples/03-comprehensive.txt" -o "$OUTPUT_DIR" --no-preview $SOURCE_TOGGLE_FLAG; then
    echo -e "${GREEN}advanced サンプル完了 → $OUTPUT_DIR${NC}"
else
    echo -e "${RED}エラー: advanced サンプルの変換に失敗${NC}"
    exit 1
fi
echo ""

# サンプル3: showcase
echo -e "${BLUE}[3/3] 機能ショーケース (--generate-sample)${NC}"
OUTPUT_DIR="$OUTPUT_BASE/showcase"
mkdir -p "$OUTPUT_DIR"

if $PYTHON_CMD -m kumihan_formatter convert --generate-sample -o "$OUTPUT_DIR" --no-preview $SOURCE_TOGGLE_FLAG; then
    echo -e "${GREEN}showcase サンプル完了 → $OUTPUT_DIR${NC}"
else
    echo -e "${RED}エラー: showcase サンプルの変換に失敗${NC}"
    exit 1
fi
echo ""

echo "=========================================="
echo -e "${GREEN}全サンプルの変換が完了しました！${NC}"
echo "=========================================="
echo ""
echo -e "${CYAN}生成されたファイル:${NC}"
echo "  ../dist/samples/basic/        - 基本的な記法のサンプル"
echo "  ../dist/samples/advanced/     - 高度な記法のサンプル"
echo "  ../dist/samples/showcase/     - 全機能のショーケース"
echo ""
echo -e "${YELLOW}HTMLファイルをブラウザで確認してください${NC}"
echo ""
echo "出力フォルダを開きますか？ [y/N]"
read -n 1 choice
echo ""
if [[ $choice =~ ^[Yy]$ ]]; then
    open "$OUTPUT_BASE"
fi

echo ""
echo "何かキーを押して終了してください..."
read -n 1