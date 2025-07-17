"""Base structured logger functionality

Single Responsibility Principle適用: 基本的な構造化ログ機能の分離
Issue #476 Phase5対応 - structured_logger.py分割
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from functools import lru_cache
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
    }

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def _is_sensitive_key(self, key: str) -> bool:
        """Check if a key contains sensitive information (optimized with pre-lowercased set)"""
        return key.lower() in self.SENSITIVE_KEYS

    def _sanitize_context(self, context: dict[str, Any]) -> dict[str, Any]:
        """Remove or mask sensitive information from context"""
        sanitized: dict[str, Any] = {}
        for key, value in context.items():
            if self._is_sensitive_key(key):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_context(value)
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                # リスト内の辞書も再帰的にサニタイズ
                sanitized_list: list[Any] = [
                    self._sanitize_context(item) if isinstance(item, dict) else item
                    for item in value
                ]
                sanitized[key] = sanitized_list
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
        """Log with structured context

        Args:
            level: Log level
            message: Log message
            context: Structured context data
            **kwargs: Additional logging parameters
        """
        if context:
            # センシティブ情報をフィルタリング
            safe_context = self._sanitize_context(context)
            # JSON形式でコンテキストを追加
            extra = kwargs.get("extra", {})
            extra["context"] = json.dumps(safe_context, ensure_ascii=False, default=str)
            kwargs["extra"] = extra

        self.logger.log(level, message, **kwargs)

    def info(self, message: str, **context: Any) -> None:
        """Log info with context"""
        self.log_with_context(logging.INFO, message, context)

    def debug(self, message: str, **context: Any) -> None:
        """Log debug with context"""
        self.log_with_context(logging.DEBUG, message, context)

    def warning(self, message: str, **context: Any) -> None:
        """Log warning with context"""
        self.log_with_context(logging.WARNING, message, context)

    def error(self, message: str, **context: Any) -> None:
        """Log error with context"""
        self.log_with_context(logging.ERROR, message, context)

    def critical(self, message: str, **context: Any) -> None:
        """Log critical with context"""
        self.log_with_context(logging.CRITICAL, message, context)

    def file_operation(
        self,
        operation: str,
        file_path: str,
        success: bool = True,
        error: Optional[str] = None,
        **additional_context: Any,
    ) -> None:
        """Log file operation with structured context"""
        context = {
            "operation": operation,
            "file_path": file_path,
            "success": success,
            "file_op": True,  # フラグでフィルタリング可能に
        }
        if error:
            context["error"] = error
        context.update(additional_context)

        level = logging.INFO if success else logging.ERROR
        message = f"File operation: {operation} on {file_path}"
        if not success:
            message += f" failed: {error}"

        self.log_with_context(level, message, context)

    def performance(
        self,
        operation: str,
        duration_ms: float,
        metadata: Optional[dict[str, Any]] = None,
        **additional_context: Any,
    ) -> None:
        """Log performance metrics"""
        context = {
            "operation": operation,
            "duration_ms": duration_ms,
            "performance": True,  # パフォーマンスログのフラグ
        }
        if metadata:
            context["metadata"] = metadata
        context.update(additional_context)

        self.info(
            f"Performance: {operation} completed in {duration_ms:.2f}ms",
            **context,
        )

    def state_change(
        self,
        component: str,
        old_state: Any,
        new_state: Any,
        reason: Optional[str] = None,
        **additional_context: Any,
    ) -> None:
        """Log state changes in the application"""
        context = {
            "component": component,
            "old_state": str(old_state),
            "new_state": str(new_state),
            "state_change": True,
        }
        if reason:
            context["reason"] = reason
        context.update(additional_context)

        self.info(
            f"State change in {component}: {old_state} -> {new_state}",
            **context,
        )

    def error_with_suggestion(
        self,
        message: str,
        error: Exception,
        suggestions: list[str],
        **additional_context: Any,
    ) -> None:
        """Log error with recovery suggestions"""
        context = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "suggestions": suggestions,
            "has_suggestions": True,
        }
        context.update(additional_context)

        suggestion_text = "\n  - ".join([""] + suggestions)
        full_message = f"{message}\nSuggestions:{suggestion_text}"

        self.error(full_message, **context)

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.now().isoformat()


@lru_cache(maxsize=128)
def get_structured_logger(name: str) -> StructuredLogger:
    """Get a cached structured logger instance

    Args:
        name: Logger name

    Returns:
        StructuredLogger instance
    """
    # Import logging directly to avoid circular imports
    import logging

    base_logger = logging.getLogger(name)
    return StructuredLogger(base_logger)
