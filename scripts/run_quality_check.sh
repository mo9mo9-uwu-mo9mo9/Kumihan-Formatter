#!/usr/bin/env bash
set -euo pipefail

echo "🧪 Running quality check (lint + tests)"
make lint
make test

