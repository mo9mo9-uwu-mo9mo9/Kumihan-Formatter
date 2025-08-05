#!/bin/bash
# check-serena-expert-config.sh
# P7原則: serena-expert設定・権限確認スクリプト

echo "🚨 P7原則強制確認 - serena-expert設定チェック"
echo "=================================================="

# Claude Code設定ファイルの確認
SETTINGS_FILE=".claude/settings.local.json"
if [[ -f "$SETTINGS_FILE" ]]; then
    echo "✅ 設定ファイル発見: $SETTINGS_FILE"

    # Taskツール権限の確認
    if grep -q '"Task"' "$SETTINGS_FILE"; then
        echo "✅ Taskツール権限: 確認済み"
    else
        echo "❌ 警告: Taskツール権限が見つかりません"
        echo "   P7原則違反の可能性があります"
    fi

    # P7原則違反ツールの確認
    FORBIDDEN_TOOLS=("Edit" "Write" "MultiEdit" "mcp__serena__replace_symbol_body" "mcp__serena__insert_after_symbol" "mcp__serena__replace_regex")
    VIOLATION_COUNT=0

    for tool in "${FORBIDDEN_TOOLS[@]}"; do
        if grep -q "\"$tool\"" "$SETTINGS_FILE"; then
            echo "❌ P7違反ツール検出: '$tool'"
            echo "   → Task + serena-expert SubAgent使用に切り替え必須"
            ((VIOLATION_COUNT++))
        fi
    done

    if [ $VIOLATION_COUNT -eq 0 ]; then
        echo "✅ P7原則準拠: 違反ツール権限なし"
    else
        echo "⚠️  警告: $VIOLATION_COUNT個のP7違反ツールが許可されています"
    fi
else
    echo "❌ エラー: Claude Code設定ファイルが見つかりません"
fi

# CLAUDE.mdのP7原則確認
if [[ -f "CLAUDE.md" ]]; then
    if grep -q "serena-expert" "CLAUDE.md"; then
        echo "✅ CLAUDE.md P7原則: 確認済み"
    else
        echo "❌ 警告: CLAUDE.mdにserena-expert指示が不完全です"
    fi
else
    echo "❌ エラー: CLAUDE.mdが見つかりません"
fi

echo "=================================================="
echo "🎯 P7原則準拠アクション:"
echo "   1. 開発・実装時: Task + subagent_type=\"serena-expert\" 必須使用"
echo "   2. 直接編集ツール・serenaツール直接使用は絶対禁止"
echo "   3. 違反検出時: 作業中断 → serena-expert SubAgent切り替え"
echo "   4. 正しい使用: Task(description=\"実装内容\", subagent_type=\"serena-expert\")"
echo "=================================================="
