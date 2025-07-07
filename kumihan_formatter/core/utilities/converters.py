"""Type conversion utilities

This module provides safe type conversion functions
and list manipulation utilities.
"""

from typing import Any, Iterator, List


def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert value to integer"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_bool(value: Any, default: bool = False) -> bool:
    """Safely convert value to boolean"""
    if isinstance(value, bool):
        return value
    elif isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    elif isinstance(value, (int, float)):
        return bool(value)
    else:
        return default


def chunks(lst: list[Any], n: int) -> Iterator[list[Any]]:
    """Yield successive n-sized chunks from list"""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]
