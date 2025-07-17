"""
パフォーマンス 最適化機能

ログシステムの自動最適化・リソース監視
Issue #492 Phase 5A - performance_logger.py分割
"""

import logging
import time
from typing import TYPE_CHECKING, Any, Optional, Union

from .performance_trackers import memory_usage_tracker

if TYPE_CHECKING:
    from .structured_logger import StructuredLogger

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


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
