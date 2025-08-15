import os
import json
from typing import Dict, Any, Optional

DEFAULT_THRESHOLD_CONFIG = {
    "volume": 1000.0,
    "difficulty": 50.0,
    "effort": 10000000.0,
    "time": 1000.0,
    "bugs": 1.0
}


def load_threshold_config(config_path: Optional[str] = None) -> Dict[str, float]:
    """
    Loads the threshold configuration from a JSON file.

    Args:
        config_path (Optional[str]): The path to the JSON configuration file.

    Returns:
        Dict[str, float]: A dictionary containing the threshold configuration.
    """
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
            return config
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading threshold config: {e}. Using default config.")
            return DEFAULT_THRESHOLD_CONFIG
    else:
        print("Using default threshold config.")
        return DEFAULT_THRESHOLD_CONFIG


def check_quality_thresholds(metrics: Dict[str, float], threshold_config: Dict[str, float]) -> Dict[str, bool]:
    """
    Checks if the Halstead metrics exceed the defined thresholds.

    Args:
        metrics (Dict[str, float]): A dictionary containing the Halstead metrics.
        threshold_config (Dict[str, float]): A dictionary containing the threshold configuration.

    Returns:
        Dict[str, bool]: A dictionary indicating whether each metric exceeds the threshold.
    """
    results: Dict[str, bool] = {}
    for metric, value in metrics.items():
        threshold = threshold_config.get(metric, float('inf'))  # Default to infinity if not defined
        results[metric] = value > threshold
    return results
