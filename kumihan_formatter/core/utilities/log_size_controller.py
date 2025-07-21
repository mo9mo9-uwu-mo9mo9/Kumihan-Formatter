"""
ログ サイズコントローラー

ログサイズ制御・圧縮・保持管理機能
Issue #492 Phase 5A - log_optimization.py分割
"""

import json
from typing import Any, Optional


class LogSizeController:
    """Phase 4: Log size control and management

    Provides intelligent log size management:
    - Automatic log rotation
    - Content compression
    - Selective retention
    - Size-based filtering
    """

    def __init__(self, logger: Any) -> None:
        """Initialize with a StructuredLogger instance"""
        self.logger = logger
        self.size_limits = {
            "max_file_size_mb": 50,
            "max_total_size_mb": 200,
            "max_entries_per_file": 100000,
            "retention_days": 7,
        }
        self.compression_enabled = True
        self.content_filters = {
            "max_message_length": 1000,
            "max_context_entries": 20,
            "sensitive_data_removal": True,
        }

    def should_include_context(self, context: dict[str, Any]) -> dict[str, Any]:
        """Filter context data to control log size

        Args:
            context: Original context dictionary

        Returns:
            Filtered context dictionary
        """
        filtered = {}
        entry_count = 0

        for key, value in context.items():
            # Limit number of context entries
            if entry_count >= self.content_filters["max_context_entries"]:
                filtered["_truncated"] = (
                    f"... {len(context) - entry_count} more entries"
                )
                break

            # Filter large values
            if (
                isinstance(value, str)
                and len(value) > self.content_filters["max_message_length"]
            ):
                filtered[key] = (
                    value[: self.content_filters["max_message_length"]]
                    + "... [truncated]"
                )
            elif (
                isinstance(value, (list, dict))
                and len(str(value)) > self.content_filters["max_message_length"]
            ):
                filtered[key] = f"[Large {type(value).__name__}: {len(value)} items]"
            else:
                filtered[key] = value

            entry_count += 1

        return filtered

    def format_message_for_size(self, message: str) -> str:
        """Format message to control size

        Args:
            message: Original message

        Returns:
            Potentially truncated message
        """
        max_length = self.content_filters["max_message_length"]

        if len(message) <= max_length:
            return message

        # Truncate with meaningful suffix
        return message[: max_length - 15] + "... [truncated]"

    def estimate_log_size(
        self, message: str, context: Optional[dict[str, Any]] = None
    ) -> int:
        """Estimate the size of a log entry in bytes

        Args:
            message: Log message
            context: Context data

        Returns:
            Estimated size in bytes
        """
        # Base message size
        size = len(message.encode("utf-8"))

        # Add context size if present
        if context:
            try:
                context_json = json.dumps(context, ensure_ascii=False)
                size += len(context_json.encode("utf-8"))
            except (TypeError, ValueError):
                # Fallback estimation
                size += len(str(context).encode("utf-8"))

        # Add overhead for JSON structure
        size += 200  # Estimated JSON overhead

        return size

    def should_skip_due_to_size(
        self, estimated_size: int, priority: str = "normal"
    ) -> bool:
        """Determine if log should be skipped due to size constraints

        Args:
            estimated_size: Estimated log entry size in bytes
            priority: Priority level (high, normal, low)

        Returns:
            True if log should be skipped
        """
        # Never skip high priority logs
        if priority == "high":
            return False

        # Skip very large logs for normal/low priority
        size_mb = estimated_size / (1024 * 1024)

        if priority == "low" and size_mb > 1.0:  # 1MB limit for low priority
            return True

        if priority == "normal" and size_mb > 5.0:  # 5MB limit for normal priority
            return True

        return False

    def get_size_statistics(self) -> dict[str, Any]:
        """Get current size statistics

        Returns:
            Dictionary with size-related statistics
        """
        return {
            "size_limits": self.size_limits,
            "content_filters": self.content_filters,
            "compression_enabled": self.compression_enabled,
            "estimated_overhead_bytes": 200,  # JSON overhead
        }

    def optimize_for_claude_code(self, context: dict[str, Any]) -> dict[str, Any]:
        """Optimize log content specifically for Claude Code consumption

        Args:
            context: Original context

        Returns:
            Optimized context for Claude Code
        """
        optimized: dict[str, Any] = {}

        # Add priority fields first
        self._add_priority_fields(context, optimized)

        # Add analysis and suggestions
        self._add_analysis_and_suggestions(context, optimized)

        # Add location and performance info
        self._add_location_info(context, optimized)
        self._add_performance_metrics(context, optimized)

        # Fill remaining space with other context
        self._add_remaining_context(context, optimized)

        return optimized

    def _add_priority_fields(
        self, context: dict[str, Any], optimized: dict[str, Any]
    ) -> None:
        """優先度の高いフィールドを追加"""
        if "claude_hint" in context:
            optimized["claude_hint"] = context["claude_hint"]

        if "operation" in context:
            optimized["operation"] = context["operation"]

    def _add_analysis_and_suggestions(
        self, context: dict[str, Any], optimized: dict[str, Any]
    ) -> None:
        """分析と提案を追加"""
        if "error_analysis" in context:
            optimized["error_analysis"] = context["error_analysis"]

        if "suggestion" in context or "suggestions" in context:
            optimized["suggestion"] = context.get("suggestion") or context.get(
                "suggestions"
            )

    def _add_location_info(
        self, context: dict[str, Any], optimized: dict[str, Any]
    ) -> None:
        """ファイルや行情報を追加"""
        location_keys = ["file_path", "line_number", "function", "module"]
        for key in location_keys:
            if key in context:
                optimized[key] = context[key]

    def _add_performance_metrics(
        self, context: dict[str, Any], optimized: dict[str, Any]
    ) -> None:
        """パフォーマンス指標を追加"""
        performance_keys = ["duration_ms", "memory_mb", "success"]
        for key in performance_keys:
            if key in context:
                optimized[key] = context[key]

    def _add_remaining_context(
        self, context: dict[str, Any], optimized: dict[str, Any]
    ) -> None:
        """残りのコンテキストを制限まで追加"""
        remaining_space = self.content_filters["max_context_entries"] - len(optimized)
        for key, value in context.items():
            if key not in optimized and remaining_space > 0:
                optimized[key] = value
                remaining_space -= 1
