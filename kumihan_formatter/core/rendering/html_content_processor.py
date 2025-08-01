"""HTML content processing utilities extracted from html_utils.py

This module handles text content processing including newline conversion,
list markers, and block content processing.
"""

import re

from .html_escaping import escape_html

# typing.Any removed as unused


def process_text_content(text: str) -> str:
    """
    Process text content, converting newlines to <br> tags

    Args:
        text: Text to process

    Returns:
        str: Processed text with <br> tags
    """
    if not text:
        return ""

    # First convert newlines to <br> tags (before HTML escaping)
    processed = text.replace("\n", "<br>")
    
    # Then HTML escape the content, but preserve <br> tags
    processed = escape_html(processed).replace("&lt;br&gt;", "<br>")

    return processed


def process_block_content(text: str) -> str:
    """
    Process block content with list marker conversion

    Args:
        text: Text to process

    Returns:
        str: Processed text with list markers converted to HTML
    """
    if not text:
        return ""

    # Convert list markers to HTML lists
    processed = _convert_list_markers(text)

    # Convert newlines to <br> tags for remaining content
    processed = processed.replace("\n", "<br>")

    return processed


def process_collapsible_content(text: str) -> str:
    """
    Process collapsible content with special handling

    Args:
        text: Text to process

    Returns:
        str: Processed text for collapsible elements
    """
    if not text:
        return ""

    # Handle list markers with HTML preservation
    processed = _convert_list_markers_with_html(text)

    # Convert remaining newlines to <br> tags
    processed = processed.replace("\n", "<br>")

    return processed


def _convert_list_markers(text: str) -> str:
    """
    Convert list markers to HTML lists

    Args:
        text: Text containing list markers

    Returns:
        str: Text with HTML lists
    """
    if not text:
        return ""

    # Convert unordered list markers (-, *, +)
    lines = text.split("\n")
    result_lines = []
    in_list = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith(("- ", "* ", "+ ")):
            if not in_list:
                result_lines.append("<ul>")
                in_list = True
            content = stripped[2:].strip()
            result_lines.append(f"<li>{escape_html(content)}</li>")
        else:
            if in_list:
                result_lines.append("</ul>")
                in_list = False
            result_lines.append(escape_html(line))

    if in_list:
        result_lines.append("</ul>")

    return "\n".join(result_lines)


def _convert_lists_to_html(text: str) -> str:
    """
    Convert various list formats to HTML

    Args:
        text: Text containing various list formats

    Returns:
        str: Text with HTML lists
    """
    if not text:
        return ""

    # Handle both ordered and unordered lists
    lines = text.split("\n")
    result_lines = []
    in_ul = False
    in_ol = False

    for line in lines:
        stripped = line.strip()

        # Unordered list markers
        if stripped.startswith(("- ", "* ", "+ ")):
            if in_ol:
                result_lines.append("</ol>")
                in_ol = False
            if not in_ul:
                result_lines.append("<ul>")
                in_ul = True
            content = stripped[2:].strip()
            result_lines.append(f"<li>{escape_html(content)}</li>")

        # Ordered list markers (1. 2. etc.)
        elif re.match(r"^\d+\.\s+", stripped):
            if in_ul:
                result_lines.append("</ul>")
                in_ul = False
            if not in_ol:
                result_lines.append("<ol>")
                in_ol = True
            content = re.sub(r"^\d+\.\s+", "", stripped)
            result_lines.append(f"<li>{escape_html(content)}</li>")

        else:
            if in_ul:
                result_lines.append("</ul>")
                in_ul = False
            if in_ol:
                result_lines.append("</ol>")
                in_ol = False
            result_lines.append(escape_html(line))

    # Close any remaining lists
    if in_ul:
        result_lines.append("</ul>")
    if in_ol:
        result_lines.append("</ol>")

    return "\n".join(result_lines)


def _convert_list_markers_with_html(text: str) -> str:
    """
    Convert list markers while preserving existing HTML

    Args:
        text: Text that may contain existing HTML

    Returns:
        str: Text with list markers converted, HTML preserved
    """
    if not text:
        return ""

    # Check if text already contains HTML
    if "<" in text and ">" in text:
        # If it contains HTML, be more careful about conversion
        return _convert_lists_to_html(text)
    else:
        # If no HTML, use simple conversion
        return _convert_list_markers(text)
