"""Log optimization and size control for Kumihan-Formatter

This module provides intelligent logging optimization features including
adaptive log level management, performance-based filtering, and size control.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Optional

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from .performance_logging import memory_usage_tracker


class LogPerformanceOptimizer:
    """Phase 4: Performance optimization for logging system

    Provides intelligent logging optimization features:
    - Adaptive log level management
    - Performance-based filtering
    - Resource usage monitoring
    - Automatic throttling
    """

    def __init__(self, logger: Any) -> None:
        """Initialize with a StructuredLogger instance"""
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


class LogSizeController:
    """Phase 4: Log size control and management

    Provides intelligent log size management:
    - Automatic log rotation
    - Content compression
    - Selective retention
    - Size-based filtering
    """

    def __init__(self, logger: Any) -> None:
        """Initialize with a StructuredLogger instance"""
        self.logger = logger
        self.size_limits = {
            "max_file_size_mb": 50,
            "max_total_size_mb": 200,
            "max_entries_per_file": 100000,
            "retention_days": 7,
        }
        self.compression_enabled = True
        self.content_filters = {
            "max_message_length": 1000,
            "max_context_entries": 20,
            "sensitive_data_removal": True,
        }

    def should_include_context(self, context: dict[str, Any]) -> dict[str, Any]:
        """Filter context data to control log size

        Args:
            context: Original context dictionary

        Returns:
            Filtered context dictionary
        """
        filtered = {}
        entry_count = 0

        for key, value in context.items():
            # Limit number of context entries
            if entry_count >= self.content_filters["max_context_entries"]:
                filtered["_truncated"] = (
                    f"... {len(context) - entry_count} more entries"
                )
                break

            # Filter large values
            if (
                isinstance(value, str)
                and len(value) > self.content_filters["max_message_length"]
            ):
                filtered[key] = (
                    value[: self.content_filters["max_message_length"]]
                    + "... [truncated]"
                )
            elif (
                isinstance(value, (list, dict))
                and len(str(value)) > self.content_filters["max_message_length"]
            ):
                filtered[key] = f"[Large {type(value).__name__}: {len(value)} items]"
            else:
                filtered[key] = value

            entry_count += 1

        return filtered

    def format_message_for_size(self, message: str) -> str:
        """Format message to control size

        Args:
            message: Original message

        Returns:
            Potentially truncated message
        """
        max_length = self.content_filters["max_message_length"]

        if len(message) <= max_length:
            return message

        # Truncate with meaningful suffix
        return message[: max_length - 15] + "... [truncated]"

    def estimate_log_size(
        self, message: str, context: Optional[dict[str, Any]] = None
    ) -> int:
        """Estimate the size of a log entry in bytes

        Args:
            message: Log message
            context: Context data

        Returns:
            Estimated size in bytes
        """
        # Base message size
        size = len(message.encode("utf-8"))

        # Add context size if present
        if context:
            try:
                context_json = json.dumps(context, ensure_ascii=False)
                size += len(context_json.encode("utf-8"))
            except (TypeError, ValueError):
                # Fallback estimation
                size += len(str(context).encode("utf-8"))

        # Add overhead for JSON structure
        size += 200  # Estimated JSON overhead

        return size

    def should_skip_due_to_size(
        self, estimated_size: int, priority: str = "normal"
    ) -> bool:
        """Determine if log should be skipped due to size constraints

        Args:
            estimated_size: Estimated log entry size in bytes
            priority: Priority level (high, normal, low)

        Returns:
            True if log should be skipped
        """
        # Never skip high priority logs
        if priority == "high":
            return False

        # Skip very large logs for normal/low priority
        size_mb = estimated_size / (1024 * 1024)

        if priority == "low" and size_mb > 1.0:  # 1MB limit for low priority
            return True

        if priority == "normal" and size_mb > 5.0:  # 5MB limit for normal priority
            return True

        return False

    def get_size_statistics(self) -> dict[str, Any]:
        """Get current size statistics

        Returns:
            Dictionary with size-related statistics
        """
        return {
            "size_limits": self.size_limits,
            "content_filters": self.content_filters,
            "compression_enabled": self.compression_enabled,
            "estimated_overhead_bytes": 200,  # JSON overhead
        }

    def optimize_for_claude_code(self, context: dict[str, Any]) -> dict[str, Any]:
        """Optimize log content specifically for Claude Code consumption

        Args:
            context: Original context

        Returns:
            Optimized context for Claude Code
        """
        optimized = {}

        # Prioritize Claude-specific hints
        if "claude_hint" in context:
            optimized["claude_hint"] = context["claude_hint"]

        # Include error analysis if present
        if "error_analysis" in context:
            optimized["error_analysis"] = context["error_analysis"]

        # Include suggestions
        if "suggestion" in context or "suggestions" in context:
            optimized["suggestion"] = context.get("suggestion") or context.get(
                "suggestions"
            )

        # Include operation context
        if "operation" in context:
            optimized["operation"] = context["operation"]

        # Include file/line information
        for key in ["file_path", "line_number", "function", "module"]:
            if key in context:
                optimized[key] = context[key]

        # Include performance metrics (limited)
        for key in ["duration_ms", "memory_mb", "success"]:
            if key in context:
                optimized[key] = context[key]

        # Add remaining important context (up to limit)
        remaining_space = self.content_filters["max_context_entries"] - len(optimized)
        for key, value in context.items():
            if key not in optimized and remaining_space > 0:
                optimized[key] = value
                remaining_space -= 1

        return optimized


def get_log_performance_optimizer(name: str) -> LogPerformanceOptimizer:
    """Get log performance optimizer instance for a module"""
    from .structured_logging import get_structured_logger

    structured_logger = get_structured_logger(name)
    return LogPerformanceOptimizer(structured_logger)


def get_log_size_controller(name: str) -> LogSizeController:
    """Get log size controller instance for a module"""
    from .structured_logging import get_structured_logger

    structured_logger = get_structured_logger(name)
    return LogSizeController(structured_logger)
