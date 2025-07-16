"""Structured logging and analysis for Kumihan-Formatter

This module provides advanced structured logging capabilities with error analysis,
dependency tracking, and execution flow monitoring for Claude Code integration.
"""

from __future__ import annotations

import json
import logging
import time
import traceback
from datetime import datetime
from functools import lru_cache
from typing import Any, Optional

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Import get_logger at runtime to avoid circular imports
from .performance_logger import call_chain_tracker, memory_usage_tracker


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

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    @lru_cache(maxsize=1000)
    def _is_sensitive_key(self, key: str) -> bool:
        """Check if a key is sensitive using LRU cache for efficiency"""
        return key.lower() in self.SENSITIVE_KEYS

    def _sanitize_context(self, context: dict[str, Any]) -> dict[str, Any]:
        """Remove sensitive information from context data

        Args:
            context: Original context dictionary

        Returns:
            Sanitized context dictionary with sensitive data filtered out
        """
        sanitized = {}
        for key, value in context.items():
            # Use LRU cache for efficient sensitive key detection
            if self._is_sensitive_key(key):
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
    # Import get_logger at runtime to avoid circular imports
    from .logger import get_logger

    standard_logger = get_logger(name)
    return StructuredLogger(standard_logger)


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

    def __init__(self, logger: StructuredLogger):
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

    def _categorize_error(self, error_message: str) -> str:
        """Categorize error based on message content"""
        for category, info in self.ERROR_CATEGORIES.items():
            if any(pattern in error_message for pattern in info["patterns"]):
                return category
        return "unknown"

    def _generate_generic_suggestions(
        self, error_type: str, error_message: str
    ) -> list[str]:
        """Generate generic suggestions for unknown error types"""
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


class DependencyTracker:
    """Track and visualize module dependencies for debugging

    Provides dependency mapping and load tracking to help
    Claude Code understand module relationships and identify
    dependency-related issues.
    """

    def __init__(self, logger: StructuredLogger):
        self.logger = logger
        self.dependencies: dict[str, set[str]] = {}
        self.load_times: dict[str, float] = {}
        self.load_order: list[str] = []

    def track_import(
        self,
        module_name: str,
        imported_from: Optional[str] = None,
        import_time: Optional[float] = None,
    ) -> None:
        """Track module import for dependency visualization

        Args:
            module_name: Name of imported module
            imported_from: Module that performed the import
            import_time: Time taken to import (seconds)
        """
        # Record dependency relationship
        if imported_from:
            if imported_from not in self.dependencies:
                self.dependencies[imported_from] = set()
            self.dependencies[imported_from].add(module_name)

        # Record import timing
        if import_time is not None:
            self.load_times[module_name] = import_time

        # Record load order
        if module_name not in self.load_order:
            self.load_order.append(module_name)

        # Log the import
        context = {
            "module": module_name,
            "imported_from": imported_from,
            "import_time_ms": round(import_time * 1000, 2) if import_time else None,
            "load_order_position": len(self.load_order),
        }

        self.logger.debug(
            f"Module imported: {module_name}",
            **context,
            claude_hint="Track dependencies for debugging import issues",
        )

    def get_dependency_map(self) -> dict[str, Any]:
        """Get complete dependency map for visualization

        Returns:
            Dictionary with dependency relationships and metrics
        """
        return {
            "dependencies": {k: list(v) for k, v in self.dependencies.items()},
            "load_times": self.load_times,
            "load_order": self.load_order,
            "total_modules": len(self.load_order),
            "slowest_imports": sorted(
                [(k, v) for k, v in self.load_times.items()],
                key=lambda x: x[1],
                reverse=True,
            )[:5],
        }

    def log_dependency_summary(self) -> None:
        """Log summary of all tracked dependencies"""
        dep_map = self.get_dependency_map()

        self.logger.info(
            "Dependency tracking summary",
            dependency_map=dep_map,
            claude_hint="Use dependency_map to understand module relationships",
        )


