"""
ログ リソースモニター

システムリソース監視・頻度制御機能
Issue #492 Phase 5A - log_optimization.py分割
"""

from __future__ import annotations

from typing import Any, Optional

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from .performance_logging import memory_usage_tracker


class LogResourceMonitor:
    """Log resource monitoring functionality

    Handles system resource monitoring, frequency tracking,
    and resource-based throttling decisions.
    """

    def __init__(self, logger: Any) -> None:
        """Initialize with a StructuredLogger instance"""
        self.logger = logger
        self.log_frequency: dict[str, int] = {}
        self.throttle_thresholds = {
            "high_frequency": 100,  # logs per second
            "memory_limit": 100,  # MB
            "cpu_limit": 80,  # percentage
        }

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

    def update_frequency(self, message_key: str) -> None:
        """Update frequency counter for message type"""
        self.log_frequency[message_key] = self.log_frequency.get(message_key, 0) + 1

    def get_resource_status(self) -> dict[str, Any]:
        """Get current resource status"""
        try:
            memory_info = memory_usage_tracker()
            return {
                "has_psutil": HAS_PSUTIL,
                "memory_usage": memory_info,
                "high_resource_usage": self._is_high_resource_usage(),
                "thresholds": self.throttle_thresholds,
            }
        except Exception:
            return {
                "has_psutil": HAS_PSUTIL,
                "memory_usage": {},
                "high_resource_usage": False,
                "thresholds": self.throttle_thresholds,
            }
