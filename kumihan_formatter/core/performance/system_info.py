"""System information providers for performance monitoring.

This module provides utilities for gathering system information
such as memory and CPU usage.
"""

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class SystemInfoProvider:
    """Provides system information for performance monitoring"""

    def get_memory_usage(self) -> int | None:
        """Get current memory usage"""
        if not HAS_PSUTIL:
            return None

        try:
            import os

            process = psutil.Process(os.getpid())
            return int(process.memory_info().rss)
        except Exception:
            return None

    def get_cpu_usage(self) -> float | None:
        """Get current CPU usage"""
        if not HAS_PSUTIL:
            return None

        try:
            import os

            process = psutil.Process(os.getpid())
            return process.cpu_percent()
        except Exception:
            return None

    def get_available_memory(self) -> int | None:
        """Get available system memory"""
        if not HAS_PSUTIL:
            return None

        try:
            return psutil.virtual_memory().available
        except Exception:
            return None
