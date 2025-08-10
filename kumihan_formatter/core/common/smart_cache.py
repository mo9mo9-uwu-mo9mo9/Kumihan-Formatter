"""
スマートキャッシュシステム - 互換性維持用レガシーファイル

Issue #319対応: cachingモジュール削除のため基本実装を統合
このファイルは既存コードとの互換性維持のために残されています。
"""

import warnings
from typing import Any, Dict, Generic, Optional, TypeVar, Protocol
from dataclasses import dataclass
from datetime import datetime, timedelta
import threading

T = TypeVar("T")
K = TypeVar("K")


@dataclass
class CacheEntry(Generic[T]):
    """キャッシュエントリ"""

    value: T
    created_at: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None


class CacheStrategy(Protocol):
    """キャッシュ戦略インターフェース"""

    def should_evict(self, entry: CacheEntry[Any]) -> bool: ...


class LRUStrategy:
    """LRU戦略"""

    def __init__(self, max_size: int = 100):
        self.max_size = max_size

    def should_evict(self, entry: CacheEntry[Any]) -> bool:
        return False  # LRU実装は簡略化


class LFUStrategy:
    """LFU戦略"""

    def __init__(self, max_size: int = 100):
        self.max_size = max_size

    def should_evict(self, entry: CacheEntry[Any]) -> bool:
        return False  # LFU実装は簡略化


class TTLStrategy:
    """TTL戦略"""

    def __init__(self, ttl_seconds: int = 3600):
        self.ttl_seconds = ttl_seconds

    def should_evict(self, entry: CacheEntry[Any]) -> bool:
        return (datetime.now() - entry.created_at).total_seconds() > self.ttl_seconds


class AdaptiveStrategy:
    """適応的戦略"""

    def should_evict(self, entry: CacheEntry[Any]) -> bool:
        return False


class PerformanceAwareStrategy:
    """パフォーマンス対応戦略"""

    def should_evict(self, entry: CacheEntry[Any]) -> bool:
        return False


class CacheStorage(Generic[K, T]):
    """キャッシュストレージ"""

    def __init__(self):
        self._data: Dict[K, CacheEntry[T]] = {}
        self._lock = threading.Lock()

    def get(self, key: K) -> Optional[CacheEntry[T]]:
        with self._lock:
            return self._data.get(key)

    def set(self, key: K, entry: CacheEntry[T]) -> None:
        with self._lock:
            self._data[key] = entry

    def remove(self, key: K) -> None:
        with self._lock:
            self._data.pop(key, None)


class SmartCache(Generic[K, T]):
    """スマートキャッシュ"""

    def __init__(self, strategy: Optional[CacheStrategy] = None):
        self.strategy = strategy or LRUStrategy()
        self.storage: CacheStorage[K, T] = CacheStorage()

    def get(self, key: K) -> Optional[T]:
        entry = self.storage.get(key)
        if entry is None:
            return None

        if self.strategy.should_evict(entry):
            self.storage.remove(key)
            return None

        entry.access_count += 1
        entry.last_accessed = datetime.now()
        return entry.value

    def set(self, key: K, value: T) -> None:
        entry = CacheEntry(value=value, created_at=datetime.now(), last_accessed=datetime.now())
        self.storage.set(key, entry)


warnings.warn(
    "smart_cache.py は廃止予定です。"
    "新しいコードでは基本的なキャッシュ機能を直接実装してください。",
    DeprecationWarning,
    stacklevel=2,
)
