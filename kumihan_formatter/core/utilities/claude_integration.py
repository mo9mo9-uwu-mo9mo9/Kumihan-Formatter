"""Claude Code integration logger for Kumihan-Formatter

This module provides a complete Claude Code integration logger that combines
all logging features into a single, optimized interface.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, Optional

from .log_analysis import ErrorAnalyzer, DependencyTracker, ExecutionFlowTracker
from .log_optimization import LogPerformanceOptimizer, LogSizeController
from .structured_logging import get_structured_logger


class ClaudeCodeIntegrationLogger:
    """Phase 4: Complete Claude Code integration logger

    Combines all Phase 1-4 features into a single, optimized logger
    specifically designed for Claude Code interaction.
    """

    def __init__(self, name: str):
        self.name = name
        self.structured_logger = get_structured_logger(name)
        self.error_analyzer = ErrorAnalyzer(self.structured_logger)
        self.dependency_tracker = DependencyTracker(self.structured_logger)
        self.flow_tracker = ExecutionFlowTracker(self.structured_logger)
        self.performance_optimizer = LogPerformanceOptimizer(self.structured_logger)
        self.size_controller = LogSizeController(self.structured_logger)

    def log_with_claude_optimization(
        self,
        level: int,
        message: str,
        context: Optional[dict[str, Any]] = None,
        operation: Optional[str] = None,
        priority: str = "normal",
    ) -> None:
        """Log with full Claude Code optimization

        Args:
            level: Log level
            message: Log message
            context: Context data
            operation: Operation name
            priority: Priority level (high, normal, low)
        """
        start_time = time.time()

        # Generate message key for performance tracking
        message_key = (
            f"{self.name}_{operation or 'general'}_{logging.getLevelName(level)}"
        )

        # Check if we should log based on performance
        if not self.performance_optimizer.should_log(level, message_key, operation):
            return

        # Optimize context for Claude Code
        if context:
            context = self.size_controller.optimize_for_claude_code(context)
            context = self.size_controller.should_include_context(context)

        # Format message for size control
        formatted_message = self.size_controller.format_message_for_size(message)

        # Estimate size and check if we should skip
        estimated_size = self.size_controller.estimate_log_size(
            formatted_message, context
        )
        if self.size_controller.should_skip_due_to_size(estimated_size, priority):
            return

        # Perform the actual logging
        if context:
            self.structured_logger.log_with_context(level, formatted_message, context)
        else:
            self.structured_logger.logger.log(level, formatted_message)

        # Record performance metrics
        duration = time.time() - start_time
        self.performance_optimizer.record_log_event(level, message_key, duration)

    def log_error_with_claude_analysis(
        self,
        error: Exception,
        message: str,
        context: Optional[dict[str, Any]] = None,
        operation: Optional[str] = None,
    ) -> None:
        """Log error with full Claude Code analysis"""
        self.error_analyzer.log_error_with_analysis(error, message, context, operation)

    def track_function_execution(
        self, function_name: str, args_info: Optional[dict[str, Any]] = None
    ) -> str:
        """Track function execution with flow tracking"""
        return self.flow_tracker.enter_function(function_name, self.name, args_info)

    def finish_function_execution(
        self,
        frame_id: str,
        success: bool = True,
        result_info: Optional[dict[str, Any]] = None,
        error_info: Optional[dict[str, Any]] = None,
    ) -> None:
        """Finish function execution tracking"""
        self.flow_tracker.exit_function(frame_id, success, result_info, error_info)

    def track_dependency_import(
        self,
        module_name: str,
        imported_from: Optional[str] = None,
        import_time: Optional[float] = None,
    ) -> None:
        """Track module dependency import"""
        self.dependency_tracker.track_import(module_name, imported_from, import_time)

    def get_comprehensive_report(self) -> dict[str, Any]:
        """Get comprehensive report combining all tracking data"""
        return {
            "module": self.name,
            "timestamp": datetime.now().isoformat(),
            "performance": self.performance_optimizer.get_performance_report(),
            "size_stats": self.size_controller.get_size_statistics(),
            "dependencies": self.dependency_tracker.get_dependency_map(),
            "execution_flow": self.flow_tracker.get_current_flow(),
            "claude_hint": "Complete integration report for debugging and optimization",
        }

    # Convenience methods for common logging patterns
    def info(self, message: str, **context: Any) -> None:
        """Log info message with Claude optimization"""
        self.log_with_claude_optimization(logging.INFO, message, context)

    def debug(self, message: str, **context: Any) -> None:
        """Log debug message with Claude optimization"""
        self.log_with_claude_optimization(logging.DEBUG, message, context)

    def warning(self, message: str, **context: Any) -> None:
        """Log warning message with Claude optimization"""
        self.log_with_claude_optimization(logging.WARNING, message, context)

    def error(self, message: str, **context: Any) -> None:
        """Log error message with Claude optimization"""
        self.log_with_claude_optimization(logging.ERROR, message, context)

    def critical(self, message: str, **context: Any) -> None:
        """Log critical message with Claude optimization"""
        self.log_with_claude_optimization(logging.CRITICAL, message, context)

    def file_operation(
        self, operation: str, file_path: str, success: bool = True, **context: Any
    ) -> None:
        """Log file operations with Claude optimization"""
        level = logging.INFO if success else logging.ERROR
        full_context = {
            "file_path": file_path,
            "operation": operation,
            "success": success,
            **context,
        }
        self.log_with_claude_optimization(
            level, f"File {operation}", full_context, operation="file_operation"
        )

    def performance(
        self, operation: str, duration_seconds: float, **context: Any
    ) -> None:
        """Log performance metrics with Claude optimization"""
        full_context = {
            "operation": operation,
            "duration_seconds": duration_seconds,
            "duration_ms": duration_seconds * 1000,
            **context,
        }
        self.log_with_claude_optimization(
            logging.INFO,
            f"Performance: {operation}",
            full_context,
            operation="performance_tracking",
        )


def get_claude_code_logger(name: str) -> ClaudeCodeIntegrationLogger:
    """Get complete Claude Code integration logger

    Args:
        name: Module name (typically __name__)

    Returns:
        ClaudeCodeIntegrationLogger with all Phase 1-4 features
    """
    return ClaudeCodeIntegrationLogger(name)