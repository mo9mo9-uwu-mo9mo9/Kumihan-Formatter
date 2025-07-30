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
    Render HTML attributes with Phase 4 enhancements

    Phase 4 improvements:
    - Color attribute processing
    - CSS class name normalization
    - Accessibility attribute validation

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
            # Process specific attribute types (Issue #665 Phase 4)
            processed_value = _process_attribute_value(key, value)
            if processed_value is not None:
                escaped_value = escape(str(processed_value))
                attr_parts.append(f'{key}="{escaped_value}"')

    return " ".join(attr_parts)


def render_attributes_with_enhancements(
    tag: str,
    attributes: dict[str, Any] | None,
    content: str = "",
    formatter=None,
) -> str:
    """
    Render HTML attributes with accessibility and semantic enhancements
    (Issue #665 Phase 4)

    Args:
        tag: HTML tag name
        attributes: Dictionary of attributes
        content: Element content for context
        formatter: HTMLFormatter instance for advanced processing

    Returns:
        str: Enhanced HTML attributes string
    """
    # Always create attributes dict to ensure Phase 4 features are applied
    if not attributes:
        attributes = {}
    else:
        attributes = attributes.copy()

    # Always add accessibility attributes if formatter is available
    if formatter and hasattr(formatter, "add_accessibility_attributes"):
        attributes = formatter.add_accessibility_attributes(tag, attributes, content)

    # Always add standardized CSS classes if formatter is available
    if formatter and hasattr(formatter, "generate_css_class"):
        existing_class = attributes.get("class", "")
        semantic_class = formatter.generate_css_class(tag)

        if existing_class:
            attributes["class"] = f"{semantic_class} {existing_class}"
        else:
            attributes["class"] = semantic_class

    # Always return processed attributes, even if originally empty
    return render_attributes(attributes)


def _process_attribute_value(key: str, value: Any) -> Any:
    """
    Process specific attribute values (Issue #665 Phase 4)

    Args:
        key: Attribute name
        value: Attribute value

    Returns:
        Processed attribute value or None if invalid
    """
    if key in ["style"]:
        # Process inline styles with color validation
        return _process_style_attribute(str(value))
    elif key in ["color", "background-color", "border-color"]:
        # Process color attributes
        return _process_color_value(str(value))
    elif key == "class":
        # Normalize CSS class names
        return _normalize_css_classes(str(value))

    return value


def _process_style_attribute(style: str) -> str:
    """Process style attribute with color validation"""
    if not style:
        return style

    # Simple style processing - could be enhanced
    style_parts = []
    for part in style.split(";"):
        part = part.strip()
        if ":" in part:
            prop, val = part.split(":", 1)
            prop = prop.strip()
            val = val.strip()

            # Process color properties
            if "color" in prop.lower():
                processed_color = _process_color_value(val)
                if processed_color:
                    style_parts.append(f"{prop}: {processed_color}")
            else:
                style_parts.append(f"{prop}: {val}")

    return "; ".join(style_parts)


def _process_color_value(color: str) -> str:
    """Process color value with validation"""
    if not color:
        return color

    color = color.strip()

    # Basic color validation - could be enhanced with HTMLFormatter
    if color.startswith("#") and len(color) in [4, 7]:
        return color.lower()
    elif color.startswith(("rgb(", "rgba(", "hsl(", "hsla(")):
        return color
    elif color.lower() in ["black", "white", "red", "green", "blue", "transparent"]:
        return color.lower()

    return color


def _normalize_css_classes(class_string: str) -> str:
    """Normalize CSS class names"""
    if not class_string:
        return class_string

    # Split, clean, and rejoin class names
    classes = []
    for cls in class_string.split():
        cls = cls.strip()
        if cls:
            # Normalize to lowercase with hyphens
            normalized = cls.lower().replace("_", "-")
            classes.append(normalized)

    return " ".join(classes)


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
