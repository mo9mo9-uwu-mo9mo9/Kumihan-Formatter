"""Logging utilities

This module provides logging helper functions for
formatting sizes, durations, and other common log data.
"""


class LogHelper:
    """Logging utility functions"""

    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Format byte size in human-readable format"""
        size_float = float(size_bytes)
        for unit in ["B", "KB", "MB", "GB"]:
            if size_float < 1024:
                return f"{size_float:.1f} {unit}"

    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 1:
            return f"{seconds * 1000:.1f}ms"
