"""Performance monitoring and error analysis for Kumihan-Formatter logging

Single Responsibility Principle適用: パフォーマンス監視とエラー分析の分離
Issue #476 Phase3対応 - logger.py分割
"""

from __future__ import annotations

import functools
import inspect
import time
import traceback
from datetime import datetime
from typing import Any, Callable, Optional

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class ErrorAnalyzer:
    """Claude Code specific error analysis support

    Provides enhanced error logging with analysis suggestions,
    error categorization, and debugging hints specifically
    designed for Claude Code integration.
    """

    # Common error categories and their solutions
    ERROR_CATEGORIES = {
        "encoding": {
            "patterns": ["encoding", "decode", "utf-8", "unicode", "ascii"],
            "suggestions": [
                "Check file encoding with 'file -I filename'",
                "Try specifying encoding explicitly: encoding='utf-8'",
                "Consider using chardet library for encoding detection",
            ],
        },
        "file_access": {
            "patterns": ["permission", "access", "not found", "no such file"],
            "suggestions": [
                "Check file permissions with 'ls -la'",
                "Verify file path exists",
                "Ensure process has read/write permissions",
            ],
        },
        "parsing": {
            "patterns": ["parse", "syntax", "invalid", "unexpected"],
            "suggestions": [
                "Check input file format",
                "Validate syntax of input content",
                "Review notation format specification",
            ],
        },
        "memory": {
            "patterns": ["memory", "out of memory", "allocation"],
            "suggestions": [
                "Process file in chunks",
                "Check available system memory",
                "Consider input file size limitations",
            ],
        },
        "dependency": {
            "patterns": ["import", "module", "not found", "missing"],
            "suggestions": [
                "Check if required package is installed",
                "Verify PYTHONPATH includes necessary directories",
                "Install missing dependencies with pip",
            ],
        },
    }

    def __init__(self, logger: Any):
        self.logger = logger

    def analyze_error(
        self,
        error: Exception,
        context: Optional[dict[str, Any]] = None,
        operation: Optional[str] = None,
    ) -> dict[str, Any]:
        """Analyze error and provide structured debugging information

        Args:
            error: Exception that occurred
            context: Additional context about the operation
            operation: Name of operation that failed

        Returns:
            Dictionary with error analysis and suggestions
        """
        error_message = str(error).lower()
        error_type = type(error).__name__

        # Categorize error
        category = self._categorize_error(error_message)

        # Get stack trace information
        stack_info = call_chain_tracker(max_depth=15)

        # Get memory usage at error time
        memory_info = memory_usage_tracker()

        # Add suggestions based on category
        suggestions: list[str]
        if category != "unknown":
            suggestions = self.ERROR_CATEGORIES[category]["suggestions"]
        else:
            suggestions = self._generate_generic_suggestions(error_type, error_message)

        analysis: dict[str, Any] = {
            "error_type": error_type,
            "error_message": str(error),
            "category": category,
            "operation": operation,
            "stack_info": stack_info,
            "memory_info": memory_info,
            "timestamp": datetime.now().isoformat(),
            "suggestions": suggestions,
        }

        if context:
            analysis["context"] = context

        return analysis

    def _categorize_error(self, error_message: str) -> str:
        """Categorize error based on message content"""
        for category, config in self.ERROR_CATEGORIES.items():
            if any(pattern in error_message for pattern in config["patterns"]):
                return category
        return "unknown"

    def _generate_generic_suggestions(
        self, error_type: str, error_message: str
    ) -> list[str]:
        """Generate generic suggestions for unknown error types"""
        suggestions = [
            f"Review {error_type} documentation",
            "Check logs for additional context",
            "Verify input parameters and their types",
        ]

        # Add specific suggestions based on error type
        if "file" in error_message.lower() or "path" in error_message.lower():
            suggestions.append("Check file paths and permissions")

        if "type" in error_message.lower() or "attribute" in error_message.lower():
            suggestions.append("Verify object types and available methods")

        return suggestions


