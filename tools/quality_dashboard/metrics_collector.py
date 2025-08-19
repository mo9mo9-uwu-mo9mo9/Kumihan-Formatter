"""
品質メトリクス収集システム

カバレッジ、複雑度、パフォーマンス等の
包括的品質指標を収集・管理する
"""

import json
import os
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


class MetricsCollector:
    """品質メトリクス収集管理"""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.quality_rules = self._load_quality_rules()
        self.coverage_thresholds = self._load_coverage_thresholds()
        self.metrics_history_file = self.project_root / "tmp" / "metrics_history.json"
        os.makedirs("tmp", exist_ok=True)

    def _load_quality_rules(self) -> Dict[str, Any]:
        """品質ルール読み込み"""
        rules_path = self.project_root / ".github" / "quality" / "quality_rules.yml"
        try:
            if rules_path.exists():
                with open(rules_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f)
            return {}
        except Exception as e:
            logger.error(f"Failed to load quality rules: {e}")
            return {}

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

    def collect_coverage_metrics(self) -> Dict[str, Any]:
        """カバレッジメトリクス収集"""
        try:
            # pytest実行でカバレッジ取得
            result = subprocess.run(
                [
                    "python3",
                    "-m",
                    "pytest",
                    "--cov=kumihan_formatter",
                    "--cov-report=json",
                    "--cov-report=term-missing",
                    "--quiet",
                ],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=300,
            )

            coverage_file = self.project_root / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file, "r") as f:
                    coverage_data = json.load(f)

                # カバレッジメトリクス構築
                total_coverage = coverage_data.get("totals", {}).get(
                    "percent_covered", 0
                )

                # モジュール別カバレッジ
                module_coverage = {}
                for file_path, file_data in coverage_data.get("files", {}).items():
                    if "kumihan_formatter" in file_path:
                        module_key = self._get_module_name(file_path)
                        if module_key not in module_coverage:
                            module_coverage[module_key] = []
                        module_coverage[module_key].append(
                            file_data.get("summary", {}).get("percent_covered", 0)
                        )

                # モジュール別平均計算
                module_averages = {}
                for module, coverages in module_coverage.items():
                    module_averages[module] = (
                        sum(coverages) / len(coverages) if coverages else 0
                    )

                # 閾値との比較
                global_threshold = self.coverage_thresholds.get(
                    "global_thresholds", {}
                ).get("minimum", 70)
                status = "PASS" if total_coverage >= global_threshold else "FAIL"

                return {
                    "timestamp": datetime.now().isoformat(),
                    "total_coverage": total_coverage,
                    "module_coverage": module_averages,
                    "threshold": global_threshold,
                    "status": status,
                    "files_count": len(coverage_data.get("files", {})),
                    "lines_covered": coverage_data.get("totals", {}).get(
                        "covered_lines", 0
                    ),
                    "lines_total": coverage_data.get("totals", {}).get(
                        "num_statements", 0
                    ),
                }

        except Exception as e:
            logger.error(f"Failed to collect coverage metrics: {e}")

        return {
            "timestamp": datetime.now().isoformat(),
            "total_coverage": 0,
            "status": "ERROR",
            "error": "Failed to collect coverage data",
        }

    def _get_module_name(self, file_path: str) -> str:
        """ファイルパスからモジュール名抽出"""
        if "core/parser" in file_path:
            return "core_parser"
        elif "core/rendering" in file_path:
            return "core_rendering"
        elif "core/" in file_path:
            return "core"
        elif "cli/" in file_path:
            return "cli"
        elif "config/" in file_path:
            return "config"
        else:
            return "other"

    def collect_complexity_metrics(self) -> Dict[str, Any]:
        """複雑度メトリクス収集"""
        try:
            # radonを使用して複雑度測定
            result = subprocess.run(
                ["python3", "-m", "radon", "cc", "kumihan_formatter", "--json"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.returncode == 0 and result.stdout:
                complexity_data = json.loads(result.stdout)

                # 複雑度統計計算
                total_functions = 0
                complexity_sum = 0
                high_complexity_count = 0
                max_complexity = (
                    self.quality_rules.get("code_quality", {})
                    .get("complexity", {})
                    .get("max_cyclomatic_complexity", 10)
                )

                for file_path, functions in complexity_data.items():
                    for func_data in functions:
                        if isinstance(func_data, dict) and "complexity" in func_data:
                            complexity = func_data["complexity"]
                            total_functions += 1
                            complexity_sum += complexity
                            if complexity > max_complexity:
                                high_complexity_count += 1

                average_complexity = (
                    complexity_sum / total_functions if total_functions > 0 else 0
                )

                return {
                    "timestamp": datetime.now().isoformat(),
                    "average_complexity": average_complexity,
                    "total_functions": total_functions,
                    "high_complexity_count": high_complexity_count,
                    "max_complexity_threshold": max_complexity,
                    "complexity_ratio": (
                        high_complexity_count / total_functions
                        if total_functions > 0
                        else 0
                    ),
                    "status": "PASS" if high_complexity_count == 0 else "WARNING",
                }

        except Exception as e:
            logger.error(f"Failed to collect complexity metrics: {e}")

        return {
            "timestamp": datetime.now().isoformat(),
            "status": "ERROR",
            "error": "Failed to collect complexity data",
        }

    def collect_performance_metrics(self) -> Dict[str, Any]:
        """パフォーマンスメトリクス収集"""
        try:
            import psutil

            # メモリ使用量測定
            process = psutil.Process()
            memory_info = process.memory_info()

            # 起動時間測定（簡易）
            start_time = time.time()
            try:
                subprocess.run(
                    ["python3", "-c", "import kumihan_formatter"],
                    capture_output=True,
                    timeout=10,
                )
            except subprocess.TimeoutExpired:
                pass
            import_time = (time.time() - start_time) * 1000  # ms

            # パフォーマンス基準読み込み
            performance_benchmarks = self._load_performance_benchmarks()
            startup_threshold = performance_benchmarks.get(
                "startup_performance", {}
            ).get("target_ms", 600)
            memory_threshold = performance_benchmarks.get("memory_performance", {}).get(
                "target_mb", 32
            )

            current_memory_mb = memory_info.rss / 1024 / 1024

            return {
                "timestamp": datetime.now().isoformat(),
                "startup_time_ms": import_time,
                "memory_usage_mb": current_memory_mb,
                "startup_threshold_ms": startup_threshold,
                "memory_threshold_mb": memory_threshold,
                "startup_status": (
                    "PASS" if import_time <= startup_threshold else "WARNING"
                ),
                "memory_status": (
                    "PASS" if current_memory_mb <= memory_threshold else "WARNING"
                ),
                "overall_status": (
                    "PASS"
                    if import_time <= startup_threshold
                    and current_memory_mb <= memory_threshold
                    else "WARNING"
                ),
            }

        except Exception as e:
            logger.error(f"Failed to collect performance metrics: {e}")

        return {
            "timestamp": datetime.now().isoformat(),
            "status": "ERROR",
            "error": "Failed to collect performance data",
        }

    def _load_performance_benchmarks(self) -> Dict[str, Any]:
        """パフォーマンス基準読み込み"""
        benchmarks_path = (
            self.project_root / ".github" / "quality" / "performance_benchmarks.yml"
        )
        try:
            if benchmarks_path.exists():
                with open(benchmarks_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f)
            return {}
        except Exception as e:
            logger.error(f"Failed to load performance benchmarks: {e}")
            return {}

    def collect_lint_metrics(self) -> Dict[str, Any]:
        """Lintメトリクス収集"""
        try:
            # flake8実行
            result = subprocess.run(
                ["python3", "-m", "flake8", "kumihan_formatter", "--format=json"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            lint_issues = []
            if result.stdout:
                try:
                    lint_data = json.loads(result.stdout)
                    lint_issues = lint_data if isinstance(lint_data, list) else []
                except json.JSONDecodeError:
                    # JSONでない場合は行数でカウント
                    lint_issues = (
                        result.stdout.strip().split("\n")
                        if result.stdout.strip()
                        else []
                    )

            # 問題の分類
            error_count = len(
                [
                    issue
                    for issue in lint_issues
                    if isinstance(issue, dict) and issue.get("code", "").startswith("E")
                ]
            )
            warning_count = len(lint_issues) - error_count

            return {
                "timestamp": datetime.now().isoformat(),
                "total_issues": len(lint_issues),
                "error_count": error_count,
                "warning_count": warning_count,
                "status": (
                    "PASS"
                    if len(lint_issues) == 0
                    else "WARNING" if error_count == 0 else "FAIL"
                ),
            }

        except Exception as e:
            logger.error(f"Failed to collect lint metrics: {e}")

        return {
            "timestamp": datetime.now().isoformat(),
            "status": "ERROR",
            "error": "Failed to collect lint data",
        }

    def collect_comprehensive_metrics(self) -> Dict[str, Any]:
        """包括的メトリクス収集"""
        logger.info("Collecting comprehensive quality metrics...")

        metrics = {
            "collection_timestamp": datetime.now().isoformat(),
            "coverage": self.collect_coverage_metrics(),
            "complexity": self.collect_complexity_metrics(),
            "performance": self.collect_performance_metrics(),
            "lint": self.collect_lint_metrics(),
        }

        # 全体品質スコア計算
        quality_score = self._calculate_quality_score(metrics)
        metrics["quality_score"] = quality_score

        # メトリクス履歴に保存
        self._save_metrics_to_history(metrics)

        return metrics

    def _calculate_quality_score(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """品質スコア計算"""
        score = 0
        max_score = 100

        # カバレッジスコア (40点満点)
        coverage_data = metrics.get("coverage", {})
        if coverage_data.get("status") == "PASS":
            coverage_percent = coverage_data.get("total_coverage", 0)
            score += min(40, coverage_percent * 0.4)

        # 複雑度スコア (25点満点)
        complexity_data = metrics.get("complexity", {})
        if complexity_data.get("status") in ["PASS", "WARNING"]:
            complexity_ratio = complexity_data.get("complexity_ratio", 1)
            score += 25 * (1 - complexity_ratio)

        # パフォーマンススコア (20点満点)
        performance_data = metrics.get("performance", {})
        if performance_data.get("overall_status") == "PASS":
            score += 20
        elif performance_data.get("overall_status") == "WARNING":
            score += 10

        # Lintスコア (15点満点)
        lint_data = metrics.get("lint", {})
        if lint_data.get("status") == "PASS":
            score += 15
        elif lint_data.get("status") == "WARNING":
            score += 10

        grade = (
            "A"
            if score >= 90
            else (
                "B"
                if score >= 75
                else "C" if score >= 60 else "D" if score >= 45 else "F"
            )
        )

        return {
            "score": round(score, 2),
            "max_score": max_score,
            "percentage": round(score / max_score * 100, 2),
            "grade": grade,
            "calculation_details": {
                "coverage": coverage_data.get("total_coverage", 0),
                "complexity_issues": complexity_data.get("high_complexity_count", 0),
                "performance_status": performance_data.get("overall_status", "UNKNOWN"),
                "lint_issues": lint_data.get("total_issues", 0),
            },
        }

    def _save_metrics_to_history(self, metrics: Dict[str, Any]) -> None:
        """メトリクス履歴保存"""
        try:
            history = []
            if self.metrics_history_file.exists():
                with open(self.metrics_history_file, "r", encoding="utf-8") as f:
                    history = json.load(f)

            history.append(metrics)

            # 過去30日間のデータのみ保持
            cutoff_date = datetime.now() - timedelta(days=30)
            history = [
                h
                for h in history
                if datetime.fromisoformat(h.get("collection_timestamp", "2020-01-01"))
                > cutoff_date
            ]

            with open(self.metrics_history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Failed to save metrics history: {e}")

    def get_metrics_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """メトリクス履歴取得"""
        try:
            if not self.metrics_history_file.exists():
                return []

            with open(self.metrics_history_file, "r", encoding="utf-8") as f:
                history = json.load(f)

            # 指定日数分のデータフィルタ
            cutoff_date = datetime.now() - timedelta(days=days)
            filtered_history = [
                h
                for h in history
                if datetime.fromisoformat(h.get("collection_timestamp", "2020-01-01"))
                > cutoff_date
            ]

            return filtered_history

        except Exception as e:
            logger.error(f"Failed to get metrics history: {e}")
            return []

    def export_metrics_csv(self, output_path: Optional[Path] = None) -> Path:
        """メトリクスCSVエクスポート"""
        if output_path is None:
            output_path = Path("tmp") / "quality_metrics.csv"

        try:
            history = self.get_metrics_history(30)  # 30日分

            if not history:
                logger.warning("No metrics history available")
                return output_path

            import csv

            with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
                fieldnames = [
                    "timestamp",
                    "quality_score",
                    "quality_grade",
                    "coverage_total",
                    "complexity_avg",
                    "performance_startup_ms",
                    "performance_memory_mb",
                    "lint_issues",
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for entry in history:
                    writer.writerow(
                        {
                            "timestamp": entry.get("collection_timestamp", ""),
                            "quality_score": entry.get("quality_score", {}).get(
                                "score", 0
                            ),
                            "quality_grade": entry.get("quality_score", {}).get(
                                "grade", "N/A"
                            ),
                            "coverage_total": entry.get("coverage", {}).get(
                                "total_coverage", 0
                            ),
                            "complexity_avg": entry.get("complexity", {}).get(
                                "average_complexity", 0
                            ),
                            "performance_startup_ms": entry.get("performance", {}).get(
                                "startup_time_ms", 0
                            ),
                            "performance_memory_mb": entry.get("performance", {}).get(
                                "memory_usage_mb", 0
                            ),
                            "lint_issues": entry.get("lint", {}).get("total_issues", 0),
                        }
                    )

            logger.info(f"Metrics exported to CSV: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to export metrics to CSV: {e}")
            return output_path


def main():
    """CLI エントリーポイント"""
    import argparse

    parser = argparse.ArgumentParser(description="Quality metrics collector")
    parser.add_argument(
        "--collect", action="store_true", help="Collect current metrics"
    )
    parser.add_argument(
        "--history", type=int, default=7, help="Get metrics history (days)"
    )
    parser.add_argument(
        "--export-csv", action="store_true", help="Export metrics to CSV"
    )
    parser.add_argument("--output", type=str, help="Output file path")

    args = parser.parse_args()

    collector = MetricsCollector()

    if args.collect:
        metrics = collector.collect_comprehensive_metrics()
        print(json.dumps(metrics, indent=2, ensure_ascii=False))

    elif args.export_csv:
        output_path = Path(args.output) if args.output else None
        csv_path = collector.export_metrics_csv(output_path)
        print(f"Metrics exported to: {csv_path}")

    else:
        history = collector.get_metrics_history(args.history)
        print(json.dumps(history, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    exit(main())
