"""Unified error handling framework for Kumihan-Formatter

This module provides a consistent error handling approach across all components.
All error classes in the system should inherit from KumihanError for consistency.
"""

import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class ErrorSeverity(Enum):
    """Standardized error severity levels"""

    CRITICAL = "critical"  # System-breaking errors
    ERROR = "error"  # Component failures
    WARNING = "warning"  # Potentially problematic situations
    INFO = "info"  # Informational messages


class ErrorCategory(Enum):
    """Error categorization for better organization"""

    FILE_SYSTEM = "file_system"  # File operations
    SYNTAX = "syntax"  # Markup syntax issues
    VALIDATION = "validation"  # Data validation
    RENDERING = "rendering"  # HTML generation
    CONFIGURATION = "configuration"  # Config issues
    PERFORMANCE = "performance"  # Performance problems
    NETWORK = "network"  # Network operations
    PERMISSION = "permission"  # Access control
    ENCODING = "encoding"  # Text encoding
    SYSTEM = "system"  # OS/environment
    UNKNOWN = "unknown"  # Unclassified


@dataclass
class ErrorContext:
    """Context information for errors"""

    file_path: Optional[str] = None
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    operation: Optional[str] = None
    user_input: Optional[str] = None
    system_info: Optional[Dict[str, Any]] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for serialization"""
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column_number": self.column_number,
            "operation": self.operation,
            "user_input": self.user_input,
            "system_info": self.system_info,
            "timestamp": self.timestamp.isoformat(),
        }


class KumihanError(Exception):
    """Base exception class for all Kumihan-Formatter errors

    This class provides:
    - Consistent error structure across the application
    - Rich context information for debugging
    - Standardized severity and categorization
    - User-friendly message formatting
    """

    def __init__(
        self,
        message: str,
        *,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        error_code: Optional[str] = None,
        context: Optional[ErrorContext] = None,
        user_message: Optional[str] = None,
        suggestions: Optional[List[str]] = None,
        technical_details: Optional[str] = None,
        cause: Optional[Exception] = None,
    ):
        """Initialize Kumihan error

        Args:
            message: Technical error message
            severity: Error severity level
            category: Error category for organization
            error_code: Unique error identifier (e.g., 'E001')
            context: Additional context information
            user_message: User-friendly error message
            suggestions: List of suggested solutions
            technical_details: Technical debugging information
            cause: Original exception that caused this error
        """
        super().__init__(message)

        self.message = message
        self.severity = severity
        self.category = category
        self.error_code = error_code or self._generate_error_code()
        self.context = context or ErrorContext()
        self.user_message = user_message or message
        self.suggestions = suggestions or []
        self.technical_details = technical_details
        self.cause = cause

        # Store the original traceback if available
        if cause:
            self.cause_traceback = "".join(traceback.format_exception(type(cause), cause, cause.__traceback__))
        else:
            self.cause_traceback = None

    def _generate_error_code(self) -> str:
        """Generate a simple error code based on category"""
        category_codes = {
            ErrorCategory.FILE_SYSTEM: "FS",
            ErrorCategory.SYNTAX: "SX",
            ErrorCategory.VALIDATION: "VL",
            ErrorCategory.RENDERING: "RN",
            ErrorCategory.CONFIGURATION: "CF",
            ErrorCategory.PERFORMANCE: "PF",
            ErrorCategory.NETWORK: "NT",
            ErrorCategory.PERMISSION: "PM",
            ErrorCategory.ENCODING: "EN",
            ErrorCategory.SYSTEM: "SY",
            ErrorCategory.UNKNOWN: "UK",
        }

        prefix = category_codes.get(self.category, "UK")
        # Use hash of message for consistency
        suffix = str(abs(hash(self.message)) % 1000).zfill(3)
        return f"{prefix}{suffix}"

    def format_for_user(self, include_suggestions: bool = True) -> str:
        """Format error message for end users"""
        parts = [f"[{self.error_code}] {self.user_message}"]

        if include_suggestions and self.suggestions:
            parts.append("\n解決方法:")
            for i, suggestion in enumerate(self.suggestions, 1):
                parts.append(f"  {i}. {suggestion}")

        return "\n".join(parts)

    def format_for_developer(self, include_traceback: bool = False) -> str:
        """Format error message for developers"""
        parts = [
            f"KumihanError [{self.error_code}]",
            f"Severity: {self.severity.value}",
            f"Category: {self.category.value}",
            f"Message: {self.message}",
        ]

        if self.context.file_path:
            location = f"File: {self.context.file_path}"
            if self.context.line_number:
                location += f", Line: {self.context.line_number}"
                if self.context.column_number:
                    location += f", Column: {self.context.column_number}"
            parts.append(location)

        if self.technical_details:
            parts.append(f"Technical Details: {self.technical_details}")

        if include_traceback and self.cause_traceback:
            parts.append(f"Caused by:\n{self.cause_traceback}")

        return "\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for serialization"""
        return {
            "error_code": self.error_code,
            "severity": self.severity.value,
            "category": self.category.value,
            "message": self.message,
            "user_message": self.user_message,
            "suggestions": self.suggestions,
            "technical_details": self.technical_details,
            "context": self.context.to_dict(),
            "cause": str(self.cause) if self.cause else None,
        }


