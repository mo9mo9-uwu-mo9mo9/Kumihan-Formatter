"""Log size control and management utilities

Single Responsibility Principle適用: ログサイズ制御の分離
Issue #476 Phase3対応 - log_optimization.py分割
"""

from typing import Any, Dict, Optional


class LogSizeController:
    """Log size control and management

    Provides intelligent log size management:
    - Automatic log rotation
    - Content compression
    - Selective retention
    - Size-based filtering
    """

    def __init__(self, structured_logger: Any):
        self.structured_logger = structured_logger
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

    def should_include_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
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
        self, message: str, context: Optional[Dict[str, Any]] = None
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
                import json

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
        elif priority == "normal" and size_mb > 5.0:  # 5MB limit for normal priority
            return True

        return False
