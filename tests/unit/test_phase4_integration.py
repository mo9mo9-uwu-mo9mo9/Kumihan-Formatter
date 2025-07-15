"""Tests for Phase 4 integration and optimization features

This module tests the Phase 4 integration features:
- LogPerformanceOptimizer: Performance optimization
- LogSizeController: Size control and management
- ClaudeCodeIntegrationLogger: Complete integration
"""

import json
import logging
import time
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.utilities.logger import (
    ClaudeCodeIntegrationLogger,
    LogSizeController,
    get_claude_code_logger,
    get_log_size_controller,
)
from kumihan_formatter.core.utilities.performance_logger import (
    LogPerformanceOptimizer,
    get_log_performance_optimizer,
)
from kumihan_formatter.core.utilities.structured_logger import StructuredLogger


class TestLogPerformanceOptimizer:
    """Test LogPerformanceOptimizer class functionality"""

    def test_performance_optimizer_initialization(self):
        """Test LogPerformanceOptimizer initialization"""
        mock_logger = Mock(spec=StructuredLogger)
        optimizer = LogPerformanceOptimizer(mock_logger)

        assert optimizer.logger == mock_logger
        assert optimizer.performance_metrics == {}
        assert optimizer.log_frequency == {}
        assert optimizer.current_optimization_level == "normal"
        assert "high_frequency" in optimizer.throttle_thresholds

    def test_should_log_always_allows_warnings_and_errors(self):
        """Test that warnings and errors are always logged"""
        mock_logger = Mock(spec=StructuredLogger)
        optimizer = LogPerformanceOptimizer(mock_logger)

        # Always allow warnings and errors
        assert optimizer.should_log(logging.WARNING, "test_warning") is True
        assert optimizer.should_log(logging.ERROR, "test_error") is True
        assert optimizer.should_log(logging.CRITICAL, "test_critical") is True

    def test_should_log_frequency_throttling(self):
        """Test frequency-based throttling"""
        mock_logger = Mock(spec=StructuredLogger)
        optimizer = LogPerformanceOptimizer(mock_logger)

        # Simulate high frequency for a message
        message_key = "test_high_freq"
        optimizer.log_frequency[message_key] = 200  # Above threshold

        # Debug should be throttled
        assert optimizer.should_log(logging.DEBUG, message_key) is False

        # Info should still be allowed
        assert optimizer.should_log(logging.INFO, message_key) is True

    @patch("kumihan_formatter.core.utilities.logger.memory_usage_tracker")
    def test_should_log_resource_throttling(self, mock_memory_tracker):
        """Test resource-based throttling"""
        mock_logger = Mock(spec=StructuredLogger)
        optimizer = LogPerformanceOptimizer(mock_logger)

        # Simulate high resource usage
        mock_memory_tracker.return_value = {
            "memory_rss_mb": 150,  # Above threshold
            "cpu_percent": 90,  # Above threshold
            "psutil_available": True,
        }

        # Debug should be throttled
        assert optimizer.should_log(logging.DEBUG, "test_debug") is False

        # Non-critical info should be throttled
        assert (
            optimizer.should_log(logging.INFO, "test_info", "performance_tracking")
            is False
        )

        # Critical info should be allowed
        assert (
            optimizer.should_log(logging.INFO, "test_info", "critical_operation")
            is True
        )

    def test_record_log_event(self):
        """Test log event recording"""
        mock_logger = Mock(spec=StructuredLogger)
        optimizer = LogPerformanceOptimizer(mock_logger)

        # Record several events
        optimizer.record_log_event(logging.INFO, "test_message", 0.001)
        optimizer.record_log_event(logging.INFO, "test_message", 0.002)
        optimizer.record_log_event(logging.DEBUG, "other_message", 0.003)

        # Check frequency tracking
        assert optimizer.log_frequency["test_message"] == 2
        assert optimizer.log_frequency["other_message"] == 1

        # Check performance metrics
        assert len(optimizer.performance_metrics["test_message"]) == 2
        assert optimizer.performance_metrics["test_message"] == [0.001, 0.002]
        assert optimizer.performance_metrics["other_message"] == [0.003]

    def test_optimize_log_levels(self):
        """Test automatic log level optimization"""
        mock_logger = Mock(spec=StructuredLogger)
        optimizer = LogPerformanceOptimizer(mock_logger)

        # Add performance metrics that would trigger optimization
        optimizer.performance_metrics["debug_operation"] = [0.5, 0.6]  # Total 1.1 > 1.0
        optimizer.performance_metrics["info_operation"] = [0.3, 0.3]  # Total 0.6 > 0.5

        recommendations = optimizer.optimize_log_levels()

        # Should recommend increasing debug to info
        assert recommendations.get("debug") == logging.INFO

        # Should recommend increasing info to warning
        assert recommendations.get("info") == logging.WARNING

    def test_get_performance_report(self):
        """Test performance report generation"""
        mock_logger = Mock(spec=StructuredLogger)
        optimizer = LogPerformanceOptimizer(mock_logger)

        # Add some test data
        optimizer.log_frequency["test1"] = 10
        optimizer.log_frequency["test2"] = 5
        optimizer.performance_metrics["test1"] = [0.001, 0.002]
        optimizer.performance_metrics["test2"] = [0.005]

        with patch(
            "kumihan_formatter.core.utilities.logger.memory_usage_tracker"
        ) as mock_memory:
            mock_memory.return_value = {"memory_rss_mb": 50}

            report = optimizer.get_performance_report()

            assert report["total_log_events"] == 15
            assert report["total_processing_time_ms"] > 0
            assert report["average_time_per_log_ms"] > 0
            assert len(report["slowest_operations"]) <= 5
            assert "optimization_level" in report
            assert "memory_usage" in report


