#!/bin/bash
# 標準ツール統合品質チェックスクリプト - Issue #1116
# カスタムツール依存を削除し、標準ツールチェーンで品質チェックを実行

set -euo pipefail

# プロジェクトルート検出
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# ログ関数
log_info() {
    echo "ℹ️  $1"
}

log_success() {
    echo "✅ $1"
}

log_error() {
    echo "❌ $1" >&2
}

log_warning() {
    echo "⚠️  $1"
}

# 品質チェック設定
TARGET_DIR="${1:-kumihan_formatter}"
VERBOSE="${VERBOSE:-false}"
EXIT_ON_ERROR="${EXIT_ON_ERROR:-true}"

# 全体の実行結果トラッキング
TOTAL_CHECKS=0
FAILED_CHECKS=0
WARNINGS=0

# ヘルプ表示
show_help() {
    cat << EOF
📋 標準ツール統合品質チェック

使用方法:
  $0 [TARGET_DIR]

オプション:
  TARGET_DIR    対象ディレクトリ (デフォルト: kumihan_formatter)

環境変数:
  VERBOSE=true          詳細ログ出力
  EXIT_ON_ERROR=false   エラー時も継続実行

品質チェック項目:
  1. Black - コードフォーマット確認
  2. mypy - 型チェック（基本）

例:
  $0                           # kumihan_formatter/を対象
  $0 tests/                    # tests/を対象
  VERBOSE=true $0              # 詳細出力
  EXIT_ON_ERROR=false $0       # エラーがあっても全チェック実行
EOF
}

# 引数解析
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    show_help
    exit 0
fi

# 依存確認
check_dependencies() {
    local missing_tools=()

    for tool in black mypy; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        fi
    done

    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log_error "必要なツールが見つかりません: ${missing_tools[*]}"
        log_info "インストール方法: pip install ${missing_tools[*]}"
        exit 1
    fi
}

# 個別チェック実行
run_check() {
    local check_name="$1"
    local command="$2"

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    log_info "実行中: $check_name"

    if [[ "$VERBOSE" == "true" ]]; then
        log_info "コマンド: $command"
    fi

    if eval "$command"; then
        log_success "$check_name 完了"
        return 0
    else
        local exit_code=$?
        log_error "$check_name 失敗 (終了コード: $exit_code)"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))

        if [[ "$EXIT_ON_ERROR" == "true" ]]; then
            exit $exit_code
        fi
        return $exit_code
    fi
}

# 警告付きチェック実行
run_check_with_warnings() {
    local check_name="$1"
    local command="$2"

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    log_info "実行中: $check_name"

    if [[ "$VERBOSE" == "true" ]]; then
        log_info "コマンド: $command"
    fi

    if eval "$command"; then
        log_success "$check_name 完了"
        return 0
    else
        local exit_code=$?
        log_warning "$check_name で警告/エラー (終了コード: $exit_code)"
        WARNINGS=$((WARNINGS + 1))
        return 0  # 警告として処理し、継続
    fi
}

# メイン品質チェック実行
main() {
    log_info "🔍 標準ツール統合品質チェック開始"
    log_info "対象ディレクトリ: $TARGET_DIR"
    log_info "プロジェクトルート: $PROJECT_ROOT"

    # 依存確認
    check_dependencies

    # 対象ディレクトリ確認
    if [[ ! -d "$TARGET_DIR" ]]; then
        log_error "対象ディレクトリが見つかりません: $TARGET_DIR"
        exit 1
    fi

    echo ""
    log_info "=== Phase 1: コードフォーマット確認 ==="

    # Black - コードフォーマット確認
    run_check "Black フォーマット確認" \
        "black --check --diff \"$TARGET_DIR\""

    echo ""
    log_info "=== Phase 2: 型チェック ===\"

    # mypy - 型チェック（基本モジュールのみ）
    if [[ "$TARGET_DIR" == "kumihan_formatter" ]]; then
        run_check_with_warnings "MyPy 基本型チェック" \
            "mypy \"$TARGET_DIR/core/ast_nodes/\" \"$TARGET_DIR/core/utilities/\" --ignore-missing-imports"
    else
        log_info "MyPy: カスタムディレクトリのためスキップ"
    fi

    # 結果サマリー
    echo ""
    log_info "=== 品質チェック結果サマリー ==="
    log_info "総チェック数: $TOTAL_CHECKS"

    if [[ $FAILED_CHECKS -eq 0 ]]; then
        log_success "全チェック完了 ($WARNINGS 警告)"
        if [[ $WARNINGS -gt 0 ]]; then
            log_warning "警告があります。詳細は上記ログを確認してください。"
        fi
        exit 0
    else
        log_error "$FAILED_CHECKS/$TOTAL_CHECKS のチェックが失敗しました"
        exit 1
    fi
}

# スクリプト実行
main "$@"
