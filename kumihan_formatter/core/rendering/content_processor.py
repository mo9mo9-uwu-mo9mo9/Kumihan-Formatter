"""Content processing functionality extracted from main_renderer.py

This module handles recursive content rendering and depth tracking
to reduce the size of main_renderer.py and maintain the 300-line limit.
"""

from html import escape
from typing import TYPE_CHECKING, Any

from ..ast_nodes import Node
from .html_utils import process_text_content

if TYPE_CHECKING:
    from .main_renderer import HTMLRenderer


class ContentProcessor:
    """Handles recursive content rendering with depth tracking"""

    MAX_DEPTH = 100  # Prevent infinite recursion

    def __init__(self, main_renderer: "HTMLRenderer") -> None:
        """Initialize with main renderer instance"""
        self.main_renderer = main_renderer

    def render_content(self, content: Any, depth: int = 0) -> str:
        """
        Render node content recursively

        Args:
            content: Content to render (str, Node, list, or other)
            depth: Current recursion depth

        Returns:
            str: Rendered HTML content
        """
        if depth > self.MAX_DEPTH:
            return "[ERROR: Maximum recursion depth reached]"

        if content is None:
            return ""
        elif isinstance(content, str):
            return process_text_content(content)
        elif isinstance(content, Node):
            # Handle single Node objects
            return self.render_node_with_depth(content, depth + 1)
        elif isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, Node):
                    parts.append(self.render_node_with_depth(item, depth + 1))
                elif isinstance(item, str):
                    parts.append(process_text_content(item))
                else:
                    parts.append(process_text_content(str(item)))
            return "".join(parts)
        else:
            return process_text_content(str(content))

    def render_node_with_depth(self, node: Node, depth: int = 0) -> str:
        """
        Render a single node with depth tracking

        Args:
            node: Node to render
            depth: Current recursion depth

        Returns:
            str: Rendered HTML
        """
        if depth > self.MAX_DEPTH:
            return "[ERROR: Maximum recursion depth reached]"

        if not isinstance(node, Node):
            return escape(str(node))  # type: ignore

        # Route to specific rendering method on main renderer
        renderer_method = getattr(
            self.main_renderer, f"_render_{node.type}", self._render_generic_with_depth
        )

        # Check if it's the generic method
        if renderer_method.__name__ == "_render_generic":
            return self._render_generic_with_depth(node, depth)
        else:
            return renderer_method(node)

    def _render_generic_with_depth(self, node: Node, depth: int = 0) -> str:
        """Generic node renderer with depth tracking"""
        return self.main_renderer.element_renderer.render_generic(node)
