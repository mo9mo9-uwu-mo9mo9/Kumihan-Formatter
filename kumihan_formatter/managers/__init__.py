"""
統合Manager システム - Issue #1146 アーキテクチャ簡素化
========================================================

Issue #1171対応 - 27個のManagerクラスを5個に統合:
1. ParseManager - 一般的な解析処理
2. RenderManager - 一般的なレンダリング処理
3. ConfigManager - 設定管理
4. ValidationManager - バリデーション処理
5. ResourceManager - リソース管理
"""

from .parse_manager import ParseManager
from .render_manager import RenderManager
from .config_manager import ConfigManager
from .validation_manager import ValidationManager
from .resource_manager import ResourceManager

__all__ = [
    "ParseManager",
    "RenderManager",
    "ConfigManager",
    "ValidationManager",
    "ResourceManager",
]
