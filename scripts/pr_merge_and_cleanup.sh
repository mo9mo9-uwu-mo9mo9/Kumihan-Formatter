#!/usr/bin/env bash
set -euo pipefail

PR_NUMBER=${1:-}

if [[ -z "${PR_NUMBER}" ]]; then
  BRANCH="$(git rev-parse --abbrev-ref HEAD)"
  echo "🔎 Locating PR for branch ${BRANCH}"
  PR_NUMBER=$(gh pr list --head "$BRANCH" --state open --json number --jq '.[0].number')
fi

if [[ -z "${PR_NUMBER}" ]]; then
  echo "❌ No open PR found. Provide a PR number explicitly." >&2
  exit 1
fi

echo "🔀 Squash-merging PR #${PR_NUMBER} and deleting branch"
gh pr merge "$PR_NUMBER" --squash --delete-branch

echo "✅ Merge complete"

