"""Central logging module for Kumihan-Formatter

This module provides a unified logging system for the entire application,
offering structured logging with levels, formatting, and output management.

This is the main entry point that integrates all logging components:
- logging_formatters.py: JSON and structured formatters
- logging_handlers.py: File and development handlers
- performance_logger.py: Performance monitoring and optimization
- structured_logger.py: Enhanced logging with context and analysis
"""

from __future__ import annotations

import logging
import logging.handlers
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .logging import LogHelper
from .logging_formatters import StructuredLogFormatter
from .logging_handlers import DevLogHandler
from .performance_logger import (
    call_chain_tracker,
    get_log_performance_optimizer,
    log_performance_decorator,
    memory_usage_tracker,
)
from .structured_logger import (
    DependencyTracker,
    ErrorAnalyzer,
    ExecutionFlowTracker,
    StructuredLogger,
    get_dependency_tracker,
    get_error_analyzer,
    get_execution_flow_tracker,
    get_structured_logger,
)


class KumihanLogger:
    """Central logger for Kumihan-Formatter

    Provides structured logging with the following features:
    - Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - Console and file output
    - Daily log rotation
    - Configurable via environment variables
    - Integration with LogHelper for formatting
    """

    _instance: "KumihanLogger" | None = None
    _loggers: dict[str, logging.Logger] = {}
    _initialized: bool
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "KumihanLogger":
        """Thread-safe singleton pattern to ensure single logger instance"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self) -> None:
        """Initialize the logger system"""
        if self._initialized:
            return

        self._initialized = True
        self.log_dir = Path("logs")
        self.log_helper = LogHelper()

        # Create logs directory if it doesn't exist
        self.log_dir.mkdir(exist_ok=True)

        # Default configuration
        self.default_level = os.environ.get("KUMIHAN_LOG_LEVEL", "INFO")
        self.enable_file_logging = (
            os.environ.get("KUMIHAN_LOG_TO_FILE", "false").lower() == "true"
        )
        self.enable_dev_logging = (
            os.environ.get("KUMIHAN_DEV_LOG", "false").lower() == "true"
        )
        self.log_format = "[%(asctime)s] [%(levelname)8s] [%(name)s] %(message)s"
        self.date_format = "%Y-%m-%d %H:%M:%S"

        # Set up root logger
        self._setup_root_logger()

    def _setup_root_logger(self) -> None:
        """Configure the root logger"""
        root_logger = logging.getLogger("kumihan_formatter")
        root_logger.setLevel(getattr(logging, self.default_level.upper()))

        # Clear existing handlers
        root_logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, self.default_level.upper()))
        console_formatter = logging.Formatter(self.log_format, self.date_format)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        # File handler (optional)
        if self.enable_file_logging:
            log_file = (
                self.log_dir
                / f"kumihan_formatter_{datetime.now().strftime('%Y%m%d')}.log"
            )
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=7,
                encoding="utf-8",
            )
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(self.log_format, self.date_format)
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)

        # Development log handler (optional)
        if self.enable_dev_logging:
            dev_handler = DevLogHandler()
            dev_handler.setLevel(logging.DEBUG)
            root_logger.addHandler(dev_handler)

    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance for a specific module

        Args:
            name: Module name (typically __name__)

        Returns:
            Logger instance configured for the module
        """
        if name not in self._loggers:
            logger = logging.getLogger(f"kumihan_formatter.{name}")
            self._loggers[name] = logger
        return self._loggers[name]

    def set_level(self, level: str | int, logger_name: Optional[str] = None) -> None:
        """Set logging level for a specific logger or all loggers

        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            logger_name: Optional specific logger to configure
        """
        if isinstance(level, str):
            level = getattr(logging, level.upper())

        if logger_name:
            if logger_name in self._loggers:
                self._loggers[logger_name].setLevel(level)
        else:
            # Set for all loggers
            logging.getLogger("kumihan_formatter").setLevel(level)
            for logger in self._loggers.values():
                logger.setLevel(level)

    def log_performance(
        self,
        logger: logging.Logger,
        operation: str,
        duration: float,
        size: Optional[int] = None,
    ) -> None:
        """Log performance metrics

        Args:
            logger: Logger instance
            operation: Operation name
            duration: Duration in seconds
            size: Optional size in bytes
        """
        duration_str = self.log_helper.format_duration(duration)
        if size is not None:
            size_str = self.log_helper.format_size(size)
            message = (
                f"Performance: {operation} completed in {duration_str} ({size_str})"
            )
        else:
            message = f"Performance: {operation} completed in {duration_str}"
        logger.info(message)