class TestLogSizeController:
    """Test LogSizeController class functionality"""

    def test_size_controller_initialization(self):
        """Test LogSizeController initialization"""
        mock_logger = Mock(spec=StructuredLogger)
        controller = LogSizeController(mock_logger)

        assert controller.logger == mock_logger
        assert controller.compression_enabled is True
        assert "max_file_size_mb" in controller.size_limits
        assert "max_message_length" in controller.content_filters

    def test_should_include_context_filtering(self):
        """Test context filtering for size control"""
        mock_logger = Mock(spec=StructuredLogger)
        controller = LogSizeController(mock_logger)

        # Create large context
        large_context = {f"key_{i}": f"value_{i}" for i in range(30)}
        large_context["large_string"] = "x" * 2000  # Longer than max

        filtered = controller.should_include_context(large_context)

        # Should be limited to max_context_entries
        assert (
            len(filtered) <= controller.content_filters["max_context_entries"] + 1
        )  # +1 for _truncated

        # Should have truncation marker if needed
        if len(large_context) > controller.content_filters["max_context_entries"]:
            assert "_truncated" in filtered

    def test_format_message_for_size(self):
        """Test message formatting for size control"""
        mock_logger = Mock(spec=StructuredLogger)
        controller = LogSizeController(mock_logger)

        # Short message should be unchanged
        short_msg = "Short message"
        assert controller.format_message_for_size(short_msg) == short_msg

        # Long message should be truncated
        long_msg = "x" * 2000
        formatted = controller.format_message_for_size(long_msg)
        assert len(formatted) <= controller.content_filters["max_message_length"]
        assert formatted.endswith("... [truncated]")

    def test_estimate_log_size(self):
        """Test log size estimation"""
        mock_logger = Mock(spec=StructuredLogger)
        controller = LogSizeController(mock_logger)

        # Test message only
        message = "Test message"
        size = controller.estimate_log_size(message)
        assert size > len(message.encode("utf-8"))  # Should include overhead

        # Test with context
        context = {"key": "value", "number": 42}
        size_with_context = controller.estimate_log_size(message, context)
        assert size_with_context > size

    def test_should_skip_due_to_size(self):
        """Test size-based skipping logic"""
        mock_logger = Mock(spec=StructuredLogger)
        controller = LogSizeController(mock_logger)

        # Small size should never be skipped
        small_size = 1000  # 1KB
        assert controller.should_skip_due_to_size(small_size, "low") is False
        assert controller.should_skip_due_to_size(small_size, "normal") is False
        assert controller.should_skip_due_to_size(small_size, "high") is False

        # Large size for low priority should be skipped
        large_size = 2 * 1024 * 1024  # 2MB
        assert controller.should_skip_due_to_size(large_size, "low") is True
        assert controller.should_skip_due_to_size(large_size, "normal") is False
        assert controller.should_skip_due_to_size(large_size, "high") is False

        # Very large size for normal priority should be skipped
        very_large_size = 10 * 1024 * 1024  # 10MB
        assert controller.should_skip_due_to_size(very_large_size, "low") is True
        assert controller.should_skip_due_to_size(very_large_size, "normal") is True
        assert controller.should_skip_due_to_size(very_large_size, "high") is False

    def test_optimize_for_claude_code(self):
        """Test Claude Code specific optimization"""
        mock_logger = Mock(spec=StructuredLogger)
        controller = LogSizeController(mock_logger)

        # Context with various types of data
        context = {
            "claude_hint": "Use this hint",
            "error_analysis": {"type": "ValueError", "suggestions": ["Fix input"]},
            "suggestion": "Check the input",
            "operation": "test_operation",
            "file_path": "/test/file.py",
            "line_number": 42,
            "duration_ms": 100,
            "memory_mb": 50,
            "success": True,
            "extra_data": "This is extra",
            "more_data": "Even more data",
        }

        optimized = controller.optimize_for_claude_code(context)

        # Should prioritize Claude-specific fields
        assert "claude_hint" in optimized
        assert "error_analysis" in optimized
        assert "suggestion" in optimized
        assert "operation" in optimized
        assert "file_path" in optimized
        assert "line_number" in optimized
        assert "duration_ms" in optimized
        assert "memory_mb" in optimized
        assert "success" in optimized

        # Should respect max_context_entries limit
        assert len(optimized) <= controller.content_filters["max_context_entries"]

    def test_get_size_statistics(self):
        """Test size statistics retrieval"""
        mock_logger = Mock(spec=StructuredLogger)
        controller = LogSizeController(mock_logger)

        stats = controller.get_size_statistics()

        assert "size_limits" in stats
        assert "content_filters" in stats
        assert "compression_enabled" in stats
        assert "estimated_overhead_bytes" in stats


