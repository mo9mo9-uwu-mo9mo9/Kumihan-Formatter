"""Utilities package for Kumihan-Formatter

This package contains utility functions organized by functionality.
All utilities maintain the same API as the original utils.py for compatibility.
"""

# Import all utility classes and functions for backward compatibility
from .text_processor import TextProcessor
from .file_system import FileSystemHelper
from .performance import PerformanceMonitor, PerformanceMetrics
from .data_structures import DataStructureHelper
from .string_similarity import StringSimilarity
from .error_recovery import ErrorRecovery
from .caching import SimpleCache
from .logging import LogHelper
from .converters import safe_int, safe_float, safe_bool, chunks

# Make everything available at package level for easy importing
__all__ = [
    'TextProcessor',
    'FileSystemHelper', 
    'PerformanceMonitor',
    'PerformanceMetrics',
    'DataStructureHelper',
    'StringSimilarity',
    'ErrorRecovery',
    'SimpleCache',
    'LogHelper',
    'safe_int',
    'safe_float', 
    'safe_bool',
    'chunks'
]