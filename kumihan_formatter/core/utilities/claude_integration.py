"""Claude Code integration utilities for logging

Single Responsibility Principle適用: Claude Code統合機能の分離
Issue #476 Phase3対応 - structured_logger.py分割
"""

import logging
from typing import Any, Dict, Optional

from .log_performance import LogPerformanceOptimizer
from .log_size_control import LogSizeController


class ClaudeCodeIntegrationLogger:
    """Complete Claude Code integration logger

    Provides comprehensive logging capabilities optimized for Claude Code:
    - Structured logging with context
    - Performance optimization
    - Size control
    - Error analysis
    - Automatic formatting
    """

    def __init__(self, name: str):
        self.name = name
        from .logger import get_logger

        base_logger = get_logger(name)

        # Import here to avoid circular imports
        from .structured_logger import StructuredLogger

        self.structured_logger = StructuredLogger(base_logger)

        # Note: ErrorAnalyzer は削除されているため、基本的なログ機能のみ使用
        self.error_analyzer = None
        self.performance_optimizer = LogPerformanceOptimizer(self.structured_logger)
        self.size_controller = LogSizeController(self.structured_logger)

    def log_with_claude_optimization(
        self,
        level: int,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        priority: str = "normal",
        **kwargs: Any,
    ) -> None:
        """Log with Claude Code optimizations

        Args:
            level: Log level
            message: Log message
            context: Optional context data
            priority: Priority level (high, normal, low)
            **kwargs: Additional logging parameters
        """
        # Performance check
        if not self.performance_optimizer.should_log(
            logging.getLevelName(level), message, context, priority
        ):
            return

        # Size check
        estimated_size = self.size_controller.estimate_log_size(message, context)
        if self.size_controller.should_skip_due_to_size(estimated_size, priority):
            return

        # Optimize context
        if context:
            context = self.performance_optimizer.optimize_context(context)
            context = self.size_controller.should_include_context(context)

        # Format message
        message = self.size_controller.format_message_for_size(message)

        # Log with structured logger
        self.structured_logger.log_with_context(level, message, context, **kwargs)

    def debug_optimized(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        priority: str = "low",
        **kwargs: Any,
    ) -> None:
        """Debug log with Claude Code optimizations"""
        self.log_with_claude_optimization(
            logging.DEBUG, message, context, priority, **kwargs
        )

    def info_optimized(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        priority: str = "normal",
        **kwargs: Any,
    ) -> None:
        """Info log with Claude Code optimizations"""
        self.log_with_claude_optimization(
            logging.INFO, message, context, priority, **kwargs
        )

    def warning_optimized(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        priority: str = "normal",
        **kwargs: Any,
    ) -> None:
        """Warning log with Claude Code optimizations"""
        self.log_with_claude_optimization(
            logging.WARNING, message, context, priority, **kwargs
        )

    def error_optimized(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        priority: str = "high",
        **kwargs: Any,
    ) -> None:
        """Error log with Claude Code optimizations"""
        self.log_with_claude_optimization(
            logging.ERROR, message, context, priority, **kwargs
        )

    def critical_optimized(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        priority: str = "high",
        **kwargs: Any,
    ) -> None:
        """Critical log with Claude Code optimizations"""
        self.log_with_claude_optimization(
            logging.CRITICAL, message, context, priority, **kwargs
        )

    def log_performance_with_claude(
        self,
        operation: str,
        duration: float,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Log performance metrics with Claude Code formatting

        Args:
            operation: Operation name
            duration: Duration in seconds
            context: Optional additional context
            **kwargs: Additional logging parameters
        """
        perf_context = {
            "operation": operation,
            "duration_seconds": duration,
            "duration_ms": duration * 1000,
            "performance_log": True,
        }

        if context:
            perf_context.update(context)

        self.info_optimized(
            f"Performance: {operation} completed in {duration:.3f}s",
            perf_context,
            priority="normal",
            **kwargs,
        )

    def log_error_with_analysis(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Log error with automatic analysis

        Args:
            error: Exception object
            context: Optional additional context
            **kwargs: Additional logging parameters
        """
        # Use structured logger for error logging
        error_context = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "error_log": True,
        }

        if context:
            error_context.update(context)

        self.structured_logger.log_with_context(
            logging.ERROR, f"Error occurred: {error}", error_context, exc_info=True, **kwargs
        )

    def log_with_dependency_tracking(
        self,
        level: int,
        message: str,
        dependencies: Optional[list[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Log with dependency tracking for Claude Code analysis

        Args:
            level: Log level
            message: Log message
            dependencies: List of dependency names
            context: Optional context data
            **kwargs: Additional logging parameters
        """
        if dependencies:
            dep_context = {"dependencies": dependencies}
            if context:
                dep_context.update(context)
            context = dep_context

        self.log_with_claude_optimization(level, message, context, **kwargs)


# Global instance cache
_claude_loggers: Dict[str, ClaudeCodeIntegrationLogger] = {}


def get_claude_code_logger(name: str) -> ClaudeCodeIntegrationLogger:
    """Get cached Claude Code integration logger

    Args:
        name: Logger name

    Returns:
        ClaudeCodeIntegrationLogger instance
    """
    if name not in _claude_loggers:
        _claude_loggers[name] = ClaudeCodeIntegrationLogger(name)
    return _claude_loggers[name]
