"""
ログ最適化 統合モジュール

分割された各コンポーネントを統合し、後方互換性を確保
Issue #492 Phase 5A - log_optimization.py分割
"""

from .log_optimization_factory import (
    get_log_performance_optimizer,
    get_log_resource_monitor,
    get_log_size_controller,
)
from .log_performance_optimizer import LogPerformanceOptimizer
from .log_resource_monitor import LogResourceMonitor
from .log_size_controller import LogSizeController

__all__ = [
    "LogPerformanceOptimizer",
    "LogSizeController",
    "LogResourceMonitor",
    "get_log_performance_optimizer",
    "get_log_size_controller",
    "get_log_resource_monitor",
]
