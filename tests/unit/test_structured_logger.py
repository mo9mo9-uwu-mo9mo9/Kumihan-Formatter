"""Tests for structured logging functionality"""

import logging
import time
from unittest.mock import MagicMock, patch

import pytest

from kumihan_formatter.core.utilities.structured_logger import (
    DependencyTracker,
    ErrorAnalyzer,
    ExecutionFlowTracker,
    StructuredLogger,
    get_dependency_tracker,
    get_error_analyzer,
    get_execution_flow_tracker,
    get_structured_logger,
)


class TestStructuredLogger:
    """Test the StructuredLogger class"""

    def test_structured_logger_creation(self):
        """Test creating a structured logger"""
        mock_logger = MagicMock(spec=logging.Logger)
        structured_logger = StructuredLogger(mock_logger)

        assert structured_logger.logger == mock_logger

    def test_sensitive_key_detection(self):
        """Test sensitive key detection using LRU cache"""
        mock_logger = MagicMock(spec=logging.Logger)
        structured_logger = StructuredLogger(mock_logger)

        # Test sensitive keys
        assert structured_logger._is_sensitive_key("password") == True
        assert structured_logger._is_sensitive_key("api_key") == True
        assert structured_logger._is_sensitive_key("token") == True
        assert structured_logger._is_sensitive_key("SECRET") == True

        # Test non-sensitive keys
        assert structured_logger._is_sensitive_key("username") == False
        assert structured_logger._is_sensitive_key("file_path") == False

    def test_context_sanitization(self):
        """Test context sanitization removes sensitive data"""
        mock_logger = MagicMock(spec=logging.Logger)
        structured_logger = StructuredLogger(mock_logger)

        context = {
            "username": "test_user",
            "password": "secret123",
            "api_key": "abc123",
            "file_path": "/tmp/test.txt",
            "token": "xyz789",
        }

        sanitized = structured_logger._sanitize_context(context)

        assert sanitized["username"] == "test_user"
        assert sanitized["password"] == "[FILTERED]"
        assert sanitized["api_key"] == "[FILTERED]"
        assert sanitized["file_path"] == "/tmp/test.txt"
        assert sanitized["token"] == "[FILTERED]"

    def test_log_with_context(self):
        """Test logging with context"""
        mock_logger = MagicMock(spec=logging.Logger)
        structured_logger = StructuredLogger(mock_logger)

        context = {"operation": "test", "file_path": "/tmp/test.txt"}
        structured_logger.log_with_context(logging.INFO, "Test message", context)

        mock_logger.log.assert_called_once()
        args, kwargs = mock_logger.log.call_args
        assert args[0] == logging.INFO
        assert args[1] == "Test message"
        assert "context" in kwargs["extra"]

    def test_convenience_methods(self):
        """Test convenience logging methods"""
        mock_logger = MagicMock(spec=logging.Logger)
        structured_logger = StructuredLogger(mock_logger)

        structured_logger.info("Info message", key="value")
        structured_logger.debug("Debug message", key="value")
        structured_logger.warning("Warning message", key="value")
        structured_logger.error("Error message", key="value")
        structured_logger.critical("Critical message", key="value")

        assert mock_logger.log.call_count == 5

    def test_file_operation_logging(self):
        """Test file operation logging"""
        mock_logger = MagicMock(spec=logging.Logger)
        structured_logger = StructuredLogger(mock_logger)

        # Test successful operation
        structured_logger.file_operation("read", "/tmp/test.txt", success=True)
        mock_logger.log.assert_called_with(
            logging.INFO,
            "File read",
            extra={
                "context": {
                    "file_path": "/tmp/test.txt",
                    "operation": "read",
                    "success": True,
                }
            },
        )

        # Test failed operation
        structured_logger.file_operation("write", "/tmp/test.txt", success=False)
        mock_logger.log.assert_called_with(
            logging.ERROR,
            "File write",
            extra={
                "context": {
                    "file_path": "/tmp/test.txt",
                    "operation": "write",
                    "success": False,
                }
            },
        )

    def test_performance_logging(self):
        """Test performance logging"""
        mock_logger = MagicMock(spec=logging.Logger)
        structured_logger = StructuredLogger(mock_logger)

        structured_logger.performance("test_operation", 0.5, memory_mb=100)

        mock_logger.log.assert_called_with(
            logging.INFO,
            "Performance: test_operation",
            extra={
                "context": {
                    "operation": "test_operation",
                    "duration_seconds": 0.5,
                    "duration_ms": 500,
                    "memory_mb": 100,
                }
            },
        )

    def test_error_with_suggestion(self):
        """Test error logging with suggestion"""
        mock_logger = MagicMock(spec=logging.Logger)
        structured_logger = StructuredLogger(mock_logger)

        structured_logger.error_with_suggestion(
            "Test error", "Check the input", error_type="ValueError"
        )

        mock_logger.log.assert_called_with(
            logging.ERROR,
            "Test error",
            extra={
                "context": {"suggestion": "Check the input", "error_type": "ValueError"}
            },
        )


