"""Syntax error types and severity definitions

This module defines error types, severity levels, and data structures
for syntax errors in Kumihan markup.
"""

from dataclasses import dataclass
from enum import Enum


class ErrorSeverity(Enum):
    """Error severity levels"""

    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class SyntaxError:
    """Represents a syntax error in Kumihan markup"""

    line_number: int
    column: int
    severity: ErrorSeverity
    error_type: str
    message: str
    context: str
    suggestion: str = ""


# Error type constants for consistency
class ErrorTypes:
    """Constants for error types"""

    ENCODING = "encoding"
    FILE_NOT_FOUND = "file-not-found"
    INVALID_KEYWORD = "invalid-keyword"
    UNKNOWN_KEYWORD = "unknown-keyword"
    UNMATCHED_BLOCK_END = "unmatched-block-end"
    UNCLOSED_BLOCK = "unclosed-block"
    MULTILINE_SYNTAX = "multiline-syntax"
    EMPTY_KEYWORD = "empty-keyword"
    INVALID_COLOR_USAGE = "invalid-color-usage"
    INVALID_COLOR_FORMAT = "invalid-color-format"
    INVALID_ALT_USAGE = "invalid-alt-usage"
    DUPLICATE_KEYWORD = "duplicate-keyword"
    MULTIPLE_HEADINGS = "multiple-headings"
    INLINE_MARKER = "inline-marker"
    INVALID_BLOCK_MARKER = "invalid-block-marker"
