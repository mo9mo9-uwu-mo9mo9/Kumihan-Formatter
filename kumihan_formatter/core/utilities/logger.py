"""Central logging module for Kumihan-Formatter

This module provides a unified logging system for the entire application,
offering structured logging with levels, formatting, and output management.
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .logging import LogHelper


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

    def set_level(self, level: str | int, logger_name: str | None = None) -> None:
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
        size: int | None = None,
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


def log_performance(operation: str, duration: float, size: int | None = None) -> None:
    """Convenience function for logging performance metrics

    Args:
        operation: Operation name
        duration: Duration in seconds
        size: Optional size in bytes
    """
    logger = get_logger("performance")
    _logger_instance.log_performance(logger, operation, duration, size)
