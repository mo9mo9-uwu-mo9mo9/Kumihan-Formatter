"""Main logging handlers and logger classes for Kumihan-Formatter

Single Responsibility Principle適用: ログハンドラーとメインロガー管理の分離
Issue #476 Phase3対応 - logger.py分割
"""

from __future__ import annotations

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union

from ..utilities.logging import LogHelper
from .logging_formatters import DevLogHandler


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
    _initialized: bool = False

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

            # Check file write permissions before creating handler
            if self._check_file_write_permissions(log_file):
                try:
                    file_handler = logging.handlers.RotatingFileHandler(
                        log_file,
                        maxBytes=10 * 1024 * 1024,  # 10MB
                        backupCount=7,
                        encoding="utf-8",
                    )
                    file_handler.setLevel(logging.DEBUG)
                    file_formatter = logging.Formatter(
                        self.log_format, self.date_format
                    )
                    file_handler.setFormatter(file_formatter)
                    root_logger.addHandler(file_handler)
                except (OSError, IOError) as e:
                    # Log to console if file logging fails
                    print(f"Warning: Could not create file handler for {log_file}: {e}")
                    self.enable_file_logging = False
            else:
                print(f"Warning: No write permissions for log file {log_file}")
                self.enable_file_logging = False

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

    def _check_file_write_permissions(self, log_file: Path) -> bool:
        """Check if we have write permissions for the log file

        Args:
            log_file: Path to the log file

        Returns:
            True if we have write permissions, False otherwise
        """
        try:
            # Check if file exists and is writable
            if log_file.exists():
                return os.access(log_file, os.W_OK)

            # Check if parent directory exists and is writable
            parent_dir = log_file.parent
            if parent_dir.exists():
                return os.access(parent_dir, os.W_OK)

            # Try to create parent directory if it doesn't exist
            try:
                parent_dir.mkdir(parents=True, exist_ok=True)
                return os.access(parent_dir, os.W_OK)
            except (OSError, IOError):
                return False

        except (OSError, IOError):
            return False


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
        # Reconfigure logger to apply changes
        _logger_instance._setup_root_logger()