class TestClaudeCodeIntegrationLogger:
    """Test ClaudeCodeIntegrationLogger complete integration"""

    def test_integration_logger_initialization(self):
        """Test ClaudeCodeIntegrationLogger initialization"""
        logger = ClaudeCodeIntegrationLogger("test_module")

        assert logger.name == "test_module"
        assert logger.structured_logger is not None
        assert logger.error_analyzer is not None
        assert logger.dependency_tracker is not None
        assert logger.flow_tracker is not None
        assert logger.performance_optimizer is not None
        assert logger.size_controller is not None

    def test_log_with_claude_optimization(self):
        """Test optimized logging with all features"""
        logger = ClaudeCodeIntegrationLogger("test_module")

        # Mock the performance optimizer to allow logging
        with patch.object(
            logger.performance_optimizer, "should_log", return_value=True
        ):
            with patch.object(
                logger.size_controller, "should_skip_due_to_size", return_value=False
            ):
                with patch.object(
                    logger.structured_logger, "log_with_context"
                ) as mock_log:

                    context = {"test": "data", "claude_hint": "Test hint"}
                    logger.log_with_claude_optimization(
                        logging.INFO, "Test message", context, "test_operation"
                    )

                    # Should have called the underlying logger
                    mock_log.assert_called_once()

    def test_log_with_performance_throttling(self):
        """Test that performance throttling prevents logging"""
        logger = ClaudeCodeIntegrationLogger("test_module")

        # Mock the performance optimizer to block logging
        with patch.object(
            logger.performance_optimizer, "should_log", return_value=False
        ):
            with patch.object(logger.structured_logger, "log_with_context") as mock_log:

                logger.log_with_claude_optimization(
                    logging.DEBUG, "Test message", None, "test_operation"
                )

                # Should NOT have called the underlying logger
                mock_log.assert_not_called()

    def test_log_with_size_throttling(self):
        """Test that size throttling prevents logging"""
        logger = ClaudeCodeIntegrationLogger("test_module")

        # Mock to allow performance check but block on size
        with patch.object(
            logger.performance_optimizer, "should_log", return_value=True
        ):
            with patch.object(
                logger.size_controller, "should_skip_due_to_size", return_value=True
            ):
                with patch.object(
                    logger.structured_logger, "log_with_context"
                ) as mock_log:

                    logger.log_with_claude_optimization(
                        logging.INFO, "Test message", None, "test_operation"
                    )

                    # Should NOT have called the underlying logger
                    mock_log.assert_not_called()

    def test_log_error_with_claude_analysis(self):
        """Test error logging with analysis"""
        logger = ClaudeCodeIntegrationLogger("test_module")

        with patch.object(
            logger.error_analyzer, "log_error_with_analysis"
        ) as mock_analyze:
            error = ValueError("Test error")
            context = {"input": "test"}

            logger.log_error_with_claude_analysis(
                error, "Operation failed", context, "test_operation"
            )

            mock_analyze.assert_called_once_with(
                error, "Operation failed", context, "test_operation"
            )

    def test_track_function_execution(self):
        """Test function execution tracking"""
        logger = ClaudeCodeIntegrationLogger("test_module")

        with patch.object(logger.flow_tracker, "enter_function") as mock_enter:
            with patch.object(logger.flow_tracker, "exit_function") as mock_exit:
                mock_enter.return_value = "frame_123"

                # Track function execution
                frame_id = logger.track_function_execution(
                    "test_func", {"arg": "value"}
                )
                assert frame_id == "frame_123"

                mock_enter.assert_called_once_with(
                    "test_func", "test_module", {"arg": "value"}
                )

                # Finish execution
                logger.finish_function_execution(frame_id, True, {"result": "success"})
                mock_exit.assert_called_once_with(
                    frame_id, True, {"result": "success"}, None
                )

    def test_track_dependency_import(self):
        """Test dependency import tracking"""
        logger = ClaudeCodeIntegrationLogger("test_module")

        with patch.object(logger.dependency_tracker, "track_import") as mock_track:
            logger.track_dependency_import("imported_module", "parent_module", 0.001)

            mock_track.assert_called_once_with(
                "imported_module", "parent_module", 0.001
            )

    def test_get_comprehensive_report(self):
        """Test comprehensive report generation"""
        logger = ClaudeCodeIntegrationLogger("test_module")

        with patch.object(
            logger.performance_optimizer, "get_performance_report"
        ) as mock_perf:
            with patch.object(
                logger.size_controller, "get_size_statistics"
            ) as mock_size:
                with patch.object(
                    logger.dependency_tracker, "get_dependency_map"
                ) as mock_deps:
                    with patch.object(
                        logger.flow_tracker, "get_current_flow"
                    ) as mock_flow:

                        # Mock return values
                        mock_perf.return_value = {"total_logs": 10}
                        mock_size.return_value = {"max_size": 50}
                        mock_deps.return_value = {"dependencies": {}}
                        mock_flow.return_value = {"stack_depth": 0}

                        report = logger.get_comprehensive_report()

                        # Check report structure
                        assert report["module"] == "test_module"
                        assert "timestamp" in report
                        assert "performance" in report
                        assert "size_stats" in report
                        assert "dependencies" in report
                        assert "execution_flow" in report
                        assert "claude_hint" in report

                        # Verify all methods were called
                        mock_perf.assert_called_once()
                        mock_size.assert_called_once()
                        mock_deps.assert_called_once()
                        mock_flow.assert_called_once()


