"""Common utilities and base classes for Kumihan-Formatter

This package contains shared functionality used across the entire codebase.
"""

from .error_framework import (
    BaseErrorHandler,
    ConfigurationError,
    ErrorCategory,
    ErrorContext,
    ErrorSeverity,
    FileSystemError,
    KumihanError,
    SyntaxError,
    ValidationError,
)

# smart_cache import temporaily removed to fix circular import
# Use: from kumihan_formatter.core.caching import SmartCache, CacheStrategy, etc.
from .validation_mixin import ValidationMixin, ValidationRule

__all__ = [
    "KumihanError",
    "BaseErrorHandler",
    "ErrorSeverity",
    "ErrorCategory",
    "ErrorContext",
    "FileSystemError",
    "SyntaxError",
    "ValidationError",
    "ConfigurationError",
    "ValidationMixin",
    "ValidationRule",
]
