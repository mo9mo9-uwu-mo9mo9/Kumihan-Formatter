"""
ベンチマーク分析器 - 結果分析と回帰検出

ベンチマーク結果の分析とパフォーマンス回帰検出
Issue #476対応 - ファイルサイズ制限遵守
"""

import statistics
from typing import Any, Dict, List

from ..utilities.logger import get_logger
from .benchmark_types import (
    PERFORMANCE_THRESHOLDS,
    BenchmarkResult,
    BenchmarkSummary,
    RegressionAnalysis,
)


class BenchmarkAnalyzer:
    """ベンチマーク結果分析器

    機能:
    - ベンチマーク結果の統計分析
    - パフォーマンス回帰検出
    - 結果サマリー生成
    - トレンド分析
    """

    def __init__(self) -> None:
        """ベンチマーク分析器を初期化"""
        self.logger = get_logger(__name__)

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
        basic_stats = self._calculate_basic_statistics(results)

        # パフォーマンス評価
        performance_score = self._calculate_performance_score(results)

        # メモリ分析
        memory_analysis = self._analyze_memory_usage(results)

        # キャッシュ分析
        cache_analysis = self._analyze_cache_performance(results)

        # 推奨事項
        recommendations = self._generate_recommendations(results)

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
            "detailed_results": [self._format_result_summary(r) for r in results],
        }

        self.logger.info(f"ベンチマーク結果分析完了: スコア={performance_score:.2f}")
        return analysis

    def analyze_regression(
        self,
        current_results: dict[str, BenchmarkResult],
        baseline_results: dict[str, BenchmarkResult],
    ) -> dict[str, Any]:
        """パフォーマンス回帰を分析

        Args:
            current_results: 現在の結果
            baseline_results: ベースライン結果

        Returns:
            dict: 回帰分析結果
        """
        self.logger.info("パフォーマンス回帰分析開始")

        regressions = []
        improvements = []

        for name, current in current_results.items():
            if name not in baseline_results:
                self.logger.warning(f"ベースラインに存在しないベンチマーク: {name}")
                continue

            baseline = baseline_results[name]
            regression_analysis = self._analyze_single_regression(current, baseline)

            if regression_analysis.is_regression:
                regressions.append(regression_analysis)
                self.logger.warning(
                    f"回帰検出: {name}, 性能悪化={regression_analysis.performance_change_percent:.1f}%"
                )
            elif regression_analysis.performance_change_percent < -5.0:  # 5%以上の改善
                improvements.append(regression_analysis)
                self.logger.info(
                    f"性能改善: {name}, 改善={abs(regression_analysis.performance_change_percent):.1f}%"
                )

        # 総合評価
        overall_regression = len(regressions) > 0
        severity = self._calculate_overall_severity(regressions)

        analysis = {
            "overall_regression": overall_regression,
            "severity": severity,
            "regressions_detected": [
                self._format_regression_analysis(r) for r in regressions
            ],
            "improvements_detected": [
                self._format_regression_analysis(r) for r in improvements
            ],
            "summary": {
                "total_benchmarks_compared": len(current_results),
                "regressions_count": len(regressions),
                "improvements_count": len(improvements),
                "overall_performance_change": self._calculate_overall_performance_change(
                    current_results, baseline_results
                ),
            },
        }

        self.logger.info(
            f"回帰分析完了: {len(regressions)}個の回帰, {len(improvements)}個の改善"
        )
        return analysis

    def generate_benchmark_summary(
        self, results: list[BenchmarkResult]
    ) -> BenchmarkSummary:
        """ベンチマーク結果サマリーを生成"""
        if not results:
            raise ValueError("No results to summarize")

        # 最速・最遅ベンチマーク
        fastest = min(results, key=lambda r: r.avg_time)
        slowest = max(results, key=lambda r: r.avg_time)

        # メモリピーク計算
        memory_peak = 0.0
        for result in results:
            if result.memory_usage and "peak_mb" in result.memory_usage:
                memory_peak = max(memory_peak, result.memory_usage["peak_mb"])

        # キャッシュヒット率計算
        cache_hit_rate = self._calculate_overall_cache_hit_rate(results)

        # パフォーマンススコア
        performance_score = self._calculate_performance_score(results)

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

    def _analyze_single_regression(
        self, current: BenchmarkResult, baseline: BenchmarkResult
    ) -> RegressionAnalysis:
        """単一ベンチマークの回帰分析"""
        performance_change_percent = (
            (current.avg_time - baseline.avg_time) / baseline.avg_time * 100
        )

        is_regression = (
            performance_change_percent
            > PERFORMANCE_THRESHOLDS["regression_threshold_percent"]
        )

        # 深刻度評価
        if (
            performance_change_percent
            > PERFORMANCE_THRESHOLDS["severe_regression_percent"]
        ):
            severity = "severe"
        elif (
            performance_change_percent
            > PERFORMANCE_THRESHOLDS["regression_threshold_percent"]
        ):
            if performance_change_percent > 20.0:
                severity = "moderate"
            else:
                severity = "minor"
        else:
            severity = "none"

        # メモリ変化計算
        memory_change_percent = None
        if current.memory_usage.get("peak_mb") and baseline.memory_usage.get("peak_mb"):
            current_memory = current.memory_usage["peak_mb"]
            baseline_memory = baseline.memory_usage["peak_mb"]
            memory_change_percent = (
                (current_memory - baseline_memory) / baseline_memory * 100
            )

        return RegressionAnalysis(
            benchmark_name=current.name,
            baseline_avg_time=baseline.avg_time,
            current_avg_time=current.avg_time,
            performance_change_percent=performance_change_percent,
            is_regression=is_regression,
            severity=severity,
            memory_change_percent=memory_change_percent,
        )

    def _calculate_basic_statistics(
        self, results: list[BenchmarkResult]
    ) -> dict[str, Any]:
        """基本統計を計算"""
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

    def _calculate_performance_score(self, results: list[BenchmarkResult]) -> float:
        """パフォーマンススコアを計算"""
        if not results:
            return 0.0

        # 実行時間スコア（短いほど高得点）
        avg_times = [r.avg_time for r in results]
        time_score = 100.0 / (1.0 + statistics.mean(avg_times))

        # スループットスコア
        throughputs = [r.throughput for r in results if r.throughput is not None]
        throughput_score = statistics.mean(throughputs) if throughputs else 0.0

        # キャッシュヒット率スコア
        cache_score = self._calculate_overall_cache_hit_rate(results) * 100

        # 総合スコア（重み付き平均）
        performance_score = (
            time_score * 0.4 + throughput_score * 0.3 + cache_score * 0.3
        )

        return min(performance_score, 100.0)  # 最大100点

    def _analyze_memory_usage(self, results: list[BenchmarkResult]) -> dict[str, Any]:
        """メモリ使用量を分析"""
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
        warnings_list: List[str] = analysis["warnings"]  # type: ignore
        if memory_data and max(memory_data) > 100.0:  # 100MB以上
            warnings_list.append("High memory usage detected (>100MB)")

        if (
            memory_increases and statistics.mean(memory_increases) > 10.0
        ):  # 平均10MB以上の増加
            warnings_list.append("Significant memory increase during benchmarks")

        return analysis

    def _analyze_cache_performance(
        self, results: list[BenchmarkResult]
    ) -> dict[str, Any]:
        """キャッシュパフォーマンスを分析"""
        cache_data: Dict[str, List[Any]] = {
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

    def _calculate_overall_cache_hit_rate(
        self, results: list[BenchmarkResult]
    ) -> float:
        """全体のキャッシュヒット率を計算"""
        hit_rates = []

        for result in results:
            for cache_type in ["file_cache", "parse_cache", "render_cache"]:
                if cache_type in result.cache_stats:
                    cache_stat = result.cache_stats[cache_type]
                    if isinstance(cache_stat, dict) and "hit_rate" in cache_stat:
                        hit_rates.append(cache_stat["hit_rate"])

        return statistics.mean(hit_rates) if hit_rates else 0.0

    def _generate_recommendations(self, results: list[BenchmarkResult]) -> list[str]:
        """推奨事項を生成"""
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
        cache_hit_rate = self._calculate_overall_cache_hit_rate(results)
        if cache_hit_rate < PERFORMANCE_THRESHOLDS["cache_hit_rate_minimum"]:
            recommendations.append("Low cache hit rate - review caching strategy")

        return recommendations

    def _calculate_overall_performance_change(
        self,
        current_results: dict[str, BenchmarkResult],
        baseline_results: dict[str, BenchmarkResult],
    ) -> float:
        """全体のパフォーマンス変化を計算"""
        changes = []

        for name, current in current_results.items():
            if name in baseline_results:
                baseline = baseline_results[name]
                change = (
                    (current.avg_time - baseline.avg_time) / baseline.avg_time * 100
                )
                changes.append(change)

        return statistics.mean(changes) if changes else 0.0

    def _calculate_overall_severity(self, regressions: list[RegressionAnalysis]) -> str:
        """全体の深刻度を計算"""
        if not regressions:
            return "none"

        severe_count = sum(1 for r in regressions if r.severity == "severe")
        moderate_count = sum(1 for r in regressions if r.severity == "moderate")

        if severe_count > 0:
            return "severe"
        elif moderate_count > 0:
            return "moderate"
        else:
            return "minor"

    def _format_result_summary(self, result: BenchmarkResult) -> dict[str, Any]:
        """結果サマリーをフォーマット"""
        return {
            "name": result.name,
            "avg_time": round(result.avg_time, 3),
            "throughput": round(result.throughput, 1) if result.throughput else None,
            "memory_peak": (
                result.memory_usage.get("peak_mb") if result.memory_usage else None
            ),
            "cache_performance": self._extract_cache_summary(result.cache_stats),
        }

    def _format_regression_analysis(
        self, analysis: RegressionAnalysis
    ) -> dict[str, Any]:
        """回帰分析をフォーマット"""
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

    def _extract_cache_summary(self, cache_stats: dict[str, Any]) -> dict[str, Any]:
        """キャッシュサマリーを抽出"""
        summary = {}
        for cache_type, stats in cache_stats.items():
            if isinstance(stats, dict) and "hit_rate" in stats:
                summary[cache_type] = round(stats["hit_rate"], 3)
        return summary
