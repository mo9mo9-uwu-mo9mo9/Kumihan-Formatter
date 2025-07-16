"""Structured logging capabilities for Kumihan-Formatter

This module provides enhanced logging with structured context data,
making it easier for Claude Code to parse and analyze logs.
"""

from __future__ import annotations

import logging
from typing import Any, Optional


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
            old_value=old_value,
            new_value=new_value,
            **context,
        )

    def error_with_suggestion(
        self,
        message: str,
        suggestion: str,
        error_type: Optional[str] = None,
        **context: Any,
    ) -> None:
        """Log error with suggested solution

        Args:
            message: Error message
            suggestion: Suggested fix or action
            error_type: Type of error
            **context: Additional context
        """
        self.log_with_context(
            logging.ERROR,
            message,
            suggestion=suggestion,
            error_type=error_type,
            **context,
        )


def get_structured_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance for a module

    Args:
        name: Module name (typically __name__)

    Returns:
        StructuredLogger instance with enhanced logging capabilities

    Example:
        >>> logger = get_structured_logger(__name__)
        >>> logger.info("Processing file", file_path="test.txt", size_bytes=1024)
        >>> logger.error_with_suggestion(
        ...     "File not found",
        ...     "Check file path and permissions",
        ...     file_path="missing.txt"
        ... )
    """
    # Import here to avoid circular import
    from .logger import get_logger

    standard_logger = get_logger(name)
    return StructuredLogger(standard_logger)
