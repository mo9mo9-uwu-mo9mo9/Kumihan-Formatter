#!/usr/bin/env bash
set -euo pipefail

DRY_RUN=false
while getopts ":n" opt; do
  case $opt in
    n) DRY_RUN=true ;;
    *) ;;
  esac
done

echo "[Serena] Project indexing start"

run() {
  echo "> $*"
  if [ "$DRY_RUN" = false ]; then
    eval "$@"
  fi
}

if command -v uvx >/dev/null 2>&1; then
  CMD="uvx --from git+https://github.com/oraios/serena serena index-project"
elif command -v uv >/dev/null 2>&1; then
  CMD="uv run --with git+https://github.com/oraios/serena serena index-project"
elif command -v pipx >/dev/null 2>&1; then
  CMD="pipx run git+https://github.com/oraios/serena serena index-project"
else
  echo "[Serena] uvx/uv/pipxが見つかりません。https://github.com/oraios/serena を参照して導入してください。"
  exit 1
fi

run "$CMD"
echo "[Serena] Project indexing done"

