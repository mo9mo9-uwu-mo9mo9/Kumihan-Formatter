#!/bin/bash

# レイアウト修正テスト用スクリプト

echo "=== レイアウト修正テスト ==="

# 仮想環境をアクティベート
source .venv/bin/activate

# テスト出力ディレクトリ
TEST_DIR="/tmp/test-layout-$(date +%s)"
mkdir -p "$TEST_DIR"

echo "出力先: $TEST_DIR"

# 全サンプルファイルを変換
for file in examples/*.txt; do
    if [ -f "$file" ]; then
        filename=$(basename "$file" .txt)
        echo "変換中: $filename"
        echo "n" | python -m kumihan_formatter convert "$file" -o "$TEST_DIR" --no-preview
    fi
done

# showcaseも生成
echo "showcase生成中"
echo "n" | python -m kumihan_formatter convert --generate-sample -o "$TEST_DIR" --no-preview

echo ""
echo "=== テスト完了 ==="
echo "生成されたファイル:"
ls -la "$TEST_DIR"/*.html

echo ""
echo "ブラウザで確認する場合："
echo "open '$TEST_DIR'"