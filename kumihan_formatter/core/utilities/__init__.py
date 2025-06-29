"""Utilities package for Kumihan-Formatter

This package contains utility functions organized by functionality.
All utilities maintain the same API as the original utils.py for compatibility.
"""

# Import all utility classes and functions for backward compatibility
from .text_processor import TextProcessor
from .file_system import FileSystemHelper
from .data_structures import DataStructureHelper
from .string_similarity import StringSimilarity
from .logging import LogHelper
from .converters import safe_int, safe_float, safe_bool, chunks

# Make everything available at package level for easy importing
__all__ = [
    'TextProcessor',
    'FileSystemHelper', 
    'DataStructureHelper',
    'StringSimilarity',
    'LogHelper',
    'safe_int',
    'safe_float', 
    'safe_bool',
    'chunks'
]