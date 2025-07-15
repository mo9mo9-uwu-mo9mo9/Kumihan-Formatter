"""Example usage of Issue#472 Claude Code logging features

This example demonstrates how to use the complete Claude Code logging system
implemented in Issue#472 across all phases (1-4).
"""

import logging
import time

from kumihan_formatter.core.utilities.logger import (  # Basic structured logging (Phase 1); Context features (Phase 2); Claude-specific features (Phase 3); Integration and optimization (Phase 4)
    call_chain_tracker,
    get_claude_code_logger,
    get_dependency_tracker,
    get_error_analyzer,
    get_execution_flow_tracker,
    get_structured_logger,
    log_performance_decorator,
    memory_usage_tracker,
)


def demonstrate_phase1_structured_logging():
    """Demonstrate Phase 1: Structured logging with context"""
    print("=== Phase 1: Structured Logging ===")

    logger = get_structured_logger(__name__)

    # Basic structured logging
    logger.info("Processing started", file_path="example.txt", operation="demo")

    # Log with various context types
    logger.debug(
        "Debug information",
        user_id=123,
        session_id="abc123",
        performance_data={"duration": 0.1},
    )

    # Error with suggestion
    logger.error_with_suggestion(
        "File processing failed",
        "Check file permissions and encoding",
        file_path="/invalid/path.txt",
        error_type="FileNotFoundError",
    )

    # Performance logging
    logger.performance("file_conversion", 1.234, size_bytes=1024 * 1024)

    print("✓ Phase 1 logging completed")


def demonstrate_phase2_context_features():
    """Demonstrate Phase 2: Context features"""
    print("\n=== Phase 2: Context Features ===")

    # Performance decorator
    @log_performance_decorator(include_memory=True, include_stack=True)
    def sample_operation(data: str) -> str:
        time.sleep(0.1)  # Simulate work
        return f"Processed: {data}"

    result = sample_operation("test_data")
    print(f"Result: {result}")

    # Call chain tracking
    chain_info = call_chain_tracker(max_depth=5)
    print(f"Call chain: {chain_info['current_function']}")

    # Memory usage tracking
    memory_info = memory_usage_tracker()
    print(f"Memory usage: {memory_info['memory_rss_mb']} MB")

    print("✓ Phase 2 context features completed")


def demonstrate_phase3_claude_features():
    """Demonstrate Phase 3: Claude-specific features"""
    print("\n=== Phase 3: Claude-Specific Features ===")

    # Error analyzer
    error_analyzer = get_error_analyzer(__name__)

    try:
        # Simulate an error
        raise ValueError("Invalid input format")
    except ValueError as e:
        error_analyzer.log_error_with_analysis(
            e,
            "Data validation failed",
            context={"input_data": "invalid_format", "expected": "json"},
            operation="data_validation",
        )

    # Dependency tracker
    dependency_tracker = get_dependency_tracker(__name__)

    # Track some imports
    dependency_tracker.track_import("json", __name__, 0.001)
    dependency_tracker.track_import("time", __name__, 0.0005)
    dependency_tracker.track_import("logging", __name__, 0.002)

    # Get dependency summary
    dependency_tracker.log_dependency_summary()

    # Execution flow tracker
    flow_tracker = get_execution_flow_tracker(__name__)

    # Track function execution
    frame_id = flow_tracker.enter_function("demo_function", __name__, {"arg": "value"})
    time.sleep(0.01)  # Simulate work
    flow_tracker.exit_function(frame_id, True, {"result": "success"})

    print("✓ Phase 3 Claude features completed")


