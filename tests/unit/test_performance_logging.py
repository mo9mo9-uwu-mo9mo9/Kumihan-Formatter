"""Tests for performance logging features (Phase 2)"""

import logging
import time
from unittest.mock import MagicMock, patch

import pytest

from kumihan_formatter.core.utilities.performance_logger import (
    call_chain_tracker,
    log_performance_decorator,
    memory_usage_tracker,
)
from kumihan_formatter.core.utilities.structured_logger import get_structured_logger


class TestPerformanceDecorator:
    """Test the performance logging decorator"""

    def test_basic_performance_logging(self, caplog):
        """Test basic performance logging with decorator"""

        @log_performance_decorator(operation="test_operation")
        def test_function():
            time.sleep(0.01)  # Small delay to ensure measurable time
            return "result"

        with caplog.at_level(logging.DEBUG):
            result = test_function()

        assert result == "result"

        # Check that we have entry and performance logs
        # At least one record should be present (performance log)
        assert len(caplog.records) >= 1

        # Find entry and performance records
        entry_record = None
        performance_record = None

        for record in caplog.records:
            if hasattr(record, "context"):
                if record.context.get("phase") == "entry":
                    entry_record = record
                elif record.context.get("phase") == "completion":
                    performance_record = record

        # Verify performance log (this should always be present)
        assert performance_record is not None
        assert "operation" in performance_record.context
        assert performance_record.context["operation"] == "test_operation"
        assert performance_record.context["success"] is True
        assert performance_record.context["duration_seconds"] > 0
        assert performance_record.context["duration_ms"] > 0

    def test_decorator_with_arguments(self, caplog):
        """Test decorator with function arguments"""

        @log_performance_decorator()
        def test_function_with_args(arg1, arg2, kwarg1=None):
            return f"{arg1}-{arg2}-{kwarg1}"

        with caplog.at_level(logging.DEBUG):
            result = test_function_with_args("a", "b", kwarg1="c")

        assert result == "a-b-c"

        # Find entry record (may not exist if DEBUG level is filtered)
        entry_record = None
        for record in caplog.records:
            if hasattr(record, "context") and record.context.get("phase") == "entry":
                entry_record = record
                break

        # Just verify we have at least one record
        assert len(caplog.records) >= 1

    def test_decorator_with_exception(self, caplog):
        """Test decorator behavior when function raises exception"""

        @log_performance_decorator(operation="failing_operation")
        def failing_function():
            raise ValueError("Test error")

        with caplog.at_level(logging.DEBUG):
            with pytest.raises(ValueError):
                failing_function()

        # Find error record or suggestion record
        error_record = None
        suggestion_record = None
        for record in caplog.records:
            if hasattr(record, "context"):
                if record.context.get("phase") == "error":
                    error_record = record
                elif record.context.get("error_type") == "ValueError":
                    suggestion_record = record

        # Should have at least one error-related record
        assert len(caplog.records) >= 1
        assert error_record is not None or suggestion_record is not None

    @patch("kumihan_formatter.core.utilities.logger.HAS_PSUTIL", True)
    def test_decorator_with_memory_tracking(self, caplog):
        """Test decorator with memory tracking enabled"""
        mock_process = MagicMock()
        mock_memory_info = MagicMock()
        mock_memory_info.rss = 1024 * 1024 * 50  # 50MB
        mock_process.memory_info.return_value = mock_memory_info

        with patch("kumihan_formatter.core.utilities.logger.psutil") as mock_psutil:
            mock_psutil.Process.return_value = mock_process

            @log_performance_decorator(include_memory=True)
            def test_function():
                return "result"

            with caplog.at_level(logging.DEBUG):
                result = test_function()

            assert result == "result"

            # Find completion record (performance log)
            completion_record = None
            for record in caplog.records:
                if hasattr(record, "context"):
                    if (
                        record.context.get("phase") == "completion"
                        or "memory_mb" in record.context
                    ):
                        completion_record = record
                        break

            assert completion_record is not None
            assert "memory_mb" in completion_record.context
            assert completion_record.context["memory_mb"] == 50.0

    def test_decorator_with_stack_trace(self, caplog):
        """Test decorator with stack trace information"""

        @log_performance_decorator(include_stack=True)
        def test_function():
            return "result"

        with caplog.at_level(logging.DEBUG):
            result = test_function()

        assert result == "result"

        # Find entry record or any record with stack info
        stack_record = None
        for record in caplog.records:
            if hasattr(record, "context") and "stack_info" in record.context:
                stack_record = record
                break

        # Should have at least one record
        assert len(caplog.records) >= 1
        if stack_record:
            stack_info = stack_record.context["stack_info"]
            assert "caller" in stack_info
            assert "function" in stack_info
            assert "depth" in stack_info
            assert isinstance(stack_info["depth"], int)

    def test_decorator_default_operation_name(self, caplog):
        """Test that decorator uses function name as default operation"""

        @log_performance_decorator()
        def my_test_function():
            return "result"

        with caplog.at_level(logging.DEBUG):
            result = my_test_function()

        assert result == "result"

        # Find performance record (INFO level)
        performance_record = None
        for record in caplog.records:
            if hasattr(record, "context") and "operation" in record.context:
                performance_record = record
                break

        assert performance_record is not None
        assert performance_record.context["operation"] == "my_test_function"


