"""Central logging module for Kumihan-Formatter

This module provides a unified logging system for the entire application,
offering structured logging with levels, formatting, and output management.
"""

from __future__ import annotations

import json
import logging
import logging.handlers
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .logging import LogHelper


class StructuredLogFormatter(logging.Formatter):
    """JSON formatter for structured logging

    Formats log records as JSON with structured context data for easier
    parsing by Claude Code and other automated tools.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON with structured context"""
        # Base log data
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
            "line_number": record.lineno,
            "function": record.funcName,
        }

        # Add structured context if available
        if hasattr(record, "context") and record.context:
            log_data["context"] = record.context

        # Add extra fields from record
        extra_fields = {
            k: v
            for k, v in record.__dict__.items()
            if k
            not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
                "exc_info",
                "exc_text",
                "stack_info",
                "context",
            }
        }
        if extra_fields:
            log_data["extra"] = extra_fields

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        try:
            return json.dumps(log_data, ensure_ascii=False, separators=(",", ":"))
        except (TypeError, ValueError) as e:
            # Fallback to standard formatting if JSON serialization fails
            # Log the error to stderr for debugging
            print(f"JSON serialization failed: {e}", file=sys.stderr)
            return super().format(record)


class DevLogHandler(logging.Handler):
    """Development log handler for temporary logging to /tmp/kumihan_formatter/

    This handler is designed for development use and creates log files in
    the system's temporary directory for Claude Code to easily access.

    Features:
    - Logs to /tmp/kumihan_formatter/ directory
    - Session-based timestamped filenames
    - Automatic cleanup of old log files (24 hours)
    - File size limits (5MB)
    - Only active when KUMIHAN_DEV_LOG=true
    """

    def __init__(self, session_id: Optional[str] = None):
        super().__init__()
        self.session_id = session_id or str(int(time.time()))
        self.log_dir = Path("/tmp/kumihan_formatter")
        self.log_file = self.log_dir / f"dev_log_{self.session_id}.log"
        self.max_size = 5 * 1024 * 1024  # 5MB
        self.cleanup_hours = 24

        # Create log directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Clean up old logs
        self._cleanup_old_logs()

        # Set up formatter (JSON for structured logging)
        use_json = os.environ.get("KUMIHAN_DEV_LOG_JSON", "true").lower() == "true"
        formatter: Union[StructuredLogFormatter, logging.Formatter]
        if use_json:
            formatter = StructuredLogFormatter()
        else:
            formatter = logging.Formatter(
                "[%(asctime)s] [%(levelname)8s] [%(name)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        self.setFormatter(formatter)

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record to the temporary log file"""
        if not self._should_log():
            return

        try:
            # Check file size limit
            if self.log_file.exists() and self.log_file.stat().st_size > self.max_size:
                self._rotate_log()

            # Format and write the log record
            msg = self.format(record)
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(msg + "\n")

        except Exception as e:
            # Log the error to stderr but don't disrupt the main application
            print(f"Log handler error: {e}", file=sys.stderr)

    def _should_log(self) -> bool:
        """Check if development logging is enabled"""
        return os.environ.get("KUMIHAN_DEV_LOG", "false").lower() == "true"

    def _rotate_log(self) -> None:
        """Rotate the current log file when it exceeds the size limit"""
        if self.log_file.exists():
            backup_file = self.log_dir / f"dev_log_{self.session_id}_backup.log"
            if backup_file.exists():
                backup_file.unlink()
            self.log_file.rename(backup_file)

    def _cleanup_old_logs(self) -> None:
        """Remove log files older than 24 hours"""
        if not self.log_dir.exists():
            return

        current_time = time.time()
        cutoff_time = current_time - (self.cleanup_hours * 3600)

        for log_file in self.log_dir.glob("dev_log_*.log"):
            try:
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
            except (OSError, FileNotFoundError):
                # Ignore errors during cleanup
                pass


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

    def __new__(cls) -> "KumihanLogger":
        """Singleton pattern to ensure single logger instance"""
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

    def set_level(
        self, level: Union[str, int], logger_name: Optional[str] = None
    ) -> None:
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

    def log_with_context(
        self, logger: logging.Logger, level: int, message: str, **context: Any
    ) -> None:
        """Log a message with additional context

        Args:
            logger: Logger instance
            level: Log level
            message: Log message
            **context: Additional context as key-value pairs
        """
        if context:
            context_str = " | ".join(f"{k}={v}" for k, v in context.items())
            message = f"{message} | {context_str}"
        logger.log(level, message)

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


class StructuredLogger:
    """Enhanced logger with structured logging capabilities

    Provides methods for logging with structured context data,
    making it easier for Claude Code to parse and analyze logs.
    """

    # Sensitive keys that should be filtered out from logs
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

    def _sanitize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive information from context data

        Args:
            context: Original context dictionary

        Returns:
            Sanitized context dictionary with sensitive data filtered out
        """
        sanitized = {}
        for key, value in context.items():
            if key.lower() in self.SENSITIVE_KEYS:
                sanitized[key] = "[FILTERED]"
            else:
                sanitized[key] = value
        return sanitized

    def log_with_context(
        self,
        level: int,
        message: str,
        context: Optional[Dict[str, Any]] = None,
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
    standard_logger = get_logger(name)
    return StructuredLogger(standard_logger)


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
