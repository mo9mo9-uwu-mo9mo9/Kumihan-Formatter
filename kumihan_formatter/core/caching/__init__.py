"""
キャッシュシステムモジュール

Smart Cache System の責任分離実装
Issue #319対応 - 単一責任原則に基づくリファクタリング

元ファイル: core/common/smart_cache.py (303行) → 4つのモジュールに分割
"""

from .cache_types import CacheEntry
from .cache_strategies import CacheStrategy, LRUStrategy, LFUStrategy
from .cache_storage import CacheStorage
from .smart_cache import SmartCache

__all__ = [
    # データ型
    "CacheEntry",
    
    # 戦略
    "CacheStrategy",
    "LRUStrategy", 
    "LFUStrategy",
    
    # ストレージ
    "CacheStorage",
    
    # メインクラス
    "SmartCache"
]