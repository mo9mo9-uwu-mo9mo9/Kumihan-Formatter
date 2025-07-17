"""
エラーハンドリングパッケージ - Issue #401対応

このパッケージは、Kumihan-Formatterの統一エラーハンドリング機能を提供します。
技術的なエラーメッセージをユーザーフレンドリーな日本語メッセージに変換し、
具体的な解決方法と自動回復機能を提示します。

モジュール構成:
- error_types: 基本的なエラー型定義
- smart_suggestions: スマート提案システム
- error_factories: エラーファクトリー
- error_handler: 従来のエラーハンドラー（後方互換性）
- unified_handler: 統一エラーハンドラー（推奨）
- context_manager: エラーコンテキスト管理
- recovery_strategies: 自動回復戦略
- error_recovery: エラー回復機能（将来の拡張用）
"""

from .context_manager import (
    ErrorContextManager,
    clear_contexts,
)
from .context_manager import get_context_manager as get_global_context_manager
from .context_manager import (
    get_current_context,
    operation_context,
    set_line_position,
    set_user_input,
)
from .context_models import (
    FileContext,
    OperationContext,
    SystemContext,
)


# 後方互換性のため
def set_global_context_manager(manager: ErrorContextManager) -> None:
    """グローバルコンテキストマネージャーの設定（後方互換性）"""
    import kumihan_formatter.core.error_handling.context_manager as cm

    cm._global_context_manager = manager


# エラーファクトリー
from .error_factories import ErrorCatalog  # 後方互換性のためのエイリアス
from .error_factories import (
    ErrorFactory,
    create_syntax_error_from_validation,
    format_file_size_error,
)

# メインエラーハンドラー
from .error_handler import ErrorHandler

# エラー回復機能（将来の拡張用）
from .error_recovery import ErrorRecovery, create_backup_file, restore_from_backup

# 基本的なエラー型のインポート
from .error_types import ErrorCategory, ErrorLevel, ErrorSolution, UserFriendlyError
from .japanese_messages import (
    JapaneseMessageCatalog,
    UserGuidanceProvider,
    create_user_friendly_error,
)
from .recovery_strategies import (
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

# スマート提案システム
from .smart_suggestions import SmartSuggestions

# 新しい統一エラーハンドリングシステム（Issue #401）
from .unified_handler import UnifiedErrorHandler, get_global_handler, set_global_handler

# パッケージ情報
__version__ = "1.0.0"
__author__ = "Kumihan-Formatter Team"

# 後方互換性のためのエクスポート
__all__ = [
    # エラー型
    "ErrorLevel",
    "ErrorCategory",
    "ErrorSolution",
    "UserFriendlyError",
    # スマート提案
    "SmartSuggestions",
    # エラーファクトリー
    "ErrorFactory",
    "ErrorCatalog",  # 後方互換性
    "create_syntax_error_from_validation",
    "format_file_size_error",
    # 従来のエラーハンドラー（後方互換性）
    "ErrorHandler",
    # エラー回復（将来の拡張用）
    "ErrorRecovery",
    "create_backup_file",
    "restore_from_backup",
    # 新しい統一エラーハンドリングシステム（推奨）
    "UnifiedErrorHandler",
    "get_global_handler",
    "set_global_handler",
    # コンテキスト管理
    "ErrorContextManager",
    "OperationContext",
    "SystemContext",
    "FileContext",
    "get_global_context_manager",
    "set_global_context_manager",
    # 回復戦略
    "RecoveryManager",
    "RecoveryStrategy",
    "FileEncodingRecoveryStrategy",
    "FilePermissionRecoveryStrategy",
    "SyntaxErrorRecoveryStrategy",
    "FileNotFoundRecoveryStrategy",
    "MemoryErrorRecoveryStrategy",
    "get_global_recovery_manager",
    "set_global_recovery_manager",
    # 日本語メッセージとガイダンス
    "JapaneseMessageCatalog",
    "UserGuidanceProvider",
    "create_user_friendly_error",
]

# 設定
DEFAULT_MAX_FILE_SIZE_MB = 10
DEFAULT_MAX_RECOVERY_ATTEMPTS = 3
