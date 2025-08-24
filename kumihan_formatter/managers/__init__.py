"""
統合Manager システム - Issue #1146 アーキテクチャ簡素化
========================================================

従来の27個のManagerクラスを5個に統合:
1. CoreManager - コア設定・IO管理
2. ParsingManager - 解析処理統括  
3. OptimizationManager - 最適化機能
4. PluginManager - プラグイン機能
5. DistributionManager - 配布処理
"""

from .core_manager import CoreManager
from .parsing_manager import ParsingManager
from .optimization_manager import OptimizationManager
from .plugin_manager import PluginManager
from .distribution_manager import DistributionManager

__all__ = [
    "CoreManager",
    "ParsingManager", 
    "OptimizationManager",
    "PluginManager",
    "DistributionManager",
]