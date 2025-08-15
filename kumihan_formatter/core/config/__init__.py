"""
設定管理モジュール

Enhanced configuration management の責任分離実装
Issue #319対応 - 単一責任原則に基づくリファクタリング

元ファイル: core/config_manager.py (342行) → 4つのモジュールに分割

⚠️  DEPRECATION NOTICE - Issue #880 Phase 3:
この設定システムは非推奨です。新しい統一設定システムをご利用ください:
from kumihan_formatter.core.unified_config import UnifiedConfigManager, get_unified_config_manager
"""

import warnings

from .config_loader import ConfigLoader
from .config_manager import EnhancedConfig
from .config_types import ConfigLevel, ValidationResult
from .config_validator import ConfigValidator

__all__ = [
    # 型定義
    "ConfigLevel",
    "ValidationResult",
    # 機能クラス
    "ConfigValidator",
    "ConfigLoader",
    "EnhancedConfig",
]
