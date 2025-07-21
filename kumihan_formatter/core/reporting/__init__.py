"""
エラーレポート機能モジュール

統一エラーレポート機能の責任分離実装
Issue #319対応 - 単一責任原則に基づくリファクタリング

元ファイル: core/error_reporting.py (498行) → 4つのモジュールに分割
"""

from .error_context import ErrorContextManager
from .error_formatter import ErrorFormatter
from .error_report import ErrorReport
from .error_report_builder import ErrorReportBuilder
from .error_types import (
    DetailedError,
    ErrorCategory,
    ErrorLocation,
    ErrorSeverity,
    FixSuggestion,
)

__all__ = [
    # エラー型定義
    "ErrorSeverity",
    "ErrorCategory",
    "ErrorLocation",
    "FixSuggestion",
    "DetailedError",
    # 機能クラス
    "ErrorFormatter",
    "ErrorReport",
    "ErrorReportBuilder",
    "ErrorContextManager",
]
