#!/usr/bin/env python3
"""
Cross-platform dependency audit (no grep/bc).

Counts Python files and import statements under a target directory,
then prints simple stats and warnings if thresholds are exceeded.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def count_imports(root: Path) -> tuple[int, int]:
    py_files = [p for p in root.rglob("*.py") if p.is_file()]
    import_re = re.compile(r"^\s*(import\s+|from\s+[^\s]+\s+import\s+)")
    import_count = 0
    for f in py_files:
        try:
            for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
                if import_re.match(line):
                    import_count += 1
        except Exception:
            # Ignore unreadable files
            pass
    return len(py_files), import_count


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="kumihan_formatter", help="target dir")
    ap.add_argument(
        "--import-threshold", type=int, default=300, help="warn above this count"
    )
    args = ap.parse_args()

    root = Path(args.target)
    file_count, import_count = count_imports(root)
    avg_imports = (import_count / file_count) if file_count else 0.0

    print("📋 依存関係分析中...")
    print("📊 依存関係統計:")
    print(f"  - 総import文: {import_count} 個 (目標: <{args.import_threshold}))")
    print(f"  - Pythonファイル数: {file_count} 個")
    print(f"  - 平均import/ファイル: {avg_imports:.1f} 個")

    if import_count > args.import_threshold:
        print("⚠️  import文が目標値を超過 - 依存関係整理が必要")
        print("💡 提案: 未使用import削除、モジュール統合を検討")
    else:
        print("✅ 依存関係は適正範囲内")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