class TestErrorAnalyzer:
    """Test the ErrorAnalyzer class"""

    def test_error_analyzer_creation(self):
        """Test creating an error analyzer"""
        mock_logger = MagicMock()
        analyzer = ErrorAnalyzer(mock_logger)

        assert analyzer.logger == mock_logger

    def test_error_categorization(self):
        """Test error categorization"""
        mock_logger = MagicMock()
        analyzer = ErrorAnalyzer(mock_logger)

        # Test encoding error
        assert analyzer._categorize_error("utf-8 encoding error") == "encoding"

        # Test file access error
        assert analyzer._categorize_error("permission denied") == "file_access"

        # Test parsing error
        assert analyzer._categorize_error("parse error: invalid syntax") == "parsing"

        # Test memory error
        assert analyzer._categorize_error("out of memory") == "memory"

        # Test dependency error
        assert analyzer._categorize_error("module missing") == "dependency"

        # Test unknown error
        assert analyzer._categorize_error("unknown error") == "unknown"

    @patch("kumihan_formatter.core.utilities.structured_logger.call_chain_tracker")
    @patch("kumihan_formatter.core.utilities.structured_logger.memory_usage_tracker")
    def test_error_analysis(self, mock_memory_tracker, mock_call_tracker):
        """Test error analysis"""
        mock_logger = MagicMock()
        analyzer = ErrorAnalyzer(mock_logger)

        # Mock return values
        mock_call_tracker.return_value = {"call_chain": [], "chain_depth": 0}
        mock_memory_tracker.return_value = {"memory_rss_mb": 100}

        error = ValueError("Test error")
        analysis = analyzer.analyze_error(
            error, {"operation": "test"}, operation="test"
        )

        assert analysis["error_type"] == "ValueError"
        assert analysis["error_message"] == "Test error"
        assert analysis["category"] == "unknown"
        assert analysis["operation"] == "test"
        assert "suggestions" in analysis
        assert "timestamp" in analysis

    def test_generic_suggestions(self):
        """Test generic suggestion generation"""
        mock_logger = MagicMock()
        analyzer = ErrorAnalyzer(mock_logger)

        # Test ValueError suggestions
        suggestions = analyzer._generate_generic_suggestions(
            "ValueError", "invalid value"
        )
        assert "Validate input values and types" in suggestions

        # Test TypeError suggestions
        suggestions = analyzer._generate_generic_suggestions("TypeError", "wrong type")
        assert "Check argument types match expected types" in suggestions

        # Test IndexError suggestions
        suggestions = analyzer._generate_generic_suggestions(
            "IndexError", "out of range"
        )
        assert "Verify data structure bounds and keys" in suggestions


class TestDependencyTracker:
    """Test the DependencyTracker class"""

    def test_dependency_tracker_creation(self):
        """Test creating a dependency tracker"""
        mock_logger = MagicMock()
        tracker = DependencyTracker(mock_logger)

        assert tracker.logger == mock_logger
        assert tracker.dependencies == {}
        assert tracker.load_times == {}
        assert tracker.load_order == []

    def test_track_import(self):
        """Test tracking module imports"""
        mock_logger = MagicMock()
        tracker = DependencyTracker(mock_logger)

        # Track import
        tracker.track_import("module_a", "module_b", 0.1)

        assert "module_b" in tracker.dependencies
        assert "module_a" in tracker.dependencies["module_b"]
        assert tracker.load_times["module_a"] == 0.1
        assert tracker.load_order == ["module_a"]

        # Verify logging
        mock_logger.debug.assert_called_once()

    def test_dependency_map(self):
        """Test getting dependency map"""
        mock_logger = MagicMock()
        tracker = DependencyTracker(mock_logger)

        # Add some dependencies
        tracker.track_import("module_a", "module_b", 0.1)
        tracker.track_import("module_c", "module_b", 0.2)

        dep_map = tracker.get_dependency_map()

        assert "dependencies" in dep_map
        assert "load_times" in dep_map
        assert "load_order" in dep_map
        assert dep_map["total_modules"] == 2
        assert "slowest_imports" in dep_map


class TestExecutionFlowTracker:
    """Test the ExecutionFlowTracker class"""

    def test_execution_flow_tracker_creation(self):
        """Test creating an execution flow tracker"""
        mock_logger = MagicMock()
        tracker = ExecutionFlowTracker(mock_logger)

        assert tracker.logger == mock_logger
        assert tracker.execution_stack == []
        assert tracker.flow_id is not None

    def test_function_entry_exit(self):
        """Test function entry and exit tracking"""
        mock_logger = MagicMock()
        tracker = ExecutionFlowTracker(mock_logger)

        # Enter function
        frame_id = tracker.enter_function(
            "test_func", "test_module", {"arg1": "value1"}
        )

        assert len(tracker.execution_stack) == 1
        assert tracker.execution_stack[0]["function_name"] == "test_func"
        assert tracker.execution_stack[0]["module_name"] == "test_module"

        # Exit function
        tracker.exit_function(frame_id, success=True, result_info={"result": "success"})

        assert len(tracker.execution_stack) == 0

        # Verify logging
        assert mock_logger.debug.call_count == 1
        assert mock_logger.log_with_context.call_count == 1

    def test_current_flow(self):
        """Test getting current flow state"""
        mock_logger = MagicMock()
        tracker = ExecutionFlowTracker(mock_logger)

        # Enter function
        frame_id = tracker.enter_function("test_func", "test_module")

        flow = tracker.get_current_flow()

        assert flow["flow_id"] == tracker.flow_id
        assert flow["stack_depth"] == 1
        assert len(flow["current_stack"]) == 1
        assert flow["current_stack"][0]["function"] == "test_func"


class TestModuleFunctions:
    """Test module-level functions"""

    def test_get_structured_logger(self):
        """Test getting structured logger instance"""
        logger = get_structured_logger("test_module")
        assert isinstance(logger, StructuredLogger)

    def test_get_error_analyzer(self):
        """Test getting error analyzer instance"""
        analyzer = get_error_analyzer("test_module")
        assert isinstance(analyzer, ErrorAnalyzer)

    def test_get_dependency_tracker(self):
        """Test getting dependency tracker instance"""
        tracker = get_dependency_tracker("test_module")
        assert isinstance(tracker, DependencyTracker)

    def test_get_execution_flow_tracker(self):
        """Test getting execution flow tracker instance"""
        tracker = get_execution_flow_tracker("test_module")
        assert isinstance(tracker, ExecutionFlowTracker)
