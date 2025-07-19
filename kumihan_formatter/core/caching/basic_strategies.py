"""
キャッシュシステム - 基本戦略実装

基本的なキャッシュ戦略（LRU/LFU/TTL）の実装
Issue #490対応 - cache_strategies.py から分離
"""

from abc import ABC, abstractmethod

from .cache_types import CacheEntry


class CacheStrategy(ABC):
    """キャッシュ戦略の抽象基底クラス"""

    @abstractmethod
    def should_evict(self, entry: CacheEntry) -> bool:
        """エントリを削除すべきかを判定"""
        pass

    @abstractmethod
    def get_priority(self, entry: CacheEntry) -> float:
        """削除優先度を取得（低い値 = 先に削除）"""
        pass


class LRUStrategy(CacheStrategy):
    """Least Recently Used (最近最少使用) 戦略"""

    def should_evict(self, entry: CacheEntry) -> bool:
        return entry.is_expired()

    def get_priority(self, entry: CacheEntry) -> float:
        return entry.last_accessed.timestamp()


class LFUStrategy(CacheStrategy):
    """Least Frequently Used (最少頻度使用) 戦略"""

    def should_evict(self, entry: CacheEntry) -> bool:
        return entry.is_expired()

    def get_priority(self, entry: CacheEntry) -> float:
        return float(entry.access_count)


class TTLStrategy(CacheStrategy):
    """Time To Live (有効期限) 戦略"""

    def should_evict(self, entry: CacheEntry) -> bool:
        return entry.is_expired()

    def get_priority(self, entry: CacheEntry) -> float:
        # 作成時刻が古いほど優先度が低い
        return entry.created_at.timestamp()
