"""
品質チェッカー実装

Enterprise級品質基準に基づく
包括的コード品質検証システム
"""

import ast
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional

import yaml

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class QualityMetric(NamedTuple):
    """品質メトリクス"""

    name: str
    value: float
    threshold: float
    status: str  # "PASS", "WARN", "FAIL"


@dataclass
class QualityIssue:
    """品質問題"""

    file_path: str
    line_number: int
    issue_type: str
    severity: str  # "ERROR", "WARNING", "INFO"
    message: str
    rule_id: str


class QualityChecker:
    """品質チェッカー"""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.quality_rules = self._load_quality_rules()
        self.coverage_thresholds = self._load_coverage_thresholds()

    def _get_safe_line_number(self, node: ast.AST) -> int:
        """Python 3.13互換: ASTノードから安全に行番号を取得"""
        if hasattr(node, "lineno") and node.lineno is not None:
            return node.lineno
        # 親ノードから行番号を取得を試みる（AST nodeにはparent属性はないが、将来の拡張性のため）
        return 0

    def _load_quality_rules(self) -> Dict[str, Any]:
        """品質ルール読み込み"""
        rules_path = self.project_root / ".github" / "quality" / "quality_rules.yml"
        try:
            if rules_path.exists():
                with open(rules_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f)
            return self._get_default_rules()
        except Exception as e:
            logger.error(f"Failed to load quality rules: {e}")
            return self._get_default_rules()

    def _load_coverage_thresholds(self) -> Dict[str, Any]:
        """カバレッジ閾値読み込み"""
        coverage_path = (
            self.project_root / ".github" / "quality" / "coverage_thresholds.yml"
        )
        try:
            if coverage_path.exists():
                with open(coverage_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f)
            return {"global_thresholds": {"minimum": 70}}
        except Exception as e:
            logger.error(f"Failed to load coverage thresholds: {e}")
            return {"global_thresholds": {"minimum": 70}}

    def _get_default_rules(self) -> Dict[str, Any]:
        """デフォルト品質ルール"""
        return {
            "code_quality": {
                "complexity": {
                    "max_cyclomatic_complexity": 10,
                    "max_cognitive_complexity": 15,
                    "max_function_length": 50,
                    "max_class_length": 300,
                },
                "duplication": {
                    "max_duplicate_lines": 20,
                    "min_tokens_for_duplication": 50,
                },
                "maintainability": {
                    "min_maintainability_index": 20,
                    "max_nesting_depth": 4,
                    "max_parameters": 7,
                },
            },
            "quality_gates": {
                "blocking_conditions": [
                    "coverage < 70",
                    "security_issues > 0",
                    "cyclomatic_complexity > 10",
                    "test_failures > 0",
                    "lint_errors > 0",
                    "type_errors > 0",
                ]
            },
        }

    def check_file_quality(self, file_path: Path) -> List[QualityIssue]:
        """ファイル品質チェック"""
        issues = []

        if not file_path.suffix == ".py":
            return issues

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # AST解析
            tree = ast.parse(content)

            # 各種品質チェック実行
            issues.extend(self._check_complexity(file_path, tree))
            issues.extend(self._check_function_length(file_path, content))
            issues.extend(self._check_class_length(file_path, content))
            issues.extend(self._check_nesting_depth(file_path, tree))
            issues.extend(self._check_parameters(file_path, tree))

        except SyntaxError as e:
            issues.append(
                QualityIssue(
                    file_path=str(file_path),
                    line_number=e.lineno or 0,
                    issue_type="syntax_error",
                    severity="ERROR",
                    message=f"Syntax error: {e.msg}",
                    rule_id="syntax",
                )
            )
        except Exception as e:
            logger.error(f"Failed to check file quality {file_path}: {e}")

        return issues

    def _check_complexity(self, file_path: Path, tree: ast.AST) -> List[QualityIssue]:
        """循環的複雑度チェック"""
        issues = []
        max_complexity = (
            self.quality_rules.get("code_quality", {})
            .get("complexity", {})
            .get("max_cyclomatic_complexity", 10)
        )

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = self._calculate_cyclomatic_complexity(node)
                if complexity > max_complexity:
                    issues.append(
                        QualityIssue(
                            file_path=str(file_path),
                            line_number=self._get_safe_line_number(node),
                            issue_type="complexity",
                            severity=(
                                "WARNING"
                                if complexity <= max_complexity + 2
                                else "ERROR"
                            ),
                            message=(
                                f"Function '{node.name}' has complexity "
                                f"{complexity} (max: {max_complexity})"
                            ),
                            rule_id="cyclomatic_complexity",
                        )
                    )

        return issues

    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """循環的複雑度計算"""
        complexity = 1  # ベース複雑度

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.comprehension):
                complexity += 1

        return complexity

    def _check_function_length(
        self, file_path: Path, content: str
    ) -> List[QualityIssue]:
        """関数長チェック"""
        issues = []
        max_length = (
            self.quality_rules.get("code_quality", {})
            .get("complexity", {})
            .get("max_function_length", 50)
        )

        lines = content.split("\n")
        in_function = False
        func_start = 0
        func_name = ""
        indent_level = 0

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            if stripped.startswith(("def ", "async def ")):
                in_function = True
                func_start = i
                func_name = (
                    stripped.split("(")[0]
                    .replace("def ", "")
                    .replace("async ", "")
                    .strip()
                )
                indent_level = len(line) - len(line.lstrip())

            elif (
                in_function
                and line.strip()
                and len(line) - len(line.lstrip()) <= indent_level
                and not line.startswith(" " * (indent_level + 1))
            ):
                # 関数終了
                func_length = i - func_start
                if func_length > max_length:
                    issues.append(
                        QualityIssue(
                            file_path=str(file_path),
                            line_number=func_start,
                            issue_type="length",
                            severity=(
                                "WARNING" if func_length <= max_length + 10 else "ERROR"
                            ),
                            message=(
                                f"Function '{func_name}' is {func_length} lines "
                                f"(max: {max_length})"
                            ),
                            rule_id="function_length",
                        )
                    )
                in_function = False

        return issues

    def _check_class_length(self, file_path: Path, content: str) -> List[QualityIssue]:
        """クラス長チェック"""
        issues = []
        max_length = (
            self.quality_rules.get("code_quality", {})
            .get("complexity", {})
            .get("max_class_length", 300)
        )

        lines = content.split("\n")
        in_class = False
        class_start = 0
        class_name = ""
        indent_level = 0

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            if stripped.startswith("class "):
                in_class = True
                class_start = i
                class_name = stripped.split("(")[0].replace("class ", "").strip(":")
                indent_level = len(line) - len(line.lstrip())

            elif (
                in_class
                and line.strip()
                and len(line) - len(line.lstrip()) <= indent_level
                and not line.startswith(" " * (indent_level + 1))
            ):
                # クラス終了
                class_length = i - class_start
                if class_length > max_length:
                    issues.append(
                        QualityIssue(
                            file_path=str(file_path),
                            line_number=class_start,
                            issue_type="length",
                            severity=(
                                "WARNING"
                                if class_length <= max_length + 50
                                else "ERROR"
                            ),
                            message=(
                                f"Class '{class_name}' is {class_length} lines "
                                f"(max: {max_length})"
                            ),
                            rule_id="class_length",
                        )
                    )
                in_class = False

        return issues

    def _check_nesting_depth(
        self, file_path: Path, tree: ast.AST
    ) -> List[QualityIssue]:
        """ネスト深度チェック"""
        issues = []
        max_depth = (
            self.quality_rules.get("code_quality", {})
            .get("maintainability", {})
            .get("max_nesting_depth", 4)
        )

        def check_depth(node: ast.AST, current_depth: int = 0, func_name: str = ""):
            if isinstance(
                node,
                (
                    ast.If,
                    ast.While,
                    ast.For,
                    ast.AsyncFor,
                    ast.With,
                    ast.AsyncWith,
                    ast.Try,
                ),
            ):
                current_depth += 1
                if current_depth > max_depth:
                    issues.append(
                        QualityIssue(
                            file_path=str(file_path),
                            line_number=self._get_safe_line_number(node),
                            issue_type="nesting",
                            severity=(
                                "WARNING" if current_depth <= max_depth + 1 else "ERROR"
                            ),
                            message=(
                                f"Excessive nesting depth {current_depth} in "
                                f"{func_name or 'code'} (max: {max_depth})"
                            ),
                            rule_id="nesting_depth",
                        )
                    )

            for child in ast.iter_child_nodes(node):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    check_depth(child, 0, node.name)
                else:
                    check_depth(child, current_depth)

        check_depth(tree)
        return issues

    def _check_parameters(self, file_path: Path, tree: ast.AST) -> List[QualityIssue]:
        """パラメータ数チェック"""
        issues = []
        max_params = (
            self.quality_rules.get("code_quality", {})
            .get("maintainability", {})
            .get("max_parameters", 7)
        )

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                param_count = len(node.args.args) + len(node.args.kwonlyargs)
                if node.args.vararg:
                    param_count += 1
                if node.args.kwarg:
                    param_count += 1

                if param_count > max_params:
                    issues.append(
                        QualityIssue(
                            file_path=str(file_path),
                            line_number=self._get_safe_line_number(node),
                            issue_type="parameters",
                            severity=(
                                "WARNING" if param_count <= max_params + 2 else "ERROR"
                            ),
                            message=(
                                f"Function '{node.name}' has {param_count} "
                                f"parameters (max: {max_params})"
                            ),
                            rule_id="parameter_count",
                        )
                    )

        return issues

    def check_coverage(self) -> QualityMetric:
        """テストカバレッジチェック"""
        try:
            # カバレッジレポート実行
            subprocess.run(
                [
                    "python3",
                    "-m",
                    "pytest",
                    "--cov=kumihan_formatter",
                    "--cov-report=json",
                    "--quiet",
                ],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            coverage_file = self.project_root / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file, "r") as f:
                    coverage_data = json.load(f)

                total_coverage = coverage_data.get("totals", {}).get(
                    "percent_covered", 0
                )
                min_threshold = self.coverage_thresholds.get(
                    "global_thresholds", {}
                ).get("minimum", 70)

                status = "PASS" if total_coverage >= min_threshold else "FAIL"

                return QualityMetric(
                    name="test_coverage",
                    value=total_coverage,
                    threshold=min_threshold,
                    status=status,
                )

        except Exception as e:
            logger.error(f"Failed to check coverage: {e}")

        return QualityMetric(
            name="test_coverage", value=0.0, threshold=70.0, status="FAIL"
        )

    def run_comprehensive_check(
        self, target_paths: Optional[List[Path]] = None
    ) -> Dict[str, Any]:
        """包括的品質チェック実行"""
        if target_paths is None:
            target_paths = [self.project_root / "kumihan_formatter"]

        all_issues = []
        metrics = []

        # ファイル品質チェック
        for target_path in target_paths:
            if target_path.is_file():
                all_issues.extend(self.check_file_quality(target_path))
            else:
                for py_file in target_path.rglob("*.py"):
                    all_issues.extend(self.check_file_quality(py_file))

        # カバレッジチェック
        coverage_metric = self.check_coverage()
        metrics.append(coverage_metric)

        # 品質ゲート判定
        quality_gate_status = self._evaluate_quality_gate(all_issues, metrics)

        return {
            "summary": {
                "total_issues": len(all_issues),
                "error_count": len([i for i in all_issues if i.severity == "ERROR"]),
                "warning_count": len(
                    [i for i in all_issues if i.severity == "WARNING"]
                ),
                "quality_gate_status": quality_gate_status,
            },
            "issues": [
                {
                    "file_path": issue.file_path,
                    "line_number": issue.line_number,
                    "issue_type": issue.issue_type,
                    "severity": issue.severity,
                    "message": issue.message,
                    "rule_id": issue.rule_id,
                }
                for issue in all_issues
            ],
            "metrics": [
                {
                    "name": metric.name,
                    "value": metric.value,
                    "threshold": metric.threshold,
                    "status": metric.status,
                }
                for metric in metrics
            ],
        }

    def _evaluate_quality_gate(
        self, issues: List[QualityIssue], metrics: List[QualityMetric]
    ) -> str:
        """品質ゲート評価"""
        blocking_conditions = self.quality_rules.get("quality_gates", {}).get(
            "blocking_conditions", []
        )

        # エラー数チェック
        error_count = len([i for i in issues if i.severity == "ERROR"])
        if error_count > 0:
            return "FAILED"

        # メトリクス閾値チェック
        for metric in metrics:
            if metric.status == "FAIL":
                return "FAILED"

        # 品質ルール条件チェック
        for condition in blocking_conditions:
            if self._evaluate_condition(condition, issues, metrics):
                return "FAILED"

        return "PASSED"

    def _evaluate_condition(
        self, condition: str, issues: List[QualityIssue], metrics: List[QualityMetric]
    ) -> bool:
        """品質ゲート条件評価"""
        # 簡易的な条件評価（実際にはより複雑なパーサーが必要）
        if "coverage <" in condition:
            threshold = float(condition.split("<")[1].strip())
            for metric in metrics:
                if metric.name == "test_coverage" and metric.value < threshold:
                    return True

        if "security_issues >" in condition:
            # セキュリティ問題チェック（banditなど）
            security_issues = [i for i in issues if i.issue_type == "security"]
            threshold = int(condition.split(">")[1].strip())
            return len(security_issues) > threshold

        return False


def main():
    """CLI エントリーポイント"""
    import argparse

    parser = argparse.ArgumentParser(description="Quality checker")
    parser.add_argument("--path", type=str, help="Target path to check")
    parser.add_argument("--output", type=str, help="Output report file")
    parser.add_argument(
        "--format", choices=["json", "yaml"], default="json", help="Output format"
    )

    args = parser.parse_args()

    checker = QualityChecker()

    target_paths = None
    if args.path:
        target_paths = [Path(args.path)]

    report = checker.run_comprehensive_check(target_paths)

    if args.output:
        os.makedirs("tmp", exist_ok=True)
        output_path = Path("tmp") / args.output

        if args.format == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
        else:
            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(report, f, default_flow_style=False, allow_unicode=True)
    else:
        if args.format == "json":
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print(yaml.dump(report, default_flow_style=False, allow_unicode=True))

    return 0 if report["summary"]["quality_gate_status"] == "PASSED" else 1


if __name__ == "__main__":
    exit(main())
