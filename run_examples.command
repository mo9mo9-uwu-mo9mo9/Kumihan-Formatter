#!/bin/bash

# macOS用 サンプル一括実行スクリプト
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
echo " Kumihan-Formatter - サンプル一括実行"
echo "=========================================="
echo "📝 全サンプルファイルを一括変換します"
echo "🎯 出力先: examples/output/"
echo "=========================================="
echo ""

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

# 仮想環境の確認
if [ -d ".venv" ]; then
    echo -e "${BLUE}🔧 仮想環境をアクティベート中...${NC}"
    source .venv/bin/activate
    PYTHON_CMD="python"
else
    echo -e "${RED}⚠️  仮想環境が見つかりません${NC}"
    echo -e "${YELLOW}💡 kumihan_convert.command を先に実行してセットアップを完了してください${NC}"
    echo ""
    echo "何かキーを押して終了してください..."
    read -n 1
    exit 1
fi

# 依存関係の確認
echo -e "${BLUE}🔍 依存関係を確認中...${NC}"
if ! $PYTHON_CMD -c "import click, jinja2, rich" 2>/dev/null; then
    echo -e "${RED}❌ エラー: 必要なライブラリが不足しています${NC}"
    echo -e "${YELLOW}💡 kumihan_convert.command を先に実行してセットアップを完了してください${NC}"
    echo ""
    echo "何かキーを押して終了してください..."
    read -n 1
    exit 1
fi

echo -e "${GREEN}✅ 環境確認完了${NC}"
echo ""

# 出力ディレクトリの準備
OUTPUT_BASE="examples/output"
mkdir -p "$OUTPUT_BASE"

echo -e "${CYAN}🚀 サンプル変換を開始します...${NC}"
echo ""

# サンプル1: basic
echo -e "${BLUE}📝 [1/3] 基本サンプル (sample.txt)${NC}"
OUTPUT_DIR="$OUTPUT_BASE/basic"
mkdir -p "$OUTPUT_DIR"

if $PYTHON_CMD -m kumihan_formatter "examples/input/sample.txt" -o "$OUTPUT_DIR" --no-preview; then
    echo -e "${GREEN}✅ basic サンプル完了 → $OUTPUT_DIR${NC}"
else
    echo -e "${RED}❌ エラー: basic サンプルの変換に失敗${NC}"
    exit 1
fi
echo ""

# サンプル2: advanced
echo -e "${BLUE}📝 [2/3] 高度なサンプル (comprehensive-sample.txt)${NC}"
OUTPUT_DIR="$OUTPUT_BASE/advanced"
mkdir -p "$OUTPUT_DIR"

if $PYTHON_CMD -m kumihan_formatter "examples/input/comprehensive-sample.txt" -o "$OUTPUT_DIR" --no-preview; then
    echo -e "${GREEN}✅ advanced サンプル完了 → $OUTPUT_DIR${NC}"
else
    echo -e "${RED}❌ エラー: advanced サンプルの変換に失敗${NC}"
    exit 1
fi
echo ""

# サンプル3: showcase
echo -e "${BLUE}📝 [3/3] 機能ショーケース (--generate-sample)${NC}"
OUTPUT_DIR="$OUTPUT_BASE/showcase"
mkdir -p "$OUTPUT_DIR"

if $PYTHON_CMD -m kumihan_formatter --generate-sample -o "$OUTPUT_DIR" --no-preview; then
    echo -e "${GREEN}✅ showcase サンプル完了 → $OUTPUT_DIR${NC}"
else
    echo -e "${RED}❌ エラー: showcase サンプルの変換に失敗${NC}"
    exit 1
fi
echo ""

echo "=========================================="
echo -e "${GREEN}✅ 全サンプルの変換が完了しました！${NC}"
echo "=========================================="
echo ""
echo -e "${CYAN}📁 生成されたファイル:${NC}"
echo "  examples/output/basic/        - 基本的な記法のサンプル"
echo "  examples/output/advanced/     - 高度な記法のサンプル"
echo "  examples/output/showcase/     - 全機能のショーケース"
echo ""
echo -e "${YELLOW}🌐 HTMLファイルをブラウザで確認してください${NC}"
echo ""
echo "📁 出力フォルダを開きますか？ [y/N]"
read -n 1 choice
echo ""
if [[ $choice =~ ^[Yy]$ ]]; then
    open "$OUTPUT_BASE"
fi

echo ""
echo "何かキーを押して終了してください..."
read -n 1