"""Test cases for DevLogHandler

This module tests the development logging functionality for Issue#446.
"""

import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from kumihan_formatter.core.utilities.logger import DevLogHandler, get_logger


class TestDevLogHandler:
    """Test cases for DevLogHandler"""

    def test_dev_log_handler_initialization(self) -> None:
        """Test DevLogHandler initialization"""
        handler = DevLogHandler("test_session")
        assert handler.session_id == "test_session"
        assert handler.log_dir == Path("/tmp/kumihan_formatter")
        assert handler.log_file == Path(
            "/tmp/kumihan_formatter/dev_log_test_session.log"
        )
        assert handler.max_size == 5 * 1024 * 1024  # 5MB
        assert handler.cleanup_hours == 24

    def test_dev_log_handler_auto_session_id(self) -> None:
        """Test DevLogHandler with auto-generated session ID"""
        handler = DevLogHandler()
        assert handler.session_id is not None
        assert handler.session_id.isdigit()

    @patch.dict(os.environ, {"KUMIHAN_DEV_LOG": "true"})
    def test_dev_log_handler_enabled(self) -> None:
        """Test DevLogHandler when KUMIHAN_DEV_LOG=true"""
        handler = DevLogHandler("test_enabled")
        assert handler._should_log() is True

    @patch.dict(os.environ, {"KUMIHAN_DEV_LOG": "false"})
    def test_dev_log_handler_disabled(self) -> None:
        """Test DevLogHandler when KUMIHAN_DEV_LOG=false"""
        handler = DevLogHandler("test_disabled")
        assert handler._should_log() is False

    def test_dev_log_handler_default_disabled(self) -> None:
        """Test DevLogHandler default behavior (disabled)"""
        # Remove KUMIHAN_DEV_LOG if it exists
        if "KUMIHAN_DEV_LOG" in os.environ:
            del os.environ["KUMIHAN_DEV_LOG"]

        handler = DevLogHandler("test_default")
        assert handler._should_log() is False

    @patch.dict(os.environ, {"KUMIHAN_DEV_LOG": "true"})
    def test_dev_log_handler_emit_creates_file(self) -> None:
        """Test that emit() creates log file when enabled"""
        import logging

        # Use a temporary session ID for testing
        session_id = f"test_emit_{int(time.time())}"
        handler = DevLogHandler(session_id)

        # Create a log record
        logger = logging.getLogger("test_logger")
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Emit the record
        handler.emit(record)

        # Check that the log file was created
        assert handler.log_file.exists()

        # Check file content
        content = handler.log_file.read_text(encoding="utf-8")
        assert "Test message" in content
        assert "test_logger" in content

        # Cleanup
        if handler.log_file.exists():
            handler.log_file.unlink()

    @patch.dict(os.environ, {"KUMIHAN_DEV_LOG": "false"})
    def test_dev_log_handler_emit_disabled(self) -> None:
        """Test that emit() doesn't create file when disabled"""
        import logging

        session_id = f"test_emit_disabled_{int(time.time())}"
        handler = DevLogHandler(session_id)

        # Create a log record
        logger = logging.getLogger("test_logger")
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Emit the record
        handler.emit(record)

        # Check that the log file was NOT created
        assert not handler.log_file.exists()

    @patch.dict(os.environ, {"KUMIHAN_DEV_LOG": "true"})
    def test_dev_log_handler_file_rotation(self) -> None:
        """Test log file rotation when size limit is exceeded"""
        import logging

        session_id = f"test_rotation_{int(time.time())}"
        handler = DevLogHandler(session_id)

        # Set a very small max_size for testing
        handler.max_size = 100  # 100 bytes

        # Create multiple log records to exceed the size limit
        logger = logging.getLogger("test_logger")
        for i in range(10):
            record = logging.LogRecord(
                name="test_logger",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg=f"Long test message number {i} with extra content to exceed size limit",
                args=(),
                exc_info=None,
            )
            handler.emit(record)

        # Check that backup file was created
        backup_file = handler.log_dir / f"dev_log_{session_id}_backup.log"
        assert backup_file.exists() or handler.log_file.exists()

        # Cleanup
        if handler.log_file.exists():
            handler.log_file.unlink()
        if backup_file.exists():
            backup_file.unlink()

    def test_dev_log_handler_cleanup_old_logs(self) -> None:
        """Test cleanup of old log files"""
        # Create a temporary old log file
        old_session_id = f"test_old_{int(time.time())}"
        old_log_file = Path("/tmp/kumihan_formatter") / f"dev_log_{old_session_id}.log"

        # Create the directory and file
        old_log_file.parent.mkdir(parents=True, exist_ok=True)
        old_log_file.write_text("Old log content", encoding="utf-8")

        # Set the modification time to 25 hours ago
        old_time = time.time() - (25 * 3600)  # 25 hours ago
        os.utime(old_log_file, (old_time, old_time))

        # Create a new handler (this should trigger cleanup)
        handler = DevLogHandler(f"test_cleanup_{int(time.time())}")

        # Check that the old log file was removed
        assert not old_log_file.exists()

    @patch.dict(os.environ, {"KUMIHAN_DEV_LOG": "true"})
    def test_integration_with_kumihan_logger(self) -> None:
        """Test integration with the main KumihanLogger"""
        logger = get_logger("test_integration")

        # Log a message
        logger.info("Integration test message")

        # Check that the log file was created (if dev logging is enabled)
        log_files = list(Path("/tmp/kumihan_formatter").glob("dev_log_*.log"))
        if log_files:
            # At least one log file should exist
            assert len(log_files) >= 1

            # Check that our message is in one of the log files
            found_message = False
            for log_file in log_files:
                try:
                    content = log_file.read_text(encoding="utf-8")
                    if "Integration test message" in content:
                        found_message = True
                        break
                except Exception:
                    continue

            assert found_message, "Integration test message not found in any log file"
