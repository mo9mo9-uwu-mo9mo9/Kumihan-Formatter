"""
スマートキャッシュシステム - 互換性維持用レガシーファイル

Issue #319対応: 新しいcachingモジュールへの移行用
このファイルは既存コードとの互換性維持のために残されています。

新しいコードでは以下を使用してください:
from kumihan_formatter.core.caching import (
    CacheEntry, CacheStrategy, LRUStrategy, LFUStrategy,
    CacheStorage, SmartCache
)
"""

# 廃止予定の警告
import warnings

# 互換性のための再エクスポート
from ..caching import (  # noqa: F401
    AdaptiveStrategy,
    CacheEntry,
    CacheStorage,
    CacheStrategy,
    LFUStrategy,
    LRUStrategy,
    PerformanceAwareStrategy,
    SmartCache,
    TTLStrategy,
)

warnings.warn(
    "smart_cache.py は廃止予定です。"
    "新しいコードでは kumihan_formatter.core.caching を使用してください。",
    DeprecationWarning,
    stacklevel=2,
)
