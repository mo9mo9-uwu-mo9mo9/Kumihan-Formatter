"""Error types and enums extracted from error_framework.py

This module contains error severity levels, categories, and context
to maintain the 300-line limit for error_framework.py.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


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

    file_path: str | None = None
    line_number: int | None = None
    column_number: int | None = None
    operation: str | None = None
    user_input: str | None = None
    system_info: dict[str, Any] | None = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary"""
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column_number": self.column_number,
            "operation": self.operation,
            "user_input": self.user_input,
            "system_info": self.system_info,
            "timestamp": self.timestamp.isoformat(),
        }

    def __str__(self) -> str:
        """String representation of context"""
        parts = []
        if self.file_path:
            parts.append(f"File: {self.file_path}")
        if self.line_number:
            parts.append(f"Line: {self.line_number}")
        if self.column_number:
            parts.append(f"Column: {self.column_number}")
        if self.operation:
            parts.append(f"Operation: {self.operation}")

        return " | ".join(parts) if parts else "No context"
