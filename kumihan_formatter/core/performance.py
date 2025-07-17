"""Performance measurement and optimization utilities for Kumihan-Formatter

DEPRECATED: This module has been split into smaller modules to comply with
the 300-line limit. New code should import from kumihan_formatter.core.performance
package directly.

This module is kept for backward compatibility and re-exports all functions
and classes from the new modular structure.
"""

# Re-export everything from the new modular structure for backward compatibility
from .performance import (
    PerformanceMonitor,
    PerformanceOptimizer,
    PerformanceReport,
    SimplePerformanceProfiler,
    SystemInfoProvider,
    get_global_monitor,
    get_global_profiler,
    get_performance_summary,
    measure_performance,
    profile_function,
)

# Keep the old class names for backward compatibility
PerformanceProfiler = SimplePerformanceProfiler


# Legacy global instances - these now delegate to the new implementation
def get_performance_monitor():
    """Legacy function - use get_global_monitor() instead"""
    return get_global_monitor()


def get_performance_profiler():
    """Legacy function - use get_global_profiler() instead"""
    return get_global_profiler()


# Expose all for backward compatibility
__all__ = [
    "PerformanceReport",
    "PerformanceMonitor",
    "PerformanceProfiler",  # Legacy alias
    "SimplePerformanceProfiler",
    "PerformanceOptimizer",
    "SystemInfoProvider",
    "get_global_monitor",
    "get_global_profiler",
    "get_performance_monitor",  # Legacy
    "get_performance_profiler",  # Legacy
    "measure_performance",
    "profile_function",
    "get_performance_summary",
]
