"""
最適化分析コアロジック - Issue #402対応

最適化効果の測定、ベースライン比較、統計分析。
"""

import json

# statistics removed as unused
from datetime import datetime
from pathlib import Path
from typing import Any

from ...performance import get_global_monitor
from ...utilities.logger import get_logger
from ..benchmark import PerformanceBenchmarkSuite
from ..benchmark_types import BenchmarkConfig
from ..memory_monitor import MemoryMonitor
from ..profiler import AdvancedProfiler
from .models import OptimizationMetrics, OptimizationReport
from .utils import (
    calculate_significance,
    calculate_total_improvement_score,
    capture_system_info,
    create_performance_summary,
    detect_regressions,
    generate_recommendations,
)


class OptimizationAnalyzer:
    """最適化効果分析システム

    機能:
    - Before/After パフォーマンス比較
    - 統計的有意性検定
    - 改善効果の定量的評価
    - 回帰リスクの評価
    """

    def __init__(self, baseline_dir: Path | None = None) -> None:
        """最適化分析器を初期化

        Args:
            baseline_dir: ベースラインデータの保存ディレクトリ
        """
        self.baseline_dir = baseline_dir or Path("./performance_baselines")
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger(__name__)

        # 測定ツール
        self.monitor = get_global_monitor()
        self.profiler = AdvancedProfiler()
        self.memory_monitor = MemoryMonitor()

        # データ保存
        self.baseline_data: dict[str, Any] = {}
        self.optimization_history: list[OptimizationReport] = []

        self.logger.info(
            f"OptimizationAnalyzer initialized: baseline_dir={self.baseline_dir}"
        )

    def capture_baseline(self, name: str, description: str = "") -> dict[str, Any]:
        """最適化前のベースライン性能を記録

        Args:
            name: ベースライン名
            description: 説明

        Returns:
            ベースラインデータ
        """
        self.logger.info(f"ベースラインキャプチャ開始: {name}")
        print(f"📈 Capturing baseline performance: {name}")

        # ベンチマーク設定（キャッシュなしで純粹な性能を測定）
        benchmark_config = BenchmarkConfig(
            iterations=5,
            warmup_iterations=2,
            enable_profiling=True,
            enable_memory_monitoring=True,
            cache_enabled=False,  # ベースラインはキャッシュなし
        )

        # ベンチマーク実行
        benchmark_suite = PerformanceBenchmarkSuite(benchmark_config)
        benchmark_results = benchmark_suite.run_full_benchmark_suite()

        # システム情報を収集
        system_info = capture_system_info()

        # ベースラインデータを作成
        baseline_data = {
            "name": name,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "benchmark_config": benchmark_config.__dict__,
            "benchmark_results": benchmark_results,
            "system_info": system_info,
        }

        # ファイルに保存
        baseline_file = self.baseline_dir / f"{name}_baseline.json"
        with open(baseline_file, "w", encoding="utf-8") as f:
            json.dump(baseline_data, f, indent=2, ensure_ascii=False)

        # メモリに保存
        self.baseline_data[name] = baseline_data

        self.logger.info(f"ベースライン保存完了: {baseline_file}")
        print(f"📏 Baseline saved to: {baseline_file}")
        return baseline_data

    def measure_optimization_impact(
        self,
        optimization_name: str,
        baseline_name: str,
        description: str = "",
    ) -> OptimizationReport:
        """最適化後の効果を測定

        Args:
            optimization_name: 最適化名
            baseline_name: 比較対象のベースライン名
            description: 最適化の説明

        Returns:
            最適化レポート
        """
        self.logger.info(f"最適化効果測定開始: {optimization_name}")
        print(f"🔍 Measuring optimization impact: {optimization_name}")

        # ベースラインデータを読み込み
        baseline_data = self._load_baseline(baseline_name)
        if not baseline_data:
            raise ValueError(f"Baseline '{baseline_name}' not found")

        # 最適化後のベンチマークを実行
        benchmark_config = BenchmarkConfig(
            iterations=5,
            warmup_iterations=2,
            enable_profiling=True,
            enable_memory_monitoring=True,
            cache_enabled=True,  # 最適化後はキャッシュを有効
        )

        benchmark_suite = PerformanceBenchmarkSuite(benchmark_config)
        optimized_results = benchmark_suite.run_full_benchmark_suite()

        # 比較分析
        metrics = self._compare_performance(
            baseline_data["benchmark_results"], optimized_results
        )

        # レポート生成
        report = OptimizationReport(
            timestamp=datetime.now().isoformat(),
            optimization_name=optimization_name,
            total_improvement_score=calculate_total_improvement_score(metrics),
            metrics=metrics,
            performance_summary=create_performance_summary(metrics),
            recommendations=generate_recommendations(metrics),
            regression_warnings=detect_regressions(metrics),
        )

        # 履歴に保存
        self.optimization_history.append(report)

        # ファイルに保存
        report_file = (
            self.baseline_dir / f"{optimization_name}_optimization_report.json"
        )
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        self.logger.info(f"最適化レポート保存完了: {report_file}")
        print(f"📈 Optimization report saved to: {report_file}")
        return report

    def _load_baseline(self, baseline_name: str) -> dict[str, Any] | None:
        """ベースラインデータを読み込み"""
        # メモリから検索
        if baseline_name in self.baseline_data:
            cached_data: dict[str, Any] = self.baseline_data[baseline_name]
            return cached_data

        # ファイルから読み込み
        baseline_file = self.baseline_dir / f"{baseline_name}_baseline.json"
        if baseline_file.exists():
            try:
                with open(baseline_file, "r", encoding="utf-8") as f:
                    loaded_data: dict[str, Any] = json.load(f)
                self.baseline_data[baseline_name] = loaded_data
                return loaded_data
            except Exception as e:
                self.logger.error(f"ベースライン読み込みエラー: {e}")

        return None

    def _compare_performance(
        self, baseline_results: dict[str, Any], optimized_results: dict[str, Any]
    ) -> list[OptimizationMetrics]:
        """パフォーマンスを比較してメトリクスを生成"""
        metrics = []

        # ベンチマーク結果の比較
        if (
            "benchmark_results" in baseline_results
            and "benchmark_results" in optimized_results
        ):
            baseline_benchmarks = baseline_results["benchmark_results"]
            optimized_benchmarks = optimized_results["benchmark_results"]

            for name, baseline_data in baseline_benchmarks.items():
                if name in optimized_benchmarks:
                    optimized_data = optimized_benchmarks[name]

                    # 実行時間の比較
                    if "avg_time" in baseline_data and "avg_time" in optimized_data:
                        baseline_time = baseline_data["avg_time"]
                        optimized_time = optimized_data["avg_time"]

                        improvement_percent = (
                            (baseline_time - optimized_time) / baseline_time * 100
                            if baseline_time > 0
                            else 0
                        )

                        significance = calculate_significance(
                            baseline_time, optimized_time, improvement_percent
                        )

                        metrics.append(
                            OptimizationMetrics(
                                name=f"{name}_execution_time",
                                before_value=baseline_time,
                                after_value=optimized_time,
                                improvement_percent=improvement_percent,
                                improvement_absolute=baseline_time - optimized_time,
                                significance=significance,
                                category="performance",
                            )
                        )

        return metrics
