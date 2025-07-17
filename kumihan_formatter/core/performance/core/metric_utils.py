"""パフォーマンス監視システムのメトリクス操作ユーティリティ

Single Responsibility Principle適用: メトリクス操作機能
Issue #476 Phase2対応 - パフォーマンスモジュール統合（ユーティリティ分離）
"""

from typing import List

from .benchmark_data import CacheStats


def merge_cache_stats(stats_list: List[CacheStats]) -> CacheStats:
    """複数のキャッシュ統計をマージ

    Args:
        stats_list: マージするキャッシュ統計のリスト

    Returns:
        マージされたキャッシュ統計
    """
    if not stats_list:
        return CacheStats()

    merged = CacheStats()
    for stats in stats_list:
        merged.hits += stats.hits
        merged.misses += stats.misses
        merged.evictions += stats.evictions
        merged.size += stats.size
        merged.max_size = max(merged.max_size, stats.max_size)

    return merged


def calculate_improvement_percentage(before: float, after: float) -> float:
    """改善率を計算

    Args:
        before: 最適化前の値
        after: 最適化後の値

    Returns:
        改善率（パーセント）
    """
    if before == 0:
        return 0.0
    return ((before - after) / before) * 100.0


def determine_significance(improvement_percent: float) -> str:
    """改善の重要度を判定

    Args:
        improvement_percent: 改善率

    Returns:
        重要度レベル
    """
    abs_improvement = abs(improvement_percent)
    if abs_improvement >= 50:
        return "critical"
    elif abs_improvement >= 20:
        return "high"
    elif abs_improvement >= 5:
        return "medium"
    else:
        return "low"
