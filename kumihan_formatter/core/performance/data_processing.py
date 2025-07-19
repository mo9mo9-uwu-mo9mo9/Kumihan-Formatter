"""
最適化データ処理 - データ集計・要約処理
最適化メトリクスの集計とパフォーマンス要約作成
Issue #476対応 - ファイルサイズ制限遵守
"""

import statistics
from typing import Any

from .optimization_types import OptimizationMetrics


class DataProcessor:
    """最適化データ処理

    機能:
    - パフォーマンス要約の作成
    - メトリクスの集計・分析
    - キャッシュ効果の分析
    """

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
