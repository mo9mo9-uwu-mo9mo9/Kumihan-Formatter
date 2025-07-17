"""
ベンチマーク分析器 コア

メインの分析器クラス・統合機能
Issue #492 Phase 5A - benchmark_analyzer.py分割
"""

from typing import Any

from ..utilities.logger import get_logger
from .benchmark_formatters import BenchmarkFormatters
from .benchmark_regression_analyzer import BenchmarkRegressionAnalyzer
from .benchmark_statistics import BenchmarkStatistics
from .benchmark_types import BenchmarkResult, BenchmarkSummary


class BenchmarkAnalyzerCore:
    """ベンチマーク結果分析器 - コア機能

    統合された分析機能:
    - 結果分析の統合
    - 分割されたコンポーネントの調整
    - 統一されたインターフェース提供
    """

    def __init__(self) -> None:
        """ベンチマーク分析器を初期化"""
        self.logger = get_logger(__name__)

        # 分離されたコンポーネント
        self.statistics = BenchmarkStatistics()
        self.regression_analyzer = BenchmarkRegressionAnalyzer()
        self.formatters = BenchmarkFormatters()

    def analyze_results(self, results: list[BenchmarkResult]) -> dict[str, Any]:
        """ベンチマーク結果を分析

        Args:
            results: ベンチマーク結果リスト

        Returns:
            dict: 分析結果
        """
        if not results:
            return {"error": "No benchmark results to analyze"}

        self.logger.info(f"ベンチマーク結果分析開始: {len(results)}個の結果")

        # 基本統計
        basic_stats = self.statistics.calculate_basic_statistics(results)

        # パフォーマンス評価
        performance_score = self.statistics.calculate_performance_score(results)

        # メモリ分析
        memory_analysis = self.statistics.analyze_memory_usage(results)

        # キャッシュ分析
        cache_analysis = self.statistics.analyze_cache_performance(results)

        # 推奨事項
        recommendations = self.statistics.generate_recommendations(results)

        analysis = {
            "summary": {
                "total_benchmarks": len(results),
                "total_runtime": sum(r.total_time for r in results),
                "average_performance": performance_score,
            },
            "basic_statistics": basic_stats,
            "performance_score": performance_score,
            "memory_analysis": memory_analysis,
            "cache_analysis": cache_analysis,
            "recommendations": recommendations,
            "detailed_results": [
                self.formatters.format_result_summary(r) for r in results
            ],
        }

        self.logger.info(f"ベンチマーク結果分析完了: スコア={performance_score:.2f}")
        return analysis

    def analyze_regression(
        self,
        current_results: dict[str, BenchmarkResult],
        baseline_results: dict[str, BenchmarkResult],
    ) -> dict[str, Any]:
        """パフォーマンス回帰を分析（統合版）

        Args:
            current_results: 現在の結果
            baseline_results: ベースライン結果

        Returns:
            dict: 回帰分析結果
        """
        # 回帰分析実行
        analysis = self.regression_analyzer.analyze_regression(
            current_results, baseline_results
        )

        # 結果をフォーマット
        analysis["regressions_detected"] = [
            self.formatters.format_regression_analysis(r)
            for r in analysis["regressions_detected"]
        ]
        analysis["improvements_detected"] = [
            self.formatters.format_regression_analysis(r)
            for r in analysis["improvements_detected"]
        ]

        return analysis

    def generate_benchmark_summary(
        self, results: list[BenchmarkResult]
    ) -> BenchmarkSummary:
        """ベンチマーク結果サマリーを生成（統合版）"""
        return self.formatters.generate_benchmark_summary(results)
