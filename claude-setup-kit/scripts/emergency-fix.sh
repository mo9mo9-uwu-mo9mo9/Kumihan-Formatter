#!/bin/bash

# 🚨 Serena-local Emergency Fix Script
# Kumihan-Formatter Claude Setup Kit
# 緊急時の設定復旧スクリプト

set -e  # エラー時に即座終了

echo "🚨 Serena-local Emergency Fix Script"
echo "=================================="

# カラーコード定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ログ関数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# OS検出
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macOS"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "Linux"
    else
        echo "Unknown"
    fi
}

OS=$(detect_os)
log_info "検出されたOS: $OS"

# Claude Desktop設定ファイルパス決定
get_config_path() {
    if [[ "$OS" == "macOS" ]]; then
        echo "$HOME/Library/Application Support/Claude/claude_desktop_config.json"
    else
        echo "$HOME/.config/claude_desktop/config.json"
    fi
}

CONFIG_PATH=$(get_config_path)

# バックアップディレクトリ
BACKUP_DIR="$HOME/.claude-setup-kit-backups"
mkdir -p "$BACKUP_DIR"

# Step 1: 現状診断
log_info "Step 1: 現状診断"

# Claude Desktop設定確認
if [[ -f "$CONFIG_PATH" ]]; then
    log_info "Claude Desktop設定ファイル存在: $CONFIG_PATH"

    # JSON構文チェック
    if python3 -c "import json; json.load(open('$CONFIG_PATH'))" 2>/dev/null; then
        log_info "JSON構文: OK"
        BACKUP_NEEDED=true
    else
        log_error "JSON構文エラー検出"
        BACKUP_NEEDED=false
    fi
else
    log_warn "Claude Desktop設定ファイルなし"
    BACKUP_NEEDED=false
fi

# Step 2: バックアップ作成
if [[ "$BACKUP_NEEDED" == "true" ]]; then
    log_info "Step 2: 設定バックアップ作成"

    BACKUP_FILE="$BACKUP_DIR/claude_config_$(date +%Y%m%d_%H%M%S).json"
    cp "$CONFIG_PATH" "$BACKUP_FILE"
    log_info "バックアップ作成: $BACKUP_FILE"
else
    log_info "Step 2: バックアップスキップ (設定ファイル問題あり)"
fi

# Step 3: 設定ディレクトリ確保
log_info "Step 3: 設定ディレクトリ確保"

CONFIG_DIR=$(dirname "$CONFIG_PATH")
if [[ ! -d "$CONFIG_DIR" ]]; then
    mkdir -p "$CONFIG_DIR"
    log_info "設定ディレクトリ作成: $CONFIG_DIR"
fi

# ディレクトリ権限修正
chmod 755 "$CONFIG_DIR"
log_info "設定ディレクトリ権限修正完了"

# Step 4: 基本設定ファイル作成
log_info "Step 4: 基本設定ファイル復旧"

# serenaのパス検索
SERENA_PATHS=(
    "$HOME/GitHub/serena"
    "$PWD/serena"
    "$HOME/.local/share/serena"
)

SERENA_PATH=""
for path in "${SERENA_PATHS[@]}"; do
    if [[ -d "$path" && -f "$path/pyproject.toml" ]]; then
        SERENA_PATH="$path"
        log_info "Serena-local発見: $SERENA_PATH"
        break
    fi
done

if [[ -z "$SERENA_PATH" ]]; then
    log_warn "Serena-localが見つかりません。基本設定のみ作成"

    # 基本設定（serenaなし）
    cat > "$CONFIG_PATH" << 'EOF'
{
  "mcpServers": {}
}
EOF
else
    log_info "Serena-local設定を含む基本設定作成"

    # serena設定を含む基本設定
    cat > "$CONFIG_PATH" << EOF
{
  "mcpServers": {
    "serena": {
      "command": "python",
      "args": [
        "-m",
        "serena_local"
      ],
      "cwd": "$SERENA_PATH",
      "env": {}
    }
  }
}
EOF
fi

# ファイル権限修正
chmod 644 "$CONFIG_PATH"
log_info "設定ファイル権限修正完了"

# Step 5: JSON構文検証
log_info "Step 5: 設定ファイル検証"

if python3 -c "import json; json.load(open('$CONFIG_PATH'))" 2>/dev/null; then
    log_info "✅ 設定ファイル復旧成功"
else
    log_error "❌ 設定ファイル復旧失敗"
    exit 1
fi

# Step 6: Serena-local動作確認（存在する場合）
if [[ -n "$SERENA_PATH" ]]; then
    log_info "Step 6: Serena-local動作確認"

    cd "$SERENA_PATH"

    # 仮想環境確認
    if [[ ! -d ".venv" ]]; then
        log_warn "仮想環境未作成 - 作成中"
        if command -v uv >/dev/null 2>&1; then
            uv venv
            log_info "仮想環境作成完了（UV）"
        else
            python3 -m venv .venv
            log_info "仮想環境作成完了（標準venv）"
        fi
    fi

    # 仮想環境有効化とテスト
    source .venv/bin/activate

    # serena_localモジュールテスト
    if python -c "import serena_local" 2>/dev/null; then
        log_info "✅ Serena-local モジュール: OK"
    else
        log_warn "Serena-localモジュール未インストール - インストール中"
        if command -v uv >/dev/null 2>&1; then
            uv pip install -e .
        else
            pip install -e .
        fi
        log_info "Serena-local再インストール完了"
    fi

    # 動作テスト
    if python -m serena_local --help >/dev/null 2>&1; then
        log_info "✅ Serena-local動作確認: OK"
    else
        log_error "❌ Serena-local動作確認: 失敗"
    fi
fi

# Step 7: 完了報告
log_info "=================================="
log_info "🎉 緊急修復完了"
log_info "=================================="

if [[ "$BACKUP_NEEDED" == "true" ]]; then
    log_info "📁 バックアップ: $BACKUP_FILE"
fi

log_info "📄 設定ファイル: $CONFIG_PATH"

if [[ -n "$SERENA_PATH" ]]; then
    log_info "🔧 Serena-local: $SERENA_PATH"
fi

echo ""
log_info "次の手順:"
echo "1. Claude Desktopを再起動してください"
echo "2. 新しい会話で動作確認を行ってください"

if [[ -n "$SERENA_PATH" ]]; then
    echo "3. 「プロジェクト構造を確認してください」でSerenaツールの動作確認"
fi

echo ""
log_warn "注意: このスクリプトは最小限の復旧のみを行います"
log_warn "詳細な設定は INSTALLATION_GUIDE.md を参照してください"

exit 0
