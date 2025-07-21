#!/usr/bin/env python3
"""ファイルサイズチェックスクリプト

技術的負債予防のため、ファイルサイズを監視し大きすぎるファイルを検出します。
Pre-commit hookで自動実行されます。

Usage:
    python scripts/check_file_size.py --max-lines=300
    python scripts/check_file_size.py --max-lines=500 --target-dir=kumihan_formatter/
"""

import argparse
import ast
import sys
from pathlib import Path
from typing import List, Tuple


class FileSizeChecker:
    """ファイルサイズとコード複雑度チェッカー"""

    def __init__(
        self, max_lines: int = 300, max_classes: int = 5, max_functions: int = 20
    ):
        self.max_lines = max_lines
        self.max_classes = max_classes
        self.max_functions = max_functions
        self.violations: List[Tuple[str, str, int, int]] = []

    def _load_legacy_files(self) -> set[str]:
        """技術的負債ファイル一覧を読み込み"""
        legacy_files = set()
        legacy_file_path = Path("technical_debt_legacy_files.txt")

        if legacy_file_path.exists():
            try:
                with open(legacy_file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            legacy_files.add(line)
            except Exception:
                pass  # ファイル読み込みエラーは無視

        return legacy_files

    def check_file(self, file_path: Path) -> bool:
        """単一ファイルをチェック

        Returns:
            True if file passes all checks, False otherwise
        """
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.splitlines()
            line_count = len(lines)

            # 1. 行数チェック
            if line_count > self.max_lines:
                self.violations.append(
                    (str(file_path), "行数過多", line_count, self.max_lines)
                )
                return False

            # 2. クラス数チェック
            try:
                tree = ast.parse(content)
                class_count = sum(
                    1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
                )
                if class_count > self.max_classes:
                    self.violations.append(
                        (str(file_path), "クラス数過多", class_count, self.max_classes)
                    )
                    return False

                # 3. 関数数チェック（メソッド含む）
                function_count = sum(
                    1
                    for node in ast.walk(tree)
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                )
                if function_count > self.max_functions:
                    self.violations.append(
                        (
                            str(file_path),
                            "関数数過多",
                            function_count,
                            self.max_functions,
                        )
                    )
                    return False

            except SyntaxError:
                # 構文エラーがある場合はスキップ（他のツールで検出される）
                pass

            return True

        except Exception as e:
            print(f"Warning: ファイル読み込みエラー {file_path}: {e}", file=sys.stderr)
            return True  # エラーは無視して続行

    def check_directory(self, target_dir: Path) -> bool:
        """ディレクトリ内の全Pythonファイルをチェック

        Returns:
            True if all files pass checks, False otherwise
        """
        python_files = list(target_dir.rglob("*.py"))

        # 除外パターン
        excluded_patterns = [
            "**/test_*.py",
            "**/tests/**",
            "**/__pycache__/**",
            "**/.*/**",
            "**/venv/**",
            "**/.venv/**",
            "**/build/**",
            "**/dist/**",
        ]

        # 技術的負債ファイルを読み込み
        legacy_files = self._load_legacy_files()

        filtered_files = []
        for file_path in python_files:
            should_exclude = any(
                file_path.match(pattern) for pattern in excluded_patterns
            )
            # 技術的負債ファイルも除外
            relative_path = str(file_path).replace(str(target_dir.parent) + "/", "")
            if not should_exclude and relative_path not in legacy_files:
                filtered_files.append(file_path)

        print(f"チェック対象: {len(filtered_files)} ファイル")

        all_passed = True
        for file_path in filtered_files:
            if not self.check_file(file_path):
                all_passed = False

        return all_passed

    def print_violations(self) -> None:
        """違反項目を出力"""
        if not self.violations:
            print("✅ 全ファイルがサイズ制限を満たしています")
            return

        print("\n❌ ファイルサイズ制限違反:")
        print("=" * 80)

        for file_path, violation_type, current, limit in self.violations:
            relative_path = (
                Path(file_path).relative_to(Path.cwd())
                if Path(file_path).is_absolute()
                else file_path
            )
            print(f"📁 {relative_path}")
            print(f"   {violation_type}: {current} (制限: {limit})")

            # 提案メッセージ
            if violation_type == "行数過多":
                print(f"   💡 提案: ファイルを機能別に分割してください")
            elif violation_type == "クラス数過多":
                print(f"   💡 提案: 関連クラスを別ファイルに分離してください")
            elif violation_type == "関数数過多":
                print(f"   💡 提案: 機能別モジュールに分割してください")
            print()

        print("🔧 対策:")
        print("  1. Single Responsibility Principleに従って分割")
        print("  2. 関連機能をモジュール単位でグループ化")
        print("  3. ユーティリティ関数は別ファイルに移動")
        print("  4. 大きなクラスは責任範囲を見直して分割")


def main() -> None:
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description="ファイルサイズとコード複雑度チェッカー"
    )
    parser.add_argument(
        "--max-lines", type=int, default=300, help="最大行数制限 (デフォルト: 300)"
    )
    parser.add_argument(
        "--max-classes", type=int, default=5, help="最大クラス数制限 (デフォルト: 5)"
    )
    parser.add_argument(
        "--max-functions", type=int, default=20, help="最大関数数制限 (デフォルト: 20)"
    )
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=Path("kumihan_formatter"),
        help="チェック対象ディレクトリ (デフォルト: kumihan_formatter)",
    )
    parser.add_argument(
        "--fail-fast", action="store_true", help="最初の違反で即座に終了"
    )

    args = parser.parse_args()

    if not args.target_dir.exists():
        print(
            f"エラー: ディレクトリが見つかりません: {args.target_dir}", file=sys.stderr
        )
        sys.exit(1)

    checker = FileSizeChecker(
        max_lines=args.max_lines,
        max_classes=args.max_classes,
        max_functions=args.max_functions,
    )

    print(f"🔍 ファイルサイズチェック開始")
    print(f"対象: {args.target_dir}")
    print(
        f"制限: 行数≤{args.max_lines}, クラス≤{args.max_classes}, 関数≤{args.max_functions}"
    )
    print("-" * 60)

    success = checker.check_directory(args.target_dir)
    checker.print_violations()

    if success:
        print("\n🎉 全てのファイルがサイズ制限を満たしています！")
        sys.exit(0)
    else:
        print(f"\n❌ {len(checker.violations)} 件の違反が見つかりました")
        print("技術的負債の蓄積を防ぐため、ファイルサイズを削減してください")
        sys.exit(1)


if __name__ == "__main__":
    main()
