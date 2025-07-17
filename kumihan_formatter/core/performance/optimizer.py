"""Performance optimization utilities.

This module provides utilities for optimizing performance including
garbage collection settings and memory management.
"""

import gc

from .system_info import SystemInfoProvider


class PerformanceOptimizer:
    """Performance optimization utilities"""

    def __init__(self) -> None:
        self._system_info = SystemInfoProvider()

    @staticmethod
    def optimize_gc_settings() -> None:
        """Optimize garbage collection settings for better performance"""
        # Disable automatic garbage collection during processing
        gc.disable()

        # Set generation thresholds for better performance
        gc.set_threshold(1000, 15, 15)

    @staticmethod
    def cleanup_memory() -> None:
        """Force garbage collection and memory cleanup"""
        gc.collect()

    @staticmethod
    def estimate_memory_for_nodes(node_count: int) -> int:
        """Estimate memory usage for given number of nodes"""
        # Rough estimate: 1KB per node on average
        return node_count * 1024

    def should_use_streaming(
        self, file_size: int, available_memory: int | None = None
    ) -> bool:
        """Determine if streaming processing should be used"""
        # Use streaming for files larger than 10MB or if memory is limited
        threshold = 10 * 1024 * 1024  # 10MB

        if file_size > threshold:
            return True

        if available_memory is None:
            available_memory = self._system_info.get_available_memory()

        if (
            available_memory and file_size > available_memory * 0.1
        ):  # 10% of available memory
            return True

        return False