class BaseErrorHandler(ABC):
    """Abstract base class for error handlers

    Provides a consistent interface for handling different types of errors
    across the application. All error handlers should inherit from this class.
    """

    def __init__(self, name: str):
        """Initialize error handler

        Args:
            name: Identifier for this error handler
        """
        self.name = name
        self.error_count = 0
        self.errors: List[KumihanError] = []

    @abstractmethod
    def handle_error(self, error: Union[KumihanError, Exception]) -> bool:
        """Handle an error

        Args:
            error: Error to handle

        Returns:
            bool: True if error was handled successfully, False otherwise
        """
        pass

    def wrap_exception(
        self,
        exception: Exception,
        *,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        user_message: Optional[str] = None,
        context: Optional[ErrorContext] = None,
    ) -> KumihanError:
        """Wrap a standard exception in a KumihanError

        Args:
            exception: Original exception
            severity: Error severity
            category: Error category
            user_message: User-friendly message
            context: Error context

        Returns:
            KumihanError: Wrapped error
        """
        if isinstance(exception, KumihanError):
            return exception

        return KumihanError(
            message=str(exception),
            severity=severity,
            category=category,
            user_message=user_message or str(exception),
            context=context,
            cause=exception,
        )

    def record_error(self, error: KumihanError) -> None:
        """Record an error for statistics"""
        self.errors.append(error)
        self.error_count += 1

    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of handled errors"""
        if not self.errors:
            return {"total": 0, "by_severity": {}, "by_category": {}}

        by_severity = {}
        by_category = {}

        for error in self.errors:
            # Count by severity
            severity = error.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1

            # Count by category
            category = error.category.value
            by_category[category] = by_category.get(category, 0) + 1

        return {"total": len(self.errors), "by_severity": by_severity, "by_category": by_category}

    def clear_errors(self) -> None:
        """Clear error history"""
        self.errors.clear()
        self.error_count = 0


# Specific error classes for common scenarios


class FileSystemError(KumihanError):
    """File system related errors"""

    def __init__(self, message: str, file_path: str, **kwargs):
        context = ErrorContext(file_path=file_path)
        super().__init__(message, category=ErrorCategory.FILE_SYSTEM, context=context, **kwargs)


class SyntaxError(KumihanError):
    """Syntax related errors"""

    def __init__(self, message: str, line_number: int, **kwargs):
        context = ErrorContext(line_number=line_number)
        super().__init__(message, category=ErrorCategory.SYNTAX, context=context, **kwargs)


class ValidationError(KumihanError):
    """Validation related errors"""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.VALIDATION, **kwargs)


class ConfigurationError(KumihanError):
    """Configuration related errors"""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.CONFIGURATION, **kwargs)
