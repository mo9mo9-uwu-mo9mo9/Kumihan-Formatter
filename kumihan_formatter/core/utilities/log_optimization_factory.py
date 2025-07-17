"""
ログ最適化 ファクトリー

ログ最適化コンポーネントの生成・初期化
Issue #492 Phase 5A - log_optimization.py分割
"""

from typing import Any

from .log_performance_optimizer import LogPerformanceOptimizer
from .log_resource_monitor import LogResourceMonitor
from .log_size_controller import LogSizeController


class LogOptimizationFactory:
    """Factory for creating log optimization components"""

    @staticmethod
    def create_performance_optimizer(logger: Any) -> LogPerformanceOptimizer:
        """Create log performance optimizer instance"""
        return LogPerformanceOptimizer(logger)

    @staticmethod
    def create_size_controller(logger: Any) -> LogSizeController:
        """Create log size controller instance"""
        return LogSizeController(logger)

    @staticmethod
    def create_resource_monitor(logger: Any) -> LogResourceMonitor:
        """Create log resource monitor instance"""
        return LogResourceMonitor(logger)


def get_log_performance_optimizer(name: str) -> LogPerformanceOptimizer:
    """Get log performance optimizer instance for a module"""
    from .structured_logging import get_structured_logger

    structured_logger = get_structured_logger(name)
    return LogPerformanceOptimizer(structured_logger)


def get_log_size_controller(name: str) -> LogSizeController:
    """Get log size controller instance for a module"""
    from .structured_logging import get_structured_logger

    structured_logger = get_structured_logger(name)
    return LogSizeController(structured_logger)


def get_log_resource_monitor(name: str) -> LogResourceMonitor:
    """Get log resource monitor instance for a module"""
    from .structured_logging import get_structured_logger

    structured_logger = get_structured_logger(name)
    return LogResourceMonitor(structured_logger)
