#!/usr/bin/env python3
"""
Kumihan-Formatter アーキテクチャバリデーター

アーキテクチャ原則の自動チェックツール
Issue #319対応 - 定期的リファクタリングを不要にする予防的品質管理
"""

import argparse
import ast
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional


class ViolationSeverity(Enum):
    """違反の重要度"""

    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ArchitectureViolation:
    """アーキテクチャ原則違反"""

    file_path: Path
    line_number: int
    severity: ViolationSeverity
    rule_name: str
    message: str
    suggestion: Optional[str] = None


class ArchitectureValidator:
    """アーキテクチャ原則バリデーター"""

    # アーキテクチャ原則の設定
    MAX_FILE_LINES = 300
    MAX_FUNCTION_LINES = 50
    MAX_CLASS_LINES = 200
    MAX_COMPLEXITY = 10

    # レイヤー依存関係ルール
    LAYER_HIERARCHY = {"cli": 0, "commands": 1, "core": 2, "utilities": 3, "utils": 3}

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.violations: List[ArchitectureViolation] = []

    def validate_all(self) -> List[ArchitectureViolation]:
        """全ての検証を実行"""
        python_files = list(self.project_root.glob("kumihan_formatter/**/*.py"))

        for file_path in python_files:
            if file_path.name.startswith("__"):
                continue

            self._validate_file(file_path)

        return self.violations

    def _validate_file(self, file_path: Path) -> None:
        """単一ファイルの検証"""
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")

            # ファイルサイズチェック
            self._check_file_size(file_path, lines)

            # AST解析による詳細チェック
            try:
                tree = ast.parse(content)
                self._check_ast(file_path, tree, lines)
            except SyntaxError as e:
                self._add_violation(
                    file_path,
                    e.lineno or 1,
                    ViolationSeverity.ERROR,
                    "syntax_error",
                    f"構文エラー: {e.msg}",
                )

        except Exception as e:
            self._add_violation(
                file_path,
                1,
                ViolationSeverity.ERROR,
                "file_read_error",
                f"ファイル読み込みエラー: {e}",
            )

    def _check_file_size(self, file_path: Path, lines: List[str]) -> None:
        """ファイルサイズチェック"""
        line_count = len([line for line in lines if line.strip()])

        if line_count > self.MAX_FILE_LINES:
            self._add_violation(
                file_path,
                1,
                ViolationSeverity.CRITICAL,
                "file_too_large",
                f"ファイルサイズが制限を超過: {line_count}行 > {self.MAX_FILE_LINES}行",
                "ファイルを複数の責任に分割してください",
            )
        elif line_count > self.MAX_FILE_LINES * 0.8:
            self._add_violation(
                file_path,
                1,
                ViolationSeverity.WARNING,
                "file_size_warning",
                f"ファイルサイズが警告レベル: {line_count}行 (制限: {self.MAX_FILE_LINES}行)",
                "ファイル分割を検討してください",
            )

    def _check_ast(self, file_path: Path, tree: ast.AST, lines: List[str]) -> None:
        """AST解析による詳細チェック"""

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self._check_function_size(file_path, node, lines)
                self._check_function_complexity(file_path, node)

            elif isinstance(node, ast.ClassDef):
                self._check_class_size(file_path, node, lines)
                self._check_class_responsibility(file_path, node)

            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                self._check_dependency_direction(file_path, node)

    def _check_function_size(
        self, file_path: Path, node: ast.FunctionDef, lines: List[str]
    ) -> None:
        """関数サイズチェック"""
        if not hasattr(node, "lineno") or not hasattr(node, "end_lineno"):
            return

        func_lines = (node.end_lineno or node.lineno) - node.lineno + 1

        if func_lines > self.MAX_FUNCTION_LINES:
            self._add_violation(
                file_path,
                node.lineno,
                ViolationSeverity.ERROR,
                "function_too_large",
                f"関数 '{node.name}' が制限を超過: {func_lines}行 > {self.MAX_FUNCTION_LINES}行",
                "関数を小さな機能に分割してください",
            )

    def _check_class_size(
        self, file_path: Path, node: ast.ClassDef, lines: List[str]
    ) -> None:
        """クラスサイズチェック"""
        if not hasattr(node, "lineno") or not hasattr(node, "end_lineno"):
            return

        class_lines = (node.end_lineno or node.lineno) - node.lineno + 1

        if class_lines > self.MAX_CLASS_LINES:
            self._add_violation(
                file_path,
                node.lineno,
                ViolationSeverity.ERROR,
                "class_too_large",
                f"クラス '{node.name}' が制限を超過: {class_lines}行 > {self.MAX_CLASS_LINES}行",
                "クラスを複数の責任に分割してください",
            )

    def _check_function_complexity(
        self, file_path: Path, node: ast.FunctionDef
    ) -> None:
        """関数の複雑度チェック (簡易版McCabe複雑度)"""
        complexity = 1  # 基本複雑度

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        if complexity > self.MAX_COMPLEXITY:
            self._add_violation(
                file_path,
                node.lineno,
                ViolationSeverity.WARNING,
                "high_complexity",
                f"関数 '{node.name}' の複雑度が高い: {complexity} > {self.MAX_COMPLEXITY}",
                "条件分岐を減らすか、複数の関数に分割してください",
            )

    def _check_class_responsibility(self, file_path: Path, node: ast.ClassDef) -> None:
        """クラスの単一責任原則チェック"""
        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]

        # 簡易チェック: メソッド数が多すぎる場合
        if len(methods) > 15:
            self._add_violation(
                file_path,
                node.lineno,
                ViolationSeverity.WARNING,
                "too_many_methods",
                f"クラス '{node.name}' のメソッド数が多い: {len(methods)}個",
                "責任を分離し、複数のクラスに分割を検討してください",
            )

    def _check_dependency_direction(self, file_path: Path, node: ast.AST) -> None:
        """依存関係の方向性チェック"""
        if isinstance(node, ast.ImportFrom) and node.module:
            # 相対インポートの場合
            if node.level > 0:
                # 未使用変数を削除
                # module_parts = node.module.split(".")
                # current_layer = self._get_file_layer(file_path)

                # 上位レイヤーへの依存は禁止
                if node.level == 1:  # ..module
                    self._add_violation(
                        file_path,
                        node.lineno,
                        ViolationSeverity.ERROR,
                        "upward_dependency",
                        f"上位レイヤーへの依存が検出: {node.module}",
                        "依存関係を逆転させるか、抽象化を検討してください",
                    )

    def _get_file_layer(self, file_path: Path) -> str:
        """ファイルの所属レイヤーを特定"""
        relative_path = file_path.relative_to(self.project_root)
        parts = relative_path.parts

        if len(parts) >= 2 and parts[0] == "kumihan_formatter":
            layer = parts[1]
            return layer if layer in self.LAYER_HIERARCHY else "unknown"

        return "unknown"

    def _add_violation(
        self,
        file_path: Path,
        line_number: int,
        severity: ViolationSeverity,
        rule_name: str,
        message: str,
        suggestion: Optional[str] = None,
    ) -> None:
        """違反を記録"""
        violation = ArchitectureViolation(
            file_path=file_path,
            line_number=line_number,
            severity=severity,
            rule_name=rule_name,
            message=message,
            suggestion=suggestion,
        )
        self.violations.append(violation)

    def generate_report(self) -> str:
        """レポート生成"""
        if not self.violations:
            return "✅ アーキテクチャ原則違反は見つかりませんでした。"

        # 重要度別に集計
        by_severity: dict[str, list[ArchitectureViolation]] = {}
        for violation in self.violations:
            severity = violation.severity.value
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(violation)

        report_lines = ["🚨 アーキテクチャ原則違反レポート", "=" * 50]

        # サマリー
        report_lines.append(f"総違反数: {len(self.violations)}")
        for severity, violations in by_severity.items():
            report_lines.append(f"  {severity}: {len(violations)}件")
        report_lines.append("")

        # 詳細
        for severity in [
            ViolationSeverity.CRITICAL,
            ViolationSeverity.ERROR,
            ViolationSeverity.WARNING,
        ]:
            if severity.value not in by_severity:
                continue

            violations = by_severity[severity.value]
            report_lines.append(f"## {severity.value.upper()} ({len(violations)}件)")

            for violation in violations:
                relative_path = violation.file_path.relative_to(self.project_root)
                report_lines.append("")
                report_lines.append(f"📁 {relative_path}:{violation.line_number}")
                report_lines.append(f"🔍 {violation.rule_name}: {violation.message}")
                if violation.suggestion:
                    report_lines.append(f"💡 提案: {violation.suggestion}")

        return "\n".join(report_lines)


def main() -> None:
    """メイン実行"""
    parser = argparse.ArgumentParser(
        description="Kumihan-Formatter アーキテクチャバリデーター"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="プロジェクトルートディレクトリ",
    )
    parser.add_argument("--output", type=Path, help="レポート出力ファイル")
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="エラーがある場合に終了コード1で終了",
    )

    args = parser.parse_args()

    validator = ArchitectureValidator(args.project_root)
    violations = validator.validate_all()
    report = validator.generate_report()

    if args.output:
        args.output.write_text(report, encoding="utf-8")
        print(f"レポートを {args.output} に出力しました。")
    else:
        print(report)

    # エラーがある場合の終了コード
    if args.fail_on_error:
        has_critical_or_error = any(
            v.severity in [ViolationSeverity.CRITICAL, ViolationSeverity.ERROR]
            for v in violations
        )
        if has_critical_or_error:
            sys.exit(1)


if __name__ == "__main__":
    main()