class ExecutionFlowTracker:
    """Track execution flow for debugging and optimization

    Records function call sequences, timing, and resource usage
    to help Claude Code understand application behavior.
    """

    def __init__(self, logger: StructuredLogger):
        self.logger = logger
        self.execution_stack: list[dict[str, Any]] = []
        self.flow_id = str(int(time.time() * 1000))  # Unique flow identifier

    def enter_function(
        self,
        function_name: str,
        module_name: str,
        args_info: Optional[dict[str, Any]] = None,
    ) -> str:
        """Record function entry in execution flow

        Args:
            function_name: Name of function being entered
            module_name: Module containing the function
            args_info: Information about function arguments

        Returns:
            Unique frame ID for this function call
        """
        frame_id = f"{self.flow_id}_{len(self.execution_stack)}"
        start_time = time.time()

        frame_info = {
            "frame_id": frame_id,
            "function_name": function_name,
            "module_name": module_name,
            "start_time": start_time,
            "args_info": args_info,
            "depth": len(self.execution_stack),
        }

        self.execution_stack.append(frame_info)

        # Log function entry
        self.logger.debug(
            f"Function entry: {function_name}",
            flow_id=self.flow_id,
            frame_id=frame_id,
            function=function_name,
            module=module_name,
            depth=len(self.execution_stack),
            args_info=args_info,
            claude_hint="Track execution flow for debugging call sequences",
        )

        return frame_id

    def exit_function(
        self,
        frame_id: str,
        success: bool = True,
        result_info: Optional[dict[str, Any]] = None,
        error_info: Optional[dict[str, Any]] = None,
    ) -> None:
        """Record function exit in execution flow

        Args:
            frame_id: Frame ID from enter_function
            success: Whether function completed successfully
            result_info: Information about function result
            error_info: Information about any error that occurred
        """
        if not self.execution_stack:
            return

        # Find and remove the frame
        frame = None
        for i, stack_frame in enumerate(reversed(self.execution_stack)):
            if stack_frame["frame_id"] == frame_id:
                frame = self.execution_stack.pop(-(i + 1))
                break

        if not frame:
            return

        end_time = time.time()
        duration = end_time - frame["start_time"]

        # Log function exit
        exit_context = {
            "flow_id": self.flow_id,
            "frame_id": frame_id,
            "function": frame["function_name"],
            "module": frame["module_name"],
            "duration_ms": round(duration * 1000, 2),
            "success": success,
            "depth": frame["depth"],
        }

        if result_info:
            exit_context["result_info"] = result_info

        if error_info:
            exit_context["error_info"] = error_info

        level = logging.DEBUG if success else logging.WARNING
        self.logger.log_with_context(
            level,
            f"Function exit: {frame['function_name']}",
            **exit_context,
            claude_hint="Analyze execution timing and call patterns",
        )

    def get_current_flow(self) -> dict[str, Any]:
        """Get current execution flow state

        Returns:
            Dictionary with current execution stack and flow info
        """
        return {
            "flow_id": self.flow_id,
            "current_stack": [
                {
                    "function": frame["function_name"],
                    "module": frame["module_name"],
                    "depth": frame["depth"],
                    "duration_so_far": round(
                        (time.time() - frame["start_time"]) * 1000, 2
                    ),
                }
                for frame in self.execution_stack
            ],
            "stack_depth": len(self.execution_stack),
            "total_execution_time": (
                round((time.time() - self.execution_stack[0]["start_time"]) * 1000, 2)
                if self.execution_stack
                else 0
            ),
        }


def get_error_analyzer(name: str) -> ErrorAnalyzer:
    """Get error analyzer instance for a module

    Args:
        name: Module name (typically __name__)

    Returns:
        ErrorAnalyzer instance with enhanced error analysis capabilities
    """
    structured_logger = get_structured_logger(name)
    return ErrorAnalyzer(structured_logger)


def get_dependency_tracker(name: str) -> DependencyTracker:
    """Get dependency tracker instance for a module

    Args:
        name: Module name (typically __name__)

    Returns:
        DependencyTracker instance for tracking module dependencies
    """
    structured_logger = get_structured_logger(name)
    return DependencyTracker(structured_logger)


def get_execution_flow_tracker(name: str) -> ExecutionFlowTracker:
    """Get execution flow tracker instance for a module

    Args:
        name: Module name (typically __name__)

    Returns:
        ExecutionFlowTracker instance for tracking execution flow
    """
    structured_logger = get_structured_logger(name)
    return ExecutionFlowTracker(structured_logger)
