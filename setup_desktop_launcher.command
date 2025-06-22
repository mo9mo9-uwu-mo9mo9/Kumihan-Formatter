#!/bin/bash

# macOS用 Kumihan-Formatter デスクトップセットアップ
# ダブルクリックで実行可能

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

# 色付き出力の設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo ""
echo "============================================"
echo " Kumihan-Formatter プロジェクト内セットアップ"
echo "============================================"
echo ""

# 現在のディレクトリを取得
CURRENT_DIR="$(pwd)"
echo -e "${BLUE}📁 現在のディレクトリ: $CURRENT_DIR${NC}"
echo ""

# コマンドファイルの存在確認
if [ ! -f "kumihan_convert.command" ]; then
    echo -e "${RED}❌ エラー: kumihan_convert.command が見つかりません${NC}"
    echo "   このセットアップスクリプトをKumihan-Formatterフォルダ内で実行してください"
    echo ""
    echo "何かキーを押して終了してください..."
    read -n 1
    exit 1
fi

echo -e "${YELLOW}🔧 プロジェクト内にエイリアスを作成しています...${NC}"

# プロジェクトディレクトリを設定
PROJECT_DIR="$CURRENT_DIR"

# エイリアスを作成
if ln -sf "$CURRENT_DIR/kumihan_convert.command" "$PROJECT_DIR/Kumihan-Formatter.command" 2>/dev/null; then
    echo -e "${GREEN}✅ エイリアスを作成しました！${NC}"
    echo -e "${CYAN}📍 場所: $PROJECT_DIR/Kumihan-Formatter.command${NC}"
    echo ""
    echo -e "${GREEN}🎉 セットアップ完了！${NC}"
    echo ""
    echo -e "${BLUE}📝 使い方:${NC}"
    echo "   1. プロジェクト内の「Kumihan-Formatter.command」をダブルクリック"
    echo "   2. .txtファイルをドラッグ&ドロップするか、パスを入力"
    echo "   3. 自動的にHTMLに変換されます"
    echo ""
    echo -e "${CYAN}💡 ヒント:${NC}"
    echo "   - .txtファイルを直接エイリアスにドラッグ&ドロップも可能です"
    echo "   - プロジェクト内実行のため「./dist/」に出力されます"
    echo "   - 初回実行時にセキュリティ警告が表示される場合があります"
    echo ""
    echo -e "${YELLOW}⚠️ セキュリティ設定について:${NC}"
    echo "   初回実行時に「開発者を確認できないため開けません」と表示された場合："
    echo "   1. システム設定 > プライバシーとセキュリティ"
    echo "   2. 「このまま開く」をクリック"
    echo "   または、右クリック > 開く で実行してください"
else
    echo -e "${RED}❌ エイリアスの作成に失敗しました${NC}"
    echo "   手動でプロジェクト内にエイリアスを作成してください"
    echo ""
    echo -e "${CYAN}手動作成方法:${NC}"
    echo "   1. Finderでこのフォルダを開く"
    echo "   2. kumihan_convert.command を右クリック"
    echo "   3. 「エイリアスを作成」を選択"
    echo "   4. 作成されたエイリアスをこのフォルダ内に配置"
fi

echo ""
echo "何かキーを押して終了してください..."
read -n 1