"""
エラーハンドリングパッケージ

このパッケージは、Kumihan-Formatterのエラーハンドリング機能を提供します。
技術的なエラーメッセージをユーザーフレンドリーな日本語メッセージに変換し、
具体的な解決方法を提示します。

モジュール構成:
- error_types: 基本的なエラー型定義
- smart_suggestions: スマート提案システム
- error_factories: エラーファクトリー
- error_handler: メインエラーハンドラー
- error_recovery: エラー回復機能（将来の拡張用）
"""

# 基本的なエラー型のインポート
from .error_types import (
    ErrorLevel,
    ErrorCategory,
    ErrorSolution,
    UserFriendlyError
)

# スマート提案システム
from .smart_suggestions import SmartSuggestions

# エラーファクトリー
from .error_factories import (
    ErrorFactory,
    ErrorCatalog,  # 後方互換性のためのエイリアス
    create_syntax_error_from_validation,
    format_file_size_error
)

# メインエラーハンドラー
from .error_handler import ErrorHandler

# エラー回復機能（将来の拡張用）
from .error_recovery import (
    ErrorRecovery,
    create_backup_file,
    restore_from_backup
)

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
    
    # エラーハンドラー
    "ErrorHandler",
    
    # エラー回復（将来の拡張用）
    "ErrorRecovery",
    "create_backup_file",
    "restore_from_backup",
]

# 設定
DEFAULT_MAX_FILE_SIZE_MB = 10
DEFAULT_MAX_RECOVERY_ATTEMPTS = 3