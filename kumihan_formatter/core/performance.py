"""Performance measurement and optimization utilities for Kumihan-Formatter

This module provides comprehensive performance monitoring, profiling,
and optimization tools to ensure efficient operation.

Dependencies:
- gc: For garbage collection control
- statistics: For statistical calculations
- threading: For thread-safe operations
- time: For execution time measurement
- functools: For decorator implementations
- typing: For type annotations
- dataclasses: For data structure definitions

Note: Uses lazy initialization pattern to avoid import-time side effects.
Use get_global_monitor() and get_global_profiler() functions instead of direct global access.
"""

import gc
import statistics
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path
from typing import Any, Callable, List, Optional, Union

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


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
            bytes_value /= 1024
        return f"{bytes_value:.1f} TB"


class PerformanceMonitor:
    """Advanced performance monitoring system"""

    def __init__(self) -> None:
        self.reports: list[PerformanceReport] = []
        self._cache_stats = {"hits": 0, "misses": 0}
        self._node_count = 0
        self._lock = threading.Lock()

    @contextmanager
    def measure(
        self,
        operation_name: str,
        node_count: int | None = None,
        file_size: int | None = None,
    ):
        """Context manager for measuring performance"""
        start_time = time.perf_counter()
        start_memory = self._get_memory_usage()
        start_cpu = self._get_cpu_usage()

        # Reset cache stats for this operation
        cache_hits_start = self._cache_stats["hits"]
        cache_misses_start = self._cache_stats["misses"]

        try:
            yield self
        finally:
            end_time = time.perf_counter()
            end_memory = self._get_memory_usage()
            end_cpu = self._get_cpu_usage()

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
            self._check_performance_warnings(report)

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

    def get_latest_report(self) -> PerformanceReport | None:
        """Get the most recent performance report"""
        with self._lock:
            return self.reports[-1] if self.reports else None

    def get_summary_stats(self) -> dict[str, Any]:
        """Get summary statistics across all reports"""
        if not self.reports:
            return {}

        execution_times = [r.execution_time for r in self.reports]
        memory_usages = [r.memory_usage for r in self.reports if r.memory_usage]

        stats = {
            "total_operations": len(self.reports),
            "avg_execution_time": statistics.mean(execution_times),
            "min_execution_time": min(execution_times),
            "max_execution_time": max(execution_times),
            "total_execution_time": sum(execution_times),
        }

        if memory_usages:
            stats.update(
                {
                    "avg_memory_usage": statistics.mean(memory_usages),
                    "max_memory_usage": max(memory_usages),
                    "total_memory_usage": sum(memory_usages),
                }
            )

        return stats

    def _get_memory_usage(self) -> int | None:
        """Get current memory usage"""
        if not HAS_PSUTIL:
            return None

        try:
            import os

            process = psutil.Process(os.getpid())
            return process.memory_info().rss
        except Exception:
            return None

    def _get_cpu_usage(self) -> float | None:
        """Get current CPU usage"""
        if not HAS_PSUTIL:
            return None

        try:
            import os

            process = psutil.Process(os.getpid())
            return process.cpu_percent()
        except Exception:
            return None

    def _check_performance_warnings(self, report: PerformanceReport) -> None:
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


class PerformanceProfiler:
    """Function-level performance profiler"""

    def __init__(self) -> None:
        self.function_stats: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def profile(self, func_name: str | None = None):
        """Decorator for profiling function performance"""

        def decorator(func: Callable) -> Callable:
            name = func_name or f"{func.__module__}.{func.__name__}"

            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    end_time = time.perf_counter()
                    execution_time = end_time - start_time

                    with self._lock:
                        if name not in self.function_stats:
                            self.function_stats[name] = []
                        self.function_stats[name].append(execution_time)

            return wrapper

        return decorator

    def get_stats(self) -> dict[str, dict[str, float]]:
        """Get profiling statistics"""
        stats = {}

        with self._lock:
            for func_name, times in self.function_stats.items():
                if times:
                    stats[func_name] = {
                        "calls": len(times),
                        "total_time": sum(times),
                        "avg_time": statistics.mean(times),
                        "min_time": min(times),
                        "max_time": max(times),
                        "median_time": statistics.median(times),
                    }

        return stats

    def get_top_functions(
        self, metric: str = "total_time", limit: int = 10
    ) -> list[tuple]:
        """Get top functions by specified metric"""
        stats = self.get_stats()

        if metric not in ["total_time", "avg_time", "calls", "max_time"]:
            raise ValueError(f"Invalid metric: {metric}")

        sorted_functions = sorted(
            stats.items(), key=lambda x: x[1][metric], reverse=True
        )

        return sorted_functions[:limit]

    def clear_stats(self) -> None:
        """Clear all profiling statistics"""
        with self._lock:
            self.function_stats.clear()


class PerformanceOptimizer:
    """Performance optimization utilities"""

    @staticmethod
    def optimize_gc_settings():
        """Optimize garbage collection settings for better performance"""
        # Disable automatic garbage collection during processing
        gc.disable()

        # Set generation thresholds for better performance
        gc.set_threshold(1000, 15, 15)

    @staticmethod
    def cleanup_memory():
        """Force garbage collection and memory cleanup"""
        gc.collect()

    @staticmethod
    def estimate_memory_for_nodes(node_count: int) -> int:
        """Estimate memory usage for given number of nodes"""
        # Rough estimate: 1KB per node on average
        return node_count * 1024

    @staticmethod
    def should_use_streaming(
        file_size: int, available_memory: int | None = None
    ) -> bool:
        """Determine if streaming processing should be used"""
        # Use streaming for files larger than 10MB or if memory is limited
        threshold = 10 * 1024 * 1024  # 10MB

        if file_size > threshold:
            return True

        if (
            available_memory and file_size > available_memory * 0.1
        ):  # 10% of available memory
            return True

        return False


class BenchmarkSuite:
    """Comprehensive benchmarking suite"""

    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
        self.benchmark_results: dict[str, list[PerformanceReport]] = {}

    def run_benchmark(
        self, name: str, func: Callable, *args, iterations: int = 5, **kwargs
    ):
        """Run benchmark with multiple iterations"""
        results = []

        print(f"Running benchmark: {name} ({iterations} iterations)")

        for i in range(iterations):
            with self.monitor.measure(f"{name}_iteration_{i+1}"):
                func(*args, **kwargs)

            if self.monitor.reports:
                results.append(self.monitor.reports[-1])

        self.benchmark_results[name] = results
        self._print_benchmark_summary(name, results)

    def _print_benchmark_summary(self, name: str, results: list[PerformanceReport]):
        """Print benchmark summary"""
        if not results:
            return

        execution_times = [r.execution_time for r in results]

        print(f"\nBenchmark Results: {name}")
        print("-" * 40)
        print(f"Iterations: {len(results)}")
        print(f"Average Time: {statistics.mean(execution_times):.3f}s")
        print(f"Min Time: {min(execution_times):.3f}s")
        print(f"Max Time: {max(execution_times):.3f}s")
        print(
            f"Std Dev: {statistics.stdev(execution_times) if len(execution_times) > 1 else 0:.3f}s"
        )

        if results[0].memory_usage:
            memory_usages = [r.memory_usage for r in results if r.memory_usage]
            if memory_usages:
                avg_memory = statistics.mean(memory_usages)
                print(
                    f"Average Memory: {PerformanceReport._format_bytes(int(avg_memory))}"
                )

    def compare_benchmarks(self, benchmark1: str, benchmark2: str) -> dict[str, float]:
        """Compare two benchmarks"""
        if (
            benchmark1 not in self.benchmark_results
            or benchmark2 not in self.benchmark_results
        ):
            raise ValueError("One or both benchmarks not found")

        results1 = self.benchmark_results[benchmark1]
        results2 = self.benchmark_results[benchmark2]

        avg_time1 = statistics.mean([r.execution_time for r in results1])
        avg_time2 = statistics.mean([r.execution_time for r in results2])

        return {
            "time_ratio": avg_time1 / avg_time2,
            "improvement_percent": ((avg_time2 - avg_time1) / avg_time2) * 100,
            "faster_benchmark": benchmark2 if avg_time1 > avg_time2 else benchmark1,
        }


# Global instances for easy access - converted to lazy initialization
_global_monitor = None
_global_profiler = None


def get_global_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance (lazy initialization)"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor


def get_global_profiler() -> PerformanceProfiler:
    """Get the global performance profiler instance (lazy initialization)"""
    global _global_profiler
    if _global_profiler is None:
        _global_profiler = PerformanceProfiler()
    return _global_profiler


def measure_performance(operation_name: str, **kwargs):
    """Convenience function for performance measurement"""
    return get_global_monitor().measure(operation_name, **kwargs)


def profile_function(func_name: str | None = None):
    """Convenience decorator for function profiling"""
    return get_global_profiler().profile(func_name)


def get_performance_summary() -> dict[str, Any]:
    """Get comprehensive performance summary"""
    return {
        "monitor_stats": get_global_monitor().get_summary_stats(),
        "profiler_stats": get_global_profiler().get_stats(),
        "top_functions": get_global_profiler().get_top_functions(),
    }
