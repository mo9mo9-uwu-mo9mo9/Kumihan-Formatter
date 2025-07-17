"""Log performance optimization utilities

Single Responsibility Principle適用: ログパフォーマンス最適化の分離
Issue #476 Phase3対応 - log_optimization.py分割
"""

import time
from typing import Any, Dict, Optional


class LogPerformanceOptimizer:
    """Log performance optimization and filtering

    Provides intelligent log filtering and optimization:
    - Frequency-based filtering
    - Performance-based throttling
    - Context-aware optimization
    - Memory usage control
    """

    def __init__(self, structured_logger: Any):
        self.structured_logger = structured_logger
        self.frequency_limits = {
            "max_logs_per_second": 100,
            "max_logs_per_minute": 1000,
            "max_logs_per_hour": 10000,
            "burst_allowance": 10,
        }
        self.performance_thresholds = {
            "cpu_usage_threshold": 80.0,
            "memory_usage_threshold": 85.0,
            "disk_usage_threshold": 90.0,
        }
        self.context_priorities = {
            "error": 100,
            "warning": 80,
            "info": 60,
            "debug": 40,
            "trace": 20,
        }

        # Internal state
        self._log_timestamps: list[float] = []
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5 minutes

    def should_log(
        self,
        level: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        priority: str = "normal",
    ) -> bool:
        """Determine if a log should be processed based on optimization rules

        Args:
            level: Log level (debug, info, warning, error)
            message: Log message
            context: Context data
            priority: Priority level (high, normal, low)

        Returns:
            True if log should be processed
        """
        current_time = time.time()

        # Clean up old timestamps periodically
        if current_time - self._last_cleanup > self._cleanup_interval:
            self._cleanup_timestamps(current_time)
            self._last_cleanup = current_time

        # Always allow high priority logs
        if priority == "high":
            return True

        # Check frequency limits
        if not self._check_frequency_limits(current_time):
            return False

        # Check performance thresholds
        if not self._check_performance_thresholds():
            return False

        # Check context-based priorities
        if not self._check_context_priority(level, context):
            return False

        # Record successful log
        self._log_timestamps.append(current_time)
        return True

    def _cleanup_timestamps(self, current_time: float) -> None:
        """Clean up old log timestamps"""
        cutoff_time = current_time - 3600  # Keep last hour
        self._log_timestamps = [ts for ts in self._log_timestamps if ts > cutoff_time]

    def _check_frequency_limits(self, current_time: float) -> bool:
        """Check if frequency limits are exceeded"""
        # Check logs per second
        recent_logs = [ts for ts in self._log_timestamps if current_time - ts <= 1.0]
        if len(recent_logs) >= self.frequency_limits["max_logs_per_second"]:
            return False

        # Check logs per minute
        recent_logs = [ts for ts in self._log_timestamps if current_time - ts <= 60.0]
        if len(recent_logs) >= self.frequency_limits["max_logs_per_minute"]:
            return False

        return True

    def _check_performance_thresholds(self) -> bool:
        """Check if system performance allows logging"""
        try:
            import psutil

            # CPU usage check
            cpu_usage = psutil.cpu_percent(interval=0.1)
            if cpu_usage > self.performance_thresholds["cpu_usage_threshold"]:
                return False

            # Memory usage check
            memory_usage = psutil.virtual_memory().percent
            if memory_usage > self.performance_thresholds["memory_usage_threshold"]:
                return False

            return True
        except ImportError:
            # If psutil not available, allow logging
            return True
        except Exception:
            # If any error occurs, allow logging
            return True

    def _check_context_priority(
        self, level: str, context: Optional[Dict[str, Any]]
    ) -> bool:
        """Check if log meets context-based priority requirements"""
        base_priority = self.context_priorities.get(level.lower(), 50)

        # Adjust priority based on context
        if context:
            # Increase priority for error-related context
            if any(key in context for key in ["error", "exception", "traceback"]):
                base_priority += 20

            # Increase priority for performance-related context
            if any(key in context for key in ["duration", "memory", "cpu"]):
                base_priority += 10

        # For now, always allow (can be enhanced with more complex logic)
        return base_priority >= 20

    def optimize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize context data for better performance

        Args:
            context: Original context dictionary

        Returns:
            Optimized context dictionary
        """
        optimized = {}

        # Limit context size
        max_entries = 50
        entry_count = 0

        for key, value in context.items():
            if entry_count >= max_entries:
                optimized["_truncated"] = (
                    f"... {len(context) - entry_count} more entries"
                )
                break

            # Optimize large values
            if isinstance(value, str) and len(value) > 500:
                optimized[key] = value[:500] + "... [truncated]"
            elif isinstance(value, (list, dict)) and len(str(value)) > 500:
                optimized[key] = f"[Large {type(value).__name__}: {len(value)} items]"
            else:
                optimized[key] = value

            entry_count += 1

        return optimized
