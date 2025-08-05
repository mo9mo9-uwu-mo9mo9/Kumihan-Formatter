#!/bin/bash
# トークン使用量監視スクリプト - Issue #801 Phase1対応
# 使用法: ./scripts/token-monitor.sh [daily|summary|reset]

set -e

# 色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 設定
SERENA_LOG_DIR="$HOME/.serena/logs"
SERENA_CONFIG="$HOME/.serena/serena_config.yml"
PROJECT_CONFIG="$PWD/.serena/project.yml"
REPORT_FILE="$PWD/token-usage-report.txt"

# ヘルプ表示
show_help() {
    echo "🚀 Claude Code トークン使用量監視ツール - Issue #801"
    echo
    echo "使用法:"
    echo "  ./scripts/token-monitor.sh [COMMAND]"
    echo
    echo "コマンド:"
    echo "  daily     日次レポート生成（デフォルト）"
    echo "  summary   現在の設定と統計サマリー"
    echo "  reset     ログファイルリセット"
    echo "  help      このヘルプを表示"
    echo
}

# ファイルサイズを人間が読みやすい形式に変換
human_readable_size() {
    local size=$1
    if [ $size -ge 1073741824 ]; then
        echo "$(($size / 1073741824))GB"
    elif [ $size -ge 1048576 ]; then
        echo "$(($size / 1048576))MB"
    elif [ $size -ge 1024 ]; then
        echo "$(($size / 1024))KB"
    else
        echo "${size}B"
    fi
}

# 設定情報表示
show_config() {
    echo -e "${BLUE}=== Serena設定状況 ===${NC}"
    echo

    if [ -f "$SERENA_CONFIG" ]; then
        echo "📊 グローバル設定:"
        grep -E "(log_level|record_tool_usage_stats)" "$SERENA_CONFIG" | sed 's/^/  /'
    else
        echo -e "${RED}❌ グローバル設定ファイルが見つかりません${NC}"
    fi

    echo

    if [ -f "$PROJECT_CONFIG" ]; then
        echo "🎯 プロジェクト設定:"
        if grep -q "tool_defaults" "$PROJECT_CONFIG"; then
            grep -A 20 "tool_defaults" "$PROJECT_CONFIG" | grep -E "(max_answer_chars|[0-9]+.*#)" | sed 's/^/  /'
        else
            echo -e "${YELLOW}  ⚠️  max_answer_chars設定なし（デフォルト200000使用中）${NC}"
        fi
    else
        echo -e "${RED}❌ プロジェクト設定ファイルが見つかりません${NC}"
    fi
    echo
}

# ログ統計表示
show_log_stats() {
    echo -e "${BLUE}=== ログファイル統計 ===${NC}"
    echo

    if [ -d "$SERENA_LOG_DIR" ]; then
        local total_size=0
        local file_count=0

        echo "📁 ログディレクトリ: $SERENA_LOG_DIR"
        echo

        # 各ログファイルのサイズを表示
        for logfile in "$SERENA_LOG_DIR"/*; do
            if [ -f "$logfile" ]; then
                local size=$(stat -f%z "$logfile" 2>/dev/null || stat -c%s "$logfile" 2>/dev/null || echo 0)
                local readable_size=$(human_readable_size $size)
                local filename=$(basename "$logfile")

                echo "  📄 $filename: $readable_size"
                total_size=$((total_size + size))
                file_count=$((file_count + 1))
            fi
        done

        echo
        echo "📊 統計サマリー:"
        echo "  📁 ファイル数: $file_count"
        echo "  💾 総サイズ: $(human_readable_size $total_size)"

        # サイズ判定とアラート
        if [ $total_size -gt 10485760 ]; then  # 10MB
            echo -e "  ${RED}🚨 アラート: ログサイズが10MBを超過${NC}"
        elif [ $total_size -gt 5242880 ]; then  # 5MB
            echo -e "  ${YELLOW}⚠️  警告: ログサイズが5MBを超過${NC}"
        else
            echo -e "  ${GREEN}✅ 正常: ログサイズは適切${NC}"
        fi

    else
        echo -e "${RED}❌ Serenaログディレクトリが見つかりません${NC}"
    fi
    echo
}

# 日次レポート生成
generate_daily_report() {
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")

    echo "🚀 Claude Code トークン使用量 日次レポート" > "$REPORT_FILE"
    echo "Generated: $timestamp" >> "$REPORT_FILE"
    echo "Issue #801 Phase1対応" >> "$REPORT_FILE"
    echo "========================================" >> "$REPORT_FILE"
    echo >> "$REPORT_FILE"

    # 設定情報をレポートに追加
    {
        show_config
        show_log_stats
    } >> "$REPORT_FILE"

    echo -e "${GREEN}✅ 日次レポートを生成しました: $REPORT_FILE${NC}"

    # コンソールにも表示
    cat "$REPORT_FILE"
}

# ログリセット
reset_logs() {
    echo -e "${YELLOW}⚠️  ログファイルリセットを実行しますか？ (y/N)${NC}"
    read -r response

    if [[ "$response" =~ ^[Yy]$ ]]; then
        if [ -d "$SERENA_LOG_DIR" ]; then
            rm -rf "$SERENA_LOG_DIR"/*
            echo -e "${GREEN}✅ ログファイルをリセットしました${NC}"
        else
            echo -e "${RED}❌ ログディレクトリが見つかりません${NC}"
        fi
    else
        echo "キャンセルしました"
    fi
}

# Phase1効果測定
show_optimization_effect() {
    echo -e "${BLUE}=== Phase1最適化効果 ===${NC}"
    echo
    echo "🎯 実装内容:"
    echo "  • log_level: INFO → WARNING (80%削減)"
    echo "  • max_answer_chars: 200000 → 5000-100000 (50-96%削減)"
    echo "  • record_tool_usage_stats: 有効化"
    echo
    echo "📈 期待効果:"
    echo "  • 日次ログサイズ: ~7MB → <2MB"
    echo "  • 平均リクエストサイズ: 200KB → <50KB"
    echo "  • 総合削減率: 60-70%"
    echo
}

# メイン処理
main() {
    case "${1:-daily}" in
        "daily")
            show_optimization_effect
            show_config
            show_log_stats
            generate_daily_report
            ;;
        "summary")
            show_optimization_effect
            show_config
            show_log_stats
            ;;
        "reset")
            reset_logs
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            echo -e "${RED}❌ 不明なコマンド: $1${NC}"
            show_help
            exit 1
            ;;
    esac
}

# スクリプト実行
main "$@"
