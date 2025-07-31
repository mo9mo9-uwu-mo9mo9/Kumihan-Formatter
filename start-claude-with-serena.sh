#!/bin/bash

# =============================================================================
# Claude Code + Serena MCP Server 統合起動スクリプト (macOS)
# =============================================================================
# 
# このスクリプトは Kumihan-Formatter プロジェクト用に Claude Code を
# Serena MCP Server と組み合わせて統合起動します。
#
# 使用方法:
#   ./start-claude-with-serena.sh
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

# クリーンアップ関数
cleanup() {
    log_info "クリーンアップ中..."
    # バックグラウンドプロセスを終了
    jobs -p | xargs -r kill 2>/dev/null || true
    exit 0
}

# シグナルハンドラー設定
trap cleanup SIGINT SIGTERM

# スクリプトの開始
clear
log_header "========================================================"
log_header "🤖 Claude Code + Serena MCP Server 統合起動"
log_header "========================================================"
echo
log_info "プロジェクト: Kumihan-Formatter"
log_info "ディレクトリ: ${PROJECT_ROOT}"
log_info "統合モード: Claude Code CLI + Serena MCP Server"
echo

# プロジェクトディレクトリに移動
if [ ! -d "${PROJECT_ROOT}" ]; then
    log_error "プロジェクトディレクトリが見つかりません: ${PROJECT_ROOT}"
    exit 1
fi

log_info "プロジェクトディレクトリに移動中..."
cd "${PROJECT_ROOT}"

# 必要なコマンドの存在確認
log_info "依存関係の確認中..."

if ! command -v claude &> /dev/null; then
    log_error "Claude Code CLI が見つかりません"
    echo "  📖 インストール方法: https://docs.anthropic.com/claude-code"
    exit 1
fi

if ! command -v uv &> /dev/null; then
    log_error "uv が見つかりません"
    echo "  📖 インストール方法: pip install uv"
    exit 1
fi

if ! command -v uvx &> /dev/null; then
    log_error "uvx が見つかりません (uv の一部)"
    echo "  📖 uv を最新版に更新してください: pip install -U uv"
    exit 1
fi

log_success "すべての依存関係が確認できました"
echo

# Serena MCP Server の情報表示
log_info "Serena MCP Server 設定:"
echo "  🔗 リポジトリ: https://github.com/oraios/serena"
echo "  🎯 コンテキスト: ide-assistant"
echo "  📁 プロジェクト: ${PROJECT_ROOT}"
echo

# 起動確認
log_warning "Claude Code を Serena MCP Server と統合起動します"
echo "  ⚠️  初回起動時は Serena のダウンロードに時間がかかる場合があります"
echo "  ⚠️  終了するには Ctrl+C を押してください"
echo

read -p "続行しますか？ (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "起動をキャンセルしました"
    exit 0
fi

echo
log_header "🚀 起動中..."
echo

# MCP Server設定用の一時ファイル作成
MCP_CONFIG_FILE=$(mktemp)
cat > "${MCP_CONFIG_FILE}" << EOF
{
  "mcpServers": {
    "serena": {
      "command": "uvx",
      "args": [
        "--from", 
        "git+https://github.com/oraios/serena",
        "serena-mcp-server",
        "--context",
        "ide-assistant",
        "--project",
        "${PROJECT_ROOT}"
      ]
    }
  }
}
EOF

log_info "MCP設定ファイルを作成しました: ${MCP_CONFIG_FILE}"

# Claude Code をMCP Serverと起動
log_info "Claude Code + Serena MCP Server を起動中..."
log_success "🎉 統合環境が開始されました！"
echo
echo "💡 使用可能な Serena ツール:"
echo "  📝 mcp__serena__find_symbol - シンボル検索"
echo "  🔍 mcp__serena__search_for_pattern - パターン検索"
echo "  ✏️  mcp__serena__replace_symbol_body - シンボル置换"
echo "  📊 mcp__serena__get_symbols_overview - シンボル概要"
echo "  🧠 mcp__serena__read_memory - メモリ読み取り"
echo "  💾 mcp__serena__write_memory - メモリ書き込み"
echo

# Claude Code を MCP サーバー設定付きで起動
exec claude --mcp-config "${MCP_CONFIG_FILE}"