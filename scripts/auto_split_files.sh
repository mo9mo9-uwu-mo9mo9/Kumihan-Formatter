#!/bin/bash
# auto_split_files.sh - pre-commit用ファイル自動分割スクリプト

# 300行を超えるPythonファイルを自動検出・分割提案

MAX_LINES=300
TARGET_DIR="kumihan_formatter"
SPLIT_SCRIPT="scripts/split_file.sh"

echo "🔍 300行超過ファイルをチェック中..."

# 300行を超えるファイルを検出
OVERSIZED_FILES=$(find "$TARGET_DIR" -name "*.py" -type f -exec wc -l {} + | awk -v max="$MAX_LINES" '$1 > max && $2 != "total" { print $2 ":" $1 }')

if [ -z "$OVERSIZED_FILES" ]; then
    echo "✅ 300行以内のファイルのみです"
    exit 0
fi

echo "⚠️ 300行を超えるファイルが見つかりました:"
echo "$OVERSIZED_FILES"
echo ""

# 分割提案
echo "💡 ファイル分割を推奨します。以下のコマンドで分割できます:"
echo "$OVERSIZED_FILES" | while IFS=':' read -r file lines; do
    echo "  bash $SPLIT_SCRIPT \"$file\""
done

echo ""
echo "📋 分割後の手順:"
echo "1. 分割されたファイルを確認"
echo "2. 必要に応じて import文を調整"
echo "3. 元ファイルを削除"
echo "4. 再度コミット"

echo ""
echo "❌ 300行超過ファイルが存在するため、コミットを中止します"
echo "   ファイル分割後に再度コミットしてください"

exit 1
