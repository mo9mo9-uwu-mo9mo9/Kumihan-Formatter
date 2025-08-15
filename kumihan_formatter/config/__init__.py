"""統合設定API - Issue #400対応

設定管理の統合リファクタリングで作成された統合API。
全ての設定機能を一元的に提供し、既存コードとの互換性を維持する。

⚠️  DEPRECATION NOTICE - Issue #880 Phase 3:
この設定システムは非推奨です。新しい統一設定システムをご利用ください:
from kumihan_formatter.core.unified_config import UnifiedConfigManager, get_unified_config_manager
"""

import warnings
from typing import cast

from .base_config import BaseConfig
from .config_manager import ConfigManager, create_config_manager, load_config
from .extended_config import ExtendedConfig

# グローバル変数宣言
_default_config: ConfigManager | None = None

# 下位互換性のためのエイリアス
Config = ConfigManager  # 既存のConfigクラスとの互換性

# 便利関数のエクスポート
__all__ = [
    "BaseConfig",
    "ExtendedConfig",
    "ConfigManager",
    "Config",
    "create_config_manager",
    "load_config",
]


# 簡易設定作成関数（simple_config.pyとの互換性）
def create_simple_config() -> ConfigManager:
    """簡素化された設定を作成（simple_config.pyとの互換性）

    Returns:
        ConfigManager: 基本設定を使用した設定管理オブジェクト
    """
    warnings.warn(
        "create_simple_config()は非推奨です。"
        "kumihan_formatter.core.unified_config.get_unified_config_manager()を使用してください。",
        DeprecationWarning,
        stacklevel=2,
    )
    return create_config_manager(config_type="base")


def get_default_config() -> ConfigManager:
    """デフォルト設定インスタンスを取得

    Returns:
        ConfigManager: デフォルト設定管理オブジェクト
    """
    warnings.warn(
        "get_default_config()は非推奨です。"
        "kumihan_formatter.core.unified_config.get_unified_config_manager()を使用してください。",
        DeprecationWarning,
        stacklevel=2,
    )
    global _default_config
    if _default_config is None:
        _default_config = create_config_manager()
    return _default_config


def reset_default_config() -> None:
    """デフォルト設定をリセット"""
    global _default_config
    _default_config = None
