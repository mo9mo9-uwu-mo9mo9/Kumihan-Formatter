#!/bin/bash
# DMGファイル作成スクリプト
# Kumihan Formatter .appをDMG形式でパッケージ

set -e  # エラーで停止

echo "================================"
echo "DMG Creation for Kumihan Formatter"
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

# 設定
APP_NAME="Kumihan Formatter"
APP_PATH="dist/${APP_NAME}.app"
DMG_NAME="KumihanFormatter-1.0.0"
DMG_PATH="dist/${DMG_NAME}.dmg"
VOLUME_NAME="Kumihan Formatter"

# .appファイルの存在確認
if [ ! -d "$APP_PATH" ]; then
    echo -e "${RED}エラー: アプリケーションが見つかりません: $APP_PATH${NC}"
    echo "先にビルドを実行してください: ./scripts/build_macos.sh"
    exit 1
fi

# 既存のDMGファイルを削除
if [ -f "$DMG_PATH" ]; then
    echo "既存のDMGファイルを削除しています..."
    rm -f "$DMG_PATH"
fi

# 一時ディレクトリの作成
echo "一時ディレクトリを作成しています..."
DMG_TEMP="dist/dmg_temp"
rm -rf "$DMG_TEMP"
mkdir -p "$DMG_TEMP"

# アプリケーションのコピー
echo "アプリケーションをコピーしています..."
cp -R "$APP_PATH" "$DMG_TEMP/"

# Applications フォルダへのシンボリックリンク作成
ln -s /Applications "$DMG_TEMP/Applications"

# DMGの背景ディレクトリ作成（将来の拡張用）
mkdir -p "$DMG_TEMP/.background"

# .DS_Storeファイルの設定（アイコン配置）
# 注: 実際のプロダクションでは、カスタムレイアウトツールを使用

# DMGの作成
echo -e "${GREEN}DMGファイルを作成しています...${NC}"

# hdiutilを使用してDMGを作成
hdiutil create -volname "$VOLUME_NAME" \
    -srcfolder "$DMG_TEMP" \
    -ov \
    -format UDZO \
    "$DMG_PATH"

# クリーンアップ
echo "一時ファイルをクリーンアップしています..."
rm -rf "$DMG_TEMP"

# 結果の確認
if [ -f "$DMG_PATH" ]; then
    echo -e "${GREEN}DMG作成成功！${NC}"
    echo "ファイル: $DMG_PATH"

    # ファイルサイズ
    DMG_SIZE=$(du -sh "$DMG_PATH" | cut -f1)
    echo "サイズ: $DMG_SIZE"

    # ハッシュ値の計算
    echo ""
    echo "SHA256:"
    shasum -a 256 "$DMG_PATH" | cut -d' ' -f1

    echo ""
    echo -e "${YELLOW}配布準備の推奨事項:${NC}"
    echo "1. DMGファイルに署名（codesign）"
    echo "2. 公証（notarization）の実行"
    echo "3. ステープル（staple）の追加"
    echo ""
    echo "署名コマンド例:"
    echo "codesign --sign \"Developer ID Application: Your Name\" \"$DMG_PATH\""
    echo ""
    echo "公証コマンド例:"
    echo "xcrun notarytool submit \"$DMG_PATH\" --apple-id your@email.com --team-id TEAMID --wait"
else
    echo -e "${RED}DMG作成失敗！${NC}"
    exit 1
fi

echo ""
echo "================================"
echo "DMG作成完了"
echo "================================"
