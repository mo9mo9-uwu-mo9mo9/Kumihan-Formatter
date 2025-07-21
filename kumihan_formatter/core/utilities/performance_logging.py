"""Performance logging utilities for Kumihan-Formatter

This module provides decorators and utilities for automatic performance
monitoring and logging with structured context data.
"""

from __future__ import annotations

import functools
import inspect
import time
import traceback
from typing import Any, Callable, Optional

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


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
            # Import here to avoid circular import
            from .structured_logging import get_structured_logger

            # Set up operation name
            op_name = operation or func.__name__

            # Set up logger
            module_name = func.__module__ if func.__module__ else "unknown"
            logger_name_final = logger_name or module_name
            structured_logger = get_structured_logger(logger_name_final)

            # Record start time and memory
            start_time = time.time()
            start_memory = None
            if include_memory and HAS_PSUTIL:
                try:
                    start_memory = psutil.Process().memory_info().rss
                except Exception:
                    pass  # Ignore memory monitoring errors

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
                    except Exception:
                        pass  # Ignore memory monitoring errors

                structured_logger.performance(op_name, duration, **completion_context)

                return result

            except Exception as e:
                # Log error completion
                end_time = time.time()
                duration = end_time - start_time

                error_context = {
                    "phase": "error",
                    "success": False,
                    "error_message": str(e),
                }

                if include_memory and HAS_PSUTIL:
                    try:
                        end_memory = psutil.Process().memory_info().rss
                        error_context["memory_mb"] = round(
                            end_memory / (1024 * 1024), 2
                        )
                    except Exception:
                        pass  # Ignore memory monitoring errors

                structured_logger.error_with_suggestion(
                    f"Function failed: {op_name}",
                    "Check function arguments and internal logic",
                    error_type=type(e).__name__,
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


def log_performance(
    operation: str, duration: float, size: Optional[int] = None
) -> None:
    """Convenience function for logging performance metrics

    Args:
        operation: Operation name
        duration: Duration in seconds
        size: Optional size in bytes
    """
    # Import here to avoid circular import
    from .logger import get_logger

    _ = get_logger("performance")  # パフォーマンスロガー（現在未使用）
    # Note: This would need the _logger_instance reference to be updated
    # when the main logger module is refactored
