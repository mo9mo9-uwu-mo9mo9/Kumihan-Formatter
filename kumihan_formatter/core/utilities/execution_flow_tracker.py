"""Execution flow tracking functionality for structured logging

Single Responsibility Principle適用: 実行フロー追跡機能の分離
Issue #476 Phase5対応 - structured_logger.py分割
"""

from __future__ import annotations

import time
from typing import Any, Optional

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Performance logger は別途インポートが必要
try:
    from .performance_logger import call_chain_tracker, memory_usage_tracker
except ImportError:
    # フォールバック実装
    class DummyTracker:
        def enter_function(self, *args: Any, **kwargs: Any) -> None:
            pass

        def exit_function(self, *args: Any, **kwargs: Any) -> None:
            pass

        def track_memory(self, *args: Any, **kwargs: Any) -> None:
            pass

    _dummy_tracker = DummyTracker()
    call_chain_tracker = _dummy_tracker  # type: ignore
    memory_usage_tracker = _dummy_tracker  # type: ignore
from .structured_logger_base import StructuredLogger


class ExecutionFlowTracker:
    """Tracks execution flow through the application

    Provides detailed tracking of:
    - Function call hierarchy
    - Execution times
    - Memory usage
    """

    def __init__(self, logger: StructuredLogger):
        self.logger = logger
        self.execution_stack: list[dict[str, Any]] = []
        self.flow_history: list[dict[str, Any]] = []

    def enter_function(
        self,
        function_name: str,
        module: Optional[str] = None,
        args: Optional[dict[str, Any]] = None,
        track_memory: bool = False,
    ) -> dict[str, Any]:
        """Track entering a function

        Args:
            function_name: Name of the function
            module: Module containing the function
            args: Function arguments (sanitized)
            track_memory: Whether to track memory usage

        Returns:
            Context dict to pass to exit_function
        """
        entry_time = time.time()
        memory_before = None

        if track_memory and HAS_PSUTIL:
            try:
                process = psutil.Process()
                memory_before = process.memory_info().rss / 1024 / 1024  # MB
            except Exception:
                pass

        context = {
            "function": function_name,
            "module": module,
            "entry_time": entry_time,
            "memory_before": memory_before,
            "depth": len(self.execution_stack),
        }

        if args:
            context["args"] = args

        self.execution_stack.append(context)

        # パフォーマンスロガーと統合
        if hasattr(call_chain_tracker, "enter_function"):
            call_chain_tracker.enter_function(function_name, module)
        if track_memory and hasattr(memory_usage_tracker, "track_memory"):
            memory_usage_tracker.track_memory(function_name, "enter")

        self.logger.debug(
            (
                f"Entering {module}.{function_name}"
                if module
                else f"Entering {function_name}"
            ),
            execution_flow=True,
            **context,
        )

        return context

    def exit_function(
        self,
        context: dict[str, Any],
        result: Any = None,
        error: Optional[Exception] = None,
        track_memory: bool = False,
    ) -> None:
        """Track exiting a function

        Args:
            context: Context from enter_function
            result: Function result (sanitized)
            error: Exception if function failed
            track_memory: Whether to track memory usage
        """
        exit_time = time.time()
        duration = exit_time - context["entry_time"]
        memory_after = None
        memory_delta = None

        if track_memory and HAS_PSUTIL and context.get("memory_before") is not None:
            try:
                process = psutil.Process()
                memory_after = process.memory_info().rss / 1024 / 1024  # MB
                memory_delta = memory_after - context["memory_before"]
            except Exception:
                pass

        # スタックから削除
        if self.execution_stack and self.execution_stack[-1] == context:
            self.execution_stack.pop()

        # 実行情報を記録
        flow_info = {
            "function": context["function"],
            "module": context.get("module"),
            "duration": duration,
            "success": error is None,
            "depth": context["depth"],
            "timestamp": exit_time,
        }

        if memory_delta is not None:
            flow_info["memory_delta_mb"] = memory_delta

        if error:
            flow_info["error"] = {
                "type": type(error).__name__,
                "message": str(error),
            }

        self.flow_history.append(flow_info)

        # パフォーマンスロガーと統合
        if hasattr(call_chain_tracker, "exit_function"):
            call_chain_tracker.exit_function(
                context["function"], duration, error is not None
            )
        if track_memory and hasattr(memory_usage_tracker, "track_memory"):
            memory_usage_tracker.track_memory(context["function"], "exit")

        # ログ出力
        log_method = self.logger.error if error else self.logger.debug
        log_message = (
            f"Exiting {context.get('module')}.{context['function']}"
            if context.get("module")
            else f"Exiting {context['function']}"
        )

        log_method(
            f"{log_message} (duration: {duration:.3f}s)",
            execution_flow=True,
            duration=duration,
            memory_delta_mb=memory_delta,
            success=error is None,
            **({"error": str(error)} if error else {}),
        )

    def get_current_flow(self) -> dict[str, Any]:
        """Get current execution flow state

        Returns:
            Dict containing current flow information
        """
        return {
            "current_stack": [
                {
                    "function": item["function"],
                    "module": item.get("module"),
                    "depth": item["depth"],
                    "duration_so_far": time.time() - item["entry_time"],
                }
                for item in self.execution_stack
            ],
            "stack_depth": len(self.execution_stack),
            "flow_history_size": len(self.flow_history),
            "recent_flows": self.flow_history[-10:],  # 最新10件
        }
