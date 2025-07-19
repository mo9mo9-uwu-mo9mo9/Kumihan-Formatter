"""
キャッシュシステム - 戦略統合インターフェース

分割されたキャッシュ戦略の統合インターフェース
Issue #490対応 - クラス数制限遵守のため分割統合
"""

# 高度戦略をインポート
from .advanced_strategies import (
    AdaptiveStrategy,
    PerformanceAwareStrategy,
    StandardStrategy,
)

# 基本戦略をインポート
from .basic_strategies import CacheStrategy, LFUStrategy, LRUStrategy, TTLStrategy

# 後方互換性のため全戦略を再エクスポート
__all__ = [
    "CacheStrategy",
    "LRUStrategy",
    "LFUStrategy",
    "TTLStrategy",
    "StandardStrategy",
    "AdaptiveStrategy",
    "PerformanceAwareStrategy",
]
