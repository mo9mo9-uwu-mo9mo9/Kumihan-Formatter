#!/bin/bash
"""
Git hooks セットアップスクリプト

ドキュメント整合性チェックのためのGit hooksを設定します。
"""

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
GIT_HOOKS_DIR="$PROJECT_ROOT/.git/hooks"
TOOLS_DIR="$PROJECT_ROOT/dev/tools"

echo "🔧 Git hooks をセットアップしています..."

# .git/hooks ディレクトリが存在することを確認
if [ ! -d "$GIT_HOOKS_DIR" ]; then
    echo "❌ .git/hooks ディレクトリが見つかりません。Gitリポジトリで実行してください。"
    exit 1
fi

# pre-commit hook の設定
PRE_COMMIT_HOOK="$GIT_HOOKS_DIR/pre-commit"

cat > "$PRE_COMMIT_HOOK" << 'EOF'
#!/bin/bash
# Kumihan-Formatter ドキュメント整合性チェック pre-commit hook

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON_CHECK_SCRIPT="$PROJECT_ROOT/dev/tools/pre-commit-doc-check.py"

# Pythonスクリプトが存在する場合のみ実行
if [ -f "$PYTHON_CHECK_SCRIPT" ]; then
    python3 "$PYTHON_CHECK_SCRIPT"
else
    echo "⚠️  ドキュメント整合性チェックスクリプトが見つかりません: $PYTHON_CHECK_SCRIPT"
    # スクリプトがない場合でもコミットは継続
    exit 0
fi
EOF

# 実行権限を付与
chmod +x "$PRE_COMMIT_HOOK"

echo "✅ pre-commit hook が設定されました: $PRE_COMMIT_HOOK"

# post-commit hook の設定（オプション）
POST_COMMIT_HOOK="$GIT_HOOKS_DIR/post-commit"

cat > "$POST_COMMIT_HOOK" << 'EOF'
#!/bin/bash
# Kumihan-Formatter ドキュメント整合性チェック post-commit hook

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON_CHECK_SCRIPT="$PROJECT_ROOT/dev/tools/doc_consistency_checker.py"

# コミット後に軽い整合性チェックを実行（バックグラウンド）
if [ -f "$PYTHON_CHECK_SCRIPT" ]; then
    echo "📋 コミット後にドキュメント整合性をチェックしています..."
    (python3 "$PYTHON_CHECK_SCRIPT" --format text > /dev/null 2>&1 && \
     echo "✅ ドキュメント整合性: OK" || \
     echo "⚠️  ドキュメント整合性に問題があります。詳細: python dev/tools/doc_consistency_checker.py") &
fi
EOF

chmod +x "$POST_COMMIT_HOOK"

echo "✅ post-commit hook が設定されました: $POST_COMMIT_HOOK"

# セットアップ完了メッセージ
echo ""
echo "🎉 Git hooks のセットアップが完了しました！"
echo ""
echo "📋 設定内容:"
echo "  • pre-commit:  ドキュメント変更時に整合性チェック"
echo "  • post-commit: コミット後に軽い整合性チェック"
echo ""
echo "💡 使用方法:"
echo "  • 手動チェック: python dev/tools/doc_consistency_checker.py"
echo "  • JSON出力:   python dev/tools/doc_consistency_checker.py --format json"
echo ""
echo "🔄 今後のコミット時に自動でドキュメント整合性がチェックされます。"