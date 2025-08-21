"""
品質チェッカー実装

Enterprise級品質基準に基づく
包括的コード品質検証システム
"""

import ast
import json
import os
import shutil
import subprocess
import sys
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
        # パス解決を絶対パスで統一
        self.project_root = self.project_root.resolve()

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
        issues: List[QualityIssue] = []

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

        def check_depth(
            node: ast.AST, current_depth: int = 0, func_name: str = ""
        ) -> None:
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
            logger.debug("Starting coverage check")

            # カバレッジレポート実行
            cmd = [
                "python3",
                "-m",
                "pytest",
                "--cov=kumihan_formatter",
                "--cov-report=json",
                "--quiet",
            ]
            logger.debug(f"Running coverage command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            logger.debug(f"Coverage command exit code: {result.returncode}")
            if result.stdout:
                logger.debug(f"Coverage stdout: {result.stdout}")
            if result.stderr:
                logger.debug(f"Coverage stderr: {result.stderr}")

            if result.returncode != 0:
                logger.warning(
                    f"pytest command failed with exit code {result.returncode}"
                )
                logger.warning(f"stderr: {result.stderr}")
                # pytest が失敗してもカバレッジファイルが作成される場合があるので続行

            coverage_file = self.project_root / "coverage.json"
            logger.debug(f"Looking for coverage file: {coverage_file}")

            if coverage_file.exists():
                logger.debug("Coverage file found, parsing data")
                with open(coverage_file, "r") as f:
                    coverage_data = json.load(f)

                logger.debug(f"Coverage data keys: {list(coverage_data.keys())}")

                total_coverage = coverage_data.get("totals", {}).get(
                    "percent_covered", 0
                )
                min_threshold = self.coverage_thresholds.get(
                    "global_thresholds", {}
                ).get("minimum", 70)

                logger.debug(
                    f"Total coverage: {total_coverage}%, threshold: {min_threshold}%"
                )

                status = "PASS" if total_coverage >= min_threshold else "FAIL"

                return QualityMetric(
                    name="test_coverage",
                    value=total_coverage,
                    threshold=min_threshold,
                    status=status,
                )
            else:
                logger.error(f"Coverage file not found: {coverage_file}")
                logger.error(
                    "This may indicate that pytest failed to run "
                    "or create coverage report"
                )

        except subprocess.SubprocessError as e:
            logger.error(f"Subprocess error during coverage check: {e}")
            logger.error("This may indicate pytest is not installed or not accessible")
        except FileNotFoundError as e:
            logger.error(f"File not found during coverage check: {e}")
            logger.error("This may indicate python3 or pytest is not in PATH")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse coverage JSON file: {e}")
            logger.error("Coverage file may be corrupted or incomplete")
        except Exception as e:
            logger.error(f"Unexpected error during coverage check: {e}")
            import traceback

            logger.error(f"Full traceback: {traceback.format_exc()}")

        logger.warning("Coverage check failed, returning default FAIL metric")
        return QualityMetric(
            name="test_coverage", value=0.0, threshold=70.0, status="FAIL"
        )

    def run_comprehensive_check(
        self,
        target_paths: Optional[List[Path]] = None,
        enable_external_tools: bool = False,
    ) -> Dict[str, Any]:
        """包括的品質チェック実行（外部ツール統合オプション付き）"""
        if target_paths is None:
            target_paths = [self.project_root / "kumihan_formatter"]

        all_issues = []
        metrics = []
        external_results = {}

        # ファイル品質チェック
        logger.debug(f"Starting file quality check for paths: {target_paths}")
        for target_path in target_paths:
            try:
                logger.debug(f"Processing target path: {target_path}")
                if target_path.is_file():
                    logger.debug(f"Checking single file: {target_path}")
                    all_issues.extend(self.check_file_quality(target_path))
                else:
                    logger.debug(f"Scanning directory for Python files: {target_path}")
                    py_files = list(target_path.rglob("*.py"))
                    logger.debug(f"Found {len(py_files)} Python files")
                    for py_file in py_files:
                        try:
                            logger.debug(f"Checking file: {py_file}")
                            all_issues.extend(self.check_file_quality(py_file))
                        except Exception as e:
                            logger.error(
                                f"Failed to check file quality for {py_file}: {e}"
                            )
                            # ファイル個別のエラーは記録するが処理は継続
            except Exception as e:
                logger.error(f"Failed to process target path {target_path}: {e}")
                # パス個別のエラーは記録するが処理は継続

        # カバレッジチェック
        coverage_metric = self.check_coverage()
        metrics.append(coverage_metric)

        # 外部ツール実行（オプション）
        if enable_external_tools:
            logger.info("外部品質ツールを実行")
            external_results = self._run_external_tools()

            # 外部ツール結果をメトリクスに追加
            for tool_name, tool_result in external_results.items():
                if tool_result.get("status") != "ERROR":
                    if "complexity" in tool_result:
                        metrics.append(
                            QualityMetric(
                                name=f"{tool_name}_complexity",
                                value=tool_result["complexity"].get("average", 0),
                                threshold=10.0,
                                status=(
                                    "PASS"
                                    if tool_result["complexity"].get("average", 0)
                                    <= 10.0
                                    else "WARN"
                                ),
                            )
                        )

        # 品質ゲート判定
        quality_gate_status = self._evaluate_quality_gate(all_issues, metrics)

        result = {
            "summary": {
                "total_issues": len(all_issues),
                "error_count": len([i for i in all_issues if i.severity == "ERROR"]),
                "warning_count": len(
                    [i for i in all_issues if i.severity == "WARNING"]
                ),
                "quality_gate_status": quality_gate_status,
                "external_tools_enabled": enable_external_tools,
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

        # 外部ツール結果を追加
        if external_results:
            result["external_tools"] = external_results

        return result

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

    def _run_external_tools(self) -> Dict[str, Any]:
        """外部品質ツール実行（radon、vulture、xenon）"""
        results = {}

        # radon複雑度チェック
        results["radon"] = self._run_radon_check()

        # vulture デッドコード検出
        results["vulture"] = self._run_vulture_check()

        # xenon 複雑度チェック（可能な場合）
        results["xenon"] = self._run_xenon_check()

        return results

    def _run_radon_check(self) -> Dict[str, Any]:
        """radon複雑度チェック実行"""
        logger.debug("radon複雑度チェックを実行")

        try:
            # 複雑度チェック
            result = subprocess.run(
                ["python3", "-m", "radon", "cc", "kumihan_formatter", "--json"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.project_root,
            )

            if result.returncode == 0 and result.stdout:
                complexity_data = json.loads(result.stdout)

                # 複雑度統計計算
                total_functions = 0
                complexity_sum = 0
                high_complexity_files = []

                for file_path, functions in complexity_data.items():
                    for func_data in functions:
                        if isinstance(func_data, dict) and "complexity" in func_data:
                            complexity = func_data["complexity"]
                            total_functions += 1
                            complexity_sum += complexity
                            if complexity > 10:
                                high_complexity_files.append(
                                    {
                                        "file": file_path,
                                        "function": func_data.get("name", "unknown"),
                                        "complexity": complexity,
                                    }
                                )

                average_complexity = (
                    complexity_sum / total_functions if total_functions > 0 else 0
                )

                return {
                    "status": "SUCCESS",
                    "complexity": {
                        "average": average_complexity,
                        "total_functions": total_functions,
                        "high_complexity_count": len(high_complexity_files),
                        "high_complexity_files": high_complexity_files[:10],  # 上位10件
                    },
                    "tool_version": "radon",
                }
            else:
                logger.warning(f"radon実行失敗: return_code={result.returncode}")
                if result.stderr:
                    logger.warning(f"radon stderr: {result.stderr}")

        except subprocess.TimeoutExpired:
            logger.error("radon実行がタイムアウト（60秒）")
        except FileNotFoundError:
            logger.error("radonコマンドが見つからない（未インストール）")
        except json.JSONDecodeError as e:
            logger.error(f"radon JSON解析失敗: {e}")
        except Exception as e:
            logger.error(f"radon実行中の予期しないエラー: {e}")

        return {
            "status": "ERROR",
            "error": "radon実行に失敗",
            "tool_version": "radon",
        }

    def _run_vulture_check(self) -> Dict[str, Any]:
        """vulture デッドコード検出実行"""
        logger.debug("vultureデッドコード検出を実行")

        try:
            result = subprocess.run(
                ["vulture", "kumihan_formatter"],
                capture_output=True,
                text=True,
                timeout=90,
                cwd=self.project_root,
            )

            # vultureは見つかった場合にreturn_code != 0になることがある
            dead_code_lines = [
                line for line in result.stdout.splitlines() if line.strip()
            ]

            return {
                "status": "SUCCESS",
                "dead_code": {
                    "count": len(dead_code_lines),
                    "issues": dead_code_lines[:20],  # 上位20件
                },
                "tool_version": "vulture",
            }

        except subprocess.TimeoutExpired:
            logger.error("vulture実行がタイムアウト（90秒）")
        except FileNotFoundError:
            logger.error("vultureコマンドが見つからない（未インストール）")
        except Exception as e:
            logger.error(f"vulture実行中の予期しないエラー: {e}")

        return {
            "status": "ERROR",
            "error": "vulture実行に失敗",
            "tool_version": "vulture",
        }

    def _run_xenon_check(self) -> Dict[str, Any]:
        """xenon 複雑度チェック実行"""
        logger.debug("xenon複雑度チェックを実行")

        try:
            result = subprocess.run(
                [
                    "xenon",
                    "--max-average",
                    "A",
                    "--max-modules",
                    "A",
                    "--max-absolute",
                    "B",
                    "kumihan_formatter",
                ],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.project_root,
            )

            return {
                "status": "SUCCESS",
                "complexity_grade": "A" if result.returncode == 0 else "B+",
                "return_code": result.returncode,
                "output": result.stdout.strip() if result.stdout else "No output",
                "tool_version": "xenon",
            }

        except subprocess.TimeoutExpired:
            logger.error("xenon実行がタイムアウト（60秒）")
        except FileNotFoundError:
            logger.error("xenonコマンドが見つからない（未インストール）")
        except Exception as e:
            logger.error(f"xenon実行中の予期しないエラー: {e}")

        return {
            "status": "ERROR",
            "error": "xenon実行に失敗",
            "tool_version": "xenon",
        }

    def _ensure_output_directory(self, dir_path: Path) -> bool:
        """安全なディレクトリ作成・権限確認（CI環境対応）"""
        try:
            logger.debug(f"Ensuring output directory: {dir_path}")

            # CI環境検出
            is_ci = any(
                [
                    os.getenv("CI") == "true",
                    os.getenv("GITHUB_ACTIONS") == "true",
                    os.getenv("CONTINUOUS_INTEGRATION") == "true",
                ]
            )
            logger.debug(f"CI environment detected: {is_ci}")

            # 親ディレクトリの確認
            parent_dir = dir_path.parent
            if not parent_dir.exists():
                logger.error(f"Parent directory does not exist: {parent_dir}")
                return False

            # 書き込み権限確認（CI環境では緩いチェック）
            if not os.access(parent_dir, os.W_OK):
                if is_ci:
                    logger.warning(
                        f"Limited write permission in CI environment: {parent_dir}"
                    )
                    # CI環境では一度作成を試みる
                    try:
                        test_file = parent_dir / ".write_test"
                        test_file.touch()
                        test_file.unlink()
                        logger.debug("Write test successful in CI environment")
                    except Exception as write_test_e:
                        logger.error(
                            f"Write test failed in CI environment: {write_test_e}"
                        )
                        return False
                else:
                    logger.error(
                        f"No write permission for parent directory: {parent_dir}"
                    )
                    return False

            # ディスク容量確認（1MB以上の余裕があるかチェック）
            try:
                _, _, free = shutil.disk_usage(parent_dir)
                if free < 1024 * 1024:  # 1MB
                    if is_ci:
                        logger.warning(
                            f"Low disk space in CI environment: {free} bytes available"
                        )
                    else:
                        logger.error(f"Insufficient disk space: {free} bytes available")
                        return False
                logger.debug(f"Disk space available: {free // (1024*1024)} MB")
            except Exception as e:
                logger.warning(f"Could not check disk usage: {e}")

            # ディレクトリ作成
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Successfully created/ensured directory: {dir_path}")

            # 作成後の権限確認
            if not os.access(dir_path, os.W_OK):
                logger.error(f"Directory created but not writable: {dir_path}")
                return False

            return True

        except PermissionError as e:
            logger.error(f"Permission denied creating directory {dir_path}: {e}")
            if is_ci:
                logger.error("This may be a CI environment permission issue")
            return False
        except OSError as e:
            logger.error(f"OS error creating directory {dir_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error creating directory {dir_path}: {e}")
            return False

    def _can_write_file(self, file_path: Path) -> bool:
        """ファイル書き込み可能性確認"""
        try:
            logger.debug(f"Checking write permissions for file: {file_path}")

            # ファイルが既に存在する場合
            if file_path.exists():
                if not os.access(file_path, os.W_OK):
                    logger.error(f"No write permission for existing file: {file_path}")
                    return False
                logger.debug(f"Existing file is writable: {file_path}")
            else:
                # 新規ファイルの場合は親ディレクトリの書き込み権限確認
                parent_dir = file_path.parent
                if not os.access(parent_dir, os.W_OK):
                    logger.error(
                        f"No write permission for parent directory: {parent_dir}"
                    )
                    return False
                logger.debug(f"Parent directory is writable for new file: {file_path}")

            return True

        except Exception as e:
            logger.error(f"Error checking file write permissions {file_path}: {e}")
            return False

    def _write_report_with_fallback(
        self, report: Dict[str, Any], output_path: Path, format_type: str
    ) -> bool:
        """フォールバック付きレポート出力"""
        try:
            logger.debug(f"Writing report to {output_path} in {format_type} format")

            if format_type == "json":
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
            else:  # yaml
                with open(output_path, "w", encoding="utf-8") as f:
                    yaml.dump(report, f, default_flow_style=False, allow_unicode=True)

            logger.info(f"Report successfully written to: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to write report to file {output_path}: {e}")
            logger.warning("Falling back to stdout output")

            # フォールバック: stdout出力
            try:
                if format_type == "json":
                    print(json.dumps(report, indent=2, ensure_ascii=False))
                else:  # yaml
                    print(
                        yaml.dump(report, default_flow_style=False, allow_unicode=True)
                    )
                logger.info("Report output to stdout as fallback")
                return False  # ファイル出力は失敗したが処理は成功
            except Exception as fallback_e:
                logger.error(f"Even stdout fallback failed: {fallback_e}")
                return False


def main() -> int:
    """CLI エントリーポイント"""
    import argparse
    import traceback

    try:
        logger.debug(f"Starting quality checker main function (Python {sys.version})")
        logger.debug(f"Running in environment: {os.getenv('GITHUB_ACTIONS', 'local')}")

        parser = argparse.ArgumentParser(description="Quality checker")
        parser.add_argument("--path", type=str, help="Target path to check")
        parser.add_argument("--output", type=str, help="Output report file")
        parser.add_argument(
            "--format", choices=["json", "yaml"], default="json", help="Output format"
        )
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Enable debug mode for detailed logging",
        )
        parser.add_argument(
            "--external-tools",
            action="store_true",
            help="Enable external quality tools (radon, vulture, xenon)",
        )

        args = parser.parse_args()
        logger.debug(f"Parsed arguments: {args}")

        # デバッグモード時はログレベルをDEBUGに設定
        if args.debug:
            logger.setLevel("DEBUG")
            logger.debug("Debug mode enabled")
            logger.debug(f"System info: Python {sys.version}, OS: {os.name}")
            logger.debug(f"Working directory: {os.getcwd()}")
            logger.debug(
                f"Environment variables: CI={os.getenv('CI')}, "
                f"GITHUB_ACTIONS={os.getenv('GITHUB_ACTIONS')}"
            )

        logger.debug("Initializing QualityChecker")
        checker = QualityChecker()
        logger.debug(f"Project root resolved to: {checker.project_root}")

        target_paths = None
        if args.path:
            target_paths = [Path(args.path)]
            logger.debug(f"Target paths set to: {target_paths}")

        logger.debug("Running comprehensive quality check")
        report: Dict[str, Any] = checker.run_comprehensive_check(
            target_paths, enable_external_tools=args.external_tools
        )
        logger.debug(
            f"Quality check completed. Report summary: {report.get('summary', {})}"
        )

        if args.external_tools:
            external_summary = {}
            for tool, result in report.get("external_tools", {}).items():
                external_summary[tool] = result.get("status", "UNKNOWN")
            logger.info(f"External tools results: {external_summary}")

        if args.output:
            logger.debug(f"Writing report to output file: {args.output}")

            # 絶対パスでの安全なディレクトリ作成
            tmp_dir = checker.project_root / "tmp"
            logger.debug(f"Using absolute tmp directory: {tmp_dir}")

            # 権限チェック付きディレクトリ作成
            if not checker._ensure_output_directory(tmp_dir):
                logger.warning(
                    "Failed to create output directory, falling back to stdout"
                )
                # フォールバック: stdout出力
                if args.format == "json":
                    print(json.dumps(report, indent=2, ensure_ascii=False))
                else:
                    print(
                        yaml.dump(report, default_flow_style=False, allow_unicode=True)
                    )
                logger.info("Report output to stdout due to directory creation failure")
            else:
                output_path = tmp_dir / args.output
                logger.debug(f"Target output path: {output_path}")

                # ファイル作成前の最終チェック
                if not checker._can_write_file(output_path):
                    logger.warning(
                        "Cannot write to target file, falling back to stdout"
                    )
                    # フォールバック: stdout出力
                    if args.format == "json":
                        print(json.dumps(report, indent=2, ensure_ascii=False))
                    else:
                        print(
                            yaml.dump(
                                report, default_flow_style=False, allow_unicode=True
                            )
                        )
                    logger.info("Report output to stdout due to file permission issues")
                else:
                    # 安全なファイル書き込み（フォールバック付き）
                    file_written = checker._write_report_with_fallback(
                        report, output_path, args.format
                    )
                    if file_written:
                        logger.debug(
                            f"{args.format.upper()} report written to: {output_path}"
                        )
                    else:
                        logger.debug("Report written via fallback mechanism")
        else:
            logger.debug("No output file specified, printing report to stdout")
            try:
                if args.format == "json":
                    print(json.dumps(report, indent=2, ensure_ascii=False))
                else:
                    print(
                        yaml.dump(report, default_flow_style=False, allow_unicode=True)
                    )
                logger.debug("Report successfully output to stdout")
            except Exception as e:
                logger.error(f"Failed to output report to stdout: {e}")
                # 最終手段としてシンプルなサマリを出力
                status = report.get('summary', {}).get('quality_gate_status', 'UNKNOWN')
                print(f"Quality check completed. Status: {status}")
                print(
                    f"Issues found: {report.get('summary', {}).get('total_issues', 0)}"
                )

        exit_code = 0 if report["summary"]["quality_gate_status"] == "PASSED" else 1
        logger.info(f"Quality check completed with exit code: {exit_code}")
        logger.debug(f"Final report summary: {report['summary']}")

        # CI環境での追加ログ
        if os.getenv("GITHUB_ACTIONS") == "true":
            gate_status = report['summary']['quality_gate_status']
            logger.info(f"GitHub Actions: Quality gate status = {gate_status}")
            logger.info(
                f"GitHub Actions: Total issues = {report['summary']['total_issues']}"
            )

        return exit_code

    except Exception as e:
        logger.error(f"Unexpected error in quality checker main function: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    exit(main())
