"""Tests for performance logging functionality"""

import logging
import time
from unittest.mock import MagicMock, patch

import pytest

from kumihan_formatter.core.utilities.performance_logger import (
    LogPerformanceOptimizer,
    call_chain_tracker,
    get_log_performance_optimizer,
    log_performance_decorator,
    memory_usage_tracker,
)


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

        # Check that we have at least one performance log record
        assert len(caplog.records) >= 1

        # Find performance record
        performance_record = None
        for record in caplog.records:
            if hasattr(record, "context"):
                if record.context.get("operation") == "test_operation":
                    performance_record = record
                    break

        # Verify performance log exists
        assert performance_record is not None
        assert "operation" in performance_record.context
        assert performance_record.context["operation"] == "test_operation"

    def test_decorator_with_arguments(self, caplog):
        """Test decorator with function arguments"""

        @log_performance_decorator()
        def test_function_with_args(arg1, arg2, kwarg1=None):
            return f"{arg1}-{arg2}-{kwarg1}"

        with caplog.at_level(logging.DEBUG):
            result = test_function_with_args("a", "b", kwarg1="c")

        assert result == "a-b-c"
        assert len(caplog.records) >= 1

    def test_decorator_with_exception(self, caplog):
        """Test decorator behavior when function raises exception"""

        @log_performance_decorator(operation="failing_operation")
        def failing_function():
            raise ValueError("Test error")

        with caplog.at_level(logging.DEBUG):
            with pytest.raises(ValueError):
                failing_function()

        # Should have at least one error-related record
        assert len(caplog.records) >= 1

        # Find error record
        error_record = None
        for record in caplog.records:
            if hasattr(record, "context"):
                if record.context.get("error_type") == "ValueError":
                    error_record = record
                    break

        assert error_record is not None

    @patch("kumihan_formatter.core.utilities.performance_logger.HAS_PSUTIL", True)
    def test_decorator_with_memory_tracking(self, caplog):
        """Test decorator with memory tracking enabled"""
        mock_process = MagicMock()
        mock_memory_info = MagicMock()
        mock_memory_info.rss = 1024 * 1024 * 50  # 50MB
        mock_process.memory_info.return_value = mock_memory_info

        with patch(
            "kumihan_formatter.core.utilities.performance_logger.psutil"
        ) as mock_psutil:
            mock_psutil.Process.return_value = mock_process

            @log_performance_decorator(include_memory=True)
            def test_function():
                return "result"

            with caplog.at_level(logging.DEBUG):
                result = test_function()

            assert result == "result"
            assert len(caplog.records) >= 1

    def test_decorator_with_stack_trace(self, caplog):
        """Test decorator with stack trace information"""

        @log_performance_decorator(include_stack=True)
        def test_function():
            return "result"

        with caplog.at_level(logging.DEBUG):
            result = test_function()

        assert result == "result"
        assert len(caplog.records) >= 1

        # Find record with stack info
        stack_record = None
        for record in caplog.records:
            if hasattr(record, "context") and "stack_info" in record.context:
                stack_record = record
                break

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
        assert len(caplog.records) >= 1

        # Find performance record
        performance_record = None
        for record in caplog.records:
            if hasattr(record, "context") and "operation" in record.context:
                performance_record = record
                break

        if performance_record:
            assert performance_record.context["operation"] == "my_test_function"


class TestCallChainTracker:
    """Test the call chain tracker"""

    def test_call_chain_tracker_basic(self):
        """Test basic call chain tracking"""

        def test_function():
            return call_chain_tracker(max_depth=5)

        chain_info = test_function()

        assert "call_chain" in chain_info
        assert "chain_depth" in chain_info
        assert "current_function" in chain_info
        assert isinstance(chain_info["call_chain"], list)
        assert chain_info["chain_depth"] >= 0

    def test_call_chain_tracker_depth_limit(self):
        """Test call chain tracker with depth limit"""

        def level_3():
            return call_chain_tracker(max_depth=2)

        def level_2():
            return level_3()

        def level_1():
            return level_2()

        chain_info = level_1()

        assert len(chain_info["call_chain"]) <= 2
        assert chain_info["chain_depth"] <= 2

    def test_call_chain_tracker_frame_info(self):
        """Test call chain tracker frame information"""
        chain_info = call_chain_tracker(max_depth=3)

        for frame in chain_info["call_chain"]:
            assert "file" in frame
            assert "line" in frame
            assert "function" in frame
            assert isinstance(frame["line"], int)


