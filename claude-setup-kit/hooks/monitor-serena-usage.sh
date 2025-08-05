#!/bin/bash
# monitor-serena-usage.sh
# serena-expert使用状況監視・ログ記録

TOOL_NAME="$1"
SUBAGENT_TYPE="$2"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_FILE=".claude/serena-expert-usage.log"

echo "📊 serena-expert SubAgent使用監視"
echo "============================"
echo "時刻: $TIMESTAMP"
echo "ツール: $TOOL_NAME"
echo "サブエージェント: $SUBAGENT_TYPE"

# ディレクトリ確認・作成
mkdir -p .claude

# Task + serena-expert SubAgent の正しい組み合わせのみを監視
if [[ "$TOOL_NAME" == "Task" && "$SUBAGENT_TYPE" == "serena-expert" ]]; then
    echo "✅ P7原則準拠: serena-expert SubAgent使用確認"
    echo "$TIMESTAMP - P7準拠: Task + serena-expert SubAgent" >> "$LOG_FILE"

    # 使用統計更新
    if [[ -f ".claude/serena-stats.json" ]]; then
        # 既存統計ファイルがある場合は更新
        python3 -c "
import json
import os
from datetime import datetime

stats_file = '.claude/serena-stats.json'
if os.path.exists(stats_file):
    with open(stats_file, 'r') as f:
        stats = json.load(f)
else:
    stats = {'total_usage': 0, 'last_used': '', 'daily_usage': {}}

stats['total_usage'] += 1
stats['last_used'] = '$TIMESTAMP'

today = datetime.now().strftime('%Y-%m-%d')
if today not in stats['daily_usage']:
    stats['daily_usage'][today] = 0
stats['daily_usage'][today] += 1

with open(stats_file, 'w') as f:
    json.dump(stats, f, indent=2)
"
    else
        # 新規統計ファイル作成
        cat > .claude/serena-stats.json << EOF
{
  "total_usage": 1,
  "last_used": "$TIMESTAMP",
  "daily_usage": {
    "$(date '+%Y-%m-%d')": 1
  }
}
EOF
    fi

    echo "📈 使用統計を更新しました"

elif [[ "$TOOL_NAME" == "Task" ]]; then
    echo "❌ P7原則違反: Task使用だがserena-expert SubAgent未指定"
    echo "   → subagent_type=\"serena-expert\" を必ず指定してください"
    echo "$TIMESTAMP - P7違反: Task使用, serena-expert未指定" >> "$LOG_FILE"

else
    echo "ℹ️  監視対象外ツール: $TOOL_NAME"
fi

# 直近のserena-expert SubAgent使用状況表示
echo ""
echo "📋 直近のserena-expert SubAgent使用状況:"
if [[ -f "$LOG_FILE" ]]; then
    tail -n 3 "$LOG_FILE" | while read line; do
        echo "   $line"
    done
else
    echo "   （使用ログなし）"
fi

echo "============================"
