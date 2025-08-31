"""
統合Manager システム - Issue #1215対応完了版
==========================================

6個のManagerクラスを5個に統合（目標達成）:
1. CoreManager - コア機能（IO・キャッシュ・チャンク管理）
2. ParsingManager - 解析・検証機能統合
3. OptimizationManager - 最適化機能
4. PluginManager - プラグイン機能
5. DistributionManager - 配布管理

統合前: 6個のManager → 統合後: 5個のManager（目標達成）
"""

from .core_manager import CoreManager
from .parsing_manager import ParsingManager
from .optimization_manager import OptimizationManager
from .plugin_manager import PluginManager

# from .distribution_manager import DistributionManager  # 移動済み: core.io.distribution_manager

__all__ = [
    "CoreManager",
    "ParsingManager",
    "OptimizationManager",
    "PluginManager",
    # "DistributionManager",  # 移動済み
]
