"""Unified error handling framework for Kumihan-Formatter - 統合モジュール

This module provides a consistent error handling approach across all components.
All error classes in the system should inherit from KumihanError for consistency.

分割されたモジュール:
- error_types: エラー種別・重要度・コンテキスト定義
- error_base: 基底エラークラス・具体的エラー型
- error_handler: エラーハンドラー基底クラス・チェーン
"""

# 分割されたモジュールからインポート
from .error_base import (
    ConfigurationError,
    FileSystemError,
    KumihanError,
    SyntaxError,
    ValidationError,
)
from .error_handler import BaseErrorHandler, DefaultErrorHandler, ErrorHandlerChain
from .error_types import ErrorCategory, ErrorContext, ErrorSeverity

# 後方互換性のため、全てのクラスと関数を再エクスポート
__all__ = [
    # エラー種別・重要度
    "ErrorSeverity",
    "ErrorCategory",
    "ErrorContext",
    # 基底エラークラス
    "KumihanError",
    # 具体的エラー型
    "FileSystemError",
    "SyntaxError",
    "ValidationError",
    "ConfigurationError",
    # エラーハンドラー
    "BaseErrorHandler",
    "DefaultErrorHandler",
    "ErrorHandlerChain",
]


# 便利な関数
def create_error_with_context(
    message: str,
    severity: ErrorSeverity = ErrorSeverity.ERROR,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    file_path: str | None = None,
    line_number: int | None = None,
    operation: str | None = None,
    suggestions: list[str] | None = None,
) -> KumihanError:
    """Create an error with context information

    Args:
        message: Error message
        severity: Error severity
        category: Error category
        file_path: File path where error occurred
        line_number: Line number where error occurred
        operation: Operation that caused the error
        suggestions: User-friendly suggestions

    Returns:
        KumihanError: Configured error instance
    """
    context = ErrorContext(
        file_path=file_path,
        line_number=line_number,
        operation=operation,
    )

    return KumihanError(
        message=message,
        severity=severity,
        category=category,
        context=context,
        suggestions=suggestions,
    )


def create_file_error(
    message: str,
    file_path: str,
    suggestions: list[str] | None = None,
) -> FileSystemError:
    """Create a file system error

    Args:
        message: Error message
        file_path: File path that caused the error
        suggestions: User-friendly suggestions

    Returns:
        FileSystemError: Configured file system error
    """
    return FileSystemError(
        message=message,
        file_path=file_path,
        suggestions=suggestions,
    )


def create_syntax_error(
    message: str,
    line_number: int | None = None,
    suggestions: list[str] | None = None,
) -> SyntaxError:
    """Create a syntax error

    Args:
        message: Error message
        line_number: Line number where error occurred
        suggestions: User-friendly suggestions

    Returns:
        SyntaxError: Configured syntax error
    """
    return SyntaxError(
        message=message,
        line_number=line_number,
        suggestions=suggestions,
    )
