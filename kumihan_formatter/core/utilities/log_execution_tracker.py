"""
ログ 実行フロートラッカー

関数呼び出しシーケンス・タイミング・リソース使用量の追跡
Issue #492 Phase 5A - log_analysis.py分割
"""

import logging
import time
from typing import Any, Optional, Union


class ExecutionFlowTracker:
    """Track execution flow for debugging and optimization

    Records function call sequences, timing, and resource usage
    to help Claude Code understand application behavior.
    """

    def __init__(self, logger: Any) -> None:
        """Initialize with a StructuredLogger instance"""
        self.logger = logger
        self.execution_stack: list[dict[str, Any]] = []
        self.flow_id = str(int(time.time() * 1000))  # Unique flow identifier

    def enter_function(
        self,
        function_name: str,
        module_name: str,
        args_info: Optional[dict[str, Any]] = None,
    ) -> str:
        """Record function entry in execution flow

        Args:
            function_name: Name of function being entered
            module_name: Module containing the function
            args_info: Information about function arguments

        Returns:
            Unique frame ID for this function call
        """
        frame_id = f"{self.flow_id}_{len(self.execution_stack)}"
        start_time = time.time()

        frame_info = {
            "frame_id": frame_id,
            "function_name": function_name,
            "module_name": module_name,
            "start_time": start_time,
            "args_info": args_info,
            "depth": len(self.execution_stack),
        }

        self.execution_stack.append(frame_info)

        # Log function entry
        self.logger.debug(
            f"Function entry: {function_name}",
            flow_id=self.flow_id,
            frame_id=frame_id,
            function=function_name,
            module=module_name,
            depth=len(self.execution_stack),
            args_info=args_info,
            claude_hint="Track execution flow for debugging call sequences",
        )

        return frame_id

    def exit_function(
        self,
        frame_id: str,
        success: bool = True,
        result_info: Optional[dict[str, Any]] = None,
        error_info: Optional[dict[str, Any]] = None,
    ) -> None:
        """Record function exit in execution flow

        Args:
            frame_id: Frame ID from enter_function
            success: Whether function completed successfully
            result_info: Information about function result
            error_info: Information about any error that occurred
        """
        if not self.execution_stack:
            return

        # Find and remove the frame
        frame = None
        for i, stack_frame in enumerate(reversed(self.execution_stack)):
            if stack_frame["frame_id"] == frame_id:
                frame = self.execution_stack.pop(-(i + 1))
                break

        if not frame:
            return

        end_time = time.time()
        duration = end_time - frame["start_time"]

        # Log function exit
        exit_context = {
            "flow_id": self.flow_id,
            "frame_id": frame_id,
            "function": frame["function_name"],
            "module": frame["module_name"],
            "duration_ms": round(duration * 1000, 2),
            "success": success,
            "depth": frame["depth"],
        }

        if result_info:
            exit_context["result_info"] = result_info

        if error_info:
            exit_context["error_info"] = error_info

        level = logging.DEBUG if success else logging.WARNING
        self.logger.log_with_context(
            level,
            f"Function exit: {frame['function_name']}",
            **exit_context,
            claude_hint="Analyze execution timing and call patterns",
        )

    def get_current_flow(self) -> dict[str, Any]:
        """Get current execution flow state

        Returns:
            Dictionary with current execution stack and flow info
        """
        return {
            "flow_id": self.flow_id,
            "current_stack": [
                {
                    "function": frame["function_name"],
                    "module": frame["module_name"],
                    "depth": frame["depth"],
                    "duration_so_far": round(
                        (time.time() - frame["start_time"]) * 1000, 2
                    ),
                }
                for frame in self.execution_stack
            ],
            "stack_depth": len(self.execution_stack),
            "total_execution_time": (
                round((time.time() - self.execution_stack[0]["start_time"]) * 1000, 2)
                if self.execution_stack
                else 0
            ),
        }