# Global logger instance
_logger_instance = KumihanLogger()


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module

    This is the primary interface for getting loggers throughout the application.

    Args:
        name: Module name (typically __name__)

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Starting process")
        >>> logger.debug("Debug information", extra={"user_id": 123})
    """
    return _logger_instance.get_logger(name)


def configure_logging(
    level: str | None = None, enable_file: bool | None = None
) -> None:
    """Configure global logging settings

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_file: Whether to enable file logging
    """
    if level:
        _logger_instance.set_level(level)

    if enable_file is not None and enable_file != _logger_instance.enable_file_logging:
        _logger_instance.enable_file_logging = enable_file
        _logger_instance._setup_root_logger()


def log_performance(
    operation: str, duration: float, size: Optional[int] = None
) -> None:
    """Convenience function for logging performance metrics

    Args:
        operation: Operation name
        duration: Duration in seconds
        size: Optional size in bytes
    """
    logger = get_logger("performance")
    _logger_instance.log_performance(logger, operation, duration, size)


class LogSizeController:
    """Log size control and management

    Provides intelligent log size management:
    - Automatic log rotation
    - Content compression
    - Selective retention
    - Size-based filtering
    """

    def __init__(self, logger: StructuredLogger):
        self.logger = logger
        self.size_limits = {
            "max_file_size_mb": 50,
            "max_total_size_mb": 200,
            "max_entries_per_file": 100000,
            "retention_days": 7,
        }
        self.compression_enabled = True
        self.content_filters = {
            "max_message_length": 1000,
            "max_context_entries": 20,
            "sensitive_data_removal": True,
        }

    def should_include_context(self, context: dict[str, Any]) -> dict[str, Any]:
        """Filter context data to control log size

        Args:
            context: Original context dictionary

        Returns:
            Filtered context dictionary
        """
        filtered = {}
        entry_count = 0

        for key, value in context.items():
            # Limit number of context entries
            if entry_count >= self.content_filters["max_context_entries"]:
                filtered["_truncated"] = (
                    f"... {len(context) - entry_count} more entries"
                )
                break

            # Filter large values
            if (
                isinstance(value, str)
                and len(value) > self.content_filters["max_message_length"]
            ):
                filtered[key] = (
                    value[: self.content_filters["max_message_length"]]
                    + "... [truncated]"
                )
            elif (
                isinstance(value, (list, dict))
                and len(str(value)) > self.content_filters["max_message_length"]
            ):
                filtered[key] = f"[Large {type(value).__name__}: {len(value)} items]"
            else:
                filtered[key] = value

            entry_count += 1

        return filtered

    def format_message_for_size(self, message: str) -> str:
        """Format message to control size

        Args:
            message: Original message

        Returns:
            Potentially truncated message
        """
        max_length = self.content_filters["max_message_length"]

        if len(message) <= max_length:
            return message

        # Truncate with meaningful suffix
        return message[: max_length - 15] + "... [truncated]"

    def estimate_log_size(
        self, message: str, context: Optional[dict[str, Any]] = None
    ) -> int:
        """Estimate the size of a log entry in bytes

        Args:
            message: Log message
            context: Context data

        Returns:
            Estimated size in bytes
        """
        # Base message size
        size = len(message.encode("utf-8"))

        # Add context size if present
        if context:
            try:
                import json

                context_json = json.dumps(context, ensure_ascii=False)
                size += len(context_json.encode("utf-8"))
            except (TypeError, ValueError):
                # Fallback estimation
                size += len(str(context).encode("utf-8"))

        # Add overhead for JSON structure
        size += 200  # Estimated JSON overhead

        return size

    def should_skip_due_to_size(
        self, estimated_size: int, priority: str = "normal"
    ) -> bool:
        """Determine if log should be skipped due to size constraints

        Args:
            estimated_size: Estimated log entry size in bytes
            priority: Priority level (high, normal, low)

        Returns:
            True if log should be skipped
        """
        # Never skip high priority logs
        if priority == "high":
            return False

        # Skip very large logs for normal/low priority
        size_mb = estimated_size / (1024 * 1024)

        if priority == "low" and size_mb > 1.0:  # 1MB limit for low priority
            return True

        if priority == "normal" and size_mb > 5.0:  # 5MB limit for normal priority
            return True

        return False

    def get_size_statistics(self) -> dict[str, Any]:
        """Get current size statistics

        Returns:
            Dictionary with size-related statistics
        """
        return {
            "size_limits": self.size_limits,
            "content_filters": self.content_filters,
            "compression_enabled": self.compression_enabled,
            "estimated_overhead_bytes": 200,  # JSON overhead
        }

    def optimize_for_claude_code(self, context: dict[str, Any]) -> dict[str, Any]:
        """Optimize log content specifically for Claude Code consumption

        Args:
            context: Original context

        Returns:
            Optimized context for Claude Code
        """
        optimized = {}

        # Prioritize Claude-specific hints
        if "claude_hint" in context:
            optimized["claude_hint"] = context["claude_hint"]

        # Include error analysis if present
        if "error_analysis" in context:
            optimized["error_analysis"] = context["error_analysis"]

        # Include suggestions
        if "suggestion" in context or "suggestions" in context:
            optimized["suggestion"] = context.get("suggestion") or context.get(
                "suggestions"
            )

        # Include operation context
        if "operation" in context:
            optimized["operation"] = context["operation"]

        # Include file/line information
        for key in ["file_path", "line_number", "function", "module"]:
            if key in context:
                optimized[key] = context[key]

        # Include performance metrics (limited)
        for key in ["duration_ms", "memory_mb", "success"]:
            if key in context:
                optimized[key] = context[key]

        # Add remaining important context (up to limit)
        remaining_space = self.content_filters["max_context_entries"] - len(optimized)
        for key, value in context.items():
            if key not in optimized and remaining_space > 0:
                optimized[key] = value
                remaining_space -= 1

        return optimized


def get_log_size_controller(name: str) -> LogSizeController:
    """Get log size controller instance for a module

    Args:
        name: Module name (typically __name__)

    Returns:
        LogSizeController instance for size management
    """
    structured_logger = get_structured_logger(name)
    return LogSizeController(structured_logger)


class ClaudeCodeIntegrationLogger:
    """Complete Claude Code integration logger

    Combines all features into a single, optimized logger
    specifically designed for Claude Code interaction.
    """

    def __init__(self, name: str):
        self.name = name
        self.structured_logger = get_structured_logger(name)
        self.error_analyzer = get_error_analyzer(name)
        self.dependency_tracker = get_dependency_tracker(name)
        self.flow_tracker = get_execution_flow_tracker(name)
        self.performance_optimizer = get_log_performance_optimizer(name)
        self.size_controller = get_log_size_controller(name)

    def log_with_claude_optimization(
        self,
        level: int,
        message: str,
        context: Optional[dict[str, Any]] = None,
        operation: Optional[str] = None,
        priority: str = "normal",
    ) -> None:
        """Log with full Claude Code optimization

        Args:
            level: Log level
            message: Log message
            context: Context data
            operation: Operation name
            priority: Priority level (high, normal, low)
        """
        import time

        start_time = time.time()

        # Generate message key for performance tracking
        message_key = (
            f"{self.name}_{operation or 'general'}_{logging.getLevelName(level)}"
        )

        # Check if we should log based on performance
        if not self.performance_optimizer.should_log(level, message_key, operation):
            return

        # Optimize context for Claude Code
        if context:
            context = self.size_controller.optimize_for_claude_code(context)
            context = self.size_controller.should_include_context(context)

        # Format message for size control
        formatted_message = self.size_controller.format_message_for_size(message)

        # Estimate size and check if we should skip
        estimated_size = self.size_controller.estimate_log_size(
            formatted_message, context
        )
        if self.size_controller.should_skip_due_to_size(estimated_size, priority):
            return

        # Perform the actual logging
        if context:
            self.structured_logger.log_with_context(level, formatted_message, context)
        else:
            self.structured_logger.logger.log(level, formatted_message)

        # Record performance metrics
        duration = time.time() - start_time
        self.performance_optimizer.record_log_event(level, message_key, duration)

    def log_error_with_claude_analysis(
        self,
        error: Exception,
        message: str,
        context: Optional[dict[str, Any]] = None,
        operation: Optional[str] = None,
    ) -> None:
        """Log error with full Claude Code analysis"""
        self.error_analyzer.log_error_with_analysis(error, message, context, operation)

    def track_function_execution(
        self, function_name: str, args_info: Optional[dict[str, Any]] = None
    ) -> str:
        """Track function execution with flow tracking"""
        return self.flow_tracker.enter_function(function_name, self.name, args_info)

    def finish_function_execution(
        self,
        frame_id: str,
        success: bool = True,
        result_info: Optional[dict[str, Any]] = None,
        error_info: Optional[dict[str, Any]] = None,
    ) -> None:
        """Finish function execution tracking"""
        self.flow_tracker.exit_function(frame_id, success, result_info, error_info)

    def track_dependency_import(
        self,
        module_name: str,
        imported_from: Optional[str] = None,
        import_time: Optional[float] = None,
    ) -> None:
        """Track module dependency import"""
        self.dependency_tracker.track_import(module_name, imported_from, import_time)

    def get_comprehensive_report(self) -> dict[str, Any]:
        """Get comprehensive report combining all tracking data"""
        return {
            "module": self.name,
            "timestamp": datetime.now().isoformat(),
            "performance": self.performance_optimizer.get_performance_report(),
            "size_stats": self.size_controller.get_size_statistics(),
            "dependencies": self.dependency_tracker.get_dependency_map(),
            "execution_flow": self.flow_tracker.get_current_flow(),
            "claude_hint": "Complete integration report for debugging and optimization",
        }


def get_claude_code_logger(name: str) -> ClaudeCodeIntegrationLogger:
    """Get complete Claude Code integration logger

    Args:
        name: Module name (typically __name__)

    Returns:
        ClaudeCodeIntegrationLogger with all Phase 1-4 features
    """
    return ClaudeCodeIntegrationLogger(name)
