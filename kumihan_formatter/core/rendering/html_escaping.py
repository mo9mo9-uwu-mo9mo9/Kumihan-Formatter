"""HTML escaping utilities extracted from html_utils.py

This module handles HTML escaping and attribute rendering
to maintain the 300-line limit for html_utils.py.
"""

import re
from html import escape
from typing import Any


def escape_html(text: str) -> str:
    """
    Escape HTML special characters

    Args:
        text: Text to escape

    Returns:
        str: HTML-escaped text
    """
    return escape(text)


def render_attributes(attributes: dict[str, Any] | None) -> str:
    """
    Render HTML attributes

    Args:
        attributes: Dictionary of attributes

    Returns:
        str: Formatted HTML attributes string
    """
    if not attributes:
        return ""

    attr_parts = []
    for key, value in attributes.items():
        if value is not None:
            escaped_value = escape(str(value))
            attr_parts.append(f'{key}="{escaped_value}"')

    return " ".join(attr_parts)


def contains_html_tags(text: str) -> bool:
    """
    Check if text contains HTML tags

    Args:
        text: Text to check

    Returns:
        bool: True if text contains HTML tags
    """
    # Simple HTML tag detection
    html_pattern = r"<[^>]+>"
    return bool(re.search(html_pattern, text))
