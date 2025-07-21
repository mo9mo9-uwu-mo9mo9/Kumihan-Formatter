"""Div and details renderer for Kumihan-Formatter

This module handles rendering of div elements and details/summary elements.
"""

from typing import Any

from ..ast_nodes import Node
from .html_utils import (
    escape_html,
    process_block_content,
    process_collapsible_content,
    render_attributes,
)


class DivRenderer:
    """Renderer for div and details elements"""

    def __init__(self) -> None:
        """Initialize div renderer"""
        self._main_renderer: Any | None = None  # Will be set by main renderer

    def render_div(self, node: Node) -> str:
        """Render div node"""
        content = self._render_div_content(node.content, 0)
        attributes = render_attributes(node.attributes)

        if attributes:
            return f"<div {attributes}>{content}</div>"
        else:
            return f"<div>{content}</div>"

    def render_details(self, node: Node) -> str:
        """Render details/summary element"""
        # Use special processing for collapsible content to handle lists properly
        if node.content and isinstance(node.content[0], str):
            # Process the raw text content with proper list handling
            content = process_collapsible_content(node.content[0])
        else:
            # Fallback to normal content rendering
            content = self._render_content(node.content, 0)

        summary = node.get_attribute("summary", "詳細を表示")

        # Check if this is a spoiler block
        is_spoiler = node.get_attribute("spoiler", False) or summary == "ネタバレを表示"
        class_attr = ' class="spoiler"' if is_spoiler else ""

        # Wrap content in a div to ensure CSS selectors work properly
        return (
            f"<details{class_attr}><summary>{escape_html(summary)}</summary>"
            f'<div class="details-content">{content}</div></details>'
        )

    def _render_content(self, content: Any, depth: int = 0) -> str:
        """
        Render node content (recursive)

        Args:
            content: Content to render
            depth: Current recursion depth

        Returns:
            str: Rendered content
        """
        max_depth = 100  # Prevent infinite recursion

        if depth > max_depth:
            return "[ERROR: Maximum recursion depth reached]"

        if content is None:
            return ""
        elif isinstance(content, str):
            from .html_utils import process_text_content

            return process_text_content(content)
        elif isinstance(content, Node):
            # Handle single Node objects using main renderer if available
            if self._main_renderer:
                result = self._main_renderer._render_node_with_depth(content, depth + 1)
                return str(result)
            else:
                return f"{{NODE:{content.type}}}"
        elif isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, Node):
                    # Handle nested nodes using main renderer if available
                    if self._main_renderer:
                        result = self._main_renderer._render_node_with_depth(
                            item, depth + 1
                        )
                        parts.append(str(result))
                    else:
                        parts.append(f"{{NODE:{item.type}}}")
                elif isinstance(item, str):
                    from .html_utils import process_text_content

                    parts.append(process_text_content(item))
                else:
                    from .html_utils import process_text_content

                    parts.append(process_text_content(str(item)))
            return "".join(parts)
        else:
            from .html_utils import process_text_content

            return process_text_content(str(content))

    def _render_div_content(self, content: Any, depth: int = 0) -> str:
        """
        Render div content with list marker conversion

        Args:
            content: Content to render
            depth: Current recursion depth

        Returns:
            str: Rendered content with list markers converted
        """
        max_depth = 100  # Prevent infinite recursion

        if depth > max_depth:
            return "[ERROR: Maximum recursion depth reached]"

        if content is None:
            return ""
        elif isinstance(content, str):
            return process_block_content(content)
        elif isinstance(content, Node):
            # Handle single Node objects using main renderer if available
            if self._main_renderer:
                result = self._main_renderer._render_node_with_depth(content, depth + 1)
                return str(result)
            else:
                return f"{{NODE:{content.type}}}"
        elif isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, Node):
                    # Handle nested nodes using main renderer if available
                    if self._main_renderer:
                        result = self._main_renderer._render_node_with_depth(
                            item, depth + 1
                        )
                        parts.append(str(result))
                    else:
                        parts.append(f"{{NODE:{item.type}}}")
                elif isinstance(item, str):
                    parts.append(process_block_content(item))
                else:
                    parts.append(process_block_content(str(item)))
            return "".join(parts)
        else:
            return process_block_content(str(content))
