"""
統合Manager システム - Issue #1253対応完了版
==========================================

6個のManagerクラスを3個に統合（目標達成）:
1. CoreManager - コア機能（IO・キャッシュ・チャンク・配布管理統合）
2. ProcessingManager - 解析・最適化・検証機能統合
3. PluginManager - プラグイン機能

統合前: 6個のManager → 統合後: 3個のManager（50%削減達成）
"""

from .core_manager import CoreManager
from .processing_manager import ProcessingManager
from .plugin_manager import PluginManager

__all__ = [
    "CoreManager",
    "ProcessingManager",
    "PluginManager",
]