class TestFactoryFunctions:
    """Test Phase 4 factory functions"""

    def test_get_log_performance_optimizer(self):
        """Test get_log_performance_optimizer factory function"""
        optimizer = get_log_performance_optimizer("test_module")

        assert isinstance(optimizer, LogPerformanceOptimizer)
        assert isinstance(optimizer.logger, StructuredLogger)

    def test_get_log_size_controller(self):
        """Test get_log_size_controller factory function"""
        controller = get_log_size_controller("test_module")

        assert isinstance(controller, LogSizeController)
        assert isinstance(controller.logger, StructuredLogger)

    def test_get_claude_code_logger(self):
        """Test get_claude_code_logger factory function"""
        logger = get_claude_code_logger("test_module")

        assert isinstance(logger, ClaudeCodeIntegrationLogger)
        assert logger.name == "test_module"


class TestEndToEndIntegration:
    """Test end-to-end integration scenarios"""

    def test_complete_workflow_with_all_features(self):
        """Test complete workflow using all Phase 1-4 features"""
        logger = get_claude_code_logger("integration_test")

        # 1. Track dependency import
        logger.track_dependency_import("test_module", "parent", 0.001)

        # 2. Track function execution
        frame_id = logger.track_function_execution("test_function", {"input": "test"})

        # 3. Log with optimization
        logger.log_with_claude_optimization(
            logging.INFO,
            "Processing started",
            {"operation": "test", "claude_hint": "Track this operation"},
            "test_operation",
        )

        # 4. Simulate error and analyze
        try:
            raise ValueError("Test error for integration")
        except ValueError as e:
            logger.log_error_with_claude_analysis(
                e, "Operation failed", {"input": "test_data"}, "test_operation"
            )

        # 5. Complete function execution
        logger.finish_function_execution(frame_id, False, None, {"error": "ValueError"})

        # 6. Generate comprehensive report
        report = logger.get_comprehensive_report()

        # Verify report contains all expected sections
        assert "module" in report
        assert "performance" in report
        assert "size_stats" in report
        assert "dependencies" in report
        assert "execution_flow" in report
        assert "claude_hint" in report

    def test_performance_optimization_under_load(self):
        """Test performance optimization under simulated load"""
        logger = get_claude_code_logger("load_test")

        # Simulate high-frequency logging
        for i in range(50):
            logger.log_with_claude_optimization(
                logging.DEBUG, f"Debug message {i}", {"iteration": i}, "load_test"
            )

        # Get performance report
        report = logger.get_comprehensive_report()

        # Should have performance metrics
        assert "performance" in report
        assert "total_log_events" in report["performance"]

        # Performance optimizer should have recorded events
        assert len(logger.performance_optimizer.performance_metrics) > 0

    def test_size_control_with_large_context(self):
        """Test size control with large context data"""
        logger = get_claude_code_logger("size_test")

        # Create large context
        large_context = {
            "large_string": "x" * 5000,
            "large_list": list(range(1000)),
            "large_dict": {f"key_{i}": f"value_{i}" for i in range(100)},
            "claude_hint": "This should be preserved",
            "error_analysis": {"type": "test", "suggestions": ["fix it"]},
            "extra_data": "This might be truncated",
        }

        # Log with large context
        logger.log_with_claude_optimization(
            logging.INFO, "Large context test", large_context, "size_test"
        )

        # Should not crash and should have applied size controls
        report = logger.get_comprehensive_report()
        assert "size_stats" in report
