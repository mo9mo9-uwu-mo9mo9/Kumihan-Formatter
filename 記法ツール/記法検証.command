#!/bin/bash

# Kumihan-Formatter 記法検証ツール
# D&D対応: ファイルをドロップして記法エラーをチェック

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"
cd ..

# 引数がない場合のメッセージ
if [ $# -eq 0 ]; then
    echo "🔍 Kumihan-Formatter 記法検証ツール"
    echo ""
    echo "使用方法:"
    echo "1. ファイルをこのスクリプトにドラッグ&ドロップ"
    echo "2. または: ./記法検証.command file1.txt file2.txt"
    echo ""
    echo "何かキーを押して終了..."
    read -n 1
    exit 0
fi

echo "🔍 Kumihan-Formatter 記法検証ツール"
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

# syntax_fixerの実行（検証のみモード）
echo "🔍 記法検証を実行中..."
echo ""

python3 dev/tools/syntax_fixer.py "${txt_files[@]}"

exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo "✅ 記法検証が完了しました！エラーはありません。"
else
    echo "⚠️  記法エラーが検出されました"
    echo "💡 自動修正を行うには「記法修正.command」を使用してください"
fi

echo ""
echo "何かキーを押して終了..."
read -n 1