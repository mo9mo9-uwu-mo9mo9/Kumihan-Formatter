"""Parse cache analytics functionality extracted from parse_cache.py

This module contains analytics and optimization features
for the parse cache system.
"""

from datetime import datetime
from typing import Any

from ..performance import get_global_monitor


class ParseCacheAnalytics:
    """パースキャッシュの分析機能"""

    def __init__(self, cache_core):
        """分析機能を初期化

        Args:
            cache_core: ParseCacheCore instance
        """
        self.cache_core = cache_core
        self.monitor = get_global_monitor()

    def get_parse_statistics(self) -> dict[str, Any]:
        """パースキャッシュの統計情報を取得

        Returns:
            dict: 統計情報
        """
        stats = self.cache_core.parse_stats.copy()

        # キャッシュヒット率を計算
        total_requests = stats["cache_hits"] + stats["cache_misses"]
        if total_requests > 0:
            stats["hit_rate"] = stats["cache_hits"] / total_requests
        else:
            stats["hit_rate"] = 0.0

        # メモリ使用状況を追加
        stats["memory_usage"] = self.cache_core.get_memory_usage()
        stats["entry_count"] = len(self.cache_core.memory_cache)

        # パフォーマンス効果を計算
        time_saved = stats["cache_hits"] * stats["avg_parse_time"]
        stats["time_saved_seconds"] = time_saved

        return stats

    def optimize_cache_for_patterns(self) -> dict[str, Any]:
        """使用パターンに基づいてキャッシュを最適化

        Returns:
            dict: 最適化結果
        """
        optimization_results = {
            "actions_taken": [],
            "performance_impact": {},
            "recommendations": [],
        }

        stats = self.get_parse_statistics()
        hit_rate = stats["hit_rate"]

        # ヒット率が低い場合の対策
        if hit_rate < 0.3:  # 30%以下
            # TTLを延長
            self.cache_core.default_ttl = int(self.cache_core.default_ttl * 1.5)
            optimization_results["actions_taken"].append("TTL延長")

            # メモリ上限を増加（可能であれば）
            if self.cache_core.max_memory_mb < 200:
                self.cache_core.max_memory_mb = min(
                    self.cache_core.max_memory_mb * 1.2, 200
                )
                optimization_results["actions_taken"].append("メモリ上限増加")

            optimization_results["recommendations"].append(
                "パースパターンの見直しを検討してください"
            )

        # メモリ使用率が高い場合の対策
        memory_usage = stats["memory_usage"]
        if memory_usage > 0.8:  # 80%以上
            # 古いエントリを積極的に削除
            self.cache_core.cleanup_expired_entries()
            optimization_results["actions_taken"].append("期限切れエントリの削除")

            # TTLを短縮
            self.cache_core.default_ttl = int(self.cache_core.default_ttl * 0.8)
            optimization_results["actions_taken"].append("TTL短縮")

            optimization_results["recommendations"].append(
                "メモリ使用量の監視を強化してください"
            )

        # パフォーマンス効果を計算
        optimization_results["performance_impact"] = {
            "current_hit_rate": hit_rate,
            "time_saved_seconds": stats["time_saved_seconds"],
            "memory_usage_percent": memory_usage * 100,
        }

        return optimization_results

    def invalidate_by_content_hash(self, content_hash: str) -> int:
        """コンテンツハッシュによる無効化

        Args:
            content_hash: 無効化するコンテンツのハッシュ

        Returns:
            int: 無効化されたエントリ数
        """
        invalidated_count = 0

        # メモリキャッシュから削除
        keys_to_remove = []
        for key in self.cache_core.memory_cache:
            if content_hash in key:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            self.cache_core.delete(key)
            invalidated_count += 1

        # パフォーマンス監視に記録
        self.monitor.record_cache_invalidation("parse_cache", invalidated_count)

        return invalidated_count

    def create_cache_snapshot(self) -> dict[str, Any]:
        """キャッシュの現在の状態のスナップショットを作成

        Returns:
            dict: スナップショット情報
        """
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "statistics": self.get_parse_statistics(),
            "cache_keys": list(self.cache_core.memory_cache.keys()),
            "configuration": {
                "max_memory_mb": self.cache_core.max_memory_mb,
                "max_entries": self.cache_core.max_memory_entries,
                "default_ttl": self.cache_core.default_ttl,
            },
        }

        return snapshot
