"""
エラー回復システム - Issue #401対応

エラーからの自動回復機能を提供するモジュール。
"""

from .base import RecoveryStrategy
from .content_strategies import MemoryErrorRecoveryStrategy, SyntaxErrorRecoveryStrategy
from .file_strategies import (
    FileEncodingRecoveryStrategy,
    FileNotFoundRecoveryStrategy,
    FilePermissionRecoveryStrategy,
)
from .manager import (
    RecoveryManager,
    get_global_recovery_manager,
    set_global_recovery_manager,
)

__all__ = [
    "RecoveryStrategy",
    "FileEncodingRecoveryStrategy",
    "FilePermissionRecoveryStrategy",
    "FileNotFoundRecoveryStrategy",
    "SyntaxErrorRecoveryStrategy",
    "MemoryErrorRecoveryStrategy",
    "RecoveryManager",
    "get_global_recovery_manager",
    "set_global_recovery_manager",
]
