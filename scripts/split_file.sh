#!/bin/bash
# split_file.sh - 効率的なファイル分割支援

TARGET_FILE=$1
SPLIT_LINES=${2:-135}  # デフォルト分割行数

if [ ! -f "$TARGET_FILE" ]; then
    echo "❌ ファイルが存在しません: $TARGET_FILE"
    exit 1
fi

TOTAL_LINES=$(wc -l < "$TARGET_FILE")
echo "📊 分割対象: $TARGET_FILE ($TOTAL_LINES 行)"

# 分割ポイント提案
echo "💡 分割ポイント提案:"
echo "- Part 1: 1-$SPLIT_LINES"
echo "- Part 2: $((SPLIT_LINES+1))-$((SPLIT_LINES*2))"
echo "- Part 3: $((SPLIT_LINES*2+1))-$TOTAL_LINES"

# 確認
read -p "分割を実行しますか？ (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 分割実行中..."

    # ファイル名とディレクトリを抽出
    FILE_DIR=$(dirname "$TARGET_FILE")
    FILE_NAME=$(basename "$TARGET_FILE")
    FILE_BASE="${FILE_NAME%.*}"
    FILE_EXT="${FILE_NAME##*.}"

    # 分割実行
    PART1_FILE="${FILE_DIR}/${FILE_BASE}_part1.${FILE_EXT}"
    PART2_FILE="${FILE_DIR}/${FILE_BASE}_part2.${FILE_EXT}"
    PART3_FILE="${FILE_DIR}/${FILE_BASE}_part3.${FILE_EXT}"

    # Part 1 (1-SPLIT_LINES)
    head -n "$SPLIT_LINES" "$TARGET_FILE" > "$PART1_FILE"
    echo "✅ Part 1 作成: $PART1_FILE (1-$SPLIT_LINES 行)"

    # Part 2 (SPLIT_LINES+1 - SPLIT_LINES*2)
    if [ $TOTAL_LINES -gt $SPLIT_LINES ]; then
        PART2_END=$((SPLIT_LINES*2))
        if [ $PART2_END -gt $TOTAL_LINES ]; then
            PART2_END=$TOTAL_LINES
        fi
        sed -n "$((SPLIT_LINES+1)),${PART2_END}p" "$TARGET_FILE" > "$PART2_FILE"
        echo "✅ Part 2 作成: $PART2_FILE ($((SPLIT_LINES+1))-$PART2_END 行)"
    fi

    # Part 3 (SPLIT_LINES*2+1 - 終端)
    if [ $TOTAL_LINES -gt $((SPLIT_LINES*2)) ]; then
        tail -n +$((SPLIT_LINES*2+1)) "$TARGET_FILE" > "$PART3_FILE"
        echo "✅ Part 3 作成: $PART3_FILE ($((SPLIT_LINES*2+1))-$TOTAL_LINES 行)"
    fi

    echo "🎉 分割完了！"
    echo "📝 元ファイル: $TARGET_FILE"
    echo "📄 分割ファイル:"
    [ -f "$PART1_FILE" ] && echo "  - $PART1_FILE"
    [ -f "$PART2_FILE" ] && echo "  - $PART2_FILE"
    [ -f "$PART3_FILE" ] && echo "  - $PART3_FILE"

else
    echo "❌ 分割をキャンセルしました"
fi