class DependencyTracker:
    """Track dependencies and their loading performance"""

    def __init__(self) -> None:
        self.loaded_modules: dict[str, float] = {}
        self.failed_imports: list[dict[str, Any]] = []

    def track_import(self, module_name: str, start_time: float, success: bool) -> None:
        """Track module import performance"""
        duration = time.time() - start_time

        if success:
            self.loaded_modules[module_name] = duration
        else:
            self.failed_imports.append(
                {
                    "module": module_name,
                    "timestamp": datetime.now().isoformat(),
                    "duration": duration,
                }
            )

    def get_summary(self) -> dict[str, Any]:
        """Get dependency loading summary"""
        return {
            "loaded_modules": len(self.loaded_modules),
            "failed_imports": len(self.failed_imports),
            "total_load_time": sum(self.loaded_modules.values()),
            "slowest_modules": sorted(
                self.loaded_modules.items(), key=lambda x: x[1], reverse=True
            )[:5],
        }


class ExecutionFlowTracker:
    """Track execution flow for debugging"""

    def __init__(self) -> None:
        self.flow_stack: list[dict[str, Any]] = []
        self.checkpoints: list[dict[str, Any]] = []

    def enter_function(self, function_name: str, args_info: dict[str, Any]) -> str:
        """Record function entry"""
        entry_id = f"{function_name}_{len(self.flow_stack)}"
        self.flow_stack.append(
            {
                "id": entry_id,
                "function": function_name,
                "entry_time": time.time(),
                "args_info": args_info,
            }
        )
        return entry_id

    def exit_function(self, entry_id: str, result_info: dict[str, Any]) -> None:
        """Record function exit"""
        if self.flow_stack and self.flow_stack[-1]["id"] == entry_id:
            entry = self.flow_stack.pop()
            duration = time.time() - entry["entry_time"]
            entry.update(
                {"exit_time": time.time(), "duration": duration, **result_info}
            )

    def add_checkpoint(self, name: str, data: dict[str, Any]) -> None:
        """Add execution checkpoint"""
        self.checkpoints.append({"name": name, "timestamp": time.time(), "data": data})

    def get_current_flow(self) -> list[dict[str, Any]]:
        """Get current execution flow"""
        return self.flow_stack.copy()


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

            # Set up logger - use basic logging if structured logger not available
            from .logging_handlers import get_logger

            module_name = func.__module__ if func.__module__ else "unknown"
            logger_name_final = logger_name or module_name
            logger = get_logger(logger_name_final)

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

                logger.debug(f"Function entry: {op_name} {entry_context}")

                # Execute function
                result = func(*args, **kwargs)

                # Calculate performance metrics
                end_time = time.time()
                duration = end_time - start_time

                # Log successful completion
                completion_context = {
                    "phase": "completion",
                    "success": True,
                    "duration": duration,
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

                logger.info(f"Performance: {op_name} completed in {duration:.3f}s")

                return result

            except Exception as e:
                # Log error completion
                end_time = time.time()
                duration = end_time - start_time

                error_context = {
                    "phase": "error",
                    "success": False,
                    "error_message": str(e),
                    "duration": duration,
                }

                if include_memory and HAS_PSUTIL:
                    try:
                        end_memory = psutil.Process().memory_info().rss
                        error_context["memory_mb"] = round(
                            end_memory / (1024 * 1024), 2
                        )
                    except Exception:
                        pass  # Ignore memory monitoring errors

                logger.error(f"Function failed: {op_name} - {str(e)} {error_context}")

                # Re-raise the exception
                raise

        return wrapper

    return decorator


def call_chain_tracker(max_depth: int = 10) -> dict[str, Any]:
    """Get current call chain information for debugging

    Args:
        max_depth: Maximum stack depth to capture

    Returns:
        Call chain information
    """
    stack_summary = traceback.extract_stack()

    # Remove the tracker function itself
    stack_frames = list(stack_summary[:-1])

    # Limit depth
    if len(stack_frames) > max_depth:
        stack_frames = stack_frames[-max_depth:]

    call_chain = []
    for frame in stack_frames:
        call_chain.append(
            {
                "file": frame.filename,
                "line": frame.lineno,
                "function": frame.name,
                "code": frame.line or "",
            }
        )

    return {
        "call_chain": call_chain,
        "depth": len(call_chain),
        "timestamp": time.time(),
    }


# Memory usage tracking optimization
_memory_cache: dict[str, Any] = {}
_memory_cache_timestamp: float = 0.0
_memory_cache_ttl: float = 1.0  # Cache TTL in seconds
_memory_sample_counter: int = 0
_memory_sample_interval: int = 10  # Sample every 10th call


def memory_usage_tracker(
    use_cache: bool = True, force_refresh: bool = False
) -> dict[str, Any]:
    """Get current memory usage information with caching and sampling

    Args:
        use_cache: Whether to use cached values to reduce overhead
        force_refresh: Whether to force refresh the cache

    Returns:
        Memory usage information
    """
    global _memory_cache, _memory_cache_timestamp, _memory_sample_counter

    current_time = time.time()

    # Implement sampling to reduce overhead
    _memory_sample_counter += 1
    if not force_refresh and _memory_sample_counter % _memory_sample_interval != 0:
        # Return cached data or minimal info for non-sampled calls
        if (
            use_cache
            and _memory_cache
            and (current_time - _memory_cache_timestamp) < _memory_cache_ttl
        ):
            return _memory_cache.copy()
        else:
            return {"timestamp": current_time, "sampled": False}

    # Check cache first
    if (
        use_cache
        and not force_refresh
        and _memory_cache
        and (current_time - _memory_cache_timestamp) < _memory_cache_ttl
    ):
        return _memory_cache.copy()

    memory_info: dict[str, Any] = {"timestamp": current_time, "sampled": True}

    if HAS_PSUTIL:
        try:
            process = psutil.Process()
            memory = process.memory_info()
            memory_info.update(
                {
                    "rss_mb": round(memory.rss / (1024 * 1024), 2),
                    "vms_mb": round(memory.vms / (1024 * 1024), 2),
                    "percent": float(process.memory_percent()),
                }
            )

            # System memory info (less frequent to reduce overhead)
            if _memory_sample_counter % (_memory_sample_interval * 5) == 0:
                system_memory = psutil.virtual_memory()
                memory_info["system"] = {
                    "total_mb": round(system_memory.total / (1024 * 1024), 2),
                    "available_mb": round(system_memory.available / (1024 * 1024), 2),
                    "percent_used": float(system_memory.percent),
                }
        except Exception:
            memory_info["error"] = "Failed to get memory info"
    else:
        memory_info["error"] = "psutil not available"

    # Update cache
    if use_cache:
        _memory_cache = memory_info.copy()
        _memory_cache_timestamp = current_time

    return memory_info


def log_performance(
    operation: str,
    duration: float,
    size: Optional[int] = None,
    logger_name: Optional[str] = None,
) -> None:
    """Log performance metrics for an operation

    Args:
        operation: Operation name
        duration: Duration in seconds
        size: Optional size in bytes
        logger_name: Optional logger name
    """
    from .logging_handlers import get_logger

    logger = get_logger(logger_name or "performance")

    message = f"Performance: {operation} completed in {duration:.3f}s"
    if size is not None:
        size_mb = size / (1024 * 1024)
        throughput = size_mb / duration if duration > 0 else 0
        message += f" ({size_mb:.2f}MB, {throughput:.2f}MB/s)"

    logger.info(message)


# Global instances for tracking
_dependency_tracker: DependencyTracker = DependencyTracker()
_execution_flow_tracker: ExecutionFlowTracker = ExecutionFlowTracker()


def get_dependency_tracker() -> DependencyTracker:
    """Get global dependency tracker instance"""
    return _dependency_tracker


def get_execution_flow_tracker() -> ExecutionFlowTracker:
    """Get global execution flow tracker instance"""
    return _execution_flow_tracker
