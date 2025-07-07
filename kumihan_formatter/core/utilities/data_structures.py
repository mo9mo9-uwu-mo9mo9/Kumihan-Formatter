"""Data structure utilities

This module provides utilities for working with complex data structures
including dictionary operations and nested data manipulation.
"""

from typing import Any, Dict, List, Tuple


class DataStructureHelper:
    """Utilities for working with data structures"""

    @staticmethod
    def deep_merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge multiple dictionaries"""
        result: Dict[str, Any] = {}

        for d in dicts:
            for key, value in d.items():
                if (
                    key in result
                    and isinstance(result[key], dict)
                    and isinstance(value, dict)
                ):
                    result[key] = DataStructureHelper.deep_merge_dicts(
                        result[key], value
                    )
                else:
                    result[key] = value

        return result

    @staticmethod
    def flatten_dict(
        d: Dict[str, Any], parent_key: str = "", sep: str = "."
    ) -> Dict[str, Any]:
        """Flatten nested dictionary"""
        items: List[Tuple[str, Any]] = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(
                    DataStructureHelper.flatten_dict(v, new_key, sep=sep).items()
                )
            else:
                items.append((new_key, v))
        return dict(items)

    @staticmethod
    def unflatten_dict(d: Dict[str, Any], sep: str = ".") -> Dict[str, Any]:
        """Unflatten dictionary with dot notation keys"""
        result: Dict[str, Any] = {}
        for key, value in d.items():
            parts = key.split(sep)
            current = result
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value
        return result

    @staticmethod
    def get_nested_value(
        d: Dict[str, Any], key_path: str, default: Any = None, sep: str = "."
    ) -> Any:
        """Get nested dictionary value using dot notation"""
        keys = key_path.split(sep)
        current = d

        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default

    @staticmethod
    def set_nested_value(
        d: Dict[str, Any], key_path: str, value: Any, sep: str = "."
    ) -> None:
        """Set nested dictionary value using dot notation"""
        keys = key_path.split(sep)
        current = d

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value
