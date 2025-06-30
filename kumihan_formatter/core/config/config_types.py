"""
設定管理 - 型定義

設定システムの基本データ型
Issue #319対応 - config_manager.py から分離
"""

from dataclasses import dataclass
from enum import Enum
from typing import List


class ConfigLevel(Enum):
    """設定の優先度レベル"""

    DEFAULT = 1
    SYSTEM = 2
    USER = 3
    PROJECT = 4
    ENVIRONMENT = 5


@dataclass
class ValidationResult:
    """設定検証結果"""

    is_valid: bool
    errors: List[str]
    warnings: List[str]

    def has_issues(self) -> bool:
        """検証で問題があるかチェック"""
        return len(self.errors) > 0 or len(self.warnings) > 0
