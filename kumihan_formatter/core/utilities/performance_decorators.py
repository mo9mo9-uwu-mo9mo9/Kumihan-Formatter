"""
パフォーマンス ログ デコレーター

関数の自動パフォーマンス追跡デコレーター
Issue #492 Phase 5A - performance_logger.py分割
"""

from __future__ import annotations

import functools
import inspect
import logging
import time
import traceback
from typing import TYPE_CHECKING, Any, Callable, Optional, Union

if TYPE_CHECKING:
    from .structured_logger import StructuredLogger

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
            # Set up operation name
            op_name = operation or func.__name__

            # Set up logger
            module_name = func.__module__ if func.__module__ else "unknown"
            logger_name_final = logger_name or module_name
            from .structured_logger import get_structured_logger

            structured_logger = get_structured_logger(logger_name_final)

            # Record start time and memory
            start_time = time.time()
            start_memory = None
            if include_memory and HAS_PSUTIL:
                try:
                    start_memory = psutil.Process().memory_info().rss
                except Exception as e:
                    # Log memory monitoring errors for debugging
                    import logging

                    logging.getLogger("kumihan_formatter.performance").debug(
                        f"Memory monitoring failed: {e}"
                    )

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
                    except Exception as e:
                        # Log memory monitoring errors for debugging
                        import logging

                        logging.getLogger("kumihan_formatter.performance").debug(
                            f"Memory monitoring failed: {e}"
                        )

                structured_logger.performance(
                    op_name, duration, metadata=completion_context
                )

                return result

            except Exception as func_error:
                # Log error completion
                end_time = time.time()
                duration = end_time - start_time

                error_context = {
                    "phase": "error",
                    "success": False,
                    "error_message": str(func_error),
                }

                if include_memory and HAS_PSUTIL:
                    try:
                        end_memory = psutil.Process().memory_info().rss
                        error_context["memory_mb"] = round(
                            end_memory / (1024 * 1024), 2
                        )
                    except Exception as memory_error:
                        # Log memory monitoring errors for debugging
                        import logging

                        logging.getLogger("kumihan_formatter.performance").debug(
                            f"Memory monitoring failed: {memory_error}"
                        )

                structured_logger.error_with_suggestion(
                    f"Function failed: {op_name}",
                    func_error,
                    ["Check function arguments and internal logic"],
                    error_type=type(func_error).__name__,
                    operation=op_name,
                    **error_context,
                )

                # Re-raise the exception
                raise

        return wrapper

    return decorator
