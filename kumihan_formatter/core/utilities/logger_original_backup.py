"""Central logging module for Kumihan-Formatter

This module provides a unified logging system for the entire application,
offering structured logging with levels, formatting, and output management.
"""

from __future__ import annotations

import functools
import inspect
import json
import logging
import logging.handlers
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional, Union

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

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
    standard_logger = get_logger(name)
    return StructuredLogger(standard_logger)


def log_performance_decorator(
    operation: Optional[str] = None,
    include_memory: bool = False,
    include_stack: bool = False,
    logger_name: Optional[str] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for automatic performance logging

    Args:
        operation: Operation name (defaults to function name)
        include_memory: Whether to include memory usage info
        include_stack: Whether to include stack trace info
        logger_name: Logger name (defaults to function's module)

    Returns:
        Decorated function with performance logging

    Example:
        @log_performance_decorator(include_memory=True)
        def convert_file(input_path: str) -> str:
            # File conversion logic
            return output_path
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Set up operation name
            op_name = operation or func.__name__

            # Set up logger
            module_name = func.__module__ if func.__module__ else "unknown"
            logger_name_final = logger_name or module_name
            structured_logger = get_structured_logger(logger_name_final)

            # Record start time and memory
            start_time = time.time()
            start_memory = None
            if include_memory and HAS_PSUTIL:
                try:
                    start_memory = psutil.Process().memory_info().rss
                except Exception:
                    pass  # Ignore memory monitoring errors

            # Get function signature and arguments
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Get call stack info
            stack_info = None
            if include_stack:
                stack = traceback.extract_stack()
                stack_info = {
                    "caller": f"{stack[-2].filename}:{stack[-2].lineno}",
                    "function": stack[-2].name,
                    "depth": len(stack) - 1,
                }

            try:
                # Log function entry
                entry_context = {
                    "phase": "entry",
                    "args_count": len(args),
                    "kwargs_count": len(kwargs),
                }

                if include_memory and start_memory:
                    entry_context["memory_mb"] = round(start_memory / (1024 * 1024), 2)

                if stack_info:
                    entry_context["stack_info"] = stack_info

                structured_logger.debug(
                    f"Function entry: {op_name}", operation=op_name, **entry_context
                )

                # Execute function
                result = func(*args, **kwargs)

                # Calculate performance metrics
                end_time = time.time()
                duration = end_time - start_time

                # Log successful completion
                completion_context = {
                    "phase": "completion",
                    "success": True,
                }

                if include_memory and HAS_PSUTIL:
                    try:
                        end_memory = psutil.Process().memory_info().rss
                        completion_context["memory_mb"] = round(
                            end_memory / (1024 * 1024), 2
                        )
                        if start_memory:
                            memory_delta = end_memory - start_memory
                            completion_context["memory_delta_mb"] = round(
                                memory_delta / (1024 * 1024), 2
                            )
                    except Exception:
                        pass  # Ignore memory monitoring errors

                structured_logger.performance(op_name, duration, **completion_context)

                return result

            except Exception as e:
                # Log error completion
                end_time = time.time()
                duration = end_time - start_time

                error_context = {
                    "phase": "error",
                    "success": False,
                    "error_message": str(e),
                }

                if include_memory and HAS_PSUTIL:
                    try:
                        end_memory = psutil.Process().memory_info().rss
                        error_context["memory_mb"] = round(
                            end_memory / (1024 * 1024), 2
                        )
                    except Exception:
                        pass  # Ignore memory monitoring errors

                structured_logger.error_with_suggestion(
                    f"Function failed: {op_name}",
                    "Check function arguments and internal logic",
                    error_type=type(e).__name__,
                    operation=op_name,
                    **error_context,
                )

                # Re-raise the exception
                raise

        return wrapper

    return decorator


def call_chain_tracker(max_depth: int = 10) -> dict[str, Any]:
    """Get current call chain information for debugging

    Args:
        max_depth: Maximum stack depth to track

    Returns:
        Dictionary with call chain information
    """
    stack = traceback.extract_stack()
    call_chain = []

    # Skip the last frame (this function) and limit depth
    for frame in stack[-max_depth - 1 : -1]:
        call_chain.append(
            {
                "file": frame.filename.split("/")[-1],  # Just filename, not full path
                "line": frame.lineno,
                "function": frame.name,
                "code": frame.line.strip() if frame.line else None,
            }
        )

    return {
        "call_chain": call_chain,
        "chain_depth": len(call_chain),
        "current_function": call_chain[-1]["function"] if call_chain else None,
    }


def memory_usage_tracker() -> dict[str, Any]:
    """Get current memory usage information

    Returns:
        Dictionary with memory usage metrics
    """
    if not HAS_PSUTIL:
        return {
            "memory_rss_mb": 0,
            "memory_vms_mb": 0,
            "memory_percent": 0,
            "cpu_percent": 0,
            "psutil_available": False,
        }

    try:
        process = psutil.Process()
        memory_info = process.memory_info()

        return {
            "memory_rss_mb": round(memory_info.rss / (1024 * 1024), 2),
            "memory_vms_mb": round(memory_info.vms / (1024 * 1024), 2),
            "memory_percent": round(process.memory_percent(), 2),
            "cpu_percent": round(process.cpu_percent(), 2),
            "psutil_available": True,
        }
    except Exception:
        return {
            "memory_rss_mb": 0,
            "memory_vms_mb": 0,
            "memory_percent": 0,
            "cpu_percent": 0,
            "psutil_available": False,
            "error": "Failed to get memory info",
        }


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


class LogPerformanceOptimizer:
    """Phase 4: Performance optimization for logging system

    Provides intelligent logging optimization features:
    - Adaptive log level management
    - Performance-based filtering
    - Resource usage monitoring
    - Automatic throttling
    """

    def __init__(self, logger: StructuredLogger):
        self.logger = logger
        self.performance_metrics: dict[str, list[float]] = {}
        self.log_frequency: dict[str, int] = {}
        self.throttle_thresholds = {
            "high_frequency": 100,  # logs per second
            "memory_limit": 100,  # MB
            "cpu_limit": 80,  # percentage
        }
        self.adaptive_levels = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
        }
        self.current_optimization_level = "normal"

    def should_log(
        self, level: int, message_key: str, operation: Optional[str] = None
    ) -> bool:
        """Determine if message should be logged based on performance metrics

        Args:
            level: Log level
            message_key: Unique key for message type
            operation: Operation being logged

        Returns:
            True if message should be logged
        """
        # Always log errors and warnings
        if level >= logging.WARNING:
            return True

        # Check frequency throttling
        if self._is_high_frequency(message_key):
            if level == logging.DEBUG:
                return False  # Skip debug in high frequency scenarios

        # Check system resource usage
        if self._is_high_resource_usage():
            if level == logging.DEBUG:
                return False
            if level == logging.INFO and self._is_non_critical_info(operation):
                return False

        return True

    def _is_high_frequency(self, message_key: str) -> bool:
        """Check if message type is being logged at high frequency"""
        current_time = time.time()

        # Initialize if first occurrence
        if message_key not in self.log_frequency:
            self.log_frequency[message_key] = 0
            return False

        # Simple frequency check (could be enhanced with time windows)
        return (
            self.log_frequency[message_key] > self.throttle_thresholds["high_frequency"]
        )

    def _is_high_resource_usage(self) -> bool:
        """Check if system resource usage is high"""
        if not HAS_PSUTIL:
            return False

        try:
            memory_info = memory_usage_tracker()
            return bool(
                memory_info["memory_rss_mb"] > self.throttle_thresholds["memory_limit"]
                or memory_info["cpu_percent"] > self.throttle_thresholds["cpu_limit"]
            )
        except Exception:
            return False

    def _is_non_critical_info(self, operation: Optional[str]) -> bool:
        """Check if info message is non-critical and can be skipped"""
        non_critical_operations = {
            "performance_tracking",
            "dependency_loading",
            "memory_monitoring",
            "debug_tracing",
        }
        return operation in non_critical_operations

    def record_log_event(
        self, level: int, message_key: str, duration: float = 0.0
    ) -> None:
        """Record logging event for performance analysis

        Args:
            level: Log level
            message_key: Message type key
            duration: Time taken to process log
        """
        # Update frequency counter
        self.log_frequency[message_key] = self.log_frequency.get(message_key, 0) + 1

        # Record performance metrics
        if message_key not in self.performance_metrics:
            self.performance_metrics[message_key] = []

        self.performance_metrics[message_key].append(duration)

        # Keep only recent metrics (last 100 entries)
        if len(self.performance_metrics[message_key]) > 100:
            self.performance_metrics[message_key] = self.performance_metrics[
                message_key
            ][-100:]

    def optimize_log_levels(self) -> dict[str, int]:
        """Automatically optimize log levels based on performance data

        Returns:
            Dictionary of recommended log level adjustments
        """
        recommendations = {}

        # Analyze performance impact of different log levels
        total_debug_time = sum(
            sum(metrics)
            for key, metrics in self.performance_metrics.items()
            if "debug" in key.lower()
        )

        total_info_time = sum(
            sum(metrics)
            for key, metrics in self.performance_metrics.items()
            if "info" in key.lower()
        )

        # Recommend level adjustments based on overhead
        if total_debug_time > 1.0:  # If debug logging takes > 1 second total
            recommendations["debug"] = logging.INFO

        if total_info_time > 0.5:  # If info logging takes > 0.5 seconds total
            recommendations["info"] = logging.WARNING

        return recommendations

    def get_performance_report(self) -> dict[str, Any]:
        """Generate performance report for logging system

        Returns:
            Dictionary with performance analysis
        """
        total_logs = sum(self.log_frequency.values())
        total_time = sum(sum(metrics) for metrics in self.performance_metrics.values())

        # Calculate average times per message type
        avg_times = {}
        for key, metrics in self.performance_metrics.items():
            if metrics:
                avg_times[key] = round(sum(metrics) / len(metrics) * 1000, 3)  # ms

        # Find slowest operations
        slowest = sorted(avg_times.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "total_log_events": total_logs,
            "total_processing_time_ms": round(total_time * 1000, 2),
            "average_time_per_log_ms": round(total_time / max(total_logs, 1) * 1000, 3),
            "slowest_operations": slowest,
            "high_frequency_messages": [
                key
                for key, count in self.log_frequency.items()
                if count > self.throttle_thresholds["high_frequency"] // 10
            ],
            "optimization_level": self.current_optimization_level,
            "memory_usage": memory_usage_tracker(),
        }


class LogSizeController:
    """Phase 4: Log size control and management

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


def get_log_performance_optimizer(name: str) -> LogPerformanceOptimizer:
    """Get log performance optimizer instance for a module

    Args:
        name: Module name (typically __name__)

    Returns:
        LogPerformanceOptimizer instance for performance optimization
    """
    structured_logger = get_structured_logger(name)
    return LogPerformanceOptimizer(structured_logger)


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
    """Phase 4: Complete Claude Code integration logger

    Combines all Phase 1-4 features into a single, optimized logger
    specifically designed for Claude Code interaction.
    """

    def __init__(self, name: str):
        self.name = name
        self.structured_logger = get_structured_logger(name)
        self.error_analyzer = ErrorAnalyzer(self.structured_logger)
        self.dependency_tracker = DependencyTracker(self.structured_logger)
        self.flow_tracker = ExecutionFlowTracker(self.structured_logger)
        self.performance_optimizer = LogPerformanceOptimizer(self.structured_logger)
        self.size_controller = LogSizeController(self.structured_logger)

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
