"""Central logging module for Kumihan-Formatter

Single Responsibility Principle適用: ログ機能の統合インターフェース
Issue #476 Phase3対応 - logger.py分割後の統合ファイル

This module provides a unified logging system for the entire application,
offering structured logging with levels, formatting, and output management.
"""

# Re-export all classes and functions from split modules
from .logging_formatters import DevLogHandler, StructuredLogFormatter
from .logging_handlers import KumihanLogger, configure_logging, get_logger
from .performance_logger import (
    DependencyTracker,
    ErrorAnalyzer,
    ExecutionFlowTracker,
    call_chain_tracker,
    get_dependency_tracker,
    get_execution_flow_tracker,
    log_performance,
    log_performance_decorator,
    memory_usage_tracker,
)
from .structured_logger import (
    ClaudeCodeIntegrationLogger,
    LogPerformanceOptimizer,
    LogSizeController,
    StructuredLogger,
    get_claude_code_logger,
    get_structured_logger,
)


# Backward compatibility functions
def get_error_analyzer(logger_name: str = "error_analyzer") -> "ErrorAnalyzer":
    """Get error analyzer instance for backward compatibility"""
    from .logging_handlers import get_logger
    from .performance_logger import ErrorAnalyzer

    return ErrorAnalyzer(get_logger(logger_name))


def get_log_performance_optimizer(
    logger_name: str = "performance_optimizer",
) -> "LogPerformanceOptimizer":
    """Get log performance optimizer instance for backward compatibility"""
    from .logging_handlers import get_logger

    return LogPerformanceOptimizer(StructuredLogger(get_logger(logger_name)))


def get_log_size_controller(
    logger_name: str = "size_controller",
) -> "LogSizeController":
    """Get log size controller instance for backward compatibility"""
    from .logging_handlers import get_logger

    return LogSizeController(StructuredLogger(get_logger(logger_name)))


# Backward compatibility - maintain all original exports
__all__ = [
    # Formatters and handlers
    "StructuredLogFormatter",
    "DevLogHandler",
    "KumihanLogger",
    # Main logger functions
    "get_logger",
    "configure_logging",
    # Structured logging
    "StructuredLogger",
    "get_structured_logger",
    # Performance logging
    "log_performance_decorator",
    "call_chain_tracker",
    "memory_usage_tracker",
    "log_performance",
    # Analysis and tracking
    "ErrorAnalyzer",
    "DependencyTracker",
    "ExecutionFlowTracker",
    "get_dependency_tracker",
    "get_execution_flow_tracker",
    # Optimization
    "LogPerformanceOptimizer",
    "LogSizeController",
    # Claude Code integration
    "ClaudeCodeIntegrationLogger",
    "get_claude_code_logger",
    # Backward compatibility functions
    "get_error_analyzer",
    "get_log_performance_optimizer",
    "get_log_size_controller",
]

# Maintain backward compatibility for any code that imports directly
# from kumihan_formatter.core.utilities.logger
try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
