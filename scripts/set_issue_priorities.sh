#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: set_issue_priorities.sh <P0|P1|P2> <ISSUE_NUMBER> [ISSUE_NUMBER...]

Bulk-apply a priority label to GitHub issues using gh CLI.

Examples:
  set_issue_priorities.sh P0 1314 1315
  set_issue_priorities.sh P2 1279
USAGE
}

if [[ $# -lt 2 ]]; then
  usage; exit 1
fi

LABEL="$1"; shift

for ISSUE in "$@"; do
  echo "🏷️  Adding label '$LABEL' to #$ISSUE"
  gh issue edit "$ISSUE" --add-label "$LABEL"
done

echo "✅ Completed labeling"

