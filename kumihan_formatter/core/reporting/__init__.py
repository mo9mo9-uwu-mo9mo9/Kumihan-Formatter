"""
エラーレポート機能モジュール

統一エラーレポート機能の責任分離実装
Issue #319対応 - 単一責任原則に基づくリファクタリング

元ファイル: core/error_reporting.py (498行) → 4つのモジュールに分割
"""

from .error_types import (
    ErrorSeverity,
    ErrorCategory, 
    ErrorLocation,
    FixSuggestion,
    DetailedError
)

from .error_formatter import ErrorFormatter
from .error_report import ErrorReport, ErrorReportBuilder
from .error_context import ErrorContextManager

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
    "ErrorContextManager"
]