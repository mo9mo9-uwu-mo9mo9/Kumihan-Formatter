#!/bin/bash
#
# Kumihan-Formatter Git Hooks Installer
# 日本語ブランチ名防止のためのGit hookを自動インストール
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

echo "🔧 Kumihan-Formatter Git Hooks インストーラー"
echo "======================================"

# Git リポジトリかチェック
if [ ! -d "$PROJECT_ROOT/.git" ]; then
    echo "❌ エラー: Git リポジトリではありません"
    echo "   このスクリプトはKumihan-Formatterのルートディレクトリで実行してください"
    exit 1
fi

# Hooks ディレクトリの存在確認
if [ ! -d "$HOOKS_DIR" ]; then
    echo "❌ エラー: .git/hooks ディレクトリが見つかりません"
    exit 1
fi

echo "📍 プロジェクトルート: $PROJECT_ROOT"
echo "📍 Hooks ディレクトリ: $HOOKS_DIR"

# Pre-push hook のインストール
PRE_PUSH_HOOK="$HOOKS_DIR/pre-push"

echo ""
echo "🚀 Pre-push hook をインストールしています..."

cat > "$PRE_PUSH_HOOK" << 'EOF'
#!/bin/sh
#
# Kumihan-Formatter Git Hook: Branch Name Validation
# 日本語ブランチ名の作成・プッシュを防止
#

# 現在のブランチ名を取得
current_branch=$(git branch --show-current)

# 日本語文字（ひらがな、カタカナ、漢字）が含まれているかチェック
if echo "$current_branch" | grep -E '[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]' > /dev/null 2>&1; then
    echo "🚨 エラー: ブランチ名に日本語が含まれています"
    echo "現在のブランチ: $current_branch"
    echo ""
    echo "📋 対応方法："
    echo "1. 英語のブランチ名に変更してください"
    echo "   例: feat/issue-{Issue番号}-{英語概要}"
    echo ""
    echo "2. ブランチ名変更コマンド例："
    echo "   git branch -m $current_branch feat/issue-XXX-english-description"
    echo ""
    echo "🔒 プッシュが拒否されました。"
    exit 1
fi

# 推奨命名規則チェック（警告）
if ! echo "$current_branch" | grep -E '^(feat|fix|docs|style|refactor|test|chore)/issue-[0-9]+-[a-zA-Z0-9-]+$' > /dev/null 2>&1; then
    if [ "$current_branch" != "main" ] && [ "$current_branch" != "develop" ]; then
        echo "⚠️  警告: 推奨ブランチ命名規則に従っていません"
        echo "現在のブランチ: $current_branch"
        echo "推奨形式: {type}/issue-{番号}-{英語概要}"
        echo "例: feat/issue-123-add-new-feature"
        echo ""
    fi
fi

echo "✅ ブランチ名検証完了: $current_branch"
EOF

# 実行権限を付与
chmod +x "$PRE_PUSH_HOOK"

echo "✅ Pre-push hook インストール完了"

# インストール結果の確認
echo ""
echo "🔍 インストール結果確認:"
if [ -f "$PRE_PUSH_HOOK" ] && [ -x "$PRE_PUSH_HOOK" ]; then
    echo "✅ Pre-push hook: インストール済み & 実行可能"
else
    echo "❌ Pre-push hook: インストール失敗"
    exit 1
fi

echo ""
echo "🎉 Git hooks インストール完了！"
echo ""
echo "📋 次のステップ:"
echo "1. これで日本語ブランチ名でのプッシュは自動的に拒否されます"
echo "2. 既存の日本語ブランチがある場合は英語名に変更してください"
echo "3. 新しいブランチは必ず {type}/issue-{番号}-{英語概要} 形式で作成してください"
echo ""
echo "🔗 詳細情報:"
echo "- ブランチ命名規則: CLAUDE.md の「ブランチ管理」セクションを参照"
echo "- GitHub Actions でも二重チェックが行われます"
echo ""
echo "✨ 品質の高いブランチ名で開発をお楽しみください！"
