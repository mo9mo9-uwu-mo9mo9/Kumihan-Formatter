"""Tests for Phase 3 Claude-specific features

This module tests the Claude Code specific features implemented in Phase 3:
- ErrorAnalyzer: Error analysis support
- DependencyTracker: Module dependency tracking
- ExecutionFlowTracker: Execution flow tracking
"""

import logging
import time
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.utilities.logger import (
    DependencyTracker,
    ErrorAnalyzer,
    ExecutionFlowTracker,
    StructuredLogger,
    get_dependency_tracker,
    get_error_analyzer,
    get_execution_flow_tracker,
)


class TestErrorAnalyzer:
    """Test ErrorAnalyzer class functionality"""

    def test_error_analyzer_initialization(self):
        """Test ErrorAnalyzer initialization"""
        mock_logger = Mock(spec=StructuredLogger)
        analyzer = ErrorAnalyzer(mock_logger)

        assert analyzer.logger == mock_logger
        assert hasattr(analyzer, "ERROR_CATEGORIES")
        assert len(analyzer.ERROR_CATEGORIES) == 5

    def test_categorize_encoding_error(self):
        """Test encoding error categorization"""
        mock_logger = Mock(spec=StructuredLogger)
        analyzer = ErrorAnalyzer(mock_logger)

        # Test encoding error
        error = UnicodeDecodeError("utf-8", b"", 0, 1, "invalid start byte")
        category = analyzer._categorize_error(str(error).lower())

        assert category == "encoding"

    def test_categorize_file_access_error(self):
        """Test file access error categorization"""
        mock_logger = Mock(spec=StructuredLogger)
        analyzer = ErrorAnalyzer(mock_logger)

        # Test file access error
        error = FileNotFoundError("No such file or directory")
        category = analyzer._categorize_error(str(error).lower())

        assert category == "file_access"

    def test_categorize_parsing_error(self):
        """Test parsing error categorization"""
        mock_logger = Mock(spec=StructuredLogger)
        analyzer = ErrorAnalyzer(mock_logger)

        # Test parsing error
        error = SyntaxError("invalid syntax")
        category = analyzer._categorize_error(str(error).lower())

        assert category == "parsing"

    def test_categorize_unknown_error(self):
        """Test unknown error categorization"""
        mock_logger = Mock(spec=StructuredLogger)
        analyzer = ErrorAnalyzer(mock_logger)

        # Test unknown error
        error = RuntimeError("Unknown runtime error")
        category = analyzer._categorize_error(str(error).lower())

        assert category == "unknown"

    def test_generate_generic_suggestions(self):
        """Test generic suggestion generation"""
        mock_logger = Mock(spec=StructuredLogger)
        analyzer = ErrorAnalyzer(mock_logger)

        # Test ValueError suggestions
        suggestions = analyzer._generate_generic_suggestions(
            "ValueError", "invalid literal"
        )
        assert len(suggestions) >= 3
        assert "Validate input values and types" in suggestions

        # Test TypeError suggestions
        suggestions = analyzer._generate_generic_suggestions(
            "TypeError", "unsupported operand"
        )
        assert "Check argument types match expected types" in suggestions

        # Test IndexError suggestions
        suggestions = analyzer._generate_generic_suggestions(
            "IndexError", "list index out of range"
        )
        assert "Verify data structure bounds and keys" in suggestions

    @patch("kumihan_formatter.core.utilities.logger.call_chain_tracker")
    @patch("kumihan_formatter.core.utilities.logger.memory_usage_tracker")
    def test_analyze_error_complete(self, mock_memory_tracker, mock_call_chain):
        """Test complete error analysis"""
        mock_logger = Mock(spec=StructuredLogger)
        analyzer = ErrorAnalyzer(mock_logger)

        # Mock the tracking functions
        mock_call_chain.return_value = {
            "call_chain": [{"function": "test_func", "line": 42}],
            "chain_depth": 1,
        }
        mock_memory_tracker.return_value = {"memory_rss_mb": 50.5, "cpu_percent": 10.2}

        # Test error analysis
        error = ValueError("Test error message")
        context = {"input_file": "test.txt"}

        analysis = analyzer.analyze_error(error, context, "test_operation")

        assert analysis["error_type"] == "ValueError"
        assert analysis["error_message"] == "Test error message"
        assert analysis["operation"] == "test_operation"
        assert analysis["context"] == context
        assert "suggestions" in analysis
        assert "stack_info" in analysis
        assert "memory_info" in analysis
        assert "timestamp" in analysis

    def test_log_error_with_analysis(self):
        """Test error logging with analysis"""
        mock_logger = Mock(spec=StructuredLogger)
        analyzer = ErrorAnalyzer(mock_logger)

        error = ValueError("Test error")
        message = "Operation failed"
        context = {"file": "test.txt"}

        with patch.object(analyzer, "analyze_error") as mock_analyze:
            mock_analyze.return_value = {
                "error_type": "ValueError",
                "suggestions": ["Check input"],
            }

            analyzer.log_error_with_analysis(error, message, context, "test_op")

            mock_analyze.assert_called_once_with(error, context, "test_op")
            mock_logger.log_with_context.assert_called_once()

    def test_log_warning_with_suggestion(self):
        """Test warning logging with suggestion"""
        mock_logger = Mock(spec=StructuredLogger)
        analyzer = ErrorAnalyzer(mock_logger)

        analyzer.log_warning_with_suggestion(
            "Test warning", "Check configuration", "config", extra_info="test"
        )

        mock_logger.log_with_context.assert_called_once_with(
            logging.WARNING,
            "Test warning",
            suggestion="Check configuration",
            category="config",
            claude_hint="Category: config - Apply suggestion to resolve",
            extra_info="test",
        )


