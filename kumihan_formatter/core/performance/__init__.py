"""
パフォーマンス最適化モジュール

高度なパフォーマンス分析・監視・最適化システム
Issue #402対応 - パフォーマンス最適化とキャッシュシステム強化
Issue #476対応 - 300行制限に準拠した分割実装
"""

from contextlib import _GeneratorContextManager
from typing import Any

from .metrics import PerformanceReport
from .monitor import PerformanceMonitor
from .optimizer import PerformanceOptimizer
from .simple_profiler import SimplePerformanceProfiler
from .system_info import SystemInfoProvider

# Global instances for easy access - converted to lazy initialization
_global_monitor = None
_global_profiler = None


def get_global_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance (lazy initialization)"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor


def get_global_profiler() -> SimplePerformanceProfiler:
    """Get the global performance profiler instance (lazy initialization)"""
    global _global_profiler
    if _global_profiler is None:
        _global_profiler = SimplePerformanceProfiler()
    return _global_profiler


def measure_performance(
    operation_name: str, **kwargs: Any
) -> _GeneratorContextManager[PerformanceMonitor]:
    """Convenience function for performance measurement"""
    return get_global_monitor().measure(operation_name, **kwargs)


def profile_function(func_name: str | None = None) -> Any:
    """Convenience decorator for function profiling"""
    return get_global_profiler().profile(func_name)


def get_performance_summary() -> dict[str, Any]:
    """Get comprehensive performance summary"""
    return {
        "monitor_stats": get_global_monitor().get_summary_stats(),
        "profiler_stats": get_global_profiler().get_stats(),
        "top_functions": get_global_profiler().get_top_functions(),
    }


# Expose main classes for backward compatibility
__all__ = [
    "PerformanceReport",
    "PerformanceMonitor",
    "SimplePerformanceProfiler",
    "PerformanceOptimizer",
    "SystemInfoProvider",
    "get_global_monitor",
    "get_global_profiler",
    "measure_performance",
    "profile_function",
    "get_performance_summary",
]
