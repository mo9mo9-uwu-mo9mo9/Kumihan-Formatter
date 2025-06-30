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
from .smart_cache import (
    CacheStrategy,
    LFUStrategy,
    LRUStrategy,
    SmartCache,
    cached,
    get_cache,
)
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
    "SmartCache",
    "CacheStrategy",
    "LRUStrategy",
    "LFUStrategy",
    "get_cache",
    "cached",
]
