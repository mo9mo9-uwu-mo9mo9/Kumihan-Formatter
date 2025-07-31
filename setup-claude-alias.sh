#!/bin/bash

# =============================================================================
# Claude Code + Serena MCP Server エイリアス設定スクリプト (macOS)
# =============================================================================
# 
# このスクリプトは Claude Code + Serena の起動エイリアスを設定します。
#
# 使用方法:
#   ./setup-claude-alias.sh
#
# 設定後の使用方法:
#   claude-kumihan  # プロジェクトディレクトリでClaude + Serena起動
#
# =============================================================================

set -euo pipefail

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ログ関数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo -e "${CYAN}$1${NC}"
}

# プロジェクトルートディレクトリ
PROJECT_ROOT="/Users/m2_macbookair_3911/GitHub/Kumihan-Formatter"

# スクリプトの開始
clear
log_header "========================================================"
log_header "🔧 Claude Code + Serena エイリアス設定"
log_header "========================================================"
echo
log_info "プロジェクト: Kumihan-Formatter"
log_info "ディレクトリ: ${PROJECT_ROOT}"
echo

# シェル検出
SHELL_NAME=$(basename "$SHELL")
case "$SHELL_NAME" in
    bash)
        RC_FILE="$HOME/.bashrc"
        PROFILE_FILE="$HOME/.bash_profile"
        ;;
    zsh)
        RC_FILE="$HOME/.zshrc"
        PROFILE_FILE="$HOME/.zprofile"
        ;;
    fish)
        RC_FILE="$HOME/.config/fish/config.fish"
        PROFILE_FILE="$HOME/.config/fish/config.fish"
        ;;
    *)
        log_warning "未知のシェル: $SHELL_NAME"
        log_info "手動で設定してください"
        RC_FILE="$HOME/.profile"
        PROFILE_FILE="$HOME/.profile"
        ;;
esac

log_info "検出されたシェル: $SHELL_NAME"
log_info "設定ファイル: $RC_FILE"
echo

# エイリアス定義
ALIAS_NAME="claude-kumihan"
ALIAS_COMMAND="cd '$PROJECT_ROOT' && ./start-claude-with-serena.sh"

# 既存のエイリアスをチェック
if grep -q "alias $ALIAS_NAME" "$RC_FILE" 2>/dev/null; then
    log_warning "エイリアス '$ALIAS_NAME' は既に存在します"
    read -p "上書きしますか？ (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "設定をキャンセルしました"
        exit 0
    fi
    
    # 既存のエイリアスを削除
    sed -i.bak "/alias $ALIAS_NAME/d" "$RC_FILE"
    log_info "既存のエイリアスを削除しました"
fi

# エイリアスを追加
echo "" >> "$RC_FILE"
echo "# Kumihan-Formatter Claude Code + Serena 起動エイリアス" >> "$RC_FILE"
echo "alias $ALIAS_NAME='$ALIAS_COMMAND'" >> "$RC_FILE"

log_success "エイリアスを設定しました！"
echo

# 設定情報表示
log_header "📋 設定完了情報"
echo "  🔗 エイリアス名: $ALIAS_NAME"
echo "  📁 プロジェクト: $PROJECT_ROOT"
echo "  ⚙️  設定ファイル: $RC_FILE"
echo

log_header "🚀 使用方法"
echo "  1. 新しいターミナルを開く、または次を実行:"
echo "     source $RC_FILE"
echo ""
echo "  2. どこからでも次のコマンドで起動:"
echo "     $ALIAS_NAME"
echo ""
echo "  3. エイリアスが正しく設定されているか確認:"
echo "     which $ALIAS_NAME"
echo

log_header "💡 ヒント"
echo "  • エイリアスは現在のターミナルセッションでは即座に有効になりません"
echo "  • 新しいターミナルタブ/ウィンドウで使用してください"
echo "  • または 'source $RC_FILE' を実行してください"
echo

log_success "設定が完了しました！"

# 現在のセッションでエイリアスを有効化
log_info "現在のセッションでエイリアスを有効化中..."
source "$RC_FILE" 2>/dev/null || true

# テスト
if command -v "$ALIAS_NAME" &> /dev/null; then
    log_success "✅ エイリアス '$ALIAS_NAME' が正常に設定されました"
else
    log_warning "⚠️  エイリアスは設定されましたが、現在のセッションでは認識されていません"
    log_info "新しいターミナルセッションで使用してください"
fi