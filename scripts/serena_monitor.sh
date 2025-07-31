#!/bin/bash
# Serena MCP Server監視・自動最適化スクリプト
# Issue #687対応 - 定期実行用

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OPTIMIZATION_SCRIPT="$SCRIPT_DIR/serena_optimization.py"

# ログファイル設定
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/serena_optimization.log"

# ログ出力関数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# プロセス数チェック
check_process_count() {
    local count
    count=$(pgrep -f "serena-mcp-server" | wc -l)
    echo "$count"
}

# メイン監視ループ
main() {
    log "Serena MCP Server監視開始"
    
    # 初期状態レポート
    log "=== 初期状態 ==="
    python3 "$OPTIMIZATION_SCRIPT" --report-only 2>&1 | tee -a "$LOG_FILE"
    
    local initial_processes
    initial_processes=$(check_process_count)
    log "初期プロセス数: $initial_processes"
    
    # 重複プロセスチェック
    if [ "$initial_processes" -gt 2 ]; then
        log "重複プロセス検出 ($initial_processes プロセス). 最適化実行中..."
        
        # 最適化実行
        python3 "$OPTIMIZATION_SCRIPT" \
            --output "$LOG_DIR/optimization_result_$(date +%Y%m%d_%H%M%S).json" \
            2>&1 | tee -a "$LOG_FILE"
        
        local final_processes
        final_processes=$(check_process_count)
        log "最適化後プロセス数: $final_processes"
        
        if [ "$final_processes" -lt "$initial_processes" ]; then
            log "最適化成功: $(($initial_processes - $final_processes))プロセス削減"
        else
            log "警告: プロセス数が削減されませんでした"
        fi
    else
        log "プロセス数正常 ($initial_processes プロセス)"
    fi
    
    # キャッシュ最適化（週1回実行）
    local last_cache_cleanup_file="$LOG_DIR/.last_cache_cleanup"
    local current_day
    current_day=$(date +%j)  # 年始からの日数
    
    if [ ! -f "$last_cache_cleanup_file" ] || [ "$(cat "$last_cache_cleanup_file")" != "$current_day" ]; then
        # 7日に1回キャッシュクリーンアップ
        local days_since_last_cleanup=7
        if [ -f "$last_cache_cleanup_file" ]; then
            local last_cleanup_day
            last_cleanup_day=$(cat "$last_cache_cleanup_file")
            days_since_last_cleanup=$(($current_day - $last_cleanup_day))
        fi
        
        if [ "$days_since_last_cleanup" -ge 7 ]; then
            log "週次キャッシュクリーンアップ実行"
            python3 "$OPTIMIZATION_SCRIPT" --no-kill --cache-days 7 2>&1 | tee -a "$LOG_FILE"
            echo "$current_day" > "$last_cache_cleanup_file"
        fi
    fi
    
    log "監視完了"
}

# エラーハンドリング
trap 'log "エラー発生: line $LINENO"' ERR

# スクリプト実行
main "$@"