"""Performance metrics and reporting functionality.

This module contains the core data structures and metrics for performance monitoring.
"""

import statistics
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PerformanceReport:
    """Comprehensive performance report"""

    operation_name: str
    execution_time: float
    memory_usage: int | None = None
    cpu_usage: float | None = None
    node_count: int | None = None
    file_size: int | None = None
    cache_hits: int = 0
    cache_misses: int = 0
    warnings: list[str] = field(default_factory=list)

    @property
    def cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio"""
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0.0

    @property
    def throughput_nodes_per_second(self) -> float | None:
        """Calculate nodes processed per second"""
        if self.node_count and self.execution_time > 0:
            return self.node_count / self.execution_time
        return None

    @property
    def throughput_mb_per_second(self) -> float | None:
        """Calculate MB processed per second"""
        if self.file_size and self.execution_time > 0:
            return (self.file_size / (1024 * 1024)) / self.execution_time
        return None

    def add_warning(self, warning: str) -> None:
        """Add performance warning"""
        self.warnings.append(warning)

    def __str__(self) -> str:
        """Format performance report"""
        lines = [f"Performance Report: {self.operation_name}"]
        lines.append("-" * 50)
        lines.append(f"Execution Time: {self.execution_time:.3f}s")

        if self.memory_usage:
            lines.append(f"Memory Usage: {self._format_bytes(self.memory_usage)}")

        if self.cpu_usage:
            lines.append(f"CPU Usage: {self.cpu_usage:.1f}%")

        if self.node_count:
            lines.append(f"Nodes Processed: {self.node_count:,}")

        if self.throughput_nodes_per_second:
            lines.append(
                f"Throughput: {self.throughput_nodes_per_second:.1f} nodes/sec"
            )

        if self.throughput_mb_per_second:
            lines.append(f"File Throughput: {self.throughput_mb_per_second:.2f} MB/sec")

        if self.cache_hits + self.cache_misses > 0:
            lines.append(f"Cache Hit Ratio: {self.cache_hit_ratio:.1%}")

        if self.warnings:
            lines.append("\nWarnings:")
            for warning in self.warnings:
                lines.append(f"  - {warning}")

        return "\n".join(lines)

    @staticmethod
    def _format_bytes(bytes_value: int) -> str:
        """Format bytes in human-readable format"""
        for unit in ["B", "KB", "MB", "GB"]:
            if bytes_value < 1024:
                return f"{bytes_value:.1f} {unit}"
            bytes_value = int(bytes_value / 1024)
        return f"{bytes_value:.1f} TB"


class PerformanceSummary:
    """Utilities for generating performance summaries"""

    @staticmethod
    def get_summary_stats(reports: list[PerformanceReport]) -> dict[str, Any]:
        """Get summary statistics across all reports"""
        if not reports:
            return {}

        execution_times = [r.execution_time for r in reports]
        memory_usages = [r.memory_usage for r in reports if r.memory_usage]

        stats = {
            "total_operations": len(reports),
            "avg_execution_time": float(statistics.mean(execution_times)),
            "min_execution_time": min(execution_times),
            "max_execution_time": max(execution_times),
            "total_execution_time": sum(execution_times),
        }

        if memory_usages:
            stats.update(
                {
                    "avg_memory_usage": float(statistics.mean(memory_usages)),
                    "max_memory_usage": max(memory_usages),
                    "total_memory_usage": sum(memory_usages),
                }
            )

        return stats


class PerformanceWarningChecker:
    """Utilities for checking performance warnings"""

    @staticmethod
    def check_performance_warnings(report: PerformanceReport) -> None:
        """Check for performance issues and add warnings"""
        # Slow execution warning
        if report.execution_time > 5.0:
            report.add_warning(f"Slow execution: {report.execution_time:.1f}s")

        # High memory usage warning
        if report.memory_usage and report.memory_usage > 100 * 1024 * 1024:  # 100MB
            report.add_warning(
                f"High memory usage: {report._format_bytes(report.memory_usage)}"
            )

        # Low cache hit ratio warning
        if (
            report.cache_hit_ratio < 0.5
            and (report.cache_hits + report.cache_misses) > 10
        ):
            report.add_warning(f"Low cache hit ratio: {report.cache_hit_ratio:.1%}")

        # Low throughput warning for large files
        if (
            report.file_size
            and report.file_size > 1024 * 1024  # > 1MB
            and report.throughput_mb_per_second
            and report.throughput_mb_per_second < 1.0
        ):
            report.add_warning(
                f"Low file throughput: {report.throughput_mb_per_second:.2f} MB/s"
            )
