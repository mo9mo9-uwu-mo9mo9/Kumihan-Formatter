"""Common utilities and base classes for Kumihan-Formatter

This package contains shared functionality used across the entire codebase.
"""

from .error_framework import (
    KumihanError,
    BaseErrorHandler,
    ErrorSeverity,
    ErrorCategory,
    ErrorContext,
    FileSystemError,
    SyntaxError,
    ValidationError,
    ConfigurationError
)
from .validation_mixin import ValidationMixin, ValidationRule
from .smart_cache import SmartCache, CacheStrategy, LRUStrategy, LFUStrategy, get_cache, cached

__all__ = [
    'KumihanError',
    'BaseErrorHandler', 
    'ErrorSeverity',
    'ErrorCategory',
    'ErrorContext',
    'FileSystemError',
    'SyntaxError',
    'ValidationError',
    'ConfigurationError',
    'ValidationMixin',
    'ValidationRule',
    'SmartCache',
    'CacheStrategy',
    'LRUStrategy',
    'LFUStrategy',
    'get_cache',
    'cached'
]