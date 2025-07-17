"""
ベンチマーク 統計計算

ベンチマーク結果の統計分析・スコア算出
Issue #492 Phase 5A - benchmark_analyzer.py分割
"""

import statistics
from typing import Any, Union

from .benchmark_types import PERFORMANCE_THRESHOLDS, BenchmarkResult


class BenchmarkStatistics:
    """ベンチマーク結果の統計計算

    責任:
    - 基本統計の計算
    - パフォーマンススコア算出
    - メモリ使用量分析
    - キャッシュパフォーマンス分析
    """

    def __init__(self) -> None:
        """統計計算器を初期化"""
        pass

    def calculate_basic_statistics(
        self, results: list[BenchmarkResult]
    ) -> dict[str, Any]:
        """基本統計を計算

        Args:
            results: ベンチマーク結果リスト

        Returns:
            基本統計情報
        """
        if not results:
            return {"error": "No results to analyze"}

        avg_times = [r.avg_time for r in results]
        total_times = [r.total_time for r in results]
        throughputs = [r.throughput for r in results if r.throughput is not None]

        return {
            "execution_times": {
                "mean": statistics.mean(avg_times),
                "median": statistics.median(avg_times),
                "min": min(avg_times),
                "max": max(avg_times),
                "std_dev": statistics.stdev(avg_times) if len(avg_times) > 1 else 0.0,
            },
            "total_runtime": sum(total_times),
            "throughput": {
                "mean": statistics.mean(throughputs) if throughputs else 0.0,
                "max": max(throughputs) if throughputs else 0.0,
            },
        }

    def calculate_performance_score(self, results: list[BenchmarkResult]) -> float:
        """パフォーマンススコアを計算

        Args:
            results: ベンチマーク結果リスト

        Returns:
            パフォーマンススコア（0-100）
        """
        if not results:
            return 0.0

        # 実行時間スコア（短いほど高得点）
        avg_times = [r.avg_time for r in results]
        time_score = 100.0 / (1.0 + statistics.mean(avg_times))

        # スループットスコア
        throughputs = [r.throughput for r in results if r.throughput is not None]
        throughput_score = statistics.mean(throughputs) if throughputs else 0.0

        # キャッシュヒット率スコア
        cache_score = self.calculate_overall_cache_hit_rate(results) * 100

        # 総合スコア（重み付き平均）
        performance_score = (
            time_score * 0.4 + throughput_score * 0.3 + cache_score * 0.3
        )

        return min(performance_score, 100.0)  # 最大100点

    def analyze_memory_usage(self, results: list[BenchmarkResult]) -> dict[str, Any]:
        """メモリ使用量を分析

        Args:
            results: ベンチマーク結果リスト

        Returns:
            メモリ使用量分析結果
        """
        memory_data = []
        memory_increases = []

        for result in results:
            if result.memory_usage:
                if "peak_mb" in result.memory_usage:
                    memory_data.append(result.memory_usage["peak_mb"])
                if "increase_mb" in result.memory_usage:
                    memory_increases.append(result.memory_usage["increase_mb"])

        analysis = {
            "peak_usage": {
                "max": max(memory_data) if memory_data else 0.0,
                "mean": statistics.mean(memory_data) if memory_data else 0.0,
            },
            "memory_increases": {
                "mean": statistics.mean(memory_increases) if memory_increases else 0.0,
                "max": max(memory_increases) if memory_increases else 0.0,
            },
            "warnings": [],
        }

        # 警告チェック
        warnings_list: list[str] = analysis["warnings"]  # type: ignore
        if memory_data and max(memory_data) > 100.0:  # 100MB以上
            warnings_list.append("High memory usage detected (>100MB)")

        if (
            memory_increases and statistics.mean(memory_increases) > 10.0
        ):  # 平均10MB以上の増加
            warnings_list.append("Significant memory increase during benchmarks")

        return analysis

    def analyze_cache_performance(
        self, results: list[BenchmarkResult]
    ) -> dict[str, Any]:
        """キャッシュパフォーマンスを分析

        Args:
            results: ベンチマーク結果リスト

        Returns:
            キャッシュパフォーマンス分析結果
        """
        cache_data: dict[str, list[Any]] = {
            "file_cache": [],
            "parse_cache": [],
            "render_cache": [],
        }

        for result in results:
            for cache_type in cache_data.keys():
                if cache_type in result.cache_stats:
                    cache_data[cache_type].append(result.cache_stats[cache_type])

        analysis = {}
        for cache_type, data in cache_data.items():
            if data:
                hit_rates = []
                for cache_stat in data:
                    if isinstance(cache_stat, dict) and "hit_rate" in cache_stat:
                        hit_rates.append(cache_stat["hit_rate"])

                if hit_rates:
                    analysis[cache_type] = {
                        "average_hit_rate": statistics.mean(hit_rates),
                        "min_hit_rate": min(hit_rates),
                        "max_hit_rate": max(hit_rates),
                    }

        return analysis

    def calculate_overall_cache_hit_rate(self, results: list[BenchmarkResult]) -> float:
        """全体のキャッシュヒット率を計算

        Args:
            results: ベンチマーク結果リスト

        Returns:
            全体のキャッシュヒット率
        """
        hit_rates = []

        for result in results:
            for cache_type in ["file_cache", "parse_cache", "render_cache"]:
                if cache_type in result.cache_stats:
                    cache_stat = result.cache_stats[cache_type]
                    if isinstance(cache_stat, dict) and "hit_rate" in cache_stat:
                        hit_rates.append(cache_stat["hit_rate"])

        return statistics.mean(hit_rates) if hit_rates else 0.0

    def generate_recommendations(self, results: list[BenchmarkResult]) -> list[str]:
        """推奨事項を生成

        Args:
            results: ベンチマーク結果リスト

        Returns:
            推奨事項のリスト
        """
        recommendations = []

        # パフォーマンス関連
        avg_times = [r.avg_time for r in results]
        if avg_times and statistics.mean(avg_times) > 1.0:
            recommendations.append(
                "Consider optimizing algorithms - average execution time is high"
            )

        # メモリ関連
        memory_data = []
        for result in results:
            if result.memory_usage and "peak_mb" in result.memory_usage:
                memory_data.append(result.memory_usage["peak_mb"])

        if memory_data and max(memory_data) > 200.0:
            recommendations.append(
                "High memory usage detected - consider memory optimization"
            )

        # キャッシュ関連
        cache_hit_rate = self.calculate_overall_cache_hit_rate(results)
        if cache_hit_rate < PERFORMANCE_THRESHOLDS["cache_hit_rate_minimum"]:
            recommendations.append("Low cache hit rate - review caching strategy")

        return recommendations
