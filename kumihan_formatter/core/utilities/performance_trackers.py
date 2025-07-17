"""
パフォーマンス トラッキング ユーティリティ

コールチェーン・メモリ使用量のトラッキング機能
Issue #492 Phase 5A - performance_logger.py分割
"""

import traceback
from typing import Any

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


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
