"""Performance monitoring functionality.

This module provides the core PerformanceMonitor class for measuring and tracking
performance metrics during operations.
"""

import threading
import time
from contextlib import contextmanager
from typing import Any, Generator

from .metrics import PerformanceReport, PerformanceSummary, PerformanceWarningChecker
from .system_info import SystemInfoProvider


class PerformanceMonitor:
    """Advanced performance monitoring system"""

    def __init__(self) -> None:
        self.reports: list[PerformanceReport] = []
        self._cache_stats = {"hits": 0, "misses": 0}
        self._node_count = 0
        self._lock = threading.Lock()
        self._system_info = SystemInfoProvider()

    @contextmanager
    def measure(
        self,
        operation_name: str,
        node_count: int | None = None,
        file_size: int | None = None,
    ) -> Generator["PerformanceMonitor", None, None]:
        """Context manager for measuring performance"""
        start_time = time.perf_counter()
        start_memory = self._system_info.get_memory_usage()
        start_cpu = self._system_info.get_cpu_usage()

        # Reset cache stats for this operation
        cache_hits_start = self._cache_stats["hits"]
        cache_misses_start = self._cache_stats["misses"]

        try:
            yield self
        finally:
            end_time = time.perf_counter()
            end_memory = self._system_info.get_memory_usage()
            end_cpu = self._system_info.get_cpu_usage()

            execution_time = end_time - start_time
            memory_usage = (
                end_memory - start_memory if start_memory and end_memory else None
            )
            cpu_usage = end_cpu if end_cpu else None

            cache_hits = self._cache_stats["hits"] - cache_hits_start
            cache_misses = self._cache_stats["misses"] - cache_misses_start

            report = PerformanceReport(
                operation_name=operation_name,
                execution_time=execution_time,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage,
                node_count=node_count,
                file_size=file_size,
                cache_hits=cache_hits,
                cache_misses=cache_misses,
            )

            # Add performance warnings
            PerformanceWarningChecker.check_performance_warnings(report)

            with self._lock:
                self.reports.append(report)

    def record_cache_hit(self) -> None:
        """Record a cache hit"""
        with self._lock:
            self._cache_stats["hits"] += 1

    def record_cache_miss(self) -> None:
        """Record a cache miss"""
        with self._lock:
            self._cache_stats["misses"] += 1

    def record_cache_invalidation(self) -> None:
        """Record a cache invalidation"""
        # Cache invalidation is a type of miss
        self.record_cache_miss()

    def record_cache_set(self) -> None:
        """Record a cache set operation"""
        # Cache set doesn't affect hit/miss ratio directly
        pass

    def record_error(self, error_type: str = "general") -> None:
        """Record an error occurrence"""
        # For now, just pass - could be extended to track error statistics
        pass

    def get_latest_report(self) -> PerformanceReport | None:
        """Get the most recent performance report"""
        with self._lock:
            return self.reports[-1] if self.reports else None

    def get_summary_stats(self) -> dict[str, Any]:
        """Get summary statistics across all reports"""
        return PerformanceSummary.get_summary_stats(self.reports)

    def clear_reports(self) -> None:
        """Clear all performance reports"""
        with self._lock:
            self.reports.clear()
            self._cache_stats = {"hits": 0, "misses": 0}
