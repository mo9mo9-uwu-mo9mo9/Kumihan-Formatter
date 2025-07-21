"""Basic HTML element renderer for Kumihan-Formatter

This module handles rendering of basic HTML elements like paragraphs,
strong, emphasis, and simple elements.
"""

from typing import Any

from ..ast_nodes import Node
from .html_utils import escape_html, process_text_content, render_attributes


class BasicElementRenderer:
    """Renderer for basic HTML elements"""

    def __init__(self) -> None:
        """Initialize basic element renderer"""
        self._main_renderer: Any | None = None  # Will be set by main renderer

    def render_paragraph(self, node: Node) -> str:
        """Render paragraph node"""
        content = self._render_content(node.content, 0)
        return f"<p>{content}</p>"

    def render_strong(self, node: Node) -> str:
        """Render strong (bold) node"""
        content = self._render_content(node.content, 0)
        return f"<strong>{content}</strong>"

    def render_emphasis(self, node: Node) -> str:
        """Render emphasis (italic) node"""
        content = self._render_content(node.content, 0)
        return f"<em>{content}</em>"

    def render_preformatted(self, node: Node) -> str:
        """Render preformatted text"""
        # For code blocks, preserve whitespace and escape HTML
        if isinstance(node.content, str):
            content = escape_html(node.content)
        else:
            content = self._render_content(node.content, 0)

        attributes = render_attributes(node.attributes)

        if attributes:
            return f"<pre {attributes}>{content}</pre>"
        else:
            return f"<pre>{content}</pre>"

    def render_code(self, node: Node) -> str:
        """Render inline code"""
        if isinstance(node.content, str):
            content = escape_html(node.content)
        else:
            content = self._render_content(node.content, 0)

        attributes = render_attributes(node.attributes)

        if attributes:
            return f"<code {attributes}>{content}</code>"
        else:
            return f"<code>{content}</code>"

    def render_image(self, node: Node) -> str:
        """Render image element"""
        filename = node.content if isinstance(node.content, str) else str(node.content)
        alt_text = node.get_attribute("alt", "")

        # Construct image path
        src = f"images/{filename}"

        if alt_text:
            return f'<img src="{escape_html(src)}" alt="{escape_html(alt_text)}" />'
        else:
            return f'<img src="{escape_html(src)}" />'

    def render_error(self, node: Node) -> str:
        """Render error node"""
        content = escape_html(str(node.content))
        line_number = node.get_attribute("line")

        error_text = f"[ERROR: {content}]"
        if line_number:
            error_text = f"[ERROR (Line {line_number}): {content}]"

        return (
            f'<span style="background-color:#ffe6e6; color:#d32f2f; '
            f'padding:2px 4px; border-radius:3px;">{error_text}</span>'
        )

    def render_toc_placeholder(self, node: Node) -> str:
        """Render table of contents marker (should be handled by TOC generator)"""
        return "<!-- TOC placeholder -->"

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
                        parts.append(
                            self._main_renderer._render_node_with_depth(item, depth + 1)
                        )
                    else:
                        parts.append(f"{{NODE:{item.type}}}")
                elif isinstance(item, str):
                    parts.append(process_text_content(item))
                else:
                    parts.append(process_text_content(str(item)))
            return "".join(parts)
        else:
            return process_text_content(str(content))
