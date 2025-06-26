#!/bin/bash

# macOS用 Kumihan記法構文チェッカー
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
echo " Kumihan-Formatter - Syntax Checker"
echo "=========================================="
echo "Kumihan記法の構文をチェックします"
echo "ドラッグ&ドロップでファイルを指定できます"
echo "=========================================="
echo ""

# Pythonのバージョン確認
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[エラー] Python 3 が見つかりません${NC}"
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
    echo -e "${RED}[警告] 仮想環境が見つかりません${NC}"
    echo -e "${YELLOW}[ヒント] サンプル実行.command を先に実行してセットアップを完了してください${NC}"
    echo ""
    echo "何かキーを押して終了してください..."
    read -n 1
    exit 1
fi

# 依存関係の確認
if ! $PYTHON_CMD -c "import click, jinja2, rich" 2>/dev/null; then
    echo -e "${RED}[エラー] 必要なライブラリが不足しています${NC}"
    echo -e "${YELLOW}[ヒント] サンプル実行.command を先に実行してセットアップを完了してください${NC}"
    echo ""
    echo "何かキーを押して終了してください..."
    read -n 1
    exit 1
fi

# 関数定義
function interactive_mode() {
    echo -e "${CYAN}[対話モード] ファイルまたはフォルダを指定してください${NC}"
    echo ""
    echo "使用方法:"
    echo "  1. ファイルパス入力: 例) example.txt"
    echo "  2. フォルダパス入力: 例) examples"
    echo "  3. ワイルドカード: 例) *.txt"
    echo "  4. 空白で区切って複数指定可能"
    echo ""
    
    read -p "チェックするファイル/フォルダ: " INPUT
    
    if [ -z "$INPUT" ]; then
        echo -e "${YELLOW}[情報] ファイルが指定されませんでした${NC}"
        return
    fi
    
    # 再帰検索の確認
    read -p "フォルダを再帰的に検索しますか？ [Y/n]: " RECURSIVE
    if [[ $RECURSIVE =~ ^[Nn]$ ]]; then
        RECURSIVE_FLAG=""
    else
        RECURSIVE_FLAG="-r"
    fi
    
    # 修正提案の確認
    read -p "修正提案を表示しますか？ [Y/n]: " SUGGESTIONS
    if [[ $SUGGESTIONS =~ ^[Nn]$ ]]; then
        SUGGESTIONS_FLAG="--no-suggestions"
    else
        SUGGESTIONS_FLAG=""
    fi
    
    echo ""
    echo -e "${CYAN}[実行] 構文チェックを開始します...${NC}"
    $PYTHON_CMD -m kumihan_formatter check-syntax $INPUT $RECURSIVE_FLAG $SUGGESTIONS_FLAG
}

function check_files() {
    echo -e "${CYAN}[実行] 指定されたファイルをチェックします...${NC}"
    echo "ファイル: $*"
    echo ""
    
    # ドラッグ&ドロップされたファイルの処理
    $PYTHON_CMD -m kumihan_formatter check-syntax "$@" -r
}

echo -e "${GREEN}[完了] 環境確認完了${NC}"
echo ""

# 引数の処理
if [ $# -eq 0 ]; then
    # ファイル指定なし - 対話モード
    interactive_mode
else
    # ファイル指定あり - 直接チェック
    check_files "$@"
fi

echo ""
echo "何かキーを押して終了してください..."
read -n 1