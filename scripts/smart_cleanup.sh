#!/bin/bash
# スマートメモリクリーンアップスクリプト
# しきい値チェック付きで効率的なクリーンアップを実行

set -e  # エラー時に停止

# 設定
THRESHOLD_MB=20  # tmp/ディレクトリのしきい値（MB）
FORCE_MODE=false
QUIET_MODE=false
LOG_FILE=""

# ヘルプ表示
show_help() {
    cat << EOF
🧹 Kumihan-Formatter スマートメモリクリーンアップ

使い方:
  $0 [オプション]

オプション:
  -f, --force     しきい値に関係なく強制実行
  -q, --quiet     詳細出力を抑制（pre-commit用）
  -l, --log FILE  ログファイルに出力
  -h, --help      このヘルプを表示

例:
  $0              # しきい値チェック付き実行
  $0 --force      # 強制実行
  $0 --quiet      # 静音モード（git hook用）
  $0 --log logs/cleanup.log  # ログファイル出力

しきい値: tmp/ディレクトリが${THRESHOLD_MB}MB以上の場合に実行
EOF
}

# ログ出力関数
log() {
    local message="$1"
    if [[ "$QUIET_MODE" == "false" ]]; then
        echo "$message"
    fi
    if [[ -n "$LOG_FILE" ]]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') $message" >> "$LOG_FILE"
    fi
}

# エラー出力関数
error() {
    echo "❌ エラー: $1" >&2
    if [[ -n "$LOG_FILE" ]]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') ERROR: $1" >> "$LOG_FILE"
    fi
    exit 1
}

# 引数解析
while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--force)
            FORCE_MODE=true
            shift
            ;;
        -q|--quiet)
            QUIET_MODE=true
            shift
            ;;
        -l|--log)
            LOG_FILE="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            error "不明なオプション: $1"
            ;;
    esac
done

# プロジェクトルートに移動
cd "$(dirname "$0")/.." || error "プロジェクトルートに移動できません"

# ログディレクトリ作成
if [[ -n "$LOG_FILE" ]]; then
    mkdir -p "$(dirname "$LOG_FILE")"
fi

# tmp/ディレクトリの存在確認
if [[ ! -d "tmp" ]]; then
    log "📁 tmp/ディレクトリが存在しません - スキップ"
    exit 0
fi

# サイズチェック
TMP_SIZE_MB=$(du -sm tmp 2>/dev/null | cut -f1)

log "📊 現在のtmp/サイズ: ${TMP_SIZE_MB}MB (しきい値: ${THRESHOLD_MB}MB)"

# しきい値チェック（強制モードでない場合）
if [[ "$FORCE_MODE" == "false" && "$TMP_SIZE_MB" -lt "$THRESHOLD_MB" ]]; then
    log "✅ しきい値未満のためクリーンアップをスキップ"
    exit 0
fi

# クリーンアップ開始
if [[ "$QUIET_MODE" == "false" ]]; then
    log "🧹 スマートメモリクリーンアップ開始..."
fi

# 実行前のファイル数カウント
BEFORE_COUNT=$(find tmp -type f 2>/dev/null | wc -l | tr -d ' ')

# 1. 大きな一時ファイルの削除（10KB以上のmdファイル）
LARGE_FILES=$(find tmp -name "*.md" -size +10k -type f 2>/dev/null | wc -l | tr -d ' ')
if [[ "$LARGE_FILES" -gt 0 ]]; then
    log "📁 大きな指示書ファイルを削除中... (${LARGE_FILES}件)"
    find tmp -name "*.md" -size +10k -type f -delete 2>/dev/null
fi

# 2. 古いファイルの削除（7日以上前）
OLD_FILES=$(find tmp \( -name "*.md" -o -name "*.json" -o -name "*.txt" \) -mtime +7 -type f 2>/dev/null | wc -l | tr -d ' ')
if [[ "$OLD_FILES" -gt 0 ]]; then
    log "📅 古いファイルを削除中... (${OLD_FILES}件)"
    find tmp -name "*.md" -mtime +7 -type f -delete 2>/dev/null
    find tmp -name "*.json" -mtime +7 -type f -delete 2>/dev/null
    find tmp -name "*.txt" -mtime +7 -type f -delete 2>/dev/null
fi

# 3. __pycache__ディレクトリのクリーンアップ
CACHE_DIRS=$(find . -type d -name "__pycache__" 2>/dev/null | wc -l | tr -d ' ')
if [[ "$CACHE_DIRS" -gt 0 ]]; then
    log "🗑️ キャッシュをクリア中... (${CACHE_DIRS}個のディレクトリ)"
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
fi

# 4. 空のディレクトリ削除
find tmp -type d -empty -delete 2>/dev/null || true

# 実行後の状態確認
AFTER_COUNT=$(find tmp -type f 2>/dev/null | wc -l | tr -d ' ')
AFTER_SIZE_MB=$(du -sm tmp 2>/dev/null | cut -f1)
CLEANED_FILES=$((BEFORE_COUNT - AFTER_COUNT))
SAVED_MB=$((TMP_SIZE_MB - AFTER_SIZE_MB))

# 結果表示
if [[ "$QUIET_MODE" == "false" ]]; then
    echo ""
    log "📊 クリーンアップ結果:"
    log "   削除ファイル数: ${CLEANED_FILES}件"
    log "   節約容量: ${SAVED_MB}MB"
    log "   現在のサイズ: ${AFTER_SIZE_MB}MB"
    echo ""
    log "✅ クリーンアップ完了!"
else
    # 静音モードでも重要な情報は出力
    if [[ "$CLEANED_FILES" -gt 0 ]]; then
        echo "🧹 Cleanup: ${CLEANED_FILES} files, ${SAVED_MB}MB saved"
    fi
fi

# ログファイルに統計出力
if [[ -n "$LOG_FILE" ]]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') STATS: files_cleaned=$CLEANED_FILES, mb_saved=$SAVED_MB, final_size=${AFTER_SIZE_MB}MB" >> "$LOG_FILE"
fi
