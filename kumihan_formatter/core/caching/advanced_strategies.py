"""
キャッシュシステム - 高度戦略実装

高度なキャッシュ戦略（適応型、パフォーマンス重視）の実装
Issue #490対応 - cache_strategies.py から分離
"""

from typing import Final

from .basic_strategies import CacheStrategy
from .cache_types import CacheEntry

# 定数定義
BYTES_PER_MB: Final[int] = 1024 * 1024
DEFAULT_SIZE_DIVISOR: Final[int] = 1024


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
        size_score = (
            1.0 / (entry.size_bytes or DEFAULT_SIZE_DIVISOR)
            if entry.size_bytes
            else 1.0
        )

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


class FrequencyBasedStrategy(CacheStrategy):
    """頻度ベース戦略 - アクセス頻度に基づく管理

    アクセス頻度が閾値未満のエントリを削除対象とし、
    よく使用されるファイルを優先的に保持する戦略。

    使用例:
        >>> strategy = FrequencyBasedStrategy(frequency_threshold=3)
        >>> entry = CacheEntry(key="file.txt", access_count=2)
        >>> strategy.should_evict(entry)  # True (低頻度のため削除)
        >>>
        >>> entry.access_count = 5
        >>> strategy.should_evict(entry)  # False (高頻度のため保持)
    """

    def __init__(self, frequency_threshold: int = 5):
        """
        Args:
            frequency_threshold: 最低保持アクセス回数閾値
        """
        self.frequency_threshold = frequency_threshold

    def should_evict(self, entry: CacheEntry) -> bool:
        # 期限切れまたは低頻度アクセスで削除対象
        return entry.is_expired() or entry.access_count < self.frequency_threshold

    def get_priority(self, entry: CacheEntry) -> float:
        # アクセス頻度が低いほど優先度が低い（先に削除）
        return float(entry.access_count)


class SizeAwareStrategy(CacheStrategy):
    """サイズ認識戦略 - ファイルサイズを考慮した管理

    大きなファイルを優先的に削除し、メモリ使用量を効率的に管理する戦略。

    使用例:
        >>> strategy = SizeAwareStrategy(max_size_mb=5.0)
        >>> large_entry = CacheEntry(key="large.txt", size_bytes=10*1024*1024)  # 10MB
        >>> strategy.should_evict(large_entry)  # True (閾値超過のため削除)
        >>>
        >>> small_entry = CacheEntry(key="small.txt", size_bytes=1024*1024)  # 1MB
        >>> strategy.should_evict(small_entry)  # False (閾値内のため保持)
    """

    def __init__(self, max_size_mb: float = 10.0):
        """
        Args:
            max_size_mb: 大きなファイルとみなすサイズ閾値（MB）
        """
        self.max_size_bytes = max_size_mb * BYTES_PER_MB

    def should_evict(self, entry: CacheEntry) -> bool:
        # 期限切れまたは大きなファイルで削除対象
        return entry.is_expired() or (entry.size_bytes or 0) > self.max_size_bytes

    def get_priority(self, entry: CacheEntry) -> float:
        # ファイルサイズが大きいほど優先度が低い（先に削除）
        return float(entry.size_bytes or 0)
