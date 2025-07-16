"""Logging formatters and handlers for Kumihan-Formatter

This module provides specialized logging formatters and handlers for different
output formats and development scenarios.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Union


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
