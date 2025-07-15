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
        self.security_matcher = SecurityPatternMatcher()

    def sanitize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize context data to remove sensitive information

        Args:
            context: Context dictionary to sanitize

        Returns:
            Sanitized context dictionary
        """
        return self.security_matcher.sanitize_dict(context)

    def log_with_context(
        self,
        level: int,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Log message with optional context data

        Args:
            level: Log level (logging.DEBUG, logging.INFO, etc.)
            message: Log message
            context: Optional context data
            **kwargs: Additional logging parameters
        """
        if context:
            sanitized_context = self.sanitize_context(context)
            extra = kwargs.get("extra", {})
            extra.update(sanitized_context)
            kwargs["extra"] = extra

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

    def log_error_with_traceback(
        self,
        message: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Log error with traceback information

        Args:
            message: Error message
            error: Exception object
            context: Optional additional context
            **kwargs: Additional logging parameters
        """
        error_context = {
            "error_type": type(error).__name__,
            "error_message": str(error),
        }

        if context:
            error_context.update(context)

        self.log_with_context(
            logging.ERROR,
            message,
            error_context,
            exc_info=True,
            **kwargs,
        )


# Global instance cache
_structured_loggers: Dict[str, StructuredLogger] = {}


def get_structured_logger(logger: logging.Logger) -> StructuredLogger:
    """Get cached structured logger instance

    Args:
        logger: Base logger instance

    Returns:
        StructuredLogger instance
    """
    logger_name = logger.name
    if logger_name not in _structured_loggers:
        _structured_loggers[logger_name] = StructuredLogger(logger)
    return _structured_loggers[logger_name]
