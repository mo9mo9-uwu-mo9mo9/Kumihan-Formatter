#!/usr/bin/env python3
"""
TDD (Test-Driven Development) 強制スクリプト

このスクリプトは開発者（特にClaude Code）がTDDを遵守することを強制します。
実装ファイルに対応するテストファイルが存在しない場合、エラーを出力します。
"""

import os
import sys
from pathlib import Path
from typing import List

# テストが不要なファイルパターン
EXCLUDED_PATTERNS = {
    "__init__.py",
    "test_*.py",
    "*_test.py",
    "conftest.py",
    "setup.py",
    "manage.py",
    # GUI関連ファイル（現実的除外）
    "*gui*.py",
    "*tk*.py",
    "*qt*.py",
    # スクリプト・ユーティリティ（現実的除外）
    "scripts/*.py",
    "*_script.py",
    "*_util.py",
    # 設定・定数ファイル（現実的除外）
    "*config*.py",
    "*constant*.py",
    "*setting*.py",
}

# テストが不要なディレクトリ
EXCLUDED_DIRS = {
    "tests",
    "test",
    "__pycache__",
    ".git",
    ".pytest_cache",
    "htmlcov",
    "dist",
    "build",
}


def find_python_files(directory: Path) -> List[Path]:
    """指定ディレクトリ内のPythonファイルを再帰的に検索"""
    python_files = []

    for root, dirs, files in os.walk(directory):
        # 除外ディレクトリをスキップ
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file

                # 除外パターンをチェック
                if not any(file_path.match(pattern) for pattern in EXCLUDED_PATTERNS):
                    python_files.append(file_path)

    return python_files


def get_expected_test_paths(source_file: Path) -> List[Path]:
    """ソースファイルに対する期待されるテストファイルパスを生成"""
    # 相対パスを取得 (絶対パスの場合の安全な処理)
    try:
        relative_path = source_file.relative_to(Path.cwd())
    except ValueError:
        # 既に相対パス、または別のルートからの場合
        relative_path = source_file

    # kumihan_formatter/core/utilities/logger.py の場合
    # tests/unit/test_logger.py
    # tests/integration/test_logger.py

    expected_paths = []

    # ファイル名からtest_プレフィックスを追加
    test_filename = f"test_{source_file.stem}.py"

    # 複数のテストディレクトリパターンを試す
    test_dirs = [
        Path("tests") / "unit",
        Path("tests") / "integration",
        Path("tests") / "e2e",
        Path("tests"),
    ]

    for test_dir in test_dirs:
        expected_paths.append(test_dir / test_filename)

    return expected_paths


def check_test_exists(source_file: Path) -> bool:
    """ソースファイルに対応するテストファイルが存在するかチェック"""
    expected_paths = get_expected_test_paths(source_file)

    return any(path.exists() for path in expected_paths)


def main() -> None:
    """メイン処理"""
    if len(sys.argv) < 2:
        print("Usage: python enforce_tdd.py <source_directory> [--lenient]")
        sys.exit(1)

    source_dir = Path(sys.argv[1])
    lenient_mode = "--lenient" in sys.argv

    if not source_dir.exists():
        print(f"Error: Directory {source_dir} does not exist")
        sys.exit(1)

    print(f"🧪 TDD Enforcement Check for {source_dir}")
    print("=" * 50)

    # 段階的採用：既存の技術的負債ファイルを除外
    legacy_files_path = Path("technical_debt_legacy_files.txt")
    excluded_files = set()

    if legacy_files_path.exists():
        with open(legacy_files_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    excluded_files.add(Path(line))
        print(
            f"   📋 Excluding {len(excluded_files)} legacy files from TDD enforcement"
        )

    python_files = find_python_files(source_dir)
    missing_tests = []

    for source_file in python_files:
        # 技術的負債ファイルは除外
        if source_file in excluded_files:
            continue

        if not check_test_exists(source_file):
            missing_tests.append(source_file)

    if missing_tests:
        if lenient_mode:
            print(
                f"⚠️  {len(missing_tests)} files are missing corresponding tests (LENIENT MODE):"
            )
            print()

            for file in missing_tests[:10]:  # 最初の10件のみ表示
                print(f"  📄 {file}")
                expected_paths = get_expected_test_paths(file)
                print(f"     Expected test files (any one of):")
                for path in expected_paths:
                    print(f"       - {path}")
                print()

            if len(missing_tests) > 10:
                print(f"  ... and {len(missing_tests) - 10} more files")
                print()

            print("⚠️  TDD COMPLIANCE WARNING!")
            print("   Consider creating test files to improve code quality.")
            print("   This is a non-blocking warning in lenient mode.")
            print()
            sys.exit(0)  # 緩和モードでは成功扱い
        else:
            print(f"❌ {len(missing_tests)} files are missing corresponding tests:")
            print()

            for file in missing_tests:
                print(f"  📄 {file}")
                expected_paths = get_expected_test_paths(file)
                print(f"     Expected test files (any one of):")
                for path in expected_paths:
                    print(f"       - {path}")
                print()

            print("🚨 TDD VIOLATION DETECTED!")
            print("   Please create test files before implementing functionality.")
            print("   Follow the Red-Green-Refactor cycle:")
            print("   1. Write failing test (RED)")
            print("   2. Implement minimal code to pass (GREEN)")
            print("   3. Refactor while keeping tests green (REFACTOR)")
            print("   Tip: Use --lenient flag for non-blocking warnings.")
            print()

            sys.exit(1)

    else:
        print(f"✅ All {len(python_files)} Python files have corresponding tests")
        print("🎉 TDD compliance verified!")
        sys.exit(0)


if __name__ == "__main__":
    main()
