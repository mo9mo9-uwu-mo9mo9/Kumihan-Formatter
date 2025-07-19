"""List renderer for Kumihan-Formatter

This module handles rendering of list elements including unordered and ordered lists.
"""

from typing import Any

from ..ast_nodes import Node


class ListRenderer:
    """Renderer for list elements"""

    def __init__(self) -> None:
        """Initialize list renderer"""
        self._main_renderer: Any | None = None  # Will be set by main renderer

    def render_unordered_list(self, node: Node) -> str:
        """Render unordered list"""
        items = []
        if isinstance(node.content, list):
            for item in node.content:
                if isinstance(item, Node) and item.type == "li":
                    items.append(self.render_list_item(item))

        items_html = "\n".join(items)
        return f"<ul>\n{items_html}\n</ul>"

    def render_ordered_list(self, node: Node) -> str:
        """Render ordered list"""
        items = []
        if isinstance(node.content, list):
            for item in node.content:
                if isinstance(item, Node) and item.type == "li":
                    items.append(self.render_list_item(item))

        items_html = "\n".join(items)
        return f"<ol>\n{items_html}\n</ol>"

    def render_list_item(self, node: Node) -> str:
        """Render list item"""
        content = self._render_content(node.content, 0)
        return f"<li>{content}</li>"

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
                return self._main_renderer._render_node_with_depth(content, depth + 1)  # type: ignore
            else:
                return f"{{NODE:{content.type}}}"
        elif isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, Node):
                    # Handle nested nodes using main renderer if available
                    if self._main_renderer:
                        parts.append(
                            self._main_renderer._render_node_with_depth(item, depth + 1)
                        )
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
