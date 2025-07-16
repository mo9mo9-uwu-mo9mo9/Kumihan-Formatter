"""Performance logging and optimization for Kumihan-Formatter

This module provides performance tracking, monitoring, and optimization
features specifically designed for Claude Code integration.
"""

from __future__ import annotations

import functools
import inspect
import logging
import time
import traceback
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, Optional

if TYPE_CHECKING:
    from .structured_logger import StructuredLogger

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Note: structured_logger imports will be resolved at runtime to avoid circular imports


def log_performance_decorator(
    operation: Optional[str] = None,
    include_memory: bool = False,
    include_stack: bool = False,
    logger_name: Optional[str] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for automatic performance logging

    Args:
        operation: Operation name (defaults to function name)
        include_memory: Whether to include memory usage info
        include_stack: Whether to include stack trace info
        logger_name: Logger name (defaults to function's module)

    Returns:
        Decorated function with performance logging

    Example:
        @log_performance_decorator(include_memory=True)
        def convert_file(input_path: str) -> str:
            # File conversion logic
            return output_path
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Set up operation name
            op_name = operation or func.__name__

            # Set up logger
            module_name = func.__module__ if func.__module__ else "unknown"
            logger_name_final = logger_name or module_name
            from .structured_logger import get_structured_logger

            structured_logger = get_structured_logger(logger_name_final)

            # Record start time and memory
            start_time = time.time()
            start_memory = None
            if include_memory and HAS_PSUTIL:
                try:
                    start_memory = psutil.Process().memory_info().rss
                except Exception as e:
                    # Log memory monitoring errors for debugging
                    import logging

                    logging.getLogger("kumihan_formatter.performance").debug(
                        f"Memory monitoring failed: {e}"
                    )

            # Get function signature and arguments
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Get call stack info
            stack_info = None
            if include_stack:
                stack = traceback.extract_stack()
                stack_info = {
                    "caller": f"{stack[-2].filename}:{stack[-2].lineno}",
                    "function": stack[-2].name,
                    "depth": len(stack) - 1,
                }

            try:
                # Log function entry
                entry_context = {
                    "phase": "entry",
                    "args_count": len(args),
                    "kwargs_count": len(kwargs),
                }

                if include_memory and start_memory:
                    entry_context["memory_mb"] = round(start_memory / (1024 * 1024), 2)

                if stack_info:
                    entry_context["stack_info"] = stack_info

                structured_logger.debug(
                    f"Function entry: {op_name}", operation=op_name, **entry_context
                )

                # Execute function
                result = func(*args, **kwargs)

                # Calculate performance metrics
                end_time = time.time()
                duration = end_time - start_time

                # Log successful completion
                completion_context = {
                    "phase": "completion",
                    "success": True,
                }

                if include_memory and HAS_PSUTIL:
                    try:
                        end_memory = psutil.Process().memory_info().rss
                        completion_context["memory_mb"] = round(
                            end_memory / (1024 * 1024), 2
                        )
                        if start_memory:
                            memory_delta = end_memory - start_memory
                            completion_context["memory_delta_mb"] = round(
                                memory_delta / (1024 * 1024), 2
                            )
                    except Exception as e:
                        # Log memory monitoring errors for debugging
                        import logging

                        logging.getLogger("kumihan_formatter.performance").debug(
                            f"Memory monitoring failed: {e}"
                        )

                structured_logger.performance(op_name, duration, **completion_context)

                return result

            except Exception as func_error:
                # Log error completion
                end_time = time.time()
                duration = end_time - start_time

                error_context = {
                    "phase": "error",
                    "success": False,
                    "error_message": str(func_error),
                }

                if include_memory and HAS_PSUTIL:
                    try:
                        end_memory = psutil.Process().memory_info().rss
                        error_context["memory_mb"] = round(
                            end_memory / (1024 * 1024), 2
                        )
                    except Exception as memory_error:
                        # Log memory monitoring errors for debugging
                        import logging

                        logging.getLogger("kumihan_formatter.performance").debug(
                            f"Memory monitoring failed: {memory_error}"
                        )

                structured_logger.error_with_suggestion(
                    f"Function failed: {op_name}",
                    "Check function arguments and internal logic",
                    error_type=type(func_error).__name__,
                    operation=op_name,
                    **error_context,
                )

                # Re-raise the exception
                raise

        return wrapper

    return decorator


def call_chain_tracker(max_depth: int = 10) -> dict[str, Any]:
    """Get current call chain information for debugging

    Args:
        max_depth: Maximum stack depth to track

    Returns:
        Dictionary with call chain information
    """
    stack = traceback.extract_stack()
    call_chain = []

    # Skip the last frame (this function) and limit depth
    for frame in stack[-max_depth - 1 : -1]:
        call_chain.append(
            {
                "file": frame.filename.split("/")[-1],  # Just filename, not full path
                "line": frame.lineno,
                "function": frame.name,
                "code": frame.line.strip() if frame.line else None,
            }
        )

    return {
        "call_chain": call_chain,
        "chain_depth": len(call_chain),
        "current_function": call_chain[-1]["function"] if call_chain else None,
    }


def memory_usage_tracker() -> dict[str, Any]:
    """Get current memory usage information

    Returns:
        Dictionary with memory usage metrics
    """
    if not HAS_PSUTIL:
        return {
            "memory_rss_mb": 0,
            "memory_vms_mb": 0,
            "memory_percent": 0,
            "cpu_percent": 0,
            "psutil_available": False,
        }

    try:
        process = psutil.Process()
        memory_info = process.memory_info()

        return {
            "memory_rss_mb": round(memory_info.rss / (1024 * 1024), 2),
            "memory_vms_mb": round(memory_info.vms / (1024 * 1024), 2),
            "memory_percent": round(process.memory_percent(), 2),
            "cpu_percent": round(process.cpu_percent(), 2),
            "psutil_available": True,
        }
    except Exception:
        return {
            "memory_rss_mb": 0,
            "memory_vms_mb": 0,
            "memory_percent": 0,
            "cpu_percent": 0,
            "psutil_available": False,
            "error": "Failed to get memory info",
        }


class LogPerformanceOptimizer:
    """Performance optimization for logging system

    Provides intelligent logging optimization features:
    - Adaptive log level management
    - Performance-based filtering
    - Resource usage monitoring
    - Automatic throttling
    """

    def __init__(self, logger: "StructuredLogger"):
        self.logger = logger
        self.performance_metrics: dict[str, list[float]] = {}
        self.log_frequency: dict[str, int] = {}
        self.throttle_thresholds = {
            "high_frequency": 100,  # logs per second
            "memory_limit": 100,  # MB
            "cpu_limit": 80,  # percentage
        }
        self.adaptive_levels = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
        }
        self.current_optimization_level = "normal"

    def should_log(
        self, level: int, message_key: str, operation: Optional[str] = None
    ) -> bool:
        """Determine if message should be logged based on performance metrics

        Args:
            level: Log level
            message_key: Unique key for message type
            operation: Operation being logged

        Returns:
            True if message should be logged
        """
        # Always log errors and warnings
        if level >= logging.WARNING:
            return True

        # Check frequency throttling
        if self._is_high_frequency(message_key):
            if level == logging.DEBUG:
                return False  # Skip debug in high frequency scenarios

        # Check system resource usage
        if self._is_high_resource_usage():
            if level == logging.DEBUG:
                return False
            if level == logging.INFO and self._is_non_critical_info(operation):
                return False

        return True

    def _is_high_frequency(self, message_key: str) -> bool:
        """Check if message type is being logged at high frequency"""
        current_time = time.time()

        # Initialize if first occurrence
        if message_key not in self.log_frequency:
            self.log_frequency[message_key] = 0
            return False

        # Simple frequency check (could be enhanced with time windows)
        return (
            self.log_frequency[message_key] > self.throttle_thresholds["high_frequency"]
        )

    def _is_high_resource_usage(self) -> bool:
        """Check if system resource usage is high"""
        if not HAS_PSUTIL:
            return False

        try:
            memory_info = memory_usage_tracker()
            return bool(
                memory_info["memory_rss_mb"] > self.throttle_thresholds["memory_limit"]
                or memory_info["cpu_percent"] > self.throttle_thresholds["cpu_limit"]
            )
        except Exception:
            return False

    def _is_non_critical_info(self, operation: Optional[str]) -> bool:
        """Check if info message is non-critical and can be skipped"""
        non_critical_operations = {
            "performance_tracking",
            "dependency_loading",
            "memory_monitoring",
            "debug_tracing",
        }
        return operation in non_critical_operations

    def record_log_event(
        self, level: int, message_key: str, duration: float = 0.0
    ) -> None:
        """Record logging event for performance analysis

        Args:
            level: Log level
            message_key: Message type key
            duration: Time taken to process log
        """
        # Update frequency counter
        self.log_frequency[message_key] = self.log_frequency.get(message_key, 0) + 1

        # Record performance metrics
        if message_key not in self.performance_metrics:
            self.performance_metrics[message_key] = []

        self.performance_metrics[message_key].append(duration)

        # Keep only recent metrics (last 100 entries)
        if len(self.performance_metrics[message_key]) > 100:
            self.performance_metrics[message_key] = self.performance_metrics[
                message_key
            ][-100:]

    def optimize_log_levels(self) -> dict[str, int]:
        """Automatically optimize log levels based on performance data

        Returns:
            Dictionary of recommended log level adjustments
        """
        recommendations = {}

        # Analyze performance impact of different log levels
        total_debug_time = sum(
            sum(metrics)
            for key, metrics in self.performance_metrics.items()
            if "debug" in key.lower()
        )

        total_info_time = sum(
            sum(metrics)
            for key, metrics in self.performance_metrics.items()
            if "info" in key.lower()
        )

        # Recommend level adjustments based on overhead
        if total_debug_time > 1.0:  # If debug logging takes > 1 second total
            recommendations["debug"] = logging.INFO

        if total_info_time > 0.5:  # If info logging takes > 0.5 seconds total
            recommendations["info"] = logging.WARNING

        return recommendations

    def get_performance_report(self) -> dict[str, Any]:
        """Generate performance report for logging system

        Returns:
            Dictionary with performance analysis
        """
        total_logs = sum(self.log_frequency.values())
        total_time = sum(sum(metrics) for metrics in self.performance_metrics.values())

        # Calculate average times per message type
        avg_times = {}
        for key, metrics in self.performance_metrics.items():
            if metrics:
                avg_times[key] = round(sum(metrics) / len(metrics) * 1000, 3)  # ms

        # Find slowest operations
        slowest = sorted(avg_times.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "total_log_events": total_logs,
            "total_processing_time_ms": round(total_time * 1000, 2),
            "average_time_per_log_ms": round(total_time / max(total_logs, 1) * 1000, 3),
            "slowest_operations": slowest,
            "high_frequency_messages": [
                key
                for key, count in self.log_frequency.items()
                if count > self.throttle_thresholds["high_frequency"] // 10
            ],
            "optimization_level": self.current_optimization_level,
            "memory_usage": memory_usage_tracker(),
        }


def get_log_performance_optimizer(name: str) -> LogPerformanceOptimizer:
    """Get log performance optimizer instance for a module

    Args:
        name: Module name (typically __name__)

    Returns:
        LogPerformanceOptimizer instance for performance optimization
    """
    from .structured_logger import get_structured_logger

    structured_logger = get_structured_logger(name)
    return LogPerformanceOptimizer(structured_logger)
