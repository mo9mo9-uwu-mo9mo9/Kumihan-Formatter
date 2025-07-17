"""Simple function-level performance profiling functionality.

This module provides a simple PerformanceProfiler class for profiling
individual function performance.
"""

import statistics
import threading
import time
from functools import wraps
from typing import Any, Callable


class SimplePerformanceProfiler:
    """Simple function-level performance profiler"""

    def __init__(self) -> None:
        self.function_stats: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def profile(
        self, func_name: str | None = None
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator for profiling function performance"""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            name = func_name or f"{func.__module__}.{func.__name__}"

            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
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
    ) -> list[tuple[str, dict[str, float]]]:
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
