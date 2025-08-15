import os
import ast
from typing import List, Tuple, Optional
from gemini_reports.halstead import calculate_halstead_metrics


def analyze_code(filepath: str) -> Tuple[int, int, int, int, float, float, float, float, float]:
    """
    Analyzes a Python file and returns Halstead metrics.

    Args:
        filepath (str): The path to the Python file.

    Returns:
        Tuple[int, int, int, int, float, float, float, float, float]: Halstead metrics.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            source_code = file.read()
        return calculate_halstead_metrics(source_code)
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}")
        return 0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0
    except Exception as e:
        print(f"Error analyzing {filepath}: {e}")
        return 0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0


def list_python_files(directory: str) -> List[str]:
    """
    Lists all Python files in a directory.

    Args:
        directory (str): The directory to search.

    Returns:
        List[str]: A list of Python file paths.
    """
    python_files: List[str] = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files
