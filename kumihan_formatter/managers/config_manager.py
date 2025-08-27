"""
ConfigManager - Issue #1171 Manager統合最適化
===========================================

設定管理を統括する統一Managerクラス
core.config.config_manager.ConfigManagerへの統合完了

統合理由:
- core.config.config_manager.ConfigManagerが最も包括的（551行 vs 269行）
- より多くの参照と依存関係を持つ
- グローバル管理機能とスレッドセーフティを完備
"""

# 統合完了 - 最も包括的な実装への統合
from kumihan_formatter.core.config.config_manager import ConfigManager

# 後方互換性エイリアス
UnifiedConfigManager = ConfigManager

__all__ = ["ConfigManager", "UnifiedConfigManager"]