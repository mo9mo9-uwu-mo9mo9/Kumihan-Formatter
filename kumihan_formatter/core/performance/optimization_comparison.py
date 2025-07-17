"""
最適化比較システム - パフォーマンス比較とメトリクス計算
ベースラインと最適化後のパフォーマンスを比較しメトリクスを計算
Issue #476対応 - ファイルサイズ制限遵守
"""

import statistics
from typing import Any

from ..utilities.logger import get_logger
from .optimization_types import (
    REGRESSION_THRESHOLDS,
    SCORE_WEIGHTS,
    SIGNIFICANCE_THRESHOLDS,
    OptimizationMetrics,
)


class OptimizationComparisonEngine:
    """最適化比較エンジン

    機能:
    - ベースラインと最適化後のパフォーマンス比較
    - 改善メトリクスの計算
    - 統計的有意性の評価
    - 回帰リスクの検出
    """

    def __init__(self) -> None:
        """比較エンジンを初期化"""
        self.logger = get_logger(__name__)

    def compare_performance(
        self, baseline_results: dict[str, Any], optimized_results: dict[str, Any]
    ) -> list[OptimizationMetrics]:
        """パフォーマンスを比較

        Args:
            baseline_results: ベースライン結果
            optimized_results: 最適化後結果

        Returns:
            最適化メトリクスのリスト
        """
        self.logger.info("パフォーマンス比較開始")
        metrics = []

        # 詳細結果から比較
        baseline_detailed = baseline_results.get("detailed_results", [])
        optimized_detailed = optimized_results.get("detailed_results", [])

        # ベンチマーク名でマッピング
        baseline_map = {result["name"]: result for result in baseline_detailed}
        optimized_map = {result["name"]: result for result in optimized_detailed}

        # 共通のベンチマークを比較
        common_benchmarks = set(baseline_map.keys()) & set(optimized_map.keys())
        self.logger.info(f"共通ベンチマーク: {len(common_benchmarks)}個")

        for name in common_benchmarks:
            baseline_result = baseline_map[name]
            optimized_result = optimized_map[name]

            # 実行時間の比較
            performance_metrics = self._compare_execution_time(
                name, baseline_result, optimized_result
            )
            if performance_metrics:
                metrics.append(performance_metrics)

            # メモリ使用量の比較
            memory_metrics = self._compare_memory_usage(
                name, baseline_result, optimized_result
            )
            if memory_metrics:
                metrics.append(memory_metrics)

        self.logger.info(f"比較完了: {len(metrics)}個のメトリクスを生成")
        return metrics

    def _compare_execution_time(
        self, benchmark_name: str, baseline: dict[str, Any], optimized: dict[str, Any]
    ) -> OptimizationMetrics | None:
        """実行時間の比較

        Args:
            benchmark_name: ベンチマーク名
            baseline: ベースライン結果
            optimized: 最適化後結果

        Returns:
            実行時間メトリクス
        """
        before_time = baseline.get("avg_time")
        after_time = optimized.get("avg_time")

        if before_time is None or after_time is None or before_time <= 0:
            return None

        improvement_percent = ((before_time - after_time) / before_time) * 100
        improvement_absolute = before_time - after_time

        return OptimizationMetrics(
            name=f"{benchmark_name}_execution_time",
            before_value=before_time,
            after_value=after_time,
            improvement_percent=improvement_percent,
            improvement_absolute=improvement_absolute,
            significance=self.calculate_significance(improvement_percent),
            category="performance",
        )

    def _compare_memory_usage(
        self, benchmark_name: str, baseline: dict[str, Any], optimized: dict[str, Any]
    ) -> OptimizationMetrics | None:
        """メモリ使用量の比較

        Args:
            benchmark_name: ベンチマーク名
            baseline: ベースライン結果
            optimized: 最適化後結果

        Returns:
            メモリ使用量メトリクス
        """
        baseline_memory = baseline.get("memory_usage", {})
        optimized_memory = optimized.get("memory_usage", {})

        before_memory = baseline_memory.get("peak_mb")
        after_memory = optimized_memory.get("peak_mb")

        if before_memory is None or after_memory is None or before_memory <= 0:
            return None

        memory_improvement = ((before_memory - after_memory) / before_memory) * 100

        return OptimizationMetrics(
            name=f"{benchmark_name}_memory_usage",
            before_value=before_memory,
            after_value=after_memory,
            improvement_percent=memory_improvement,
            improvement_absolute=before_memory - after_memory,
            significance=self.calculate_significance(memory_improvement),
            category="memory",
        )

    def calculate_significance(self, improvement_percent: float) -> str:
        """改善の有意性を計算

        Args:
            improvement_percent: 改善率

        Returns:
            有意性レベル
        """
        abs_improvement = abs(improvement_percent)

        for level, threshold in SIGNIFICANCE_THRESHOLDS.items():
            if abs_improvement >= threshold:
                return level

        return "low"

    def calculate_total_improvement_score(
        self, metrics: list[OptimizationMetrics]
    ) -> float:
        """総合改善スコアを計算

        Args:
            metrics: 最適化メトリクスのリスト

        Returns:
            総合改善スコア
        """
        if not metrics:
            return 0.0

        total_score = 0.0

        for metric in metrics:
            # 改善のみをスコアに含める
            if metric.is_improvement:
                weight = SCORE_WEIGHTS.get(metric.significance, 1.0)
                total_score += metric.improvement_percent * weight

        return total_score

    def create_performance_summary(
        self, metrics: list[OptimizationMetrics]
    ) -> dict[str, Any]:
        """パフォーマンス要約を作成

        Args:
            metrics: 最適化メトリクスのリスト

        Returns:
            パフォーマンス要約
        """
        improved = [m for m in metrics if m.is_improvement]
        degraded = [
            m for m in metrics if not m.is_improvement and m.improvement_percent < -1
        ]
        stable = [m for m in metrics if -1 <= m.improvement_percent <= 1]

        summary = {
            "total_benchmarks": len(metrics),
            "improved_metrics": len(improved),
            "degraded_metrics": len(degraded),
            "stable_metrics": len(stable),
        }

        # キャッシュ効果の分析
        cache_metrics = [m for m in metrics if "cache" in m.name.lower()]
        if cache_metrics:
            cache_improvements = [m for m in cache_metrics if m.is_improvement]
            summary["cache_effectiveness"] = {  # type: ignore
                "total_cache_metrics": len(cache_metrics),
                "cache_improvements": len(cache_improvements),
                "avg_cache_improvement": (
                    statistics.mean([m.improvement_percent for m in cache_improvements])
                    if cache_improvements
                    else 0
                ),
            }

        return summary

    def detect_regressions(self, metrics: list[OptimizationMetrics]) -> list[str]:
        """回帰を検出

        Args:
            metrics: 最適化メトリクスのリスト

        Returns:
            回帰警告のリスト
        """
        warnings = []

        for metric in metrics:
            if not metric.is_improvement:
                improvement_percent = metric.improvement_percent

                # 回帰の重大度を判定
                severity = None
                for level, threshold in REGRESSION_THRESHOLDS.items():
                    if improvement_percent <= threshold:
                        severity = level
                        break

                if severity:
                    severity_jp = {
                        "severe": "重大",
                        "moderate": "中程度",
                        "minor": "軽微",
                    }.get(severity, "不明")

                    warnings.append(
                        f"{severity_jp}な回帰: {metric.name} が "
                        f"{abs(improvement_percent):.1f}% 劣化"
                    )

        return warnings

    def generate_recommendations(self, metrics: list[OptimizationMetrics]) -> list[str]:
        """推奨事項を生成

        Args:
            metrics: 最適化メトリクスのリスト

        Returns:
            推奨事項のリスト
        """
        recommendations = []

        # パフォーマンス改善の推奨
        perf_metrics = [m for m in metrics if m.category == "performance"]
        if perf_metrics:
            improved_perf = [m for m in perf_metrics if m.is_improvement]
            if improved_perf:
                avg_improvement = statistics.mean(
                    [m.improvement_percent for m in improved_perf]
                )
                if avg_improvement > 20:
                    recommendations.append(
                        "キャッシュ最適化が非常に効果的です。"
                        "同様の戦略を他の処理にも適用することを検討してください。"
                    )
                elif avg_improvement > 10:
                    recommendations.append(
                        "パフォーマンス改善が確認されました。"
                        "さらなる最適化の余地があります。"
                    )

        # メモリ使用量の推奨
        memory_metrics = [m for m in metrics if m.category == "memory"]
        memory_improvements = [m for m in memory_metrics if m.is_improvement]
        if memory_metrics and len(memory_improvements) > len(memory_metrics) * 0.7:
            recommendations.append(
                "メモリ使用量が効果的に削減されています。"
                "メモリ監視を継続することを推奨します。"
            )

        return recommendations
