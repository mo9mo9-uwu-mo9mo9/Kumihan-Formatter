"""
統一エラーレポート機能 - 互換性維持用レガシーファイル

Issue #319対応: 新しいreportingモジュールへの移行用
このファイルは既存コードとの互換性維持のために残されています。

新しいコードでは以下を使用してください:
from kumihan_formatter.core.reporting import (
    ErrorSeverity, ErrorCategory, ErrorLocation,
    FixSuggestion, DetailedError, ErrorReport,
    ErrorReportBuilder, ErrorFormatter, ErrorContextManager
)
"""

# 廃止予定の警告
import warnings

# 互換性のための再エクスポート

warnings.warn(
    "error_reporting.py は廃止予定です。"
    "新しいコードでは kumihan_formatter.core.reporting を使用してください。",
    DeprecationWarning,
    stacklevel=2,
)
