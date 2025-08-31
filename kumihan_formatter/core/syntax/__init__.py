"""Syntax validation module for Kumihan markup

本パッケージは構文検証機能の公開エントリです。後方互換のために
いくつかの関数を再エクスポートしていますが、将来的に整理予定です。

移行ガイド（Deprecation Policy / #1279）:
- 旧エイリアスは段階的に非公開化→削除。
- 公開APIは `SyntaxReporter` と `check_files`/`format_error_report` を利用してください。
"""

# Import main classes and functions for backward compatibility
from .syntax_reporter import SyntaxReporter

# NOTE: 実装が必要なモジュール - Issue #1217対応
# from .syntax_validator import KumihanSyntaxValidator

# Backward compatibility aliases - 一時的に無効化
# KumihanSyntaxChecker = KumihanSyntaxValidator
check_files = SyntaxReporter.check_files
format_error_report = SyntaxReporter.format_error_report

# Export public API
__all__ = [
    # Error types
    "SyntaxError",
    "ErrorSeverity",
    "ErrorTypes",
    # Rules and validation
    "SyntaxRules",
    # "KumihanSyntaxValidator",  # 実装待ち
    "SyntaxReporter",
    # Backward compatibility
    # "KumihanSyntaxChecker",  # 実装待ち
    "check_files",
    "format_error_report",
]
