"""
統合API設計 - コアAPIモジュール

Issue #1249: 統合API設計統一対応
KumihanFormatterの責任を明確に分離:

1. FormatterConfig - 設定管理
2. FormatterCore - コアロジック
3. FormatterAPI - ユーザーインターフェース
4. ManagerCoordinator - Manager間の調整
"""

from .formatter_config import FormatterConfig
from .formatter_core import FormatterCore
from .formatter_api import FormatterAPI
from .manager_coordinator import ManagerCoordinator

__all__ = [
    "FormatterConfig",
    "FormatterCore",
    "FormatterAPI",
    "ManagerCoordinator",
]
