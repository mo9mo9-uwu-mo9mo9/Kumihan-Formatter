"""
パフォーマンス ファクトリー

ログパフォーマンス最適化インスタンスの取得
Issue #492 Phase 5A - performance_logger.py分割
"""

from .performance_optimizer import LogPerformanceOptimizer


def get_log_performance_optimizer(name: str) -> LogPerformanceOptimizer:
    """Get log performance optimizer instance for a module

    Args:
        name: Module name (typically __name__)

    Returns:
        LogPerformanceOptimizer instance for performance optimization
    """
    from .structured_logger import get_structured_logger

    structured_logger = get_structured_logger(name)
    return LogPerformanceOptimizer(structured_logger)
