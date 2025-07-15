"""Structured logging for Kumihan-Formatter

Single Responsibility Principle適用: 構造化ログ機能の分離
Issue #476 Phase3対応 - structured_logger.py分割
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .security_patterns import SecurityPatternMatcher


class StructuredLogger:
    """Enhanced logger with structured logging capabilities

    Provides methods for logging with structured context data,
    making it easier for Claude Code to parse and analyze logs.
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def _sanitize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive information from context data

        Args:
            context: Original context dictionary

        Returns:
            Sanitized context dictionary
        """
        sanitized = {}
        for key, value in context.items():
            # Check if key is sensitive
            if SecurityPatternMatcher.is_sensitive_key(key):
                sanitized[key] = "[FILTERED]"
            else:
                # Check if value contains sensitive patterns
                if isinstance(value, str):
                    sanitized_value = SecurityPatternMatcher.sanitize_value(value)
                    sanitized[key] = sanitized_value
                else:
                    sanitized[key] = value
        return sanitized

    def log_with_context(
        self,
        level: int,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Log message with structured context

        Args:
            level: Log level
            message: Log message
            context: Optional context data
            **kwargs: Additional logging parameters
        """
        if context:
            sanitized_context = self._sanitize_context(context)
            # Add context to extra for structured logging
            kwargs["extra"] = kwargs.get("extra", {})
            kwargs["extra"]["context"] = sanitized_context

        self.logger.log(level, message, **kwargs)

    def debug_with_context(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Debug log with context"""
        self.log_with_context(logging.DEBUG, message, context, **kwargs)

    def info_with_context(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Info log with context"""
        self.log_with_context(logging.INFO, message, context, **kwargs)

    def warning_with_context(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Warning log with context"""
        self.log_with_context(logging.WARNING, message, context, **kwargs)

    def error_with_context(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Error log with context"""
        self.log_with_context(logging.ERROR, message, context, **kwargs)

    def critical_with_context(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Critical log with context"""
        self.log_with_context(logging.CRITICAL, message, context, **kwargs)

    def log_performance(
        self,
        operation: str,
        duration: float,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Log performance metrics

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

        self.info_with_context(
            f"Performance: {operation} completed in {duration:.3f}s",
            perf_context,
            **kwargs,
        )

    def log_error_with_traceback(
        self,
        message: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Log error with traceback

        Args:
            message: Error message
            error: Exception object
            context: Optional additional context
            **kwargs: Additional logging parameters
        """
        error_context = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "error_log": True,
        }

        if context:
            error_context.update(context)

        self.error_with_context(message, error_context, exc_info=True, **kwargs)


# Global instance cache
_structured_loggers: Dict[str, StructuredLogger] = {}


def get_structured_logger(name: str) -> StructuredLogger:
    """Get cached structured logger instance

    Args:
        name: Logger name

    Returns:
        StructuredLogger instance
    """
    if name not in _structured_loggers:
        from .logging_handlers import get_logger

        base_logger = get_logger(name)
        _structured_loggers[name] = StructuredLogger(base_logger)
    return _structured_loggers[name]
