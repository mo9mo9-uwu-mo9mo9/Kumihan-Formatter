"""
ベンチマーク フォーマッター

ベンチマーク結果のフォーマット・サマリー生成
Issue #492 Phase 5A - benchmark_analyzer.py分割
"""

from typing import Any, Union

from .benchmark_statistics import BenchmarkStatistics
from .benchmark_types import BenchmarkResult, BenchmarkSummary, RegressionAnalysis


class BenchmarkFormatters:
    """ベンチマーク結果フォーマッター

    責任:
    - ベンチマークサマリー生成
    - 結果のフォーマット
    - 回帰分析結果のフォーマット
    - キャッシュサマリー抽出
    """

    def __init__(self) -> None:
        """フォーマッターを初期化"""
        self.statistics = BenchmarkStatistics()

    def generate_benchmark_summary(
        self, results: list[BenchmarkResult]
    ) -> BenchmarkSummary:
        """ベンチマーク結果サマリーを生成

        Args:
            results: ベンチマーク結果リスト

        Returns:
            ベンチマークサマリー
        """
        if not results:
            raise ValueError("No results to summarize")

        # 最速・最遅ベンチマーク
        fastest = min(results, key=lambda r: r.avg_time)
        slowest = max(results, key=lambda r: r.avg_time)

        # メモリピーク計算
        memory_peak = self._calculate_memory_peak(results)

        # キャッシュヒット率計算
        cache_hit_rate = self.statistics.calculate_overall_cache_hit_rate(results)

        # パフォーマンススコア
        performance_score = self.statistics.calculate_performance_score(results)

        return BenchmarkSummary(
            total_benchmarks=len(results),
            total_runtime=sum(r.total_time for r in results),
            fastest_benchmark=fastest,
            slowest_benchmark=slowest,
            memory_peak=memory_peak,
            cache_hit_rate=cache_hit_rate,
            regressions_detected=[],  # 回帰検出は別途実行
            performance_score=performance_score,
        )

    def format_result_summary(self, result: BenchmarkResult) -> dict[str, Any]:
        """結果サマリーをフォーマット

        Args:
            result: ベンチマーク結果

        Returns:
            フォーマットされた結果サマリー
        """
        return {
            "name": result.name,
            "avg_time": round(result.avg_time, 3),
            "throughput": round(result.throughput, 1) if result.throughput else None,
            "memory_peak": (
                result.memory_usage.get("peak_mb") if result.memory_usage else None
            ),
            "cache_performance": self.extract_cache_summary(result.cache_stats),
        }

    def format_regression_analysis(
        self, analysis: RegressionAnalysis
    ) -> dict[str, Any]:
        """回帰分析をフォーマット

        Args:
            analysis: 回帰分析結果

        Returns:
            フォーマットされた回帰分析
        """
        return {
            "benchmark_name": analysis.benchmark_name,
            "performance_change_percent": round(analysis.performance_change_percent, 2),
            "severity": analysis.severity,
            "baseline_time": round(analysis.baseline_avg_time, 3),
            "current_time": round(analysis.current_avg_time, 3),
            "memory_change_percent": (
                round(analysis.memory_change_percent, 2)
                if analysis.memory_change_percent is not None
                else None
            ),
        }

    def extract_cache_summary(self, cache_stats: dict[str, Any]) -> dict[str, Any]:
        """キャッシュサマリーを抽出

        Args:
            cache_stats: キャッシュ統計情報

        Returns:
            キャッシュサマリー
        """
        summary = {}
        for cache_type, stats in cache_stats.items():
            if isinstance(stats, dict) and "hit_rate" in stats:
                summary[cache_type] = round(stats["hit_rate"], 3)
        return summary

    def _calculate_memory_peak(self, results: list[BenchmarkResult]) -> float:
        """メモリピークを計算

        Args:
            results: ベンチマーク結果リスト

        Returns:
            メモリピーク値
        """
        memory_peak = 0.0
        for result in results:
            if result.memory_usage and "peak_mb" in result.memory_usage:
                memory_peak = max(memory_peak, result.memory_usage["peak_mb"])
        return memory_peak
