"""
最適化比較ロジック - コア比較・計算処理
ベースラインと最適化後のパフォーマンス比較ロジック
Issue #476対応 - ファイルサイズ制限遵守
"""

from typing import Any

from ..utilities.logger import get_logger
from .optimization_types import (
    SCORE_WEIGHTS,
    SIGNIFICANCE_THRESHOLDS,
    OptimizationMetrics,
)


class ComparisonLogic:
    """最適化比較ロジック

    機能:
    - 実行時間とメモリ使用量の比較
    - 改善メトリクスの計算
    - 統計的有意性の評価
    - 総合改善スコアの計算
    """

    def __init__(self) -> None:
        """比較ロジックを初期化"""
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
            performance_metrics = self.compare_execution_time(
                name, baseline_result, optimized_result
            )
            if performance_metrics:
                metrics.append(performance_metrics)

            # メモリ使用量の比較
            memory_metrics = self.compare_memory_usage(
                name, baseline_result, optimized_result
            )
            if memory_metrics:
                metrics.append(memory_metrics)

        self.logger.info(f"比較完了: {len(metrics)}個のメトリクスを生成")
        return metrics

    def compare_execution_time(
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

    def compare_memory_usage(
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