class TestDependencyTracker:
    """Test DependencyTracker class functionality"""

    def test_dependency_tracker_initialization(self):
        """Test DependencyTracker initialization"""
        mock_logger = Mock(spec=StructuredLogger)
        tracker = DependencyTracker(mock_logger)

        assert tracker.logger == mock_logger
        assert tracker.dependencies == {}
        assert tracker.load_times == {}
        assert tracker.load_order == []

    def test_track_import_basic(self):
        """Test basic import tracking"""
        mock_logger = Mock(spec=StructuredLogger)
        tracker = DependencyTracker(mock_logger)

        tracker.track_import("test_module", "parent_module", 0.001)

        assert "parent_module" in tracker.dependencies
        assert "test_module" in tracker.dependencies["parent_module"]
        assert tracker.load_times["test_module"] == 0.001
        assert tracker.load_order == ["test_module"]

        # Check logging was called
        mock_logger.debug.assert_called_once()

    def test_track_import_without_parent(self):
        """Test import tracking without parent module"""
        mock_logger = Mock(spec=StructuredLogger)
        tracker = DependencyTracker(mock_logger)

        tracker.track_import("root_module", None, 0.002)

        assert "root_module" not in tracker.dependencies
        assert tracker.load_times["root_module"] == 0.002
        assert tracker.load_order == ["root_module"]

    def test_track_multiple_imports(self):
        """Test tracking multiple imports"""
        mock_logger = Mock(spec=StructuredLogger)
        tracker = DependencyTracker(mock_logger)

        tracker.track_import("module1", "parent", 0.001)
        tracker.track_import("module2", "parent", 0.002)
        tracker.track_import("module3", "module1", 0.003)

        assert len(tracker.dependencies["parent"]) == 2
        assert "module1" in tracker.dependencies["parent"]
        assert "module2" in tracker.dependencies["parent"]
        assert "module3" in tracker.dependencies["module1"]
        assert tracker.load_order == ["module1", "module2", "module3"]

    def test_get_dependency_map(self):
        """Test dependency map generation"""
        mock_logger = Mock(spec=StructuredLogger)
        tracker = DependencyTracker(mock_logger)

        tracker.track_import("module1", "parent", 0.001)
        tracker.track_import("module2", "parent", 0.003)
        tracker.track_import("module3", "module1", 0.002)

        dep_map = tracker.get_dependency_map()

        assert "dependencies" in dep_map
        assert "load_times" in dep_map
        assert "load_order" in dep_map
        assert "total_modules" in dep_map
        assert "slowest_imports" in dep_map

        assert dep_map["total_modules"] == 3
        assert dep_map["slowest_imports"][0] == ("module2", 0.003)

    def test_log_dependency_summary(self):
        """Test dependency summary logging"""
        mock_logger = Mock(spec=StructuredLogger)
        tracker = DependencyTracker(mock_logger)

        tracker.track_import("module1", "parent", 0.001)
        tracker.log_dependency_summary()

        mock_logger.info.assert_called_once()
        args, kwargs = mock_logger.info.call_args
        assert args[0] == "Dependency tracking summary"
        assert "dependency_map" in kwargs
        assert "claude_hint" in kwargs


