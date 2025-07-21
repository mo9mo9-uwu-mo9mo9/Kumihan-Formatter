#!/usr/bin/env python3
"""アーキテクチャルールチェックスクリプト

コードアーキテクチャの品質を監視し、Single Responsibility Principleの
違反や設計上の問題を早期発見します。

Usage:
    python scripts/architecture_check.py
    python scripts/architecture_check.py --strict
    python scripts/architecture_check.py --target-dir=kumihan_formatter/
"""

import argparse
import ast
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class ArchitectureChecker:
    """アーキテクチャ品質チェッカー"""

    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self.violations: List[Tuple[str, str, str, Optional[int]]] = []
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.metrics: Dict[str, Dict[str, int]] = {}

    def analyze_file(self, file_path: Path) -> Dict[str, int]:
        """ファイルを分析してメトリクスを収集"""
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)

            metrics = {
                "lines": len(content.splitlines()),
                "classes": 0,
                "functions": 0,
                "methods": 0,
                "imports": 0,
                "complexity": 0,
                "max_function_lines": 0,
                "max_class_lines": 0,
            }

            # 各ノードを分析
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    metrics["classes"] += 1
                    class_lines = self._get_node_lines(node, content)
                    metrics["max_class_lines"] = max(
                        metrics["max_class_lines"], class_lines
                    )

                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if self._is_method(node, tree):
                        metrics["methods"] += 1
                    else:
                        metrics["functions"] += 1

                    func_lines = self._get_node_lines(node, content)
                    metrics["max_function_lines"] = max(
                        metrics["max_function_lines"], func_lines
                    )

                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    metrics["imports"] += 1

                elif isinstance(node, (ast.If, ast.While, ast.For, ast.Try)):
                    metrics["complexity"] += 1

            return metrics

        except Exception as e:
            print(f"Warning: ファイル分析エラー {file_path}: {e}", file=sys.stderr)
            return {}

    def _get_node_lines(self, node: ast.AST, content: str) -> int:
        """ASTノードの行数を計算"""
        lines = content.splitlines()
        if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
            if node.end_lineno:
                return int(node.end_lineno - node.lineno + 1)
        return 0

    def _is_method(
        self, func_node: ast.FunctionDef | ast.AsyncFunctionDef, tree: ast.AST
    ) -> bool:
        """関数がクラスメソッドかどうか判定"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if item == func_node:
                        return True
        return False

    def check_single_responsibility(
        self, file_path: Path, metrics: Dict[str, int]
    ) -> bool:
        """Single Responsibility Principleの違反をチェック"""
        violations_found = False

        # 1. ファイルサイズチェック
        if metrics.get("lines", 0) > 300:
            self.violations.append(
                (
                    str(file_path),
                    "SRP違反",
                    f"ファイルが大きすぎます ({metrics['lines']}行)",
                    metrics["lines"],
                )
            )
            violations_found = True

        # 2. クラス数チェック
        if metrics.get("classes", 0) > 3:
            self.violations.append(
                (
                    str(file_path),
                    "SRP違反",
                    f"クラス数が多すぎます ({metrics['classes']}個)",
                    metrics["classes"],
                )
            )
            violations_found = True

        # 3. 大きすぎるクラスチェック
        if metrics.get("max_class_lines", 0) > 100:
            self.violations.append(
                (
                    str(file_path),
                    "SRP違反",
                    f"大きすぎるクラスがあります ({metrics['max_class_lines']}行)",
                    metrics["max_class_lines"],
                )
            )
            violations_found = True

        # 4. 大きすぎる関数チェック
        if metrics.get("max_function_lines", 0) > 20:
            self.violations.append(
                (
                    str(file_path),
                    "SRP違反",
                    f"大きすぎる関数があります ({metrics['max_function_lines']}行)",
                    metrics["max_function_lines"],
                )
            )
            violations_found = True

        return not violations_found

    def check_naming_conventions(self, file_path: Path) -> bool:
        """命名規則の違反をチェック"""
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)
            violations_found = False

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # クラス名はPascalCase
                    if not re.match(r"^[A-Z][a-zA-Z0-9]*$", node.name):
                        self.violations.append(
                            (
                                str(file_path),
                                "命名規則違反",
                                f"クラス名 '{node.name}' はPascalCaseである必要があります",
                                node.lineno,
                            )
                        )
                        violations_found = True

                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # 関数名はsnake_case
                    if not re.match(
                        r"^[a-z_][a-z0-9_]*$", node.name
                    ) and not node.name.startswith("__"):
                        self.violations.append(
                            (
                                str(file_path),
                                "命名規則違反",
                                f"関数名 '{node.name}' はsnake_caseである必要があります",
                                node.lineno,
                            )
                        )
                        violations_found = True

            return not violations_found

        except Exception as e:
            print(f"Warning: 命名規則チェックエラー {file_path}: {e}", file=sys.stderr)
            return True

    def check_import_organization(self, file_path: Path) -> bool:
        """インポート構成の問題をチェック"""
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.splitlines()
            violations_found = False

            import_count = content.count("import ") + content.count("from ")

            # インポートが多すぎる場合
            if import_count > 20:
                self.violations.append(
                    (
                        str(file_path),
                        "インポート過多",
                        f"インポート数が多すぎます ({import_count}個)",
                        None,
                    )
                )
                violations_found = True

            # 循環インポートの可能性チェック（簡易版）
            relative_imports = [
                line for line in lines if line.strip().startswith("from .")
            ]
            if len(relative_imports) > 5:
                self.violations.append(
                    (
                        str(file_path),
                        "相対インポート過多",
                        f"相対インポートが多く循環依存の可能性があります ({len(relative_imports)}個)",
                        None,
                    )
                )
                violations_found = True

            return not violations_found

        except Exception as e:
            print(
                f"Warning: インポートチェックエラー {file_path}: {e}", file=sys.stderr
            )
            return True

    def check_complexity(self, file_path: Path, metrics: Dict[str, int]) -> bool:
        """コード複雑度をチェック"""
        violations_found = False

        # 複雑度が高すぎる場合
        complexity = metrics.get("complexity", 0)
        lines = metrics.get("lines", 1)
        complexity_ratio = complexity / lines if lines > 0 else 0

        if complexity_ratio > 0.1:  # 10行に1つ以上の分岐
            self.violations.append(
                (
                    str(file_path),
                    "複雑度過多",
                    f"分岐が多すぎます (複雑度: {complexity}, 比率: {complexity_ratio:.2f})",
                    complexity,
                )
            )
            violations_found = True

        return not violations_found

    def check_directory(self, target_dir: Path) -> bool:
        """ディレクトリ全体をチェック"""
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
            "**/scripts/**",
        ]

        filtered_files = []
        for file_path in python_files:
            should_exclude = any(
                file_path.match(pattern) for pattern in excluded_patterns
            )
            if not should_exclude:
                filtered_files.append(file_path)

        print(f"チェック対象: {len(filtered_files)} ファイル")

        all_passed = True
        for file_path in filtered_files:
            metrics = self.analyze_file(file_path)
            self.metrics[str(file_path)] = metrics

            # 各種チェック実行
            checks = [
                self.check_single_responsibility(file_path, metrics),
                self.check_naming_conventions(file_path),
                self.check_import_organization(file_path),
                self.check_complexity(file_path, metrics),
            ]

            if not all(checks):
                all_passed = False

        return all_passed

    def print_violations(self) -> None:
        """違反項目を出力"""
        if not self.violations:
            print("✅ アーキテクチャルールに違反はありません")
            return

        print("\n❌ アーキテクチャルール違反:")
        print("=" * 80)

        # 違反タイプ別にグループ化
        by_type = defaultdict(list)
        for violation in self.violations:
            by_type[violation[1]].append(violation)

        for violation_type, violations in by_type.items():
            print(f"\n🚨 {violation_type} ({len(violations)}件)")
            print("-" * 40)

            for file_path, _, message, line_num in violations:
                relative_path = (
                    Path(file_path).relative_to(Path.cwd())
                    if Path(file_path).is_absolute()
                    else file_path
                )
                line_info = f" (行: {line_num})" if line_num else ""
                print(f"📁 {relative_path}{line_info}")
                print(f"   {message}")

        print("\n🔧 推奨対策:")
        if "SRP違反" in by_type:
            print("  • Single Responsibility Principleに従ってファイル・クラスを分割")
        if "命名規則違反" in by_type:
            print("  • PascalCase (クラス) / snake_case (関数・変数) に統一")
        if "インポート過多" in by_type:
            print("  • 関連する機能をモジュール単位でグループ化")
        if "複雑度過多" in by_type:
            print("  • 条件分岐を関数に分割、ストラテジーパターンの適用")

    def print_summary(self) -> None:
        """全体サマリーを出力"""
        if not self.metrics:
            return

        total_lines = sum(m.get("lines", 0) for m in self.metrics.values())
        total_classes = sum(m.get("classes", 0) for m in self.metrics.values())
        total_functions = sum(m.get("functions", 0) for m in self.metrics.values())

        print(f"\n📊 コードベース統計:")
        print(f"  • 総ファイル数: {len(self.metrics)}")
        print(f"  • 総行数: {total_lines:,}")
        print(f"  • 総クラス数: {total_classes}")
        print(f"  • 総関数数: {total_functions}")

        # 最大ファイルを特定
        largest_file = max(self.metrics.items(), key=lambda x: x[1].get("lines", 0))
        if largest_file[1].get("lines", 0) > 0:
            relative_path = (
                Path(largest_file[0]).relative_to(Path.cwd())
                if Path(largest_file[0]).is_absolute()
                else largest_file[0]
            )
            print(f"  • 最大ファイル: {relative_path} ({largest_file[1]['lines']}行)")


def main() -> None:
    """メイン処理"""
    parser = argparse.ArgumentParser(description="アーキテクチャルールチェッカー")
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=Path("kumihan_formatter"),
        help="チェック対象ディレクトリ (デフォルト: kumihan_formatter)",
    )
    parser.add_argument(
        "--strict", action="store_true", help="厳格モード（より厳しいチェック）"
    )

    args = parser.parse_args()

    if not args.target_dir.exists():
        print(
            f"エラー: ディレクトリが見つかりません: {args.target_dir}", file=sys.stderr
        )
        sys.exit(1)

    checker = ArchitectureChecker(strict_mode=args.strict)

    print(f"🏗️  アーキテクチャチェック開始")
    print(f"対象: {args.target_dir}")
    print(f"モード: {'厳格' if args.strict else '標準'}")
    print("-" * 60)

    success = checker.check_directory(args.target_dir)
    checker.print_violations()
    checker.print_summary()

    if success:
        print("\n🎉 アーキテクチャルールに準拠しています！")
        sys.exit(0)
    else:
        print(f"\n❌ {len(checker.violations)} 件の違反が見つかりました")
        print("技術的負債の蓄積を防ぐため、アーキテクチャを改善してください")
        sys.exit(1)


if __name__ == "__main__":
    main()
