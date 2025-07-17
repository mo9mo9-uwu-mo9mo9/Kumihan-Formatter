#!/bin/bash

# ブランチ保護設定スクリプト
# GitHub CLIを使用してmainブランチの保護設定を自動化

set -e

# 色付きログ出力
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# GitHub CLIの確認
if ! command -v gh &> /dev/null; then
    log_error "GitHub CLI (gh) が見つかりません"
    log_info "インストール: https://cli.github.com/"
    exit 1
fi

# 認証確認
if ! gh auth status &> /dev/null; then
    log_error "GitHub CLIでログインしてください"
    log_info "実行: gh auth login"
    exit 1
fi

# リポジトリ情報取得
REPO_INFO=$(gh repo view --json owner,name)
OWNER=$(echo "$REPO_INFO" | jq -r .owner.login)
REPO_NAME=$(echo "$REPO_INFO" | jq -r .name)

log_info "リポジトリ: $OWNER/$REPO_NAME"

# 現在のブランチ保護設定確認
log_info "現在のブランチ保護設定を確認中..."
if gh api "repos/$OWNER/$REPO_NAME/branches/main/protection" &> /dev/null; then
    log_warn "main ブランチには既に保護設定が存在します"
    echo "現在の設定:"
    gh api "repos/$OWNER/$REPO_NAME/branches/main/protection" | jq .

    read -p "設定を上書きしますか? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "設定を中止しました"
        exit 0
    fi
fi

# ブランチ保護設定の適用
log_info "ブランチ保護設定を適用中..."

# 設定JSON作成
PROTECTION_CONFIG=$(cat <<EOF
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "quality-check / quality-check",
      "quality-check / pre-commit-check"
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true
}
EOF
)

# 設定適用
if gh api "repos/$OWNER/$REPO_NAME/branches/main/protection" \
   --method PUT \
   --input - <<< "$PROTECTION_CONFIG"; then
    log_info "✅ ブランチ保護設定が正常に適用されました"
else
    log_error "❌ ブランチ保護設定の適用に失敗しました"
    exit 1
fi

# 設定確認
log_info "設定確認中..."
gh api "repos/$OWNER/$REPO_NAME/branches/main/protection" | jq '{
  required_status_checks: .required_status_checks,
  enforce_admins: .enforce_admins,
  required_pull_request_reviews: .required_pull_request_reviews,
  allow_force_pushes: .allow_force_pushes,
  allow_deletions: .allow_deletions
}'

echo ""
log_info "🎉 ブランチ保護設定が完了しました！"
echo ""
echo "設定内容:"
echo "- main ブランチへの直接プッシュ禁止"
echo "- PR必須（承認者1名以上）"
echo "- CI/CD必須通過（quality-check / quality-check, quality-check / pre-commit-check）"
echo "- 管理者も設定に従う"
echo "- Force push禁止"
echo "- ブランチ削除禁止"
echo ""
log_warn "注意: 今後、main ブランチへの全ての変更はPR経由で行ってください"
