"""Syntax validation module for Kumihan markup

This module provides comprehensive syntax validation for Kumihan markup files.
It has been refactored from a single large file into focused modules for
better maintainability and organization.
"""

# Import main classes and functions for backward compatibility
from .syntax_errors import ErrorSeverity, ErrorTypes, SyntaxError
from .syntax_reporter import SyntaxReporter
from .syntax_rules import SyntaxRules
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
