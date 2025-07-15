"""Tests for structured logging functionality"""

import json
import logging
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from kumihan_formatter.core.utilities.logging_formatters import StructuredLogFormatter
from kumihan_formatter.core.utilities.structured_logger import (
    StructuredLogger,
    get_structured_logger,
)


class TestStructuredLogFormatter:
    """Test the JSON formatter for structured logs"""

    def test_basic_json_formatting(self):
        """Test basic JSON log formatting"""
        formatter = StructuredLogFormatter()
        record = logging.LogRecord(
            name="test.module",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
            func="test_function",
        )

        result = formatter.format(record)
        log_data = json.loads(result)

        assert log_data["level"] == "INFO"
        assert log_data["module"] == "test.module"
        assert log_data["message"] == "Test message"
        assert log_data["line_number"] == 42
        assert log_data["function"] == "test_function"
        assert "timestamp" in log_data

    def test_context_formatting(self):
        """Test formatting with structured context"""
        formatter = StructuredLogFormatter()
        record = logging.LogRecord(
            name="test.module",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
            func="test_function",
        )
        record.context = {"file_path": "test.txt", "size": 1024}

        result = formatter.format(record)
        log_data = json.loads(result)

        assert log_data["context"]["file_path"] == "test.txt"
        assert log_data["context"]["size"] == 1024

    def test_extra_fields_formatting(self):
        """Test formatting with extra fields"""
        formatter = StructuredLogFormatter()
        record = logging.LogRecord(
            name="test.module",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
            func="test_function",
        )
        record.custom_field = "custom_value"

        result = formatter.format(record)
        log_data = json.loads(result)

        assert log_data["extra"]["custom_field"] == "custom_value"

    def test_json_serialization_fallback(self):
        """Test that JSON serialization handles non-serializable objects"""
        formatter = StructuredLogFormatter()
        record = logging.LogRecord(
            name="test.module",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
            func="test_function",
        )
        # Add a non-serializable object
        record.context = {"non_serializable": object()}

        # Should fall back to standard formatting without raising an exception
        result = formatter.format(record)
        assert isinstance(result, str)
        # Should not be JSON if fallback occurred
        try:
            json.loads(result)
            # If this succeeds, the object was somehow serializable
            assert False, "Expected fallback formatting, but got JSON"
        except json.JSONDecodeError:
            # Expected - fallback to standard formatting
            assert "Test message" in result


class TestStructuredLogger:
    """Test the enhanced structured logger"""

    def setup_method(self):
        """Set up test logger"""
        self.test_logger = logging.getLogger("test_structured")
        self.test_logger.setLevel(logging.DEBUG)
        self.structured_logger = StructuredLogger(self.test_logger)

    def test_log_with_context(self, caplog):
        """Test logging with context"""
        with caplog.at_level(logging.INFO):
            self.structured_logger.log_with_context(
                logging.INFO, "Test message", {"safe_key": "value"}
            )

        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert hasattr(record, "context")
        assert record.context["safe_key"] == "value"

    def test_info_with_context(self, caplog):
        """Test info logging with context"""
        with caplog.at_level(logging.INFO):
            self.structured_logger.info("Test info", file_path="test.txt", size=1024)

        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.levelname == "INFO"
        assert record.context["file_path"] == "test.txt"
        assert record.context["size"] == 1024

    def test_error_with_suggestion(self, caplog):
        """Test error logging with suggestion"""
        with caplog.at_level(logging.ERROR):
            self.structured_logger.error_with_suggestion(
                "File not found",
                "Check file path",
                error_type="FileNotFoundError",
                file_path="missing.txt",
            )

        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.levelname == "ERROR"
        assert record.context["suggestion"] == "Check file path"
        assert record.context["error_type"] == "FileNotFoundError"
        assert record.context["file_path"] == "missing.txt"

    def test_file_operation_success(self, caplog):
        """Test file operation logging (success)"""
        with caplog.at_level(logging.INFO):
            self.structured_logger.file_operation(
                "read", "/path/to/file.txt", success=True, size_bytes=2048
            )

        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.levelname == "INFO"
        assert record.context["operation"] == "read"
        assert record.context["file_path"] == "/path/to/file.txt"
        assert record.context["success"] is True
        assert record.context["size_bytes"] == 2048

    def test_file_operation_failure(self, caplog):
        """Test file operation logging (failure)"""
        with caplog.at_level(logging.ERROR):
            self.structured_logger.file_operation(
                "write", "/path/to/file.txt", success=False, error="Permission denied"
            )

        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.levelname == "ERROR"
        assert record.context["operation"] == "write"
        assert record.context["success"] is False
        assert record.context["error"] == "Permission denied"

    def test_performance_logging(self, caplog):
        """Test performance metrics logging"""
        with caplog.at_level(logging.INFO):
            self.structured_logger.performance("file_conversion", 0.125, lines=500)

        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.levelname == "INFO"
        assert record.context["operation"] == "file_conversion"
        assert record.context["duration_seconds"] == 0.125
        assert record.context["duration_ms"] == 125.0
        assert record.context["lines"] == 500

    def test_state_change_logging(self, caplog):
        """Test state change logging"""
        with caplog.at_level(logging.DEBUG):
            self.structured_logger.state_change(
                "config updated", old_value="debug", new_value="info", module="logger"
            )

        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.levelname == "DEBUG"
        assert record.context["what_changed"] == "config updated"
        assert record.context["old_value"] == "debug"
        assert record.context["new_value"] == "info"
        assert record.context["module"] == "logger"

    def test_sensitive_data_filtering(self, caplog):
        """Test that sensitive data is filtered out"""
        with caplog.at_level(logging.INFO):
            self.structured_logger.info(
                "User login",
                username="test_user",
                password="secret123",  # Should be filtered
                token="bearer_token",  # Should be filtered
                api_key="api_secret",  # Should be filtered
            )

        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.context["username"] == "test_user"
        # Sensitive data should be replaced with [FILTERED]
        assert record.context["password"] == "[FILTERED]"
        assert record.context["token"] == "[FILTERED]"
        assert record.context["api_key"] == "[FILTERED]"


class TestStructuredLoggerIntegration:
    """Integration tests for structured logging"""

    def test_get_structured_logger(self):
        """Test getting a structured logger instance"""
        logger = get_structured_logger("test.integration")
        assert isinstance(logger, StructuredLogger)
        assert logger.logger.name == "kumihan_formatter.test.integration"

    @patch.dict(
        "os.environ", {"KUMIHAN_DEV_LOG": "true", "KUMIHAN_DEV_LOG_JSON": "true"}
    )
    def test_development_logging_integration(self):
        """Test integration with development logging"""
        logger = get_structured_logger("test.dev")

        # Test that we can log without errors
        logger.info("Development test", test_id=123)
        logger.error_with_suggestion(
            "Test error", "Test suggestion", error_type="TestError"
        )

    def test_large_context_handling(self, caplog):
        """Test handling of large context data"""
        logger = get_structured_logger("test.large")

        # Create large context data
        large_context = {f"key_{i}": f"value_{i}" for i in range(100)}

        with caplog.at_level(logging.INFO):
            logger.info("Large context test", **large_context)

        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert len(record.context) == 100
        assert record.context["key_0"] == "value_0"
        assert record.context["key_99"] == "value_99"


if __name__ == "__main__":
    pytest.main([__file__])