class TestExecutionFlowTracker:
    """Test ExecutionFlowTracker class functionality"""

    def test_execution_flow_tracker_initialization(self):
        """Test ExecutionFlowTracker initialization"""
        mock_logger = Mock(spec=StructuredLogger)
        tracker = ExecutionFlowTracker(mock_logger)

        assert tracker.logger == mock_logger
        assert tracker.execution_stack == []
        assert tracker.flow_id is not None
        assert isinstance(tracker.flow_id, str)

    def test_enter_function(self):
        """Test function entry tracking"""
        mock_logger = Mock(spec=StructuredLogger)
        tracker = ExecutionFlowTracker(mock_logger)

        args_info = {"arg1": "value1", "arg2": 42}
        frame_id = tracker.enter_function("test_func", "test_module", args_info)

        assert len(tracker.execution_stack) == 1
        assert tracker.execution_stack[0]["function_name"] == "test_func"
        assert tracker.execution_stack[0]["module_name"] == "test_module"
        assert tracker.execution_stack[0]["args_info"] == args_info
        assert tracker.execution_stack[0]["frame_id"] == frame_id
        assert tracker.execution_stack[0]["depth"] == 0

        # Check logging was called
        mock_logger.debug.assert_called_once()

    def test_exit_function(self):
        """Test function exit tracking"""
        mock_logger = Mock(spec=StructuredLogger)
        tracker = ExecutionFlowTracker(mock_logger)

        # Enter function first
        frame_id = tracker.enter_function("test_func", "test_module")

        # Small delay to ensure duration > 0
        time.sleep(0.001)

        # Exit function
        result_info = {"result": "success"}
        tracker.exit_function(frame_id, True, result_info)

        assert len(tracker.execution_stack) == 0

        # Check logging was called twice (enter + exit)
        assert mock_logger.debug.call_count == 1
        assert mock_logger.log_with_context.call_count == 1

    def test_exit_function_with_error(self):
        """Test function exit with error tracking"""
        mock_logger = Mock(spec=StructuredLogger)
        tracker = ExecutionFlowTracker(mock_logger)

        # Enter function first
        frame_id = tracker.enter_function("test_func", "test_module")

        # Exit with error
        error_info = {"error": "Test error", "type": "ValueError"}
        tracker.exit_function(frame_id, False, None, error_info)

        assert len(tracker.execution_stack) == 0

        # Check warning level logging was called for error
        mock_logger.log_with_context.assert_called_once()
        args, kwargs = mock_logger.log_with_context.call_args
        assert args[0] == logging.WARNING

    def test_nested_function_calls(self):
        """Test nested function call tracking"""
        mock_logger = Mock(spec=StructuredLogger)
        tracker = ExecutionFlowTracker(mock_logger)

        # Enter first function
        frame_id1 = tracker.enter_function("func1", "module1")
        assert len(tracker.execution_stack) == 1
        assert tracker.execution_stack[0]["depth"] == 0

        # Enter nested function
        frame_id2 = tracker.enter_function("func2", "module2")
        assert len(tracker.execution_stack) == 2
        assert tracker.execution_stack[1]["depth"] == 1

        # Exit nested function
        tracker.exit_function(frame_id2, True)
        assert len(tracker.execution_stack) == 1

        # Exit first function
        tracker.exit_function(frame_id1, True)
        assert len(tracker.execution_stack) == 0

    def test_get_current_flow(self):
        """Test current flow state retrieval"""
        mock_logger = Mock(spec=StructuredLogger)
        tracker = ExecutionFlowTracker(mock_logger)

        # Test empty flow
        flow = tracker.get_current_flow()
        assert flow["stack_depth"] == 0
        assert flow["total_execution_time"] == 0
        assert flow["current_stack"] == []

        # Test with active functions
        tracker.enter_function("func1", "module1")
        tracker.enter_function("func2", "module2")

        flow = tracker.get_current_flow()
        assert flow["stack_depth"] == 2
        assert flow["total_execution_time"] > 0
        assert len(flow["current_stack"]) == 2
        assert flow["current_stack"][0]["function"] == "func1"
        assert flow["current_stack"][1]["function"] == "func2"


