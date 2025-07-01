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
echo "Output: ../dist/samples/"
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
if [ -d "$OUTPUT_BASE" ]; then
    # ファイルやディレクトリの存在をチェック
    shopt -s nullglob
    files=("$OUTPUT_BASE"/*)
    shopt -u nullglob
    
    if [ ${#files[@]} -gt 0 ]; then
        echo -e "${YELLOW}[警告]  警告: 出力ディレクトリ内にファイルが存在します${NC}"
        echo -e "${YELLOW}   以下のファイルが上書きされます:${NC}"
        echo ""
        for file in "${files[@]}"; do
            echo -e "${YELLOW}     - $(basename "$file")${NC}"
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
fi

mkdir -p "$OUTPUT_BASE"

echo -e "${CYAN}サンプル変換を開始します...${NC}"
echo -e "${CYAN}出力先: ../dist/samples/ (自動作成されます)${NC}"
echo ""

# 記法表示機能の選択を事前に確認
echo -e "${CYAN}Kumihan記法をHTML表示に切り替える機能があります${NC}"
echo -e "${CYAN}記法学習に便利な機能で、ボタン一つで記法とプレビューが切り替えられます${NC}"
echo -n "この機能を使用しますか？ (Y/n): "
read -n 1 choice
echo ""
echo ""

# 選択に基づいてフラグを設定
if [[ $choice =~ ^[Yy]$ ]] || [ -z "$choice" ]; then
    SOURCE_TOGGLE_FLAG="--include-source"
    echo -e "${GREEN}Kumihan記法切り替え機能を有効にして変換します${NC}"
else
    SOURCE_TOGGLE_FLAG=""
    echo -e "${YELLOW}通常モードで変換します（記法切り替え機能なし）${NC}"
fi
echo ""

# サンプル1: quickstart
echo -e "${BLUE}[1/4] クイックスタートサンプル (01-quickstart.txt)${NC}"
OUTPUT_DIR="$OUTPUT_BASE/01-quickstart"
mkdir -p "$OUTPUT_DIR"

if $PYTHON_CMD -m kumihan_formatter convert "../examples/01-quickstart.txt" -o "$OUTPUT_DIR" --no-preview $SOURCE_TOGGLE_FLAG; then
    echo -e "${GREEN}quickstart サンプル完了 → $OUTPUT_DIR${NC}"
else
    echo -e "${RED}エラー: quickstart サンプルの変換に失敗${NC}"
    exit 1
fi
echo ""

# サンプル2: basic
echo -e "${BLUE}[2/4] 基本サンプル (02-basic.txt)${NC}"
OUTPUT_DIR="$OUTPUT_BASE/02-basic"
mkdir -p "$OUTPUT_DIR"

if $PYTHON_CMD -m kumihan_formatter convert "../examples/02-basic.txt" -o "$OUTPUT_DIR" --no-preview $SOURCE_TOGGLE_FLAG; then
    echo -e "${GREEN}basic サンプル完了 → $OUTPUT_DIR${NC}"
else
    echo -e "${RED}エラー: basic サンプルの変換に失敗${NC}"
    exit 1
fi
echo ""

# サンプル3: advanced
echo -e "${BLUE}[3/4] 高度なサンプル (03-comprehensive.txt)${NC}"
OUTPUT_DIR="$OUTPUT_BASE/03-advanced"
mkdir -p "$OUTPUT_DIR"

if $PYTHON_CMD -m kumihan_formatter convert "../examples/03-comprehensive.txt" -o "$OUTPUT_DIR" --no-preview $SOURCE_TOGGLE_FLAG; then
    echo -e "${GREEN}advanced サンプル完了 → $OUTPUT_DIR${NC}"
else
    echo -e "${RED}エラー: advanced サンプルの変換に失敗${NC}"
    exit 1
fi
echo ""

# サンプル4: showcase
echo -e "${BLUE}[4/12] 機能ショーケース (generate-sample)${NC}"
OUTPUT_DIR="$OUTPUT_BASE/04-showcase"
mkdir -p "$OUTPUT_DIR"

# Showcaseサンプルは記法表示機能を使用しない（CLAUDE.md仕様）
if $PYTHON_CMD -m kumihan_formatter generate-sample -o "$OUTPUT_DIR" --quiet; then
    echo -e "${GREEN}showcase サンプル完了 → $OUTPUT_DIR${NC}"
else
    echo -e "${RED}エラー: showcase サンプルの変換に失敗${NC}"
    exit 1
fi
echo ""

# === 🆕 実践的サンプル集 ===
echo -e "${CYAN}=== 🎲 CoC6th実践的サンプル集 ===${NC}"
echo ""

# サンプル5: 基本シナリオテンプレート
echo -e "${BLUE}[5/12] 基本シナリオテンプレート (templates/basic-scenario.txt)${NC}"
OUTPUT_DIR="$OUTPUT_BASE/05-basic-scenario"
mkdir -p "$OUTPUT_DIR"
if $PYTHON_CMD -m kumihan_formatter convert "../examples/templates/basic-scenario.txt" -o "$OUTPUT_DIR" --no-preview $SOURCE_TOGGLE_FLAG; then
    echo -e "${GREEN}基本シナリオテンプレート完了 → $OUTPUT_DIR${NC}"
else
    echo -e "${RED}エラー: 基本シナリオテンプレートの変換に失敗${NC}"
    exit 1
fi
echo ""

# サンプル6: クローズド型シナリオテンプレート
echo -e "${BLUE}[6/12] クローズド型シナリオテンプレート (templates/closed-scenario.txt)${NC}"
OUTPUT_DIR="$OUTPUT_BASE/06-closed-scenario"
mkdir -p "$OUTPUT_DIR"
if $PYTHON_CMD -m kumihan_formatter convert "../examples/templates/closed-scenario.txt" -o "$OUTPUT_DIR" --no-preview $SOURCE_TOGGLE_FLAG; then
    echo -e "${GREEN}クローズド型テンプレート完了 → $OUTPUT_DIR${NC}"
else
    echo -e "${RED}エラー: クローズド型テンプレートの変換に失敗${NC}"
    exit 1
fi
echo ""

# サンプル7: シティ型シナリオテンプレート
echo -e "${BLUE}[7/12] シティ型シナリオテンプレート (templates/city-scenario.txt)${NC}"
OUTPUT_DIR="$OUTPUT_BASE/07-city-scenario"
mkdir -p "$OUTPUT_DIR"
if $PYTHON_CMD -m kumihan_formatter convert "../examples/templates/city-scenario.txt" -o "$OUTPUT_DIR" --no-preview $SOURCE_TOGGLE_FLAG; then
    echo -e "${GREEN}シティ型テンプレート完了 → $OUTPUT_DIR${NC}"
else
    echo -e "${RED}エラー: シティ型テンプレートの変換に失敗${NC}"
    exit 1
fi
echo ""

# サンプル8: 戦闘重視型シナリオテンプレート
echo -e "${BLUE}[8/12] 戦闘重視型シナリオテンプレート (templates/combat-scenario.txt)${NC}"
OUTPUT_DIR="$OUTPUT_BASE/08-combat-scenario"
mkdir -p "$OUTPUT_DIR"
if $PYTHON_CMD -m kumihan_formatter convert "../examples/templates/combat-scenario.txt" -o "$OUTPUT_DIR" --no-preview $SOURCE_TOGGLE_FLAG; then
    echo -e "${GREEN}戦闘重視型テンプレート完了 → $OUTPUT_DIR${NC}"
else
    echo -e "${RED}エラー: 戦闘重視型テンプレートの変換に失敗${NC}"
    exit 1
fi
echo ""

# サンプル9: NPCテンプレート
echo -e "${BLUE}[9/12] NPCテンプレート (elements/npc-template.txt)${NC}"
OUTPUT_DIR="$OUTPUT_BASE/09-npc-template"
mkdir -p "$OUTPUT_DIR"
if $PYTHON_CMD -m kumihan_formatter convert "../examples/elements/npc-template.txt" -o "$OUTPUT_DIR" --no-preview $SOURCE_TOGGLE_FLAG; then
    echo -e "${GREEN}NPCテンプレート完了 → $OUTPUT_DIR${NC}"
else
    echo -e "${RED}エラー: NPCテンプレートの変換に失敗${NC}"
    exit 1
fi
echo ""

# サンプル10: アイテム・クリーチャーテンプレート
echo -e "${BLUE}[10/12] アイテム・クリーチャーテンプレート (elements/item-template.txt)${NC}"
OUTPUT_DIR="$OUTPUT_BASE/10-item-template"
mkdir -p "$OUTPUT_DIR"
if $PYTHON_CMD -m kumihan_formatter convert "../examples/elements/item-template.txt" -o "$OUTPUT_DIR" --no-preview $SOURCE_TOGGLE_FLAG; then
    echo -e "${GREEN}アイテムテンプレート完了 → $OUTPUT_DIR${NC}"
else
    echo -e "${RED}エラー: アイテムテンプレートの変換に失敗${NC}"
    exit 1
fi
echo ""

# サンプル11: 技能ロールテンプレート
echo -e "${BLUE}[11/12] 技能ロールテンプレート (elements/skill-template.txt)${NC}"
OUTPUT_DIR="$OUTPUT_BASE/11-skill-template"
mkdir -p "$OUTPUT_DIR"
if $PYTHON_CMD -m kumihan_formatter convert "../examples/elements/skill-template.txt" -o "$OUTPUT_DIR" --no-preview $SOURCE_TOGGLE_FLAG; then
    echo -e "${GREEN}技能ロールテンプレート完了 → $OUTPUT_DIR${NC}"
else
    echo -e "${RED}エラー: 技能ロールテンプレートの変換に失敗${NC}"
    exit 1
fi
echo ""

# サンプル12: 完成版サンプルシナリオ「深夜図書館の怪」
echo -e "${BLUE}[12/12] 完成版サンプルシナリオ「深夜図書館の怪」 (showcase/complete-scenario.txt)${NC}"
OUTPUT_DIR="$OUTPUT_BASE/12-complete-scenario"
mkdir -p "$OUTPUT_DIR"
if $PYTHON_CMD -m kumihan_formatter convert "../examples/showcase/complete-scenario.txt" -o "$OUTPUT_DIR" --no-preview $SOURCE_TOGGLE_FLAG; then
    echo -e "${GREEN}完成版シナリオ完了 → $OUTPUT_DIR${NC}"
else
    echo -e "${RED}エラー: 完成版シナリオの変換に失敗${NC}"
    exit 1
fi
echo ""

echo "=========================================="
echo -e "${GREEN}全サンプルの変換が完了しました！${NC}"
echo "=========================================="
echo ""
echo -e "${CYAN}生成されたファイル:${NC}"
echo ""
echo -e "${YELLOW}📚 学習用サンプル${NC}"
echo "  01-quickstart/   - クイックスタートチュートリアル"
echo "  02-basic/        - 基本的な記法のサンプル"
echo "  03-advanced/     - 高度な記法のサンプル"
echo "  04-showcase/     - 全機能のショーケース"
echo ""
echo -e "${YELLOW}🎲 CoC6th実践用テンプレート${NC}"
echo "  05-basic-scenario/    - 基本シナリオテンプレート"
echo "  06-closed-scenario/   - クローズド型シナリオテンプレート"
echo "  07-city-scenario/     - シティ型シナリオテンプレート"
echo "  08-combat-scenario/   - 戦闘重視型シナリオテンプレート"
echo "  09-npc-template/      - NPCテンプレート"
echo "  10-item-template/     - アイテム・クリーチャーテンプレート"
echo "  11-skill-template/    - 技能ロールテンプレート"
echo "  12-complete-scenario/ - 完成版サンプルシナリオ「深夜図書館の怪」"
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