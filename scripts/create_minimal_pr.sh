#!/usr/bin/env bash
set -euo pipefail

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
TITLE=${1:-"chore: minimal PR for ${BRANCH}"}
BODY=${2:-"Auto-created minimal PR from ${BRANCH}."}

echo "📦 Creating PR from ${BRANCH} -> main"
gh pr create -t "$TITLE" -b "$BODY" -B main -H "$BRANCH"

echo "✅ PR created"

