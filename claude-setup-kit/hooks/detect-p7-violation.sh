#!/bin/bash
# detect-p7-violation.sh
# P7原則違反検出・警告システム

TOOL_NAME="$1"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "⚠️  P7原則違反検出システム"
echo "=========================="
echo "時刻: $TIMESTAMP"
echo "実行予定ツール: $TOOL_NAME"

# P7原則違反対象ツールの定義（直接編集ツール + serena直接使用）
VIOLATION_TOOLS=("Edit" "Write" "MultiEdit" "mcp__serena__replace_symbol_body" "mcp__serena__insert_after_symbol" "mcp__serena__replace_regex" "mcp__serena__find_symbol" "mcp__serena__search_for_pattern")

# 違反チェック
IS_VIOLATION=false
for violation_tool in "${VIOLATION_TOOLS[@]}"; do
    if [[ "$TOOL_NAME" == *"$violation_tool"* ]]; then
        IS_VIOLATION=true
        break
    fi
done

if [[ "$IS_VIOLATION" == "true" ]]; then
    echo "🚨 P7原則違反警告!"
    echo "=========================="
    echo "❌ 禁止ツールの使用が検出されました: $TOOL_NAME"
    echo ""
    echo "🔧 P7原則に従い、serena-expert SubAgentに切り替え:"
    echo "   1. 作業を即座に中断"
    echo "   2. Taskツール使用に変更"
    echo "   3. subagent_type=\"serena-expert\" 必須指定"
    echo "   4. 全ての実装・編集をserena-expert SubAgentに委任"
    echo ""
    echo "📝 正しい使用例:"
    echo "   Task tool with:"
    echo "   - description: \"コード実装\""
    echo "   - prompt: \"具体的な実装内容\""
    echo "   - subagent_type: \"serena-expert\""
    echo ""
    echo "⏰ 5秒後に処理を継続します..."
    echo "   Ctrl+C で中断可能"

    # 違反ログ記録
    echo "$TIMESTAMP - P7違反: $TOOL_NAME" >> .claude/p7-violations.log

    # 警告表示
    sleep 5

    echo "=========================="
    echo "⚠️  P7原則違反を記録しました"
    echo "   ログファイル: .claude/p7-violations.log"
    echo "=========================="
else
    echo "✅ P7原則チェック: 通過"
    echo "   使用ツール: $TOOL_NAME"
fi