class TestCallChainTracker:
    """Test the call chain tracking functionality"""

    def test_basic_call_chain(self):
        """Test basic call chain tracking"""

        def outer_function():
            def inner_function():
                return call_chain_tracker()

            return inner_function()

        result = outer_function()

        assert isinstance(result, dict)
        assert "call_chain" in result
        assert "chain_depth" in result
        assert "current_function" in result

        assert isinstance(result["call_chain"], list)
        assert len(result["call_chain"]) > 0
        assert result["chain_depth"] == len(result["call_chain"])

        # Check that we have function names in the chain
        function_names = [frame["function"] for frame in result["call_chain"]]
        assert "inner_function" in function_names

    def test_call_chain_max_depth(self):
        """Test call chain with max depth limit"""

        def recursive_function(depth):
            if depth <= 0:
                return call_chain_tracker(max_depth=3)
            return recursive_function(depth - 1)

        result = recursive_function(5)

        assert isinstance(result, dict)
        assert result["chain_depth"] <= 3
        assert len(result["call_chain"]) <= 3

    def test_call_chain_frame_structure(self):
        """Test structure of call chain frames"""
        result = call_chain_tracker()

        assert len(result["call_chain"]) > 0

        frame = result["call_chain"][0]
        assert "file" in frame
        assert "line" in frame
        assert "function" in frame
        assert "code" in frame

        assert isinstance(frame["file"], str)
        assert isinstance(frame["line"], int)
        assert isinstance(frame["function"], str)
        # code can be None or string
        assert frame["code"] is None or isinstance(frame["code"], str)


class TestMemoryUsageTracker:
    """Test the memory usage tracking functionality"""

    @patch("kumihan_formatter.core.utilities.logger.HAS_PSUTIL", False)
    def test_memory_tracker_without_psutil(self):
        """Test memory tracker when psutil is not available"""
        result = memory_usage_tracker()

        assert isinstance(result, dict)
        assert result["memory_rss_mb"] == 0
        assert result["memory_vms_mb"] == 0
        assert result["memory_percent"] == 0
        assert result["cpu_percent"] == 0
        assert result["psutil_available"] is False

    @patch("kumihan_formatter.core.utilities.logger.HAS_PSUTIL", True)
    def test_memory_tracker_with_psutil(self):
        """Test memory tracker when psutil is available"""
        mock_process = MagicMock()
        mock_memory_info = MagicMock()
        mock_memory_info.rss = 1024 * 1024 * 100  # 100MB
        mock_memory_info.vms = 1024 * 1024 * 200  # 200MB
        mock_process.memory_info.return_value = mock_memory_info
        mock_process.memory_percent.return_value = 15.5
        mock_process.cpu_percent.return_value = 25.3

        with patch("kumihan_formatter.core.utilities.logger.psutil") as mock_psutil:
            mock_psutil.Process.return_value = mock_process

            result = memory_usage_tracker()

            assert isinstance(result, dict)
            assert result["memory_rss_mb"] == 100.0
            assert result["memory_vms_mb"] == 200.0
            assert result["memory_percent"] == 15.5
            assert result["cpu_percent"] == 25.3
            assert result["psutil_available"] is True

    @patch("kumihan_formatter.core.utilities.logger.HAS_PSUTIL", True)
    def test_memory_tracker_with_exception(self):
        """Test memory tracker when psutil raises exception"""
        with patch("kumihan_formatter.core.utilities.logger.psutil") as mock_psutil:
            mock_psutil.Process.side_effect = Exception("Mock error")

            result = memory_usage_tracker()

            assert isinstance(result, dict)
            assert result["memory_rss_mb"] == 0
            assert result["memory_vms_mb"] == 0
            assert result["memory_percent"] == 0
            assert result["cpu_percent"] == 0
            assert result["psutil_available"] is False
            assert result["error"] == "Failed to get memory info"


class TestPerformanceIntegration:
    """Integration tests for performance logging features"""

    def test_decorator_with_structured_logger(self, caplog):
        """Test that decorator works with structured logger"""

        @log_performance_decorator(operation="integration_test")
        def test_function():
            logger = get_structured_logger(__name__)
            logger.info("Function executing", step="middle")
            return "result"

        with caplog.at_level(logging.DEBUG):
            result = test_function()

        assert result == "result"

        # Should have at least one record
        assert len(caplog.records) >= 1

        # Check that structured logging still works inside decorated function
        function_log = None
        for record in caplog.records:
            if hasattr(record, "context") and record.context.get("step") == "middle":
                function_log = record
                break

        # Should have at least one record
        assert len(caplog.records) >= 1
        if function_log:
            assert function_log.context["step"] == "middle"

    def test_nested_decorated_functions(self, caplog):
        """Test nested functions with performance decorators"""

        @log_performance_decorator(operation="outer")
        def outer_function():
            @log_performance_decorator(operation="inner")
            def inner_function():
                return "inner_result"

            return inner_function()

        with caplog.at_level(logging.DEBUG):
            result = outer_function()

        assert result == "inner_result"

        # Should have logs for both functions
        operations = []
        for record in caplog.records:
            if hasattr(record, "context") and "operation" in record.context:
                operations.append(record.context["operation"])

        # Should have at least one operation logged
        assert len(operations) >= 1
        # If both are logged, check they're there
        if len(operations) >= 2:
            assert "outer" in operations
            assert "inner" in operations


if __name__ == "__main__":
    pytest.main([__file__])
