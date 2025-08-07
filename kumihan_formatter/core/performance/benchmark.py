"""
パフォーマンスベンチマークシステム
Issue #813対応 - performance_metrics.pyから分離
"""

import json
import time
from datetime import datetime
from pathlib import Path
from statistics import mean, median, stdev
from typing import Any, Callable, Dict, List, Optional

from ..utilities.logger import get_logger


class PerformanceBenchmark:
    """
    パフォーマンスベンチマーク実行システム

    機能:
    - 標準化されたベンチマーク実行
    - 複数実行での統計分析
    - 結果比較・トレンド分析
    - ベンチマーク結果の永続化
    """

    def __init__(self):
        self.logger = get_logger(__name__)
        self.benchmark_results: List[Dict[str, Any]] = []

        # ベンチマークカテゴリ設定
        self.benchmark_categories = {
            "text_processing": {
                "description": "テキスト処理性能",
                "metrics": ["processing_time", "memory_usage", "tokens_per_second"],
            },
            "file_operations": {
                "description": "ファイル操作性能",
                "metrics": ["read_time", "write_time", "throughput_mb_s"],
            },
            "memory_management": {
                "description": "メモリ管理性能",
                "metrics": ["allocation_time", "gc_time", "peak_memory"],
            },
            "optimization": {
                "description": "最適化機能性能",
                "metrics": [
                    "optimization_time",
                    "efficiency_gain",
                    "resource_reduction",
                ],
            },
        }

        self.logger.info("PerformanceBenchmark initialized")

    def run_benchmark(
        self,
        benchmark_name: str,
        benchmark_func: Callable,
        category: str = "general",
        iterations: int = 5,
        warmup_iterations: int = 1,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        ベンチマーク実行

        Args:
            benchmark_name: ベンチマーク名
            benchmark_func: ベンチマーク対象関数
            category: ベンチマークカテゴリ
            iterations: 実行回数
            warmup_iterations: ウォームアップ回数
            **kwargs: ベンチマーク関数への引数

        Returns:
            Dict[str, Any]: ベンチマーク結果
        """
        self.logger.info(
            f"Starting benchmark: {benchmark_name} ({iterations} iterations)"
        )

        # ウォームアップ実行
        for i in range(warmup_iterations):
            try:
                benchmark_func(**kwargs)
                self.logger.debug(f"Warmup iteration {i+1} completed")
            except Exception as e:
                self.logger.warning(f"Warmup iteration {i+1} failed: {e}")

        # ベンチマーク実行
        execution_times = []
        memory_usages = []
        errors = []

        for iteration in range(iterations):
            try:
                # メモリ使用量測定開始
                import os

                import psutil

                process = psutil.Process(os.getpid())
                start_memory = process.memory_info().rss / 1024 / 1024

                # 実行時間測定
                start_time = time.perf_counter()
                _ = benchmark_func(**kwargs)  # Benchmark execution only
                end_time = time.perf_counter()

                # メモリ使用量測定終了
                end_memory = process.memory_info().rss / 1024 / 1024
                memory_used = end_memory - start_memory

                execution_time = end_time - start_time
                execution_times.append(execution_time)
                memory_usages.append(memory_used)

                self.logger.debug(
                    f"Iteration {iteration+1}: {execution_time:.4f}s, "
                    f"Memory: {memory_used:.2f}MB"
                )

            except Exception as e:
                errors.append(f"Iteration {iteration+1}: {str(e)}")
                self.logger.error(f"Benchmark iteration {iteration+1} failed: {e}")

        # 統計分析
        if execution_times:
            stats = self._calculate_statistics(execution_times, memory_usages)
        else:
            stats = {"error": "All benchmark iterations failed"}

        # 結果構築
        benchmark_result = {
            "name": benchmark_name,
            "category": category,
            "timestamp": datetime.now().isoformat(),
            "iterations": iterations,
            "successful_iterations": len(execution_times),
            "failed_iterations": len(errors),
            "statistics": stats,
            "errors": errors,
            "metadata": {
                "warmup_iterations": warmup_iterations,
                "python_version": self._get_python_version(),
                "system_info": self._get_system_info(),
            },
        }

        # 結果を履歴に追加
        self.benchmark_results.append(benchmark_result)

        # 結果をtmp/配下に保存
        self._save_benchmark_result(benchmark_result)

        self.logger.info(
            f"Benchmark {benchmark_name} completed: "
            f"{len(execution_times)}/{iterations} successful iterations"
        )

        return benchmark_result

    def _calculate_statistics(
        self, execution_times: List[float], memory_usages: List[float]
    ) -> Dict[str, Any]:
        """統計情報を計算"""
        if not execution_times:
            return {}

        stats = {
            "execution_time": {
                "mean": mean(execution_times),
                "median": median(execution_times),
                "min": min(execution_times),
                "max": max(execution_times),
                "std_dev": stdev(execution_times) if len(execution_times) > 1 else 0.0,
                "cv_percent": (
                    (stdev(execution_times) / mean(execution_times)) * 100
                    if len(execution_times) > 1 and mean(execution_times) > 0
                    else 0.0
                ),
            }
        }

        if memory_usages:
            stats["memory_usage"] = {
                "mean": mean(memory_usages),
                "median": median(memory_usages),
                "min": min(memory_usages),
                "max": max(memory_usages),
                "std_dev": stdev(memory_usages) if len(memory_usages) > 1 else 0.0,
            }

        return stats

    def _get_python_version(self) -> str:
        """Python バージョン情報を取得"""
        import sys

        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    def _get_system_info(self) -> Dict[str, Any]:
        """システム情報を取得"""
        import platform

        import psutil

        return {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "cpu_count": psutil.cpu_count(),
            "total_memory_gb": psutil.virtual_memory().total / 1024 / 1024 / 1024,
        }

    def _save_benchmark_result(self, result: Dict[str, Any]):
        """ベンチマーク結果をtmp/配下に保存"""
        tmp_dir = Path("tmp")
        tmp_dir.mkdir(exist_ok=True)

        filename = f"benchmark_{result['name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        file_path = tmp_dir / filename

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Benchmark result saved to {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to save benchmark result: {e}")

    def compare_benchmarks(
        self, benchmark_names: List[str], metric: str = "execution_time.mean"
    ) -> Dict[str, Any]:
        """
        複数ベンチマークの比較分析

        Args:
            benchmark_names: 比較対象ベンチマーク名のリスト
            metric: 比較メトリクス

        Returns:
            Dict[str, Any]: 比較結果
        """
        if not benchmark_names:
            return {"error": "No benchmark names provided"}

        # 該当するベンチマーク結果を取得
        comparison_data = {}
        for name in benchmark_names:
            matching_results = [
                result
                for result in self.benchmark_results
                if result["name"] == name and "statistics" in result
            ]

            if matching_results:
                latest_result = max(matching_results, key=lambda x: x["timestamp"])
                comparison_data[name] = latest_result
            else:
                self.logger.warning(f"No results found for benchmark: {name}")

        if not comparison_data:
            return {"error": "No valid benchmark data found for comparison"}

        # メトリクス値を抽出
        metric_values = {}
        for name, result in comparison_data.items():
            try:
                # ネストされたメトリクスパスをサポート（例: "execution_time.mean"）
                value = result["statistics"]
                for key in metric.split("."):
                    value = value[key]
                metric_values[name] = value
            except (KeyError, TypeError):
                self.logger.warning(f"Metric {metric} not found for {name}")

        if not metric_values:
            return {"error": f"Metric {metric} not found in any benchmark"}

        # 比較分析
        best_performance = min(metric_values.items(), key=lambda x: x[1])
        worst_performance = max(metric_values.items(), key=lambda x: x[1])

        improvements = {}
        baseline_value = worst_performance[1]
        for name, value in metric_values.items():
            if baseline_value > 0:
                improvement_percent = ((baseline_value - value) / baseline_value) * 100
                improvements[name] = improvement_percent

        comparison_result = {
            "metric": metric,
            "values": metric_values,
            "best_performance": {
                "benchmark": best_performance[0],
                "value": best_performance[1],
            },
            "worst_performance": {
                "benchmark": worst_performance[0],
                "value": worst_performance[1],
            },
            "improvements_percent": improvements,
            "analysis_timestamp": datetime.now().isoformat(),
        }

        return comparison_result

    def generate_benchmark_report(self, category: Optional[str] = None) -> str:
        """
        ベンチマークレポートを生成

        Args:
            category: フィルタリング対象カテゴリ

        Returns:
            str: HTMLフォーマットのレポート
        """
        # フィルタリング
        if category:
            filtered_results = [
                r for r in self.benchmark_results if r.get("category") == category
            ]
        else:
            filtered_results = self.benchmark_results

        if not filtered_results:
            return "<html><body><h1>No benchmark results found</h1></body></html>"

        # HTMLレポート生成
        html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>Kumihan-Formatter ベンチマークレポート</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .benchmark-card {{
            background: #f8f9fa; padding: 15px; margin: 10px 0;
            border-radius: 6px; border-left: 4px solid #007bff;
        }}
        .stats-table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        .stats-table th, .stats-table td {{
            border: 1px solid #ddd; padding: 8px; text-align: left;
        }}
        .stats-table th {{ background-color: #007bff; color: white; }}
        .success {{ color: #28a745; }}
        .warning {{ color: #ffc107; }}
        .error {{ color: #dc3545; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏃‍♂️ Kumihan-Formatter ベンチマークレポート</h1>
        <p>生成時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>ベンチマーク結果: {len(filtered_results)}件</p>
"""

        for result in filtered_results[-10:]:  # 最新10件
            success_rate = (
                result["successful_iterations"] / result["iterations"] * 100
                if result["iterations"] > 0
                else 0
            )

            status_class = (
                "success"
                if success_rate == 100
                else "warning" if success_rate > 50 else "error"
            )

            html_content += f"""
        <div class="benchmark-card">
            <h3>{result['name']} ({result.get('category', 'general')})</h3>
            <p>実行時刻: {result['timestamp']}</p>
            <p class="{status_class}">成功率: {success_rate:.1f}%
               ({result['successful_iterations']}/{result['iterations']} iterations)</p>
"""

            if "statistics" in result and "execution_time" in result["statistics"]:
                stats = result["statistics"]["execution_time"]
                html_content += f"""
            <table class="stats-table">
                <tr><th>メトリクス</th><th>値</th></tr>
                <tr><td>平均実行時間</td><td>{stats['mean']:.4f}秒</td></tr>
                <tr><td>中央値</td><td>{stats['median']:.4f}秒</td></tr>
                <tr><td>最小値</td><td>{stats['min']:.4f}秒</td></tr>
                <tr><td>最大値</td><td>{stats['max']:.4f}秒</td></tr>
                <tr><td>標準偏差</td><td>{stats['std_dev']:.4f}秒</td></tr>
                <tr><td>変動係数</td><td>{stats['cv_percent']:.2f}%</td></tr>
            </table>
"""

            if result.get("errors"):
                html_content += """
            <div class="error">
                <h4>エラー:</h4>
                <ul>
"""
                for error in result["errors"][:5]:  # 最初の5個のエラー
                    html_content += f"<li>{error}</li>"
                html_content += "</ul></div>"

            html_content += "</div>"

        html_content += """
    </div>
</body>
</html>"""

        # tmp/配下に保存
        tmp_dir = Path("tmp")
        tmp_dir.mkdir(exist_ok=True)
        report_path = (
            tmp_dir
            / f"benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        )

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        self.logger.info(f"Benchmark report generated: {report_path}")
        return str(report_path)

    def get_benchmark_summary(self) -> Dict[str, Any]:
        """ベンチマーク概要を取得"""
        if not self.benchmark_results:
            return {"total_benchmarks": 0}

        # カテゴリ別集計
        category_counts = {}
        total_iterations = 0
        total_successful = 0

        for result in self.benchmark_results:
            category = result.get("category", "general")
            category_counts[category] = category_counts.get(category, 0) + 1
            total_iterations += result["iterations"]
            total_successful += result["successful_iterations"]

        success_rate = (
            (total_successful / total_iterations * 100) if total_iterations > 0 else 0
        )

        return {
            "total_benchmarks": len(self.benchmark_results),
            "categories": category_counts,
            "total_iterations": total_iterations,
            "successful_iterations": total_successful,
            "overall_success_rate_percent": success_rate,
            "latest_benchmark": (
                self.benchmark_results[-1]["timestamp"]
                if self.benchmark_results
                else None
            ),
        }
