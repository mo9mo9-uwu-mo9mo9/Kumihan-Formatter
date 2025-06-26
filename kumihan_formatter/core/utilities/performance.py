"""Performance monitoring utilities

This module provides performance measurement tools including
execution time tracking and memory usage monitoring.
"""

import time
from dataclasses import dataclass
from functools import wraps
from typing import Optional


@dataclass
class PerformanceMetrics:
    """Performance measurement results"""
    execution_time: float
    memory_usage: Optional[int] = None
    operations_count: Optional[int] = None
    
    def __str__(self) -> str:
        parts = [f"Time: {self.execution_time:.3f}s"]
        if self.memory_usage:
            parts.append(f"Memory: {self.memory_usage:,} bytes")
        if self.operations_count:
            parts.append(f"Operations: {self.operations_count:,}")
        return " | ".join(parts)


class PerformanceMonitor:
    """Performance monitoring utilities"""
    
    @staticmethod
    def measure_time(func):
        """Decorator to measure function execution time"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            
            execution_time = end_time - start_time
            print(f"{func.__name__} executed in {execution_time:.3f} seconds")
            
            return result
        return wrapper
    
    @staticmethod
    def measure_performance(func):
        """Decorator to measure comprehensive performance metrics"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            start_memory = process.memory_info().rss
            start_time = time.perf_counter()
            
            result = func(*args, **kwargs)
            
            end_time = time.perf_counter()
            end_memory = process.memory_info().rss
            
            metrics = PerformanceMetrics(
                execution_time=end_time - start_time,
                memory_usage=end_memory - start_memory
            )
            
            print(f"{func.__name__} performance: {metrics}")
            
            return result
        return wrapper