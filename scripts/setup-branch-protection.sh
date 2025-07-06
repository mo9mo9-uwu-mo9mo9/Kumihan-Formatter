#!/bin/bash

# GitHub Branch Protection Setup Script
# mo9mo9ユーザー専用の自動マージ設定

set -e

REPO="mo9mo9-uwu-mo9mo9/Kumihan-Formatter"
BRANCH="main"

echo "🔧 Setting up branch protection for $REPO/$BRANCH..."

# ブランチ保護ルールを設定
gh api \
  --method PUT \
  repos/$REPO/branches/$BRANCH/protection \
  --field required_status_checks='{"strict":true,"checks":[{"context":"quick-check","app_id":-1},{"context":"full-test","app_id":-1}]}' \
  --field enforce_admins=false \
  --field required_pull_request_reviews='{"required_approving_review_count":0,"dismiss_stale_reviews":true,"require_code_owner_reviews":false,"require_last_push_approval":false,"bypass_pull_request_allowances":{"users":["mo9mo9-uwu-mo9mo9"]}}' \
  --field restrictions='{"users":["mo9mo9-uwu-mo9mo9"],"teams":[],"apps":[]}' \
  --field required_linear_history=false \
  --field allow_force_pushes=false \
  --field allow_deletions=false \
  --field block_creations=false \
  --field required_conversation_resolution=false \
  --field lock_branch=false \
  --field allow_fork_syncing=true

echo "✅ Branch protection rules updated successfully!"

echo ""
echo "📋 Current protection settings:"
echo "- Required status checks: quick-check, full-test"
echo "- Pull request reviews: Not required for mo9mo9-uwu-mo9mo9"
echo "- Restrictions: Only mo9mo9-uwu-mo9mo9 can push"
echo "- Auto-merge: Enabled for mo9mo9-uwu-mo9mo9's PRs after tests pass"

echo ""
echo "🎯 Next steps:"
echo "1. Commit and push the auto-merge workflow"
echo "2. Test with a new PR"
echo "3. Verify auto-merge functionality"