class TestFactoryFunctions:
    """Test factory functions for getting tracker instances"""

    def test_get_error_analyzer(self):
        """Test get_error_analyzer factory function"""
        analyzer = get_error_analyzer("test_module")

        assert isinstance(analyzer, ErrorAnalyzer)
        assert isinstance(analyzer.logger, StructuredLogger)

    def test_get_dependency_tracker(self):
        """Test get_dependency_tracker factory function"""
        tracker = get_dependency_tracker("test_module")

        assert isinstance(tracker, DependencyTracker)
        assert isinstance(tracker.logger, StructuredLogger)

    def test_get_execution_flow_tracker(self):
        """Test get_execution_flow_tracker factory function"""
        tracker = get_execution_flow_tracker("test_module")

        assert isinstance(tracker, ExecutionFlowTracker)
        assert isinstance(tracker.logger, StructuredLogger)


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple features"""

    def test_error_analysis_with_flow_tracking(self):
        """Test error analysis combined with flow tracking"""
        error_analyzer = get_error_analyzer("test_module")
        flow_tracker = get_execution_flow_tracker("test_module")

        # Simulate function execution with error
        frame_id = flow_tracker.enter_function("problematic_func", "test_module")

        try:
            # Simulate error
            raise ValueError("Test error for integration")
        except ValueError as e:
            error_analyzer.log_error_with_analysis(
                e,
                "Function failed during execution",
                {"frame_id": frame_id},
                "test_operation",
            )
            flow_tracker.exit_function(frame_id, False, None, {"error": str(e)})

        # Verify flow is clean
        assert len(flow_tracker.execution_stack) == 0

    def test_dependency_tracking_with_performance(self):
        """Test dependency tracking with performance monitoring"""
        dependency_tracker = get_dependency_tracker("test_module")

        # Simulate module imports with timing
        start_time = time.time()
        time.sleep(0.001)  # Simulate import time
        import_time = time.time() - start_time

        dependency_tracker.track_import("slow_module", "main", import_time)
        dependency_tracker.track_import("fast_module", "main", 0.0001)

        # Get dependency map
        dep_map = dependency_tracker.get_dependency_map()

        # Verify tracking
        assert dep_map["total_modules"] == 2
        assert len(dep_map["slowest_imports"]) == 2
        assert dep_map["slowest_imports"][0][0] == "slow_module"

        # Log summary
        dependency_tracker.log_dependency_summary()
