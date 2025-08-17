#!/bin/bash
# メモリ最適化・クリーンアップスクリプト
# Kumihan-Formatter プロジェクト用

echo "🧹 Kumihan-Formatter メモリ最適化開始..."

# 1. 大きな一時ファイルの削除（10KB以上のmdファイル）
echo "📁 大きな指示書ファイルを削除中..."
find tmp -name "*.md" -size +10k -type f -delete 2>/dev/null

# 2. 古いファイルの削除（7日以上前）
echo "📅 古いファイルを削除中..."
find tmp -name "*.md" -mtime +7 -type f -delete 2>/dev/null
find tmp -name "*.json" -mtime +7 -type f -delete 2>/dev/null
find tmp -name "*.txt" -mtime +7 -type f -delete 2>/dev/null

# 3. __pycache__ディレクトリのクリーンアップ
echo "🗑️ キャッシュをクリア中..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# 4. ログファイルのローテーション（100MB以上）
echo "📝 大きなログファイルを確認中..."
find logs -name "*.log" -size +100M -type f -exec echo "警告: {} が100MB以上です" \;

# 5. 残りのファイル数とサイズを表示
echo ""
echo "📊 クリーンアップ後の状態:"
echo "tmp/ディレクトリ内のファイル数: $(find tmp -type f 2>/dev/null | wc -l)"
echo "tmp/ディレクトリの合計サイズ: $(du -sh tmp 2>/dev/null | cut -f1)"

echo ""
echo "✅ クリーンアップ完了!"
echo ""
echo "💡 ヒント:"
echo "  - Node.jsメモリ上限を確認: echo \$NODE_OPTIONS"
echo "  - 新しいターミナルで設定を反映: source ~/.zshrc"
echo "  - Claude Codeを再起動するとメモリがリセットされます"
