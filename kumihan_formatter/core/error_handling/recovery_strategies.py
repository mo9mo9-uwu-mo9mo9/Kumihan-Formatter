"""
エラー回復戦略 - Issue #401対応（分割後の統合インポート）

エラー発生時の自動回復機能を提供し、
可能な限り処理を継続できるようにするシステム。

このファイルは技術的負債解消（Issue #476）により分割されました：
- recovery/base.py: 基底クラス
- recovery/file_strategies.py: ファイル系戦略
- recovery/content_strategies.py: コンテンツ系戦略
- recovery/manager.py: 管理システム
"""

# 後方互換性のため、分割されたモジュールからインポート
from .recovery import (
    FileEncodingRecoveryStrategy,
    FileNotFoundRecoveryStrategy,
    FilePermissionRecoveryStrategy,
    MemoryErrorRecoveryStrategy,
    RecoveryManager,
    RecoveryStrategy,
    SyntaxErrorRecoveryStrategy,
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
