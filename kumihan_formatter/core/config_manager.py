"""
拡張設定管理 - 互換性維持用レガシーファイル

Issue #319対応: 新しいconfigモジュールへの移行用
このファイルは既存コードとの互換性維持のために残されています。

新しいコードでは以下を使用してください:
from kumihan_formatter.core.config import (
    ConfigLevel, ValidationResult, ConfigValidator,
    ConfigLoader, EnhancedConfig
)
"""

# 廃止予定の警告
import warnings

# 互換性のための再エクスポート
from .config import (
    ConfigLevel,
    ConfigLoader,
    ConfigValidator,
    EnhancedConfig,
    ValidationResult,
)

warnings.warn(
    "config_manager.py は廃止予定です。"
    "新しいコードでは kumihan_formatter.core.config を使用してください。",
    DeprecationWarning,
    stacklevel=2,
)
