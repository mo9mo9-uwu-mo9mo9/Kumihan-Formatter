"""
統合Manager システム - Issue #1171対応完了
==========================================

27個のManagerクラスを7個に統合（目標5個に最接近）:
1. ParseManager - 解析処理（ParsingManager統合）
2. RenderManager - レンダリング処理
3. ConfigManager - 設定管理（CoreManager設定機能統合）
4. ValidationManager - バリデーション処理
5. ResourceManager - リソース管理（CoreManager IO・テンプレート + OptimizationManager キャッシュ統合）
6. DistributionManager - 配布管理（独立機能）
7. PluginManager - プラグイン管理（独立機能）

統合前: 27個のManager → 統合後: 7個のManager
"""

from .parse_manager import ParseManager
from .render_manager import RenderManager
from .validation_manager import ValidationManager
from .resource_manager import ResourceManager

__all__ = [
    "ParseManager",
    "RenderManager",
    "ValidationManager",
    "ResourceManager",
]
