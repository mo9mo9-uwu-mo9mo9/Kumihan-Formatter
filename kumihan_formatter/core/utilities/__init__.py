"""Utilities package for Kumihan-Formatter

This package contains utility functions organized by functionality.
All utilities maintain the same API as the original utils.py for compatibility.
"""

from .parallel_processor import (
    ChunkInfo,
    ParallelChunkProcessor,
    ParallelStreamingParser,
)
from .processor_core import ParallelChunkProcessor as ParallelChunkProcessorCore
from .streaming_parser import ParallelStreamingParser as ParallelStreamingParserCore

# Import all utility classes and functions for backward compatibility
from .text_processor import TextProcessor

# Make everything available at package level for easy importing
__all__ = [
    "TextProcessor",
    "ChunkInfo",
    "ParallelChunkProcessor",
    "ParallelStreamingParser",
    "ParallelChunkProcessorCore",
    "ParallelStreamingParserCore",
]
