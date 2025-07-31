#!/bin/bash

# =============================================================================
# Claude Code + Serena MCP Server 起動スクリプト (macOS)
# =============================================================================
# 
# このスクリプトは Kumihan-Formatter プロジェクト用に Claude Code を
# Serena MCP Server と組み合わせて起動します。
#
# 使用方法:
#   ./start-claude-serena.sh
#
# 必要な前提条件:
#   - Claude Code CLI がインストール済み
#   - uv がインストール済み (pip install uv)
#   - インターネット接続
#
# =============================================================================

set -euo pipefail

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# プロジェクトルートディレクトリ
PROJECT_ROOT="/Users/m2_macbookair_3911/GitHub/Kumihan-Formatter"

# スクリプトの開始
log_info "Claude Code + Serena MCP Server 起動スクリプト開始"
echo "========================================================"
echo "プロジェクト: Kumihan-Formatter"
echo "ディレクトリ: ${PROJECT_ROOT}"
echo "========================================================"

# プロジェクトディレクトリに移動
if [ ! -d "${PROJECT_ROOT}" ]; then
    log_error "プロジェクトディレクトリが見つかりません: ${PROJECT_ROOT}"
    exit 1
fi

log_info "プロジェクトディレクトリに移動: ${PROJECT_ROOT}"
cd "${PROJECT_ROOT}"

# 必要なコマンドの存在確認
log_info "必要なコマンドの確認..."

if ! command -v claude &> /dev/null; then
    log_error "Claude Code CLI が見つかりません"
    log_info "インストール方法: https://docs.anthropic.com/claude-code"
    exit 1
fi

if ! command -v uv &> /dev/null; then
    log_error "uv が見つかりません"
    log_info "インストール方法: pip install uv"
    exit 1
fi

log_success "必要なコマンドが確認できました"

# Serena MCP Server の準備
log_info "Serena MCP Server を準備中..."
log_info "実行コマンド: uvx --from git+https://github.com/oraios/serena serena-mcp-server --context ide-assistant --project ${PROJECT_ROOT}"

# Claude Code の起動
log_info "Claude Code を Serena MCP Server と組み合わせて起動中..."

# Serena MCP Server をバックグラウンドで起動し、Claude Code を起動
exec uvx --from git+https://github.com/oraios/serena serena-mcp-server \
    --context ide-assistant \
    --project "${PROJECT_ROOT}"