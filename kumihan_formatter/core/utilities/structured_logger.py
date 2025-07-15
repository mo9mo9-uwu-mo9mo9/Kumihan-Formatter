"""Structured logging and Claude Code integration for Kumihan-Formatter

Single Responsibility Principle適用: 構造化ログとClaude Code連携機能の分離
Issue #476 Phase3対応 - logger.py分割
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, Optional

from .performance_logger import ErrorAnalyzer


class StructuredLogger:
    """Enhanced logger with structured logging capabilities

    Provides methods for logging with structured context data,
    making it easier for Claude Code to parse and analyze logs.
    """

    # Sensitive keys that should be filtered out from logs (pre-lowercased for performance)
    SENSITIVE_KEYS = {
        "password",
        "passwd",
        "pwd",
        "secret",
        "token",
        "key",
        "api_key",
        "auth_token",
        "bearer_token",
        "access_token",
        "refresh_token",
        "credential",
        "authorization",
        "session_id",
        "cookie",
    }

    # Cache for lowercased keys to avoid repeated string operations
    _key_cache: dict[str, str] = {}

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def _sanitize_context(self, context: dict[str, Any]) -> dict[str, Any]:
        """Remove sensitive information from context data

        Args:
            context: Original context dictionary

        Returns:
            Sanitized context dictionary with sensitive data filtered out
        """
        sanitized = {}
        for key, value in context.items():
            # Use cache to avoid repeated string.lower() operations
            if key not in self._key_cache:
                self._key_cache[key] = key.lower()
                # Limit cache size to prevent memory issues
                if len(self._key_cache) > 1000:
                    self._key_cache.clear()

            if self._key_cache[key] in self.SENSITIVE_KEYS:
                sanitized[key] = "[FILTERED]"
            else:
                sanitized[key] = value
        return sanitized

    def log_with_context(
        self,
        level: int,
        message: str,
        context: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Log message with structured context

        Args:
            level: Log level (logging.INFO, etc.)
            message: Log message
            context: Structured context data
            **kwargs: Additional context as keyword arguments
        """
        if context or kwargs:
            full_context = {**(context or {}), **kwargs}
            # Sanitize sensitive information
            sanitized_context = self._sanitize_context(full_context)
            extra = {"context": sanitized_context}
            self.logger.log(level, message, extra=extra)
        else:
            self.logger.log(level, message)

    def info(self, message: str, **context: Any) -> None:
        """Log info with context"""
        self.log_with_context(logging.INFO, message, **context)

    def debug(self, message: str, **context: Any) -> None:
        """Log debug with context"""
        self.log_with_context(logging.DEBUG, message, **context)

    def warning(self, message: str, **context: Any) -> None:
        """Log warning with context"""
        self.log_with_context(logging.WARNING, message, **context)

    def error(self, message: str, **context: Any) -> None:
        """Log error with context"""
        self.log_with_context(logging.ERROR, message, **context)

    def critical(self, message: str, **context: Any) -> None:
        """Log critical with context"""
        self.log_with_context(logging.CRITICAL, message, **context)

    def file_operation(
        self, operation: str, file_path: str, success: bool = True, **context: Any
    ) -> None:
        """Log file operations with standardized context

        Args:
            operation: Operation type (read, write, convert, etc.)
            file_path: Path to file being operated on
            success: Whether operation succeeded
            **context: Additional context
        """
        level = logging.INFO if success else logging.ERROR
        self.log_with_context(
            level,
            f"File {operation}",
            file_path=file_path,
            operation=operation,
            success=success,
            **context,
        )

    def performance(
        self, operation: str, duration_seconds: float, **context: Any
    ) -> None:
        """Log performance metrics

        Args:
            operation: Operation name
            duration_seconds: Duration in seconds
            **context: Additional metrics
        """
        self.log_with_context(
            logging.INFO,
            f"Performance: {operation}",
            operation=operation,
            duration_seconds=duration_seconds,
            duration_ms=duration_seconds * 1000,
            **context,
        )

    def state_change(
        self,
        what_changed: str,
        old_value: Any = None,
        new_value: Any = None,
        **context: Any,
    ) -> None:
        """Log state changes for debugging

        Args:
            what_changed: Description of what changed
            old_value: Previous value
            new_value: New value
            **context: Additional context
        """
        self.log_with_context(
            logging.DEBUG,
            f"State change: {what_changed}",
            what_changed=what_changed,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(new_value) if new_value is not None else None,
            **context,
        )

    def error_with_suggestion(
        self,
        message: str,
        suggestion: str,
        error_type: Optional[str] = None,
        **context: Any,
    ) -> None:
        """Log error with debugging suggestion

        Args:
            message: Error message
            suggestion: Debugging suggestion
            error_type: Type of error
            **context: Additional context
        """
        self.log_with_context(
            logging.ERROR,
            message,
            suggestion=suggestion,
            error_type=error_type,
            claude_hint="Error with debugging suggestion",
            **context,
        )


class LogPerformanceOptimizer:
    """Optimize logging performance for high-frequency operations"""

    def __init__(self, logger: StructuredLogger):
        self.logger = logger
        self.message_counts: dict[str, int] = {}
        self.last_reset = time.time()
        self.reset_interval = 300  # 5 minutes

    def should_log(
        self, level: int, message_key: str, operation: Optional[str] = None
    ) -> bool:
        """Determine if we should log based on frequency and level"""
        # Reset counts periodically
        current_time = time.time()
        if current_time - self.last_reset > self.reset_interval:
            self.message_counts.clear()
            self.last_reset = current_time

        # Count this message
        self.message_counts[message_key] = self.message_counts.get(message_key, 0) + 1

        # Rate limiting based on level
        if level >= logging.ERROR:
            return True  # Always log errors
        elif level >= logging.WARNING:
            return self.message_counts[message_key] <= 50  # Limit warnings
        elif level >= logging.INFO:
            return self.message_counts[message_key] <= 20  # Limit info
        else:
            return self.message_counts[message_key] <= 5  # Heavily limit debug

    def record_log_event(self, level: int, message_key: str, duration: float) -> None:
        """Record logging performance metrics"""
        # Simple performance tracking - could be expanded
        pass

    def get_performance_report(self) -> dict[str, Any]:
        """Get performance report"""
        return {
            "message_counts": dict(self.message_counts),
            "total_messages": sum(self.message_counts.values()),
            "last_reset": self.last_reset,
        }


class LogSizeController:
    """Control log size and optimize for Claude Code parsing"""

    def __init__(self, logger: StructuredLogger):
        self.logger = logger
        self.max_context_size = 1000  # characters
        self.max_message_size = 500  # characters

    def optimize_for_claude_code(self, context: dict[str, Any]) -> dict[str, Any]:
        """Optimize context for Claude Code parsing"""
        optimized = {}
        for key, value in context.items():
            # Convert to string and limit size
            str_value = str(value)
            if len(str_value) > 100:
                str_value = str_value[:97] + "..."
            optimized[key] = str_value
        return optimized

    def should_include_context(self, context: dict[str, Any]) -> dict[str, Any]:
        """Determine if context should be included based on size"""
        context_str = str(context)
        if len(context_str) > self.max_context_size:
            # Reduce context size
            reduced_context = {}
            for key, value in list(context.items())[:5]:  # Keep only first 5 items
                reduced_context[key] = value
            reduced_context["__truncated__"] = True
            return reduced_context
        return context

    def format_message_for_size(self, message: str) -> str:
        """Format message to fit size constraints"""
        if len(message) > self.max_message_size:
            return message[: self.max_message_size - 3] + "..."
        return message

    def estimate_log_size(
        self, message: str, context: Optional[dict[str, Any]] = None
    ) -> int:
        """Estimate log entry size"""
        size = len(message)
        if context:
            size += len(str(context))
        return size

    def should_skip_due_to_size(self, estimated_size: int, priority: str) -> bool:
        """Determine if log should be skipped due to size"""
        if priority == "high":
            return False
        elif priority == "normal":
            return estimated_size > 2000
        else:  # low priority
            return estimated_size > 1000

    def get_size_statistics(self) -> dict[str, Any]:
        """Get size control statistics"""
        return {
            "max_context_size": self.max_context_size,
            "max_message_size": self.max_message_size,
        }


class ClaudeCodeIntegrationLogger:
    """Complete Claude Code integration logger

    Combines all logging features into a single, optimized logger
    specifically designed for Claude Code interaction.
    """

    def __init__(self, name: str):
        self.name = name
        from .logging_handlers import get_logger

        base_logger = get_logger(name)
        self.structured_logger = StructuredLogger(base_logger)
        self.error_analyzer = ErrorAnalyzer(self.structured_logger)
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
        analysis = self.error_analyzer.analyze_error(error, context, operation)
        self.structured_logger.error_with_suggestion(
            message,
            "See analysis for debugging suggestions",
            error_analysis=analysis,
            operation=operation,
        )

    def get_comprehensive_report(self) -> dict[str, Any]:
        """Get comprehensive report combining all tracking data"""
        return {
            "module": self.name,
            "timestamp": datetime.now().isoformat(),
            "performance": self.performance_optimizer.get_performance_report(),
            "size_stats": self.size_controller.get_size_statistics(),
            "claude_hint": "Complete integration report for debugging and optimization",
        }


# Global cache for structured loggers
_structured_loggers: dict[str, StructuredLogger] = {}


def get_structured_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance

    Args:
        name: Module name (typically __name__)

    Returns:
        StructuredLogger instance
    """
    if name not in _structured_loggers:
        from .logging_handlers import get_logger

        base_logger = get_logger(name)
        _structured_loggers[name] = StructuredLogger(base_logger)
    return _structured_loggers[name]


def get_claude_code_logger(name: str) -> ClaudeCodeIntegrationLogger:
    """Get complete Claude Code integration logger

    Args:
        name: Module name (typically __name__)

    Returns:
        ClaudeCodeIntegrationLogger with all features
    """
    return ClaudeCodeIntegrationLogger(name)
