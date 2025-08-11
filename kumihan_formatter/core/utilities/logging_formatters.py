"""Logging formatters for Kumihan-Formatter

This module provides specialized formatters for different types of log output,
focusing on structured logging and Claude Code integration.
"""

from __future__ import annotations

import json
import logging

# import sys  # Removed: unused import
from datetime import datetime

# typing.Any removed as unused


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
        except Exception:
            # フォールバック: 基本的な文字列フォーマット
            return f"{record.levelname}: {record.getMessage()}"
