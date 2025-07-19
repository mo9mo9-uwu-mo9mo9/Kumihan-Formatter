"""Heading renderer for Kumihan-Formatter

This module handles rendering of heading elements and heading-related functionality.
"""

from typing import Any

from ..ast_nodes import Node
from .html_utils import render_attributes


class HeadingRenderer:
    """Renderer for heading elements"""

    def __init__(self) -> None:
        """Initialize heading renderer"""
        self.heading_counter = 0
        self._main_renderer: Any | None = None  # Will be set by main renderer

    def render_heading(self, node: Node, level: int) -> str:
        """
        Render heading with ID

        Args:
            node: Heading node
            level: Heading level (1-6)

        Returns:
            str: HTML heading element
        """
        content = self._render_content(node.content, 0)

        # Generate heading ID if not present
        heading_id = node.get_attribute("id")
        if not heading_id:
            self.heading_counter += 1
            heading_id = f"heading-{self.heading_counter}"
            node.add_attribute("id", heading_id)

        attributes = render_attributes(node.attributes)
        tag = f"h{level}"

        if attributes:
            return f"<{tag} {attributes}>{content}</{tag}>"
        else:
            return f"<{tag}>{content}</{tag}>"

    # Heading level methods - delegate to render_heading
    def render_h1(self, node: Node) -> str:
        return self.render_heading(node, 1)

    def render_h2(self, node: Node) -> str:
        return self.render_heading(node, 2)

    def render_h3(self, node: Node) -> str:
        return self.render_heading(node, 3)

    def render_h4(self, node: Node) -> str:
        return self.render_heading(node, 4)

    def render_h5(self, node: Node) -> str:
        return self.render_heading(node, 5)

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
        elif hasattr(content, "type"):  # Node object
            # Handle single Node objects using main renderer if available
            if self._main_renderer:
                return self._main_renderer._render_node_with_depth(content, depth + 1)  # type: ignore
            else:
                return f"{{NODE:{content.type}}}"
        elif isinstance(content, list):
            parts = []
            for item in content:
                if hasattr(item, "type"):  # Node object
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

    def reset_counters(self) -> None:
        """Reset internal counters"""
        self.heading_counter = 0
