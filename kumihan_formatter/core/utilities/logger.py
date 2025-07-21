"""Central logging module for Kumihan-Formatter

This module provides a unified logging system for the entire application,
offering structured logging with levels, formatting, and output management.

This is the main entry point that integrates all logging components:
- logging_formatters.py: JSON and structured formatters
- logging_handlers.py: File and development handlers
- performance_logger.py: Performance monitoring and optimization
- structured_logger.py: Enhanced logging with context and analysis

Single Responsibility Principle適用: 589行から240行に削減
Issue #476 Phase5対応 - 大規模ファイルの機能別分割完了
"""

from __future__ import annotations

import logging
import logging.handlers
import os
import threading

# datetime.datetime removed as unused
from pathlib import Path
from typing import Optional

# 分割済み機能のインポート
# .log_size_control.LogSizeController removed as unused
from .logging import LogHelper
from .logging_formatters import StructuredLogFormatter
from .logging_handlers import DevLogHandler
from .performance_logger import (
    get_log_performance_optimizer,
)
from .structured_logger import (
    get_structured_logger,
)

# .claude_integration removed as unused


class KumihanLogger:
    """Central logger for Kumihan-Formatter

    Provides structured logging with the following features:
    - Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - Console and file output
    - Daily log rotation
    - Structured JSON formatting
    - Claude Code integration
    - Performance monitoring
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls) -> "KumihanLogger":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        self.loggers: dict[str, logging.Logger] = {}
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)

        # 開発ログ機能の状態
        self.dev_log_enabled = os.getenv("KUMIHAN_DEV_LOG", "false").lower() == "true"
        self.dev_log_json = os.getenv("KUMIHAN_DEV_LOG_JSON", "false").lower() == "true"

        # ルートロガーの設定
        self._setup_root_logger()

        # パフォーマンスロガーの初期化
        self.performance_logger = get_log_performance_optimizer("kumihan_performance")

        # LogHelper の初期化
        self.log_helper = LogHelper()

    def _setup_root_logger(self) -> None:
        """Configure root logger with formatters and handlers"""
        root_logger = logging.getLogger()

        # 既存のハンドラーをクリア
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # ログレベルの設定
        log_level = os.getenv("KUMIHAN_LOG_LEVEL", "INFO").upper()
        root_logger.setLevel(getattr(logging, log_level, logging.INFO))

        # コンソールハンドラー
        console_handler = logging.StreamHandler()
        console_formatter = StructuredLogFormatter()
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        # ファイルハンドラー（日次ローテーション）
        file_handler = logging.handlers.TimedRotatingFileHandler(
            self.log_dir / "kumihan.log",
            when="midnight",
            interval=1,
            backupCount=30,
            encoding="utf-8",
        )
        file_formatter = StructuredLogFormatter()
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        # 開発ログハンドラー
        if self.dev_log_enabled:
            dev_handler = DevLogHandler(str(self.log_dir / "dev.log"))
            root_logger.addHandler(dev_handler)

    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance for the given name

        Args:
            name: Logger name (typically __name__)

        Returns:
            Configured logger instance
        """
        if name not in self.loggers:
            logger = logging.getLogger(name)
            self.loggers[name] = logger
        return self.loggers[name]

    def set_level(self, level: str | int, logger_name: Optional[str] = None) -> None:
        """Set log level for a specific logger or root logger

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) or integer
            logger_name: Specific logger name, or None for root logger
        """
        if isinstance(level, str):
            level = getattr(logging, level.upper())

        if logger_name:
            logger = self.get_logger(logger_name)
            logger.setLevel(level)
        else:
            logging.getLogger().setLevel(level)

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
        self.performance_logger.record_log_event(
            logging.INFO, f"performance_{operation}", duration
        )

        context = {
            "operation": operation,
            "duration_seconds": duration,
            "performance_log": True,
        }

        if size is not None:
            context["size_bytes"] = size

        # 構造化ログとして記録
        structured_logger = get_structured_logger(logger.name)
        structured_logger.performance(operation, duration * 1000, context)


# シングルトンインスタンス
_logger_instance = KumihanLogger()


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance (convenience function)

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return _logger_instance.get_logger(name)


def configure_logging(
    level: str = "INFO",
    dev_log: bool = False,
    dev_log_json: bool = False,
) -> None:
    """Configure global logging settings

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        dev_log: Enable development logging
        dev_log_json: Use JSON format for development logs
    """
    os.environ["KUMIHAN_LOG_LEVEL"] = level
    os.environ["KUMIHAN_DEV_LOG"] = "true" if dev_log else "false"
    os.environ["KUMIHAN_DEV_LOG_JSON"] = "true" if dev_log_json else "false"

    # 新しいインスタンスを作成
    global _logger_instance
    _logger_instance = KumihanLogger()


def log_performance(
    operation: str, duration: float, size: Optional[int] = None
) -> None:
    """Log performance metrics (convenience function)

    Args:
        operation: Operation name
        duration: Duration in seconds
        size: Optional size in bytes
    """
    logger = get_logger("performance")
    _logger_instance.log_performance(logger, operation, duration, size)