class TestMemoryUsageTracker:
    """Test the memory usage tracker"""

    @patch("kumihan_formatter.core.utilities.performance_logger.HAS_PSUTIL", False)
    def test_memory_usage_tracker_no_psutil(self):
        """Test memory usage tracker without psutil"""
        usage = memory_usage_tracker()

        assert usage["memory_rss_mb"] == 0
        assert usage["memory_vms_mb"] == 0
        assert usage["memory_percent"] == 0
        assert usage["cpu_percent"] == 0
        assert usage["psutil_available"] == False

    @patch("kumihan_formatter.core.utilities.performance_logger.HAS_PSUTIL", True)
    def test_memory_usage_tracker_with_psutil(self):
        """Test memory usage tracker with psutil"""
        mock_process = MagicMock()
        mock_memory_info = MagicMock()
        mock_memory_info.rss = 1024 * 1024 * 100  # 100MB
        mock_memory_info.vms = 1024 * 1024 * 200  # 200MB
        mock_process.memory_info.return_value = mock_memory_info
        mock_process.memory_percent.return_value = 5.0
        mock_process.cpu_percent.return_value = 10.0

        with patch(
            "kumihan_formatter.core.utilities.performance_logger.psutil"
        ) as mock_psutil:
            mock_psutil.Process.return_value = mock_process

            usage = memory_usage_tracker()

            assert usage["memory_rss_mb"] == 100.0
            assert usage["memory_vms_mb"] == 200.0
            assert usage["memory_percent"] == 5.0
            assert usage["cpu_percent"] == 10.0
            assert usage["psutil_available"] == True

    @patch("kumihan_formatter.core.utilities.performance_logger.HAS_PSUTIL", True)
    def test_memory_usage_tracker_exception(self):
        """Test memory usage tracker with exception"""
        with patch(
            "kumihan_formatter.core.utilities.performance_logger.psutil"
        ) as mock_psutil:
            mock_psutil.Process.side_effect = Exception("Test error")

            usage = memory_usage_tracker()

            assert usage["memory_rss_mb"] == 0
            assert usage["memory_vms_mb"] == 0
            assert usage["memory_percent"] == 0
            assert usage["cpu_percent"] == 0
            assert usage["psutil_available"] == False
            assert "error" in usage


class TestLogPerformanceOptimizer:
    """Test the LogPerformanceOptimizer class"""

    def test_log_performance_optimizer_creation(self):
        """Test creating a log performance optimizer"""
        mock_logger = MagicMock()
        optimizer = LogPerformanceOptimizer(mock_logger)

        assert optimizer.logger == mock_logger
        assert optimizer.performance_metrics == {}
        assert optimizer.log_frequency == {}
        assert optimizer.current_optimization_level == "normal"

    def test_should_log_always_log_errors(self):
        """Test that errors and warnings are always logged"""
        mock_logger = MagicMock()
        optimizer = LogPerformanceOptimizer(mock_logger)

        assert optimizer.should_log(logging.ERROR, "test_error", "test_op") == True
        assert optimizer.should_log(logging.WARNING, "test_warning", "test_op") == True

    def test_should_log_frequency_throttling(self):
        """Test frequency-based log throttling"""
        mock_logger = MagicMock()
        optimizer = LogPerformanceOptimizer(mock_logger)

        # Set high frequency
        optimizer.log_frequency["test_key"] = 150  # Above threshold

        # Debug should be throttled
        assert optimizer.should_log(logging.DEBUG, "test_key", "test_op") == False

        # Info should still pass
        assert optimizer.should_log(logging.INFO, "test_key", "test_op") == True

    def test_record_log_event(self):
        """Test recording log events"""
        mock_logger = MagicMock()
        optimizer = LogPerformanceOptimizer(mock_logger)

        optimizer.record_log_event(logging.INFO, "test_key", 0.1)

        assert "test_key" in optimizer.log_frequency
        assert optimizer.log_frequency["test_key"] == 1
        assert "test_key" in optimizer.performance_metrics
        assert optimizer.performance_metrics["test_key"] == [0.1]

    def test_optimize_log_levels(self):
        """Test log level optimization"""
        mock_logger = MagicMock()
        optimizer = LogPerformanceOptimizer(mock_logger)

        # Add some debug metrics with high overhead
        optimizer.performance_metrics["debug_operation"] = [0.5, 0.6, 0.7]

        recommendations = optimizer.optimize_log_levels()

        assert "debug" in recommendations
        assert recommendations["debug"] == logging.INFO

    def test_performance_report(self):
        """Test performance report generation"""
        mock_logger = MagicMock()
        optimizer = LogPerformanceOptimizer(mock_logger)

        # Add some test data
        optimizer.log_frequency["test_key"] = 10
        optimizer.performance_metrics["test_key"] = [0.1, 0.2, 0.3]

        report = optimizer.get_performance_report()

        assert "total_log_events" in report
        assert "total_processing_time_ms" in report
        assert "average_time_per_log_ms" in report
        assert "slowest_operations" in report
        assert "high_frequency_messages" in report
        assert "optimization_level" in report
        assert "memory_usage" in report

    @patch("kumihan_formatter.core.utilities.performance_logger.memory_usage_tracker")
    def test_is_high_resource_usage(self, mock_memory_tracker):
        """Test high resource usage detection"""
        mock_logger = MagicMock()
        optimizer = LogPerformanceOptimizer(mock_logger)

        # Mock low resource usage
        mock_memory_tracker.return_value = {"memory_rss_mb": 50, "cpu_percent": 30}

        assert optimizer._is_high_resource_usage() == False

        # Mock high resource usage
        mock_memory_tracker.return_value = {
            "memory_rss_mb": 150,  # Above threshold
            "cpu_percent": 30,
        }

        assert optimizer._is_high_resource_usage() == True

    def test_is_non_critical_info(self):
        """Test non-critical info detection"""
        mock_logger = MagicMock()
        optimizer = LogPerformanceOptimizer(mock_logger)

        assert optimizer._is_non_critical_info("performance_tracking") == True
        assert optimizer._is_non_critical_info("debug_tracing") == True
        assert optimizer._is_non_critical_info("important_operation") == False


class TestModuleFunctions:
    """Test module-level functions"""

    def test_get_log_performance_optimizer(self):
        """Test getting log performance optimizer instance"""
        optimizer = get_log_performance_optimizer("test_module")
        assert isinstance(optimizer, LogPerformanceOptimizer)
