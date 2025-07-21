"""
ログ エラー分析器

エラー分析・カテゴリ化・デバッグ支援
Issue #492 Phase 5A - log_analysis.py分割
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

from .performance_logging import call_chain_tracker, memory_usage_tracker


class ErrorAnalyzer:
    """Claude Code specific error analysis support

    Provides enhanced error logging with analysis suggestions,
    error categorization, and debugging hints specifically
    designed for Claude Code integration.
    """

    # Common error categories and their solutions
    ERROR_CATEGORIES = {
        "encoding": {
            "patterns": ["encoding", "decode", "utf-8", "unicode", "ascii"],
            "suggestions": [
                "Check file encoding with 'file -I filename'",
                "Try specifying encoding explicitly: encoding='utf-8'",
                "Consider using chardet library for encoding detection",
            ],
        },
        "file_access": {
            "patterns": ["permission", "access", "not found", "no such file"],
            "suggestions": [
                "Check file permissions with 'ls -la'",
                "Verify file path exists",
                "Ensure process has read/write permissions",
            ],
        },
        "parsing": {
            "patterns": ["parse", "syntax", "invalid", "unexpected"],
            "suggestions": [
                "Check input file format",
                "Validate syntax of input content",
                "Review notation format specification",
            ],
        },
        "memory": {
            "patterns": ["memory", "out of memory", "allocation"],
            "suggestions": [
                "Process file in chunks",
                "Check available system memory",
                "Consider input file size limitations",
            ],
        },
        "dependency": {
            "patterns": ["import", "module", "not found", "missing"],
            "suggestions": [
                "Check if required package is installed",
                "Verify PYTHONPATH includes necessary directories",
                "Install missing dependencies with pip",
            ],
        },
    }

    def __init__(self, logger: Any) -> None:
        """Initialize with a StructuredLogger instance"""
        self.logger = logger

    def analyze_error(
        self,
        error: Exception,
        context: Optional[dict[str, Any]] = None,
        operation: Optional[str] = None,
    ) -> dict[str, Any]:
        """Analyze error and provide structured debugging information

        Args:
            error: Exception that occurred
            context: Additional context about the operation
            operation: Name of operation that failed

        Returns:
            Dictionary with error analysis and suggestions
        """
        error_message = str(error).lower()
        error_type = type(error).__name__

        # Categorize error
        category = self._categorize_error(error_message)

        # Get stack trace information
        stack_info = call_chain_tracker(max_depth=15)

        # Get memory usage at error time
        memory_info = memory_usage_tracker()

        # Add suggestions based on category
        suggestions: list[str]
        if category != "unknown":
            suggestions = self.ERROR_CATEGORIES[category]["suggestions"]
        else:
            suggestions = self._generate_generic_suggestions(error_type, error_message)

        analysis: dict[str, Any] = {
            "error_type": error_type,
            "error_message": str(error),
            "category": category,
            "operation": operation,
            "stack_info": stack_info,
            "memory_info": memory_info,
            "timestamp": datetime.now().isoformat(),
            "suggestions": suggestions,
        }

        # Add context if provided
        if context:
            analysis["context"] = context

        return analysis

    def log_error_with_analysis(
        self,
        error: Exception,
        message: str,
        context: Optional[dict[str, Any]] = None,
        operation: Optional[str] = None,
    ) -> None:
        """Log error with comprehensive analysis

        Args:
            error: Exception that occurred
            message: Human-readable error description
            context: Additional context
            operation: Operation that failed
        """
        analysis = self.analyze_error(error, context, operation)

        self.logger.log_with_context(
            logging.ERROR,
            message,
            error_analysis=analysis,
            claude_hint="Use error_analysis.suggestions for debugging steps",
        )

    def log_warning_with_suggestion(
        self, message: str, suggestion: str, category: str = "general", **context: Any
    ) -> None:
        """Log warning with specific suggestion

        Args:
            message: Warning message
            suggestion: Specific suggestion for resolution
            category: Warning category
            **context: Additional context
        """
        self.logger.log_with_context(
            logging.WARNING,
            message,
            suggestion=suggestion,
            category=category,
            claude_hint=f"Category: {category} - Apply suggestion to resolve",
            **context,
        )

    def _categorize_error(self, error_message: str) -> str:
        """Categorize error based on message content

        Args:
            error_message: Error message to categorize

        Returns:
            Error category
        """
        for category, info in self.ERROR_CATEGORIES.items():
            if any(pattern in error_message for pattern in info["patterns"]):
                return category
        return "unknown"

    def _generate_generic_suggestions(
        self, error_type: str, error_message: str
    ) -> list[str]:
        """Generate generic suggestions for unknown error types

        Args:
            error_type: Type of error
            error_message: Error message content

        Returns:
            List of generic suggestions
        """
        suggestions = [
            f"Check the specific {error_type} details",
            "Review input parameters and validate data",
            "Enable debug logging for more details",
        ]

        # Add type-specific suggestions
        if "Value" in error_type:
            suggestions.append("Validate input values and types")
        elif "Type" in error_type:
            suggestions.append("Check argument types match expected types")
        elif "Index" in error_type or "Key" in error_type:
            suggestions.append("Verify data structure bounds and keys")

        return suggestions
