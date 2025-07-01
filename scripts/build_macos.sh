#!/bin/bash
# macOS向けビルドスクリプト
# Kumihan Formatter .app形式のビルド

set -e  # エラーで停止

echo "================================"
echo "Kumihan Formatter macOS Build"
echo "================================"

# カラー定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# プロジェクトルートディレクトリ
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo -e "${GREEN}プロジェクトルート: $PROJECT_ROOT${NC}"

# 仮想環境のチェック
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}仮想環境が見つかりません。作成します...${NC}"
    python3 -m venv venv
fi

# 仮想環境の有効化
echo "仮想環境を有効化しています..."
source venv/bin/activate

# 依存関係のインストール
echo "依存関係をインストールしています..."
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# アイコンファイルの確認
ICON_PATH="$PROJECT_ROOT/assets/icon.icns"
if [ ! -f "$ICON_PATH" ]; then
    echo -e "${YELLOW}警告: アイコンファイルが見つかりません: $ICON_PATH${NC}"
    echo "デフォルトアイコンを使用します。"
fi

# ビルドディレクトリのクリーンアップ
echo "ビルドディレクトリをクリーンアップしています..."
rm -rf build/ dist/

# PyInstallerでビルド
echo -e "${GREEN}ビルドを開始します...${NC}"
pyinstaller --clean pyinstaller/kumihan_formatter_macos.spec

# ビルド成功チェック
if [ -d "dist/Kumihan Formatter.app" ]; then
    echo -e "${GREEN}ビルド成功！${NC}"
    echo "アプリケーション: dist/Kumihan Formatter.app"

    # アプリケーションの情報を表示
    echo ""
    echo "アプリケーション情報:"
    defaults read "$PROJECT_ROOT/dist/Kumihan Formatter.app/Contents/Info.plist" CFBundleShortVersionString 2>/dev/null || echo "バージョン: 1.0.0"

    # ファイルサイズ
    APP_SIZE=$(du -sh "dist/Kumihan Formatter.app" | cut -f1)
    echo "サイズ: $APP_SIZE"

    # DMG作成の提案
    echo ""
    echo -e "${YELLOW}DMGファイルを作成しますか？ (y/n)${NC}"
    read -r CREATE_DMG

    if [ "$CREATE_DMG" = "y" ]; then
        ./scripts/create_dmg.sh
    fi
else
    echo -e "${RED}ビルド失敗！${NC}"
    echo "ログを確認してください: build/*/warn-*.txt"
    exit 1
fi

echo ""
echo "================================"
echo "ビルド完了"
echo "================================"
