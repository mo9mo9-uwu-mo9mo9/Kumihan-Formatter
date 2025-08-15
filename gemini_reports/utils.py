from datetime import datetime
from typing import Any, Union


def format_timestamp(timestamp: Union[float, int], fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Formats a Unix timestamp into a human-readable string.

    Args:
        timestamp: The Unix timestamp (float or int).
        fmt: The format string for datetime.strftime. Defaults to "%Y-%m-%d %H:%M:%S".

    Returns:
        A formatted datetime string.
    """
    dt_object: datetime = datetime.fromtimestamp(timestamp)
    return dt_object.strftime(fmt)


def safe_get(data: dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Safely gets a value from a dictionary, returning a default if the key is not found.

    Args:
        data: The dictionary to query.
        key: The key to look for.
        default: The value to return if the key is not found. Defaults to None.

    Returns:
        The value associated with the key, or the default value if the key is not found.
    """
    return data.get(key, default)


def calculate_average(numbers: list[Union[int, float]]) -> float:
    """
    Calculates the average of a list of numbers.

    Args:
        numbers: A list of integers or floats.

    Returns:
        The average of the numbers.

    Raises:
        ValueError: If the input list is empty, as an average cannot be calculated.
    """
    if not numbers:
        raise ValueError("Input list cannot be empty.")
    return sum(numbers) / len(numbers)
