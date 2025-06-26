#!/bin/bash

# Kumihan-Formatter 記法自動修正ツール
# D&D対応: ファイルをこのスクリプトにドロップして自動修正

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"
cd ..

# 引数がない場合のメッセージ
if [ $# -eq 0 ]; then
    echo "🔧 Kumihan-Formatter 記法自動修正ツール"
    echo ""
    echo "使用方法:"
    echo "1. ファイルをこのスクリプトにドラッグ&ドロップ"
    echo "2. または: ./記法修正.command file1.txt file2.txt"
    echo ""
    echo "何かキーを押して終了..."
    read -n 1
    exit 0
fi

echo "🔧 Kumihan-Formatter 記法自動修正ツール"
echo "処理対象: $# ファイル"
echo ""

# .txtファイルのみをフィルタ
txt_files=()
for file in "$@"; do
    if [[ "$file" == *.txt ]]; then
        txt_files+=("$file")
    else
        echo "⏭️  スキップ: $file (.txtファイルではありません)"
    fi
done

if [ ${#txt_files[@]} -eq 0 ]; then
    echo "❌ 処理可能な.txtファイルがありません"
    echo ""
    echo "何かキーを押して終了..."
    read -n 1
    exit 1
fi

# 仮想環境の確認・アクティベート
if [ -d ".venv" ]; then
    echo "🔄 仮想環境をアクティベート中..."
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo "🔄 仮想環境をアクティベート中..."
    source venv/bin/activate
else
    echo "⚠️  仮想環境が見つかりません。システムPythonを使用します。"
fi

# syntax_fixerの実行
echo "🔧 記法修正を実行中..."
echo ""

python3 dev/tools/syntax_fixer.py "${txt_files[@]}" --fix

exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo "✅ 記法修正が完了しました！"
else
    echo "❌ エラーが発生しました (終了コード: $exit_code)"
fi

echo ""
echo "何かキーを押して終了..."
read -n 1