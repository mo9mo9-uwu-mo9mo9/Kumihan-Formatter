"""
キャッシュシステム - 高度戦略実装

高度なキャッシュ戦略（適応型、パフォーマンス重視）の実装
Issue #490対応 - cache_strategies.py から分離
"""

from .basic_strategies import CacheStrategy
from .cache_types import CacheEntry


class StandardStrategy(CacheStrategy):
    """標準戦略 - LRU/LFUを統合"""

    def __init__(self, strategy_type: str = "lru"):
        """
        Args:
            strategy_type: "lru" (最新アクセス時刻) または "lfu" (アクセス回数)
        """
        self.strategy_type = strategy_type

    def should_evict(self, entry: CacheEntry) -> bool:
        return entry.is_expired()

    def get_priority(self, entry: CacheEntry) -> float:
        if self.strategy_type == "lru":
            return entry.last_accessed.timestamp()
        elif self.strategy_type == "lfu":
            return float(entry.access_count)
        else:
            # デフォルトはlru
            return entry.last_accessed.timestamp()


class AdaptiveStrategy(CacheStrategy):
    """適応型戦略 - アクセス頻度とファイルサイズを考慮"""

    def __init__(self, frequency_weight: float = 0.6, size_weight: float = 0.4):
        self.frequency_weight = frequency_weight
        self.size_weight = size_weight

    def should_evict(self, entry: CacheEntry) -> bool:
        return entry.is_expired()

    def get_priority(self, entry: CacheEntry) -> float:
        # アクセス頻度による優先度 (高頻度 = 高優先度)
        frequency_score = entry.access_count

        # サイズによる優先度 (小さいファイル = 高優先度)
        size_score = 1.0 / (entry.size_bytes or 1024) if entry.size_bytes else 1.0

        # 重み付き合計 (低い値 = 先に削除)
        return -(
            self.frequency_weight * frequency_score + self.size_weight * size_score
        )


class PerformanceAwareStrategy(CacheStrategy):
    """パフォーマンス重視戦略 - 処理コストを考慮"""

    def __init__(self) -> None:
        self.processing_costs: dict[str, float] = {}  # key -> processing_time の記録

    def should_evict(self, entry: CacheEntry) -> bool:
        return entry.is_expired()

    def get_priority(self, entry: CacheEntry) -> float:
        # 処理コストが高いほど優先度が高い (保持優先)
        # 最後にアクセスされた時間も考慮
        access_score = entry.last_accessed.timestamp()
        frequency_score = entry.access_count

        # アクセス頻度と最新アクセスの組み合わせ
        return -(frequency_score * 0.7 + access_score * 0.3)
