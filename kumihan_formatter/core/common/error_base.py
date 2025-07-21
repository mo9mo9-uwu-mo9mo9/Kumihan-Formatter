"""Base error classes extracted from error_framework.py

This module contains the base KumihanError class and specific error types
to maintain the 300-line limit for error_framework.py.
"""

import traceback
from typing import Any

from .error_types import ErrorCategory, ErrorContext, ErrorSeverity


class KumihanError(Exception):
    """Base exception class for all Kumihan-Formatter errors"""

    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        context: ErrorContext | None = None,
        suggestions: list[str] | None = None,
        original_error: Exception | None = None,
    ):
        """Initialize Kumihan error

        Args:
            message: Error message
            severity: Error severity level
            category: Error category
            context: Error context information
            suggestions: User-friendly suggestions
            original_error: Original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.severity = severity
        self.category = category
        self.context = context or ErrorContext()
        self.suggestions = suggestions or []
        self.original_error = original_error
        self.traceback_info = traceback.format_exc() if original_error else None

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary representation"""
        return {
            "message": self.message,
            "severity": self.severity.value,
            "category": self.category.value,
            "context": self.context.to_dict(),
            "suggestions": self.suggestions,
            "original_error": str(self.original_error) if self.original_error else None,
            "traceback": self.traceback_info,
        }

    def __str__(self) -> str:
        """String representation of error"""
        parts = [f"[{self.severity.value.upper()}] {self.message}"]

        if self.context and str(self.context) != "No context":
            parts.append(f"Context: {self.context}")

        if self.suggestions:
            parts.append(f"Suggestions: {'; '.join(self.suggestions)}")

        return "\n".join(parts)

    def get_user_message(self) -> str:
        """Get user-friendly error message"""
        user_msg = self.message

        if self.suggestions:
            user_msg += f"\n\nSuggestions:\n"
            for i, suggestion in enumerate(self.suggestions, 1):
                user_msg += f"{i}. {suggestion}\n"

        return user_msg

    def is_critical(self) -> bool:
        """Check if error is critical"""
        return self.severity == ErrorSeverity.CRITICAL

    def is_recoverable(self) -> bool:
        """Check if error is recoverable"""
        return self.severity in [ErrorSeverity.WARNING, ErrorSeverity.INFO]

    def add_suggestion(self, suggestion: str) -> None:
        """Add a suggestion to the error"""
        self.suggestions.append(suggestion)

    def with_context(self, **context_updates: Any) -> "KumihanError":
        """Create a new error with updated context"""
        new_context = ErrorContext(
            file_path=context_updates.get("file_path", self.context.file_path),
            line_number=context_updates.get("line_number", self.context.line_number),
            column_number=context_updates.get(
                "column_number", self.context.column_number
            ),
            operation=context_updates.get("operation", self.context.operation),
            user_input=context_updates.get("user_input", self.context.user_input),
            system_info=context_updates.get("system_info", self.context.system_info),
        )

        return KumihanError(
            message=self.message,
            severity=self.severity,
            category=self.category,
            context=new_context,
            suggestions=self.suggestions.copy(),
            original_error=self.original_error,
        )


# Specific error types
class FileSystemError(KumihanError):
    """File system operation errors"""

    def __init__(
        self, message: str, file_path: str | None = None, **kwargs: Any
    ) -> None:
        context = ErrorContext(file_path=file_path, operation="file_system")
        super().__init__(
            message, category=ErrorCategory.FILE_SYSTEM, context=context, **kwargs
        )


class SyntaxError(KumihanError):
    """Syntax parsing errors"""

    def __init__(
        self, message: str, line_number: int | None = None, **kwargs: Any
    ) -> None:
        context = ErrorContext(line_number=line_number, operation="syntax_parsing")
        super().__init__(
            message, category=ErrorCategory.SYNTAX, context=context, **kwargs
        )


class ValidationError(KumihanError):
    """Data validation errors"""

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, category=ErrorCategory.VALIDATION, **kwargs)


class ConfigurationError(KumihanError):
    """Configuration errors"""

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, category=ErrorCategory.CONFIGURATION, **kwargs)
