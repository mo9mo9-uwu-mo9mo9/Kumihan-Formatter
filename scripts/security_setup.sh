#!/bin/bash
# セキュリティ対応（コード署名・公証）スクリプト
# Apple Developer Program登録が必要

set -e

echo "================================"
echo "Kumihan Formatter セキュリティ対応"
echo "================================"

# カラー定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

# プロジェクトルートディレクトリ
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# 設定（環境変数で上書き可能）
APP_PATH="${APP_PATH:-dist/Kumihan Formatter.app}"
DMG_PATH="${DMG_PATH:-dist/KumihanFormatter-1.0.0.dmg}"
DEVELOPER_ID="${DEVELOPER_ID:-Developer ID Application: Your Name (TEAMID)}"
APPLE_ID="${APPLE_ID:-your@email.com}"
TEAM_ID="${TEAM_ID:-YOURTEAMID}"

# 前提条件チェック
echo "前提条件をチェックしています..."

# Apple Developer Programの確認
if ! security find-identity -p codesigning -v | grep -q "Developer ID Application"; then
    echo -e "${RED}エラー: Developer ID Application証明書が見つかりません${NC}"
    echo "Apple Developer Programに登録し、証明書をインストールしてください。"
    echo ""
    echo "手順:"
    echo "1. Apple Developer Program (https://developer.apple.com/programs/) に登録"
    echo "2. Certificates, Identifiers & Profiles で Developer ID Certificate を作成"
    echo "3. Keychain Access で証明書をインストール"
    exit 1
fi

# .appファイルの存在確認
if [ ! -d "$APP_PATH" ]; then
    echo -e "${RED}エラー: アプリケーションが見つかりません: $APP_PATH${NC}"
    echo "先にビルドを実行してください: ./scripts/build_macos.sh"
    exit 1
fi

echo -e "${GREEN}前提条件OK${NC}"

# ステップ1: アプリケーションのコード署名
echo ""
echo "ステップ1: アプリケーションのコード署名"
echo "=========================================="

echo "利用可能な証明書:"
security find-identity -p codesigning -v

echo ""
echo -e "${YELLOW}使用する証明書ID（上記リストから選択）: ${NC}"
read -r CERT_ID

if [ -z "$CERT_ID" ]; then
    echo -e "${RED}証明書IDが指定されていません${NC}"
    exit 1
fi

echo "アプリケーションに署名しています..."
codesign --sign "$CERT_ID" \
    --force \
    --verbose \
    --options runtime \
    --timestamp \
    --deep \
    "$APP_PATH"

# 署名の確認
echo "署名を確認しています..."
codesign --verify --verbose "$APP_PATH"
echo -e "${GREEN}アプリケーションの署名完了${NC}"

# ステップ2: DMGファイルの作成と署名
echo ""
echo "ステップ2: DMGファイルの署名"
echo "=========================="

if [ -f "$DMG_PATH" ]; then
    echo "DMGファイルに署名しています..."
    codesign --sign "$CERT_ID" \
        --force \
        --verbose \
        --timestamp \
        "$DMG_PATH"

    # 署名の確認
    echo "DMG署名を確認しています..."
    codesign --verify --verbose "$DMG_PATH"
    echo -e "${GREEN}DMGファイルの署名完了${NC}"
else
    echo -e "${YELLOW}警告: DMGファイルが見つかりません: $DMG_PATH${NC}"
    echo "DMGを作成してから署名してください。"
fi

# ステップ3: 公証（Notarization）
echo ""
echo "ステップ3: Apple公証サービスへの送信"
echo "================================="

echo -e "${YELLOW}Apple IDとTeam IDを入力してください:${NC}"
echo "Apple ID (例: your@email.com): "
read -r APPLE_ID_INPUT
echo "Team ID (例: ABCD123456): "
read -r TEAM_ID_INPUT

if [ -n "$APPLE_ID_INPUT" ]; then
    APPLE_ID="$APPLE_ID_INPUT"
fi
if [ -n "$TEAM_ID_INPUT" ]; then
    TEAM_ID="$TEAM_ID_INPUT"
fi

# 公証の実行（DMGがある場合）
if [ -f "$DMG_PATH" ]; then
    echo "DMGファイルを公証サービスに送信しています..."
    echo "（この処理には数分から数十分かかる場合があります）"

    # 実際の公証コマンド（ユーザーが実行）
    echo ""
    echo -e "${YELLOW}以下のコマンドを実行してください:${NC}"
    echo "xcrun notarytool submit \"$DMG_PATH\" \\"
    echo "    --apple-id \"$APPLE_ID\" \\"
    echo "    --team-id \"$TEAM_ID\" \\"
    echo "    --wait"
    echo ""
    echo "公証が完了したら、以下のコマンドでステープル:"
    echo "xcrun stapler staple \"$DMG_PATH\""
else
    echo "公証するDMGファイルがありません。"
fi

# ステップ4: 最終確認
echo ""
echo "ステップ4: 最終確認"
echo "================="

echo "署名されたファイル:"
if [ -d "$APP_PATH" ]; then
    echo "- $APP_PATH"
    codesign -dv "$APP_PATH" 2>&1 | grep "Authority="
fi

if [ -f "$DMG_PATH" ]; then
    echo "- $DMG_PATH"
    codesign -dv "$DMG_PATH" 2>&1 | grep "Authority=" || echo "  （署名なし）"
fi

echo ""
echo -e "${GREEN}セキュリティ対応の準備完了${NC}"
echo ""
echo "次のステップ:"
echo "1. 公証コマンドを実行"
echo "2. 公証完了後、stapleコマンドを実行"
echo "3. 配布用ファイルの動作確認"
echo ""
echo "参考資料:"
echo "- Apple Developer Documentation: Notarizing macOS Software"
echo "- https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution"
