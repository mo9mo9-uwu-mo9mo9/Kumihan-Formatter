#!/bin/bash

# 🔧 Serena-local Installation Script
# Kumihan-Formatter Claude Setup Kit
# 実際の手動インストール支援スクリプト

set -e  # エラー時に即座終了

echo "🔧 Serena-local Installation Script"
echo "==================================="

# カラーコード定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 使用方法表示
show_usage() {
    echo "使用方法:"
    echo "  $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  --install-path PATH  インストール先パス (デフォルト: ~/GitHub/serena)"
    echo "  --help              このヘルプを表示"
    echo ""
    echo "例:"
    echo "  $0 --install-path ~/my-serena"
}

# デフォルト設定
INSTALL_PATH="$HOME/GitHub/serena"
SERENA_REPO="https://github.com/tommyip/serena.git"

# コマンドライン引数解析
while [[ $# -gt 0 ]]; do
    case $1 in
        --install-path)
            INSTALL_PATH="$2"
            shift 2
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            log_error "不明なオプション: $1"
            show_usage
            exit 1
            ;;
    esac
done

log_info "インストール先: $INSTALL_PATH"

# Step 1: 前提条件確認
log_step "Step 1: 前提条件確認"

# Python確認
if command -v python3 >/dev/null 2>&1; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    log_info "Python発見: $PYTHON_VERSION"

    # Python 3.12以上の確認
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 12) else 1)" 2>/dev/null; then
        log_info "✅ Python 3.12以上: OK"
    else
        log_error "Python 3.12以上が必要です。現在: $PYTHON_VERSION"
        echo "インストール方法:"
        echo "  Ubuntu/Debian: sudo apt update && sudo apt install python3.12"
        echo "  macOS: brew install python@3.12"
        exit 1
    fi
else
    log_error "Python3が見つかりません"
    exit 1
fi

# Git確認
if command -v git >/dev/null 2>&1; then
    log_info "✅ Git: $(git --version)"
else
    log_error "Gitが見つかりません"
    echo "インストール方法:"
    echo "  Ubuntu/Debian: sudo apt install git"
    echo "  macOS: brew install git"
    exit 1
fi

# UV確認・インストール
if command -v uv >/dev/null 2>&1; then
    log_info "✅ UV: $(uv --version)"
else
    log_warn "UVが見つかりません - 自動インストール中"
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # パス更新
    export PATH="$HOME/.cargo/bin:$PATH"

    if command -v uv >/dev/null 2>&1; then
        log_info "✅ UV自動インストール完了"
    else
        log_error "UV自動インストール失敗"
        echo "手動でインストールしてください:"
        echo "  https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    fi
fi

# Step 2: インストールディレクトリ準備
log_step "Step 2: インストールディレクトリ準備"

# インストール先の親ディレクトリ作成
INSTALL_DIR=$(dirname "$INSTALL_PATH")
if [[ ! -d "$INSTALL_DIR" ]]; then
    mkdir -p "$INSTALL_DIR"
    log_info "親ディレクトリ作成: $INSTALL_DIR"
fi

# 既存インストールの確認
if [[ -d "$INSTALL_PATH" ]]; then
    log_warn "既存のインストールが見つかりました: $INSTALL_PATH"
    echo -n "上書きしますか? [y/N]: "
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        log_info "インストール中止"
        exit 0
    fi
    rm -rf "$INSTALL_PATH"
    log_info "既存インストール削除完了"
fi

# Step 3: Serena-localクローン
log_step "Step 3: Serena-localクローン"

log_info "リポジトリクローン中..."
if git clone "$SERENA_REPO" "$INSTALL_PATH"; then
    log_info "✅ クローン完了"
else
    log_error "クローン失敗"
    exit 1
fi

cd "$INSTALL_PATH"

# Step 4: 仮想環境作成・インストール
log_step "Step 4: 仮想環境作成・インストール"

log_info "仮想環境作成中..."
if uv venv; then
    log_info "✅ 仮想環境作成完了"
else
    log_error "仮想環境作成失敗"
    exit 1
fi

log_info "依存関係インストール中..."
source .venv/bin/activate

if uv pip install -e .; then
    log_info "✅ インストール完了"
else
    log_error "インストール失敗"
    exit 1
fi

# Step 5: 動作確認
log_step "Step 5: 動作確認"

if python -m serena_local --help >/dev/null 2>&1; then
    log_info "✅ Serena-local動作確認: OK"
else
    log_error "❌ 動作確認失敗"
    echo "トラブルシューティングガイドを参照してください:"
    echo "  claude-setup-kit/TROUBLESHOOTING.md"
    exit 1
fi

# Step 6: Claude Desktop設定ガイド
log_step "Step 6: 次のステップ"

echo ""
log_info "🎉 Serena-localインストール完了!"
log_info "インストール先: $INSTALL_PATH"
echo ""
log_warn "次に必要な手順:"
echo "1. Claude Desktop設定ファイルの編集"
echo "   詳細: claude-setup-kit/INSTALLATION_GUIDE.md"
echo ""
echo "2. 設定ファイルに以下を追加:"
echo "   \\"serena\\": {"
echo "     \\"command\\": \\"python\\","
echo "     \\"args\\": [\\"-m\\", \\"serena_local\\"],"
echo "     \\"cwd\\": \\"$INSTALL_PATH\\","
echo "     \\"env\\": {}"
echo "   }"
echo ""
echo "3. Claude Desktopの再起動"
echo ""

# 自動設定提案（オプション）
echo -n "Claude Desktop設定の自動追加を試みますか? [y/N]: "
read -r auto_config
if [[ "$auto_config" =~ ^[Yy]$ ]]; then
    log_info "緊急修復スクリプトで自動設定を実行します"

    if [[ -x "claude-setup-kit/scripts/emergency-fix.sh" ]]; then
        ./claude-setup-kit/scripts/emergency-fix.sh
    else
        log_error "緊急修復スクリプトが見つかりません"
        echo "手動で設定してください"
    fi
fi

log_info "インストール完了!"
exit 0
