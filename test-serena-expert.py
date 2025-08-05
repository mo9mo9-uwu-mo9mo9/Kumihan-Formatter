"""
Simple test file for serena-expert system verification.

This module contains basic functions for testing the serena-expert hook system
and ensuring proper functionality of the automated development tools.
"""

from typing import Union


def calculate_sum(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    """
    Calculate the sum of two numbers.

    Args:
        a: First number (int or float)
        b: Second number (int or float)

    Returns:
        The sum of a and b

    Examples:
        >>> calculate_sum(2, 3)
        5
        >>> calculate_sum(2.5, 3.7)
        6.2
    """
    return a + b


def test_calculate_sum() -> None:
    """
    Basic test function for calculate_sum.

    Tests various scenarios:
    - Integer addition
    - Float addition
    - Mixed type addition
    """
    # Test integer addition
    result = calculate_sum(2, 3)
    assert result == 5, f"Expected 5, got {result}"

    # Test float addition
    result = calculate_sum(2.5, 3.7)
    assert result == 6.2, f"Expected 6.2, got {result}"

    # Test mixed type addition
    result = calculate_sum(2, 3.5)
    assert result == 5.5, f"Expected 5.5, got {result}"

    print("All tests passed!")


def main() -> None:
    """
    Main function for running the test.
    """
    print("Running serena-expert hook system test...")
    test_calculate_sum()
    print("Test completed successfully!")


if __name__ == "__main__":
    main()