def demonstrate_phase4_integration():
    """Demonstrate Phase 4: Complete integration"""
    print("\n=== Phase 4: Complete Integration ===")

    # Get the complete Claude Code logger
    claude_logger = get_claude_code_logger(__name__)

    # Track dependency import
    claude_logger.track_dependency_import("example_module", __name__, 0.001)

    # Track function execution
    frame_id = claude_logger.track_function_execution(
        "integrated_operation", {"input": "test_data", "options": {"optimize": True}}
    )

    # Log with full optimization
    claude_logger.log_with_claude_optimization(
        logging.INFO,
        "Integrated operation started",
        context={
            "operation": "demo_integration",
            "claude_hint": "This demonstrates full integration",
            "performance_tracking": True,
            "optimization_level": "high",
        },
        operation="integration_demo",
        priority="high",
    )

    # Simulate some work
    time.sleep(0.05)

    # Log error with analysis
    try:
        raise RuntimeError("Simulated integration error")
    except RuntimeError as e:
        claude_logger.log_error_with_claude_analysis(
            e,
            "Integration operation failed",
            context={"step": "data_processing", "retry_count": 1},
            operation="integration_demo",
        )

    # Complete function execution
    claude_logger.finish_function_execution(
        frame_id,
        success=False,
        result_info=None,
        error_info={"error": "RuntimeError", "handled": True},
    )

    # Generate comprehensive report
    report = claude_logger.get_comprehensive_report()
    print(f"Report generated with {len(report)} sections")

    print("✓ Phase 4 integration completed")


def demonstrate_performance_optimization():
    """Demonstrate performance optimization features"""
    print("\n=== Performance Optimization ===")

    claude_logger = get_claude_code_logger(__name__)

    # Simulate high-frequency logging
    for i in range(20):
        claude_logger.log_with_claude_optimization(
            logging.DEBUG,
            f"High frequency message {i}",
            context={"iteration": i, "batch": "performance_test"},
            operation="performance_test",
            priority="low",
        )

    # Get performance report
    report = claude_logger.get_comprehensive_report()
    perf_data = report["performance"]

    print(f"Total log events: {perf_data['total_log_events']}")
    print(f"Average time per log: {perf_data['average_time_per_log_ms']}ms")

    print("✓ Performance optimization demonstrated")


def demonstrate_size_control():
    """Demonstrate size control features"""
    print("\n=== Size Control ===")

    claude_logger = get_claude_code_logger(__name__)

    # Large context that will be optimized
    large_context = {
        "large_string": "x" * 2000,  # Will be truncated
        "large_list": list(range(500)),  # Will be summarized
        "claude_hint": "This should be preserved",
        "error_analysis": {
            "type": "MemoryError",
            "suggestions": ["Reduce data size", "Process in chunks"],
        },
        "operation": "size_control_demo",
        "file_path": "/very/long/path/to/file.txt",
        "line_number": 42,
        "additional_data": {f"key_{i}": f"value_{i}" for i in range(50)},
    }

    # This will be optimized for Claude Code
    claude_logger.log_with_claude_optimization(
        logging.WARNING,
        "Large context demonstration",
        context=large_context,
        operation="size_control_demo",
        priority="normal",
    )

    # Get size statistics
    report = claude_logger.get_comprehensive_report()
    size_stats = report["size_stats"]

    print(f"Max message length: {size_stats['content_filters']['max_message_length']}")
    print(
        f"Max context entries: {size_stats['content_filters']['max_context_entries']}"
    )

    print("✓ Size control demonstrated")


def main():
    """Main demonstration function"""
    print("🚀 Kumihan-Formatter Issue#472 Claude Code Logging Demo")
    print("=" * 60)

    # Enable development logging
    import os

    os.environ["KUMIHAN_DEV_LOG"] = "true"
    os.environ["KUMIHAN_DEV_LOG_JSON"] = "true"

    try:
        demonstrate_phase1_structured_logging()
        demonstrate_phase2_context_features()
        demonstrate_phase3_claude_features()
        demonstrate_phase4_integration()
        demonstrate_performance_optimization()
        demonstrate_size_control()

        print("\n🎉 All demonstrations completed successfully!")
        print("\nCheck /tmp/kumihan_formatter/ for development log files")
        print("Log files are in JSON format for easy Claude Code parsing")

    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")

        # Use error analyzer for the demo error
        error_analyzer = get_error_analyzer(__name__)
        error_analyzer.log_error_with_analysis(
            e,
            "Demo execution failed",
            context={"demo_stage": "main"},
            operation="demo_execution",
        )


if __name__ == "__main__":
    main()
