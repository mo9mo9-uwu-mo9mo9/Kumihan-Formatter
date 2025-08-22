import argparse
import ast
import json
import math
import os
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)

# デフォルト品質しきい値設定
DEFAULT_THRESHOLDS = {
    "cognitive_complexity": 15,
    "maintainability_index": 20,
    "code_duplication": 5.0,  # %
    "max_dead_code": 10,  # files
    "halstead_volume": 1000.0,
    "halstead_difficulty": 50.0,
    "halstead_effort": 100000.0,
    "halstead_bugs": 1.0,
}


class TechDebtMonitor:
    """
    技術的負債を監視し、レポートを生成するクラス。
    """

    def __init__(
        self,
        target_directory: str = "kumihan_formatter/",
        threshold_config: Optional[str] = None,
    ):
        """
        初期化処理。

        Args:
            target_directory (str): 分析対象のディレクトリ。デフォルトは "kumihan_formatter/"。
            threshold_config (Optional[str]): しきい値設定ファイルパス。
        """
        self.target_directory = target_directory
        self.thresholds = self._load_threshold_config(threshold_config)

    def measure_cognitive_complexity(self) -> Dict[str, float]:
        """
        Cognitive Complexityを測定する（強化されたエラーハンドリング付き）。

        Returns:
            Dict[str, float]: ファイル名とCognitive Complexityの辞書。
        """
        logger.debug("認知複雑度測定を開始")

        try:
            logger.debug(f"radon ccコマンドを実行: {self.target_directory}")
            result = subprocess.run(
                ["radon", "cc", self.target_directory, "-j"],
                capture_output=True,
                text=True,
                check=True,
                timeout=60,  # 60秒タイムアウト
            )

            logger.debug(f"radon cc実行完了: return_code={result.returncode}")
            if result.stderr:
                logger.warning(f"radon cc stderr: {result.stderr}")

            try:
                result_data = json.loads(result.stdout)
                complexity_dict = dict(result_data) if isinstance(result_data, dict) else {}
                logger.info(f"認知複雑度測定成功: {len(complexity_dict)}ファイルを解析")
                return complexity_dict

            except json.JSONDecodeError as e:
                logger.error(f"radon cc JSON解析失敗: {e}")
                logger.warning("空の辞書を返して処理継続")
                return {}

        except subprocess.TimeoutExpired:
            logger.error("radon ccコマンドがタイムアウト（60秒）")
            logger.warning("graceful degradation: 空の結果を返して処理継続")
            return {}

        except FileNotFoundError:
            logger.error("radonコマンドが見つからない（未インストール）")
            logger.warning("graceful degradation: 空の結果を返して処理継続")
            return {}

        except subprocess.CalledProcessError as e:
            logger.error(f"radon ccコマンド実行失敗: return_code={e.returncode}")
            logger.error(
                f"stderr: {e.stderr}" if hasattr(e, "stderr") and e.stderr else "stderrなし"
            )
            logger.warning("graceful degradation: 空の結果を返して処理継続")
            return {}

        except Exception as e:
            logger.error(f"Cognitive Complexity測定中の予期しないエラー: {e}")
            logger.warning("graceful degradation: 空の結果を返して処理継続")
            return {}

    def calculate_maintainability_index(self) -> Dict[str, float]:
        """
        Maintainability Indexを計算する（強化されたエラーハンドリング付き）。

        Returns:
            Dict[str, float]: ファイル名とMaintainability Indexの辞書。
        """
        logger.debug("保守性指標計算を開始")

        try:
            logger.debug(f"radon miコマンドを実行: {self.target_directory}")
            result = subprocess.run(
                ["radon", "mi", self.target_directory, "-j"],
                capture_output=True,
                text=True,
                check=True,
                timeout=60,  # 60秒タイムアウト
            )

            logger.debug(f"radon mi実行完了: return_code={result.returncode}")
            if result.stderr:
                logger.warning(f"radon mi stderr: {result.stderr}")

            try:
                result_data = json.loads(result.stdout)
                maintainability_dict = dict(result_data) if isinstance(result_data, dict) else {}
                logger.info(f"保守性指標計算成功: {len(maintainability_dict)}ファイルを解析")
                return maintainability_dict

            except json.JSONDecodeError as e:
                logger.error(f"radon mi JSON解析失敗: {e}")
                logger.warning("空の辞書を返して処理継続")
                return {}

        except subprocess.TimeoutExpired:
            logger.error("radon miコマンドがタイムアウト（60秒）")
            logger.warning("graceful degradation: 空の結果を返して処理継続")
            return {}

        except FileNotFoundError:
            logger.error("radonコマンドが見つからない（未インストール）")
            logger.warning("graceful degradation: 空の結果を返して処理継続")
            return {}

        except subprocess.CalledProcessError as e:
            logger.error(f"radon miコマンド実行失敗: return_code={e.returncode}")
            logger.error(
                f"stderr: {e.stderr}" if hasattr(e, "stderr") and e.stderr else "stderrなし"
            )
            logger.warning("graceful degradation: 空の結果を返して処理継続")
            return {}

        except Exception as e:
            logger.error(f"Maintainability Index計算中の予期しないエラー: {e}")
            logger.warning("graceful degradation: 空の結果を返して処理継続")
            return {}

    def detect_code_duplication(self) -> List[Dict[Any, Any]]:
        """
        コードの重複を検出する。

        Returns:
            List[Dict]: 重複コードの情報リスト。
        """
        try:
            # duplicated が利用できないため、radon でファイル複雑度チェック
            result = subprocess.run(
                ["radon", "raw", self.target_directory, "-j"],
                capture_output=True,
                text=True,
                check=True,
            )
            result_data = json.loads(result.stdout)
            # 簡易的な重複検出（高複雑度ファイルを重複候補とする）
            duplicates = []
            if isinstance(result_data, dict):
                for file_path, metrics in result_data.items():
                    if isinstance(metrics, dict) and metrics.get("loc", 0) > 100:
                        duplicates.append(
                            {
                                "file": file_path,
                                "lines": metrics.get("loc", 0),
                                "reason": "高複雑度ファイル",
                            }
                        )
            return duplicates
        except subprocess.CalledProcessError as e:
            logger.error(f"コード分析に失敗しました: {e}")
            return []

    def detect_dead_code(self) -> List[str]:
        """
        デッドコードを検出する（強化されたエラーハンドリング付き）。

        Returns:
            List[str]: デッドコードのリスト。
        """
        logger.debug("デッドコード検出を開始")

        try:
            logger.debug(f"vultureコマンドを実行: {self.target_directory}")
            result = subprocess.run(
                ["vulture", self.target_directory],
                capture_output=True,
                text=True,
                timeout=90,  # 90秒タイムアウト
            )

            # vultureはreturn_codeが0以外でも正常な出力をする場合がある
            logger.debug(f"vulture実行完了: return_code={result.returncode}")
            if result.stderr:
                logger.warning(f"vulture stderr: {result.stderr}")

            dead_code_lines = [line for line in result.stdout.splitlines() if line.strip()]
            logger.info(f"デッドコード検出成功: {len(dead_code_lines)}件を検出")
            return dead_code_lines

        except subprocess.TimeoutExpired:
            logger.error("vultureコマンドがタイムアウト（90秒）")
            logger.warning("graceful degradation: 空のリストを返して処理継続")
            return []

        except FileNotFoundError:
            logger.error("vultureコマンドが見つからない（未インストール）")
            logger.warning("graceful degradation: 空のリストを返して処理継続")
            return []

        except subprocess.CalledProcessError as e:
            # vultureはデッドコードを発見した場合にreturn_codeが0以外になることがある
            logger.debug(f"vultureコマンド結果: return_code={e.returncode}")
            if hasattr(e, "stdout") and e.stdout:
                dead_code_lines = [line for line in e.stdout.splitlines() if line.strip()]
                logger.info(f"デッドコード検出成功: {len(dead_code_lines)}件を検出")
                return dead_code_lines
            else:
                logger.warning(f"vultureコマンド実行失敗: {e}")
                logger.warning("graceful degradation: 空のリストを返して処理継続")
                return []

        except Exception as e:
            logger.error(f"デッドコード検出中の予期しないエラー: {e}")
            logger.warning("graceful degradation: 空のリストを返して処理継続")
            return []

    def _load_threshold_config(self, config_path: Optional[str]) -> Dict[str, float]:
        """
        しきい値設定を読み込む。

        Args:
            config_path (Optional[str]): 設定ファイルパス。

        Returns:
            Dict[str, float]: しきい値設定。
        """
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    # デフォルト値とマージ
                    thresholds = DEFAULT_THRESHOLDS.copy()
                    thresholds.update(config)
                    return thresholds
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logger.warning(f"しきい値設定の読み込みに失敗: {e}. デフォルト値を使用")
        return DEFAULT_THRESHOLDS.copy()

    def calculate_halstead_metrics(self) -> Dict[str, Any]:
        """
        Halstead Metricsを計算する。

        Returns:
            Dict[str, Any]: ファイル別Halstead Metrics。
        """
        halstead_data = {}

        for root, _, files in os.walk(self.target_directory):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            source_code = f.read()
                        metrics = self._calculate_file_halstead(source_code)
                        if metrics:
                            halstead_data[file_path] = metrics
                    except Exception as e:
                        logger.warning(f"Halstead metrics計算失敗 {file_path}: {e}")

        return halstead_data

    def _calculate_file_halstead(self, source_code: str) -> Optional[Dict[str, float]]:
        """
        単一ファイルのHalstead Metricsを計算する。

        Args:
            source_code (str): ソースコード。

        Returns:
            Optional[Dict[str, float]]: Halstead Metrics。
        """
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return None

        operators = []
        operands = []

        class HalsteadVisitor(ast.NodeVisitor):
            def visit_BinOp(self, node: ast.BinOp) -> None:
                operators.append(type(node.op).__name__)
                self.generic_visit(node)

            def visit_UnaryOp(self, node: ast.UnaryOp) -> None:
                operators.append(type(node.op).__name__)
                self.generic_visit(node)

            def visit_Compare(self, node: ast.Compare) -> None:
                for op in node.ops:
                    operators.append(type(op).__name__)
                self.generic_visit(node)

            def visit_Name(self, node: ast.Name) -> None:
                operands.append(node.id)
                self.generic_visit(node)

            def visit_Constant(self, node: ast.Constant) -> None:
                operands.append(str(node.value))
                self.generic_visit(node)

        visitor = HalsteadVisitor()
        visitor.visit(tree)

        if not operators and not operands:
            return None

        n1 = len(set(operators))  # distinct operators
        n2 = len(set(operands))  # distinct operands
        N1 = len(operators)  # total operators
        N2 = len(operands)  # total operands

        if n1 == 0 or n2 == 0:
            return None

        vocabulary = n1 + n2
        length = N1 + N2

        try:
            calculated_length = n1 * math.log2(n1) + n2 * math.log2(n2)
            volume = length * math.log2(vocabulary) if vocabulary > 1 else 0
            difficulty = (n1 / 2) * (N2 / n2)
            effort = difficulty * volume
            time_required = effort / 18
            bugs = volume / 3000

            return {
                "volume": volume,
                "difficulty": difficulty,
                "effort": effort,
                "time": time_required,
                "bugs": bugs,
                "vocabulary": vocabulary,
                "length": length,
                "calculated_length": calculated_length,
            }
        except (ValueError, ZeroDivisionError):
            return None

    def check_quality_thresholds(self, all_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        品質しきい値をチェックし、違反項目を返す。

        Args:
            all_metrics (Dict[str, Any]): 全メトリクス。

        Returns:
            List[Dict[str, Any]]: 違反項目のリスト。
        """
        violations = []

        # Halstead Metricsのチェック
        if "halstead_metrics" in all_metrics:
            for file_path, metrics in all_metrics["halstead_metrics"].items():
                if not isinstance(metrics, dict):
                    continue

                for metric_name, value in metrics.items():
                    threshold_key = f"halstead_{metric_name}"
                    if threshold_key in self.thresholds:
                        threshold = self.thresholds[threshold_key]
                        if value > threshold:
                            violations.append(
                                {
                                    "file": file_path,
                                    "metric": metric_name,
                                    "value": value,
                                    "threshold": threshold,
                                    "severity": ("WARNING" if value < threshold * 1.5 else "ERROR"),
                                }
                            )

        return violations

    def generate_html_report(self, output_path: str) -> str:
        """
        HTMLレポートを生成する。

        Args:
            output_path (str): 出力ファイルパス。

        Returns:
            str: HTMLレポートのパス。
        """
        # TODO: Bootstrapを使用して、チャート表示を行うHTMLレポートを生成する
        #       Cognitive Complexity, Maintainability Index, 重複コード, デッドコードの情報を表示する
        #       この部分は外部ライブラリの利用も検討する (例: Jinja2)
        #       現状はプレースホルダーとして、簡単なHTMLを生成する
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Tech Debt Report</title>
        </head>
        <body>
            <h1>Tech Debt Report</h1>
            <p>This is a placeholder for the HTML report.</p>
            <p>Output Path: {output_path}</p>
        </body>
        </html>
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w") as f:
                f.write(html_content)
            return output_path
        except Exception as e:
            logger.error(f"HTMLレポートの生成に失敗しました: {e}")
            return ""

    def generate_json_report(self, output_path: str) -> Dict[str, Any]:
        """
        JSONレポートを生成する。

        Args:
            output_path (str): 出力ファイルパス。

        Returns:
            Dict: JSONレポートのデータ。
        """
        cognitive_complexity = self.measure_cognitive_complexity()
        maintainability_index = self.calculate_maintainability_index()
        code_duplication = self.detect_code_duplication()
        dead_code = self.detect_dead_code()
        halstead_metrics = self.calculate_halstead_metrics()

        report_data = {
            "cognitive_complexity": cognitive_complexity,
            "maintainability_index": maintainability_index,
            "code_duplication": code_duplication,
            "dead_code": dead_code,
            "halstead_metrics": halstead_metrics,
        }

        # 品質しきい値チェック
        violations = self.check_quality_thresholds(report_data)
        if violations:
            report_data["threshold_violations"] = violations

        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(report_data, f, indent=4)
            return report_data
        except Exception as e:
            logger.error(f"JSONレポートの生成に失敗しました: {e}")
            return {}

    def run_ci_validation(self) -> bool:
        """
        CI/CDの品質ゲートを実行する。

        Returns:
            bool: 品質基準を満たしている場合はTrue、そうでない場合はFalse。
        """
        # 全メトリクス収集
        all_metrics = {
            "cognitive_complexity": self.measure_cognitive_complexity(),
            "maintainability_index": self.calculate_maintainability_index(),
            "code_duplication": self.detect_code_duplication(),
            "dead_code": self.detect_dead_code(),
            "halstead_metrics": self.calculate_halstead_metrics(),
        }

        # 品質しきい値チェック
        violations = self.check_quality_thresholds(all_metrics)

        # デッドコード数チェック
        dead_code_count = len(all_metrics["dead_code"])
        if dead_code_count > self.thresholds["max_dead_code"]:
            violations.append(
                {
                    "file": "global",
                    "metric": "dead_code_count",
                    "value": dead_code_count,
                    "threshold": self.thresholds["max_dead_code"],
                    "severity": "ERROR",
                }
            )

        # 重複コード率チェック
        duplication_count = len(all_metrics["code_duplication"])
        if duplication_count > 0:
            total_files = sum(
                len(files)
                for _, _, files in os.walk(self.target_directory)
                if any(f.endswith(".py") for f in files)
            )
            duplication_rate = (duplication_count / total_files * 100) if total_files > 0 else 0

            if duplication_rate > self.thresholds["code_duplication"]:
                violations.append(
                    {
                        "file": "global",
                        "metric": "code_duplication_rate",
                        "value": duplication_rate,
                        "threshold": self.thresholds["code_duplication"],
                        "severity": "WARNING",
                    }
                )

        is_valid = len([v for v in violations if v["severity"] == "ERROR"]) == 0

        if violations:
            logger.warning(f"品質しきい値違反: {len(violations)}件")
            for violation in violations:
                logger.warning(
                    f"  {violation['severity']}: {violation['file']} - {violation['metric']}: "
                    f"{violation['value']:.2f} > {violation['threshold']}"
                )

        if not is_valid:
            logger.error("CI/CD品質ゲートに失敗しました。")
        else:
            logger.info("CI/CD品質ゲートに成功しました。")

        return is_valid

    def generate_improvement_report(self, output_path: str, format_type: str = "html") -> str:
        """
        改善提案レポートをHTMLまたはMarkdown形式で出力する。

        Args:
            output_path (str): 出力ファイルパス。
            format_type (str): 出力形式（"html" または "markdown"）。

        Returns:
            str: 生成されたレポートのパス。
        """
        # 全メトリクス収集
        all_metrics = {
            "cognitive_complexity": self.measure_cognitive_complexity(),
            "maintainability_index": self.calculate_maintainability_index(),
            "code_duplication": self.detect_code_duplication(),
            "dead_code": self.detect_dead_code(),
            "halstead_metrics": self.calculate_halstead_metrics(),
        }

        engine = QualityImprovementEngine(all_metrics)
        suggestions = engine.generate_improvement_suggestions()

        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            if format_type == "html":
                content = self._generate_html_improvement_report(suggestions, all_metrics)
            else:  # markdown
                content = self._generate_markdown_improvement_report(suggestions, all_metrics)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"改善提案レポートを生成しました: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"改善提案レポートの生成に失敗しました: {e}")
            return ""

    def _generate_html_improvement_report(
        self, suggestions: List[Dict[str, Any]], all_metrics: Dict[str, Any]
    ) -> str:
        """
        HTML形式の改善提案レポートを生成する。

        Args:
            suggestions (List[Dict[str, Any]]): 改善提案リスト。
            all_metrics (Dict[str, Any]): 全メトリクス。

        Returns:
            str: HTML形式のレポート。
        """
        html = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>コード品質改善提案レポート</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css"
          \n          rel="stylesheet">
    <style>
        .priority-high { border-left: 5px solid #dc3545; }
        .priority-medium { border-left: 5px solid #ffc107; }
        .priority-low { border-left: 5px solid #28a745; }
        .metric-card { margin-bottom: 1rem; }
    </style>
</head>
<body>
    <div class="container mt-4">
        <h1 class="mb-4">🎯 コード品質改善提案レポート</h1>
        <div class="row">
            <div class="col-md-8">
"""
        from datetime import datetime

        html += (
            f'                <p class="text-muted">生成日時: '
            f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>\n'
        )
        html += f"                <p><strong>検出された問題:</strong> {len(suggestions)}件</p>\n"

        if not suggestions:
            html += (
                '                <div class="alert alert-success">'
                "✅ 主要な品質問題は検出されませんでした。素晴らしいコードです！"
                "</div>\n"
            )
        else:
            # 優先度別グループ化
            high_priority = [s for s in suggestions if s["priority"] >= 0.7]
            medium_priority = [s for s in suggestions if 0.4 <= s["priority"] < 0.7]
            low_priority = [s for s in suggestions if s["priority"] < 0.4]

            for priority_level, suggestions_group, color_class in [
                ("高優先度（即座対応推奨）", high_priority, "priority-high"),
                ("中優先度（計画的対応推奨）", medium_priority, "priority-medium"),
                ("低優先度（余裕がある時に対応）", low_priority, "priority-low"),
            ]:
                if suggestions_group:
                    if "高" in priority_level:
                        html += f'                <h2 class="mt-4">🔴 {priority_level}</h2>\n'
                    elif "中" in priority_level:
                        html += f'                <h2 class="mt-4">🟡 {priority_level}</h2>\n'
                    else:
                        html += f'                <h2 class="mt-4">🟢 {priority_level}</h2>\n'
                    for suggestion in suggestions_group:
                        html += f"""                <div class="card metric-card {color_class}">
                    <div class="card-body">
                        <h5 class="card-title">{suggestion["file"]}</h5>
                        <p class="card-text">{suggestion["description"]}</p>
                        <div class="row">
                            <div class="col-md-4"><strong>優先度:</strong> {suggestion["priority"]:.2f}</div>
                            <div class="col-md-4"><strong>工数:</strong> {suggestion["effort_estimate"]}</div>
                            <div class="col-md-4"><strong>影響度:</strong> {suggestion["impact"]}</div>
                        </div>
                        <h6 class="mt-3">推奨アクション:</h6>
                        <ul>
"""
                        for action in suggestion["actions"]:
                            html += f"                            <li>{action}</li>\n"
                        html += """                        </ul>
                    </div>
                </div>
"""

        html += """            </div>
            <div class="col-md-4">
                <h3>📊 メトリクス概要</h3>
"""

        # メトリクス概要を追加
        html+= (
            f'                <div class="card"><div class="card-body"><h6>Cognitive Complexity</h6><p>{len(all_metrics.get("cognitive_complexity", {}))}ファイル分析</p></div></div>\n'
        )
        html+= (
            f'                <div class="card"><div class="card-body"><h6>Maintainability Index</h6><p>{len(all_metrics.get("maintainability_index", {}))}ファイル分析</p></div></div>\n'
        )
        html+= (
            f'                <div class="card"><div class="card-body"><h6>Halstead Metrics</h6><p>{len(all_metrics.get("halstead_metrics", {}))}ファイル分析</p></div></div>\n'
        )
        html+= (
            f'                <div class="card"><div class="card-body"><h6>Dead Code</h6><p>{len(all_metrics.get("dead_code", []))}件検出</p></div></div>\n'
        )

        html += """            </div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""
        return html

    def _generate_markdown_improvement_report(
        self, suggestions: List[Dict[str, Any]], all_metrics: Dict[str, Any]
    ) -> str:
        """
        Markdown形式の改善提案レポートを生成する。

        Args:
            suggestions (List[Dict[str, Any]]): 改善提案リスト。
            all_metrics (Dict[str, Any]): 全メトリクス。

        Returns:
            str: Markdown形式のレポート。
        """
        engine = QualityImprovementEngine(all_metrics)
        return engine.create_action_plan()

    def get_quality_score(self) -> float:
        """
        総合的な品質スコア（0-100）を算出する。

        Returns:
            float: 品質スコア。
        """
        # 全メトリクス収集
        all_metrics = {
            "cognitive_complexity": self.measure_cognitive_complexity(),
            "maintainability_index": self.calculate_maintainability_index(),
            "code_duplication": self.detect_code_duplication(),
            "dead_code": self.detect_dead_code(),
            "halstead_metrics": self.calculate_halstead_metrics(),
        }

        engine = QualityImprovementEngine(all_metrics)
        issues = engine.analyze_code_issues()

        if not issues:
            return 100.0

        # 問題の重要度に基づいてスコア減点
        total_penalty = 0.0
        for issue in issues:
            if issue["severity"] == "high":
                total_penalty += 20.0
            elif issue["severity"] == "medium":
                total_penalty += 10.0
            else:  # low
                total_penalty += 5.0

        # 最低スコアは10点とする
        quality_score = max(10.0, 100.0 - total_penalty)
        return quality_score


class QualityImprovementEngine:
    """
    コード品質改善のための提案を生成するエンジン。
    """

    def __init__(self, all_metrics: Dict[str, Any]) -> None:
        """
        初期化処理。

        Args:
            all_metrics (Dict[str, Any]): 全メトリクス分析結果。
        """
        self.all_metrics = all_metrics

    def analyze_code_issues(self) -> List[Dict[str, Any]]:
        """
        品質問題を分析し、改善可能な項目を特定する。

        Returns:
            List[Dict[str, Any]]: 検出された問題点のリスト。
        """
        issues = []

        # Cognitive Complexity問題検出
        if "cognitive_complexity" in self.all_metrics:
            for file_path, complexity in self.all_metrics["cognitive_complexity"].items():
                if isinstance(complexity, (int, float)) and complexity > 15:
                    issues.append(
                        {
                            "file": file_path,
                            "issue_type": "high_cognitive_complexity",
                            "metric": "cognitive_complexity",
                            "value": complexity,
                            "severity": "high" if complexity > 25 else "medium",
                            "description": f"認知複雑性が高すぎます（{complexity}）。関数分割を検討してください。",
                        }
                    )

        # Maintainability Index問題検出
        if "maintainability_index" in self.all_metrics:
            for file_path, index in self.all_metrics["maintainability_index"].items():
                if isinstance(index, (int, float)) and index < 20:
                    issues.append(
                        {
                            "file": file_path,
                            "issue_type": "low_maintainability",
                            "metric": "maintainability_index",
                            "value": index,
                            "severity": "high" if index < 10 else "medium",
                            "description": f"保守性指標が低いです（{index}）。コードの可読性向上が必要です。",
                        }
                    )

        # Halstead Metrics問題検出
        if "halstead_metrics" in self.all_metrics:
            for file_path, metrics in self.all_metrics["halstead_metrics"].items():
                if isinstance(metrics, dict):
                    volume = metrics.get("volume", 0)
                    difficulty = metrics.get("difficulty", 0)
                    effort = metrics.get("effort", 0)

                    if volume > 1000:
                        issues.append(
                            {
                                "file": file_path,
                                "issue_type": "high_halstead_volume",
                                "metric": "halstead_volume",
                                "value": volume,
                                "severity": "medium",
                                "description": (
                                    f"Halstead Volumeが高いです（{volume:.2f}）。コード分割を検討してください。",
                                ),
                            }
                        )

                    if difficulty > 50:
                        issues.append(
                            {
                                "file": file_path,
                                "issue_type": "high_halstead_difficulty",
                                "metric": "halstead_difficulty",
                                "value": difficulty,
                                "severity": "medium",
                                "description": (
                                    f"Halstead Difficultyが高いです（{difficulty:.2f}）。コード簡略化を検討してください。",
                                ),
                            }
                        )

        # Dead Code問題検出
        if "dead_code" in self.all_metrics:
            dead_code_files = self.all_metrics["dead_code"]
            if len(dead_code_files) > 0:
                issues.append(
                    {
                        "file": "multiple",
                        "issue_type": "dead_code_detected",
                        "metric": "dead_code_count",
                        "value": len(dead_code_files),
                        "severity": "low",
                        "description": f"未使用コードが検出されました（{len(dead_code_files)}件）。削除を検討してください。",
                    }
                )

        return issues

    def generate_improvement_suggestions(self) -> List[Dict[str, Any]]:
        """
        具体的な改善提案を生成する。

        Returns:
            List[Dict[str, Any]]: 改善提案のリスト。
        """
        issues = self.analyze_code_issues()
        suggestions = []

        for issue in issues:
            suggestion = {
                "file": issue["file"],
                "issue_type": issue["issue_type"],
                "priority": self.calculate_roi_priority(issue),
                "effort_estimate": self._estimate_effort(issue),
                "impact": self._estimate_impact(issue),
                "description": issue["description"],
            }

            # 具体的な改善アクション提案
            if issue["issue_type"] == "high_cognitive_complexity":
                suggestion["actions"] = [
                    "長いメソッドを複数の小さなメソッドに分割",
                    "複雑な条件分岐をearly returnパターンで簡略化",
                    "ネストした処理を別メソッドとして抽出",
                ]
            elif issue["issue_type"] == "low_maintainability":
                suggestion["actions"] = [
                    "変数・メソッド名をより分かりやすく命名",
                    "処理に対するコメント・docstringを追加",
                    "型ヒントを追加して可読性向上",
                ]
            elif issue["issue_type"] == "high_halstead_volume":
                suggestion["actions"] = [
                    "大きなメソッドを責任別に分割",
                    "共通処理をユーティリティ関数として抽出",
                    "データ構造を見直してロジック簡略化",
                ]
            elif issue["issue_type"] == "high_halstead_difficulty":
                suggestion["actions"] = [
                    "複雑な演算子の使用を避ける",
                    "条件分岐を guard clause で簡略化",
                    "一行で複数の処理を行わない",
                ]
            elif issue["issue_type"] == "dead_code_detected":
                suggestion["actions"] = [
                    "未使用の変数・関数・インポートを削除",
                    "到達不能なコードブロックを除去",
                    "使用されていないクラス・メソッドを削除",
                ]

            suggestions.append(suggestion)

        # 優先度でソート
        suggestions.sort(key=lambda x: x["priority"], reverse=True)
        return suggestions

    def calculate_roi_priority(self, issue: Dict[str, Any]) -> float:
        """
        ROI（Return on Investment）ベースで優先度を計算する。

        Args:
            issue (Dict[str, Any]): 問題情報。

        Returns:
            float: ROIベースの優先度（0.0-1.0）。
        """
        severity_weights = {"high": 0.8, "medium": 0.6, "low": 0.4}
        issue_type_weights = {
            "high_cognitive_complexity": 0.9,
            "low_maintainability": 0.8,
            "high_halstead_difficulty": 0.7,
            "high_halstead_volume": 0.6,
            "dead_code_detected": 0.5,
        }

        severity_score = severity_weights.get(issue.get("severity", "medium"), 0.6)
        issue_type_score = issue_type_weights.get(issue.get("issue_type", ""), 0.5)

        # 値の大きさによる重み付け
        value_score = 0.5
        if issue.get("metric") == "cognitive_complexity":
            value_score = min(1.0, issue.get("value", 0) / 50.0)
        elif issue.get("metric") == "maintainability_index":
            value_score = max(0.0, 1.0 - issue.get("value", 50) / 50.0)

        return severity_score * 0.4 + issue_type_score * 0.4 + value_score * 0.2

    def _estimate_effort(self, issue: Dict[str, Any]) -> str:
        """
        改善に必要な工数を推定する。

        Args:
            issue (Dict[str, Any]): 問題情報。

        Returns:
            str: 工数推定（"低", "中", "高"）。
        """
        effort_map = {
            "high_cognitive_complexity": "高",
            "low_maintainability": "中",
            "high_halstead_difficulty": "高",
            "high_halstead_volume": "高",
            "dead_code_detected": "低",
        }
        return effort_map.get(issue.get("issue_type", ""), "中")

    def _estimate_impact(self, issue: Dict[str, Any]) -> str:
        """
        改善による影響度を推定する。

        Args:
            issue (Dict[str, Any]): 問題情報。

        Returns:
            str: 影響度推定（"低", "中", "高"）。
        """
        impact_map = {
            "high_cognitive_complexity": "高",
            "low_maintainability": "高",
            "high_halstead_difficulty": "中",
            "high_halstead_volume": "中",
            "dead_code_detected": "低",
        }
        return impact_map.get(issue.get("issue_type", ""), "中")

    def create_action_plan(self) -> str:
        """
        統合的なアクションプランをMarkdown形式で生成する。

        Returns:
            str: Markdown形式のアクションプラン。
        """
        suggestions = self.generate_improvement_suggestions()

        action_plan = "# 🎯 コード品質改善アクションプラン\n\n"
        action_plan += f"**生成日時:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        action_plan += f"**検出された問題:** {len(suggestions)}件\n\n"

        if not suggestions:
            action_plan += "✅ **素晴らしいニュース！** 主要な品質問題は検出されませんでした。\n"
            return action_plan

        # 優先度別グループ化
        high_priority = [s for s in suggestions if s["priority"] >= 0.7]
        medium_priority = [s for s in suggestions if 0.4 <= s["priority"] < 0.7]
        low_priority = [s for s in suggestions if s["priority"] < 0.4]

        if high_priority:
            action_plan += "## 🔴 高優先度（即座対応推奨）\n\n"
            for suggestion in high_priority:
                action_plan += f"### {suggestion['file']}\n"
                action_plan += f"**問題:** {suggestion['description']}\n\n"
                action_plan +=(
                    f"**優先度:** {suggestion['priority']:.2f} | **工数:** {suggestion['effort_estimate']} | **影響度:** {suggestion['impact']}\n\n"
                )
                action_plan += "**推奨アクション:**\n"
                for action in suggestion["actions"]:
                    action_plan += f"- [ ] {action}\n"
                action_plan += "\n---\n\n"

        if medium_priority:
            action_plan += "## 🟡 中優先度（計画的対応推奨）\n\n"
            for suggestion in medium_priority:
                action_plan += f"### {suggestion['file']}\n"
                action_plan += f"**問題:** {suggestion['description']}\n\n"
                action_plan +=(
                    f"**優先度:** {suggestion['priority']:.2f} | **工数:** {suggestion['effort_estimate']} | **影響度:** {suggestion['impact']}\n\n"
                )
                action_plan += "**推奨アクション:**\n"
                for action in suggestion["actions"]:
                    action_plan += f"- [ ] {action}\n"
                action_plan += "\n---\n\n"

        if low_priority:
            action_plan += "## 🟢 低優先度（余裕がある時に対応）\n\n"
            for suggestion in low_priority:
                action_plan += f"### {suggestion['file']}\n"
                action_plan += f"**問題:** {suggestion['description']}\n\n"
                action_plan +=(
                    f"**優先度:** {suggestion['priority']:.2f} | **工数:** {suggestion['effort_estimate']} | **影響度:** {suggestion['impact']}\n\n"
                )
                action_plan += "**推奨アクション:**\n"
                for action in suggestion["actions"]:
                    action_plan += f"- [ ] {action}\n"
                action_plan += "\n---\n\n"

        action_plan += "## 📊 改善効果予測\n\n"
        action_plan += f"- **高優先度対応:** コード品質 +{len(high_priority) * 15}%向上見込み\n"
        action_plan += f"- **中優先度対応:** コード品質 +{len(medium_priority) * 10}%向上見込み\n"
        action_plan +=(
            f"- **全対応完了:** コード品質 +{(len(high_priority) * 15) + (len(medium_priority) * 10) + (len(low_priority) * 5)}%向上見込み\n\n"
        )

        return action_plan


def main() -> None:
    """
    メイン関数。
    """
    parser = argparse.ArgumentParser(description="技術的負債監視ツール")
    parser.add_argument(
        "--format",
        choices=["console", "html", "json"],
        default="console",
        help="出力フォーマット (console, html, json)",
    )
    parser.add_argument(
        "--output",
        default="tmp/tech_debt_report.html",
        help="出力ファイルパス",
    )
    parser.add_argument("--ci", action="store_true", help="CI/CDモード（品質ゲート）")
    parser.add_argument("--threshold-config", help="カスタムしきい値設定ファイルパス")
    # Phase 3: 自動改善提案システムのCLI引数
    parser.add_argument("--improvement", action="store_true", help="改善提案レポート生成モード")
    parser.add_argument("--action-plan", action="store_true", help="アクションプラン生成モード")
    parser.add_argument("--quality-score", action="store_true", help="品質スコア表示のみ")
    parser.add_argument(
        "--report-format",
        choices=["html", "markdown"],
        default="html",
        help="改善提案レポートの出力形式（html または markdown）",
    )

    args = parser.parse_args()

    monitor = TechDebtMonitor(threshold_config=args.threshold_config)

    if args.ci:
        if not monitor.run_ci_validation():
            exit(1)  # CI/CD失敗時はexit code 1
        else:
            exit(0)  # CI/CD成功時はexit code 0

    # Phase 3: 自動改善提案システム機能
    if args.improvement:
        output_path = (
            args.output.replace(".html", "_improvement.html")
            if args.report_format == "html"
            else args.output.replace(".html", "_improvement.md")
        )
        if not output_path.startswith("tmp/"):
            output_path = f"tmp/{os.path.basename(output_path)}"

        result_path = monitor.generate_improvement_report(output_path, args.report_format)
        if result_path:
            print(f"改善提案レポートを生成しました: {result_path}")
        else:
            print("改善提案レポートの生成に失敗しました。")

    elif args.action_plan:
        # 全メトリクス収集してアクションプラン生成
        all_metrics = {
            "cognitive_complexity": monitor.measure_cognitive_complexity(),
            "maintainability_index": monitor.calculate_maintainability_index(),
            "code_duplication": monitor.detect_code_duplication(),
            "dead_code": monitor.detect_dead_code(),
            "halstead_metrics": monitor.calculate_halstead_metrics(),
        }

        engine = QualityImprovementEngine(all_metrics)
        action_plan = engine.create_action_plan()

        # tmp/配下にMarkdownファイルとして保存
        output_path = "tmp/action_plan.md"
        try:
            os.makedirs("tmp", exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(action_plan)
            print(f"アクションプランを生成しました: {output_path}")
            print("\n" + action_plan)
        except Exception as e:
            logger.error(f"アクションプランの保存に失敗しました: {e}")
            print(action_plan)  # 保存に失敗してもコンソールには表示

    elif args.quality_score:
        score = monitor.get_quality_score()
        print(f"📊 総合品質スコア: {score:.1f}/100")

        if score >= 90:
            print("🎉 優秀！コード品質は非常に高いレベルです。")
        elif score >= 75:
            print("👍 良好！コード品質は十分なレベルです。")
        elif score >= 60:
            print("⚠️  普通。いくつかの改善点があります。")
        elif score >= 40:
            print("🔄 要改善。品質向上が必要です。")
        else:
            print("🚨 要緊急対応。大幅な品質改善が必要です。")

    elif args.format == "console":
        cognitive_complexity = monitor.measure_cognitive_complexity()
        maintainability_index = monitor.calculate_maintainability_index()
        code_duplication = monitor.detect_code_duplication()
        dead_code = monitor.detect_dead_code()
        halstead_metrics = monitor.calculate_halstead_metrics()

        print("Cognitive Complexity:", cognitive_complexity)
        print("Maintainability Index:", maintainability_index)
        print("Code Duplication:", code_duplication)
        print("Dead Code:", dead_code)
        print("Halstead Metrics:", f"{len(halstead_metrics)} files analyzed")

    elif args.format == "html":
        monitor.generate_html_report(args.output)
        print(f"HTMLレポートを生成しました: {args.output}")

    elif args.format == "json":
        monitor.generate_json_report(args.output)
        print(f"JSONレポートを生成しました: {args.output}")


if __name__ == "__main__":
    main()
