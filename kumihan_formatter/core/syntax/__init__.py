"""Syntax validation module for Kumihan markup

This module provides comprehensive syntax validation for Kumihan markup files.
It has been refactored from a single large file into focused modules for
better maintainability and organization.
"""

# Import main classes and functions for backward compatibility
from .syntax_errors import ErrorSeverity, ErrorTypes, SyntaxError
from .syntax_reporter import SyntaxReporter
from .syntax_rules import SyntaxRules
from .syntax_validator import KumihanSyntaxValidator

# Backward compatibility aliases
KumihanSyntaxChecker = KumihanSyntaxValidator
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
    "KumihanSyntaxValidator",
    "SyntaxReporter",
    # Backward compatibility
    "KumihanSyntaxChecker",
    "check_files",
    "format_error_report",
]
