"""Utilities package for Kumihan-Formatter

This package contains utility functions organized by functionality.
All utilities maintain the same API as the original utils.py for compatibility.
"""

from .caching import SimpleCache
from .converters import chunks, safe_bool, safe_float, safe_int
from .data_structures import DataStructureHelper
from .error_recovery import ErrorRecovery
from .file_system import FileSystemHelper
from .logging import LogHelper
from .performance import PerformanceMetrics, PerformanceMonitor
from .string_similarity import StringSimilarity

# Import all utility classes and functions for backward compatibility
from .text_processor import TextProcessor

# Make everything available at package level for easy importing
__all__ = [
    "TextProcessor",
    "FileSystemHelper",
    "PerformanceMonitor",
    "PerformanceMetrics",
    "DataStructureHelper",
    "StringSimilarity",
    "ErrorRecovery",
    "SimpleCache",
    "LogHelper",
    "safe_int",
    "safe_float",
    "safe_bool",
    "chunks",
]
