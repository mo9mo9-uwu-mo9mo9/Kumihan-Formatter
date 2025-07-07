"""Basic HTML element renderer for Kumihan-Formatter

This module handles rendering of basic HTML elements like paragraphs,
headings, lists, and other simple elements.
"""

from typing import Any

from ..ast_nodes import Node
from .html_utils import (
    create_simple_tag,
    escape_html,
    process_block_content,
    process_collapsible_content,
    process_text_content,
    render_attributes,
)


class ElementRenderer:
    """Renderer for basic HTML elements"""

    def __init__(self) -> None:
        """Initialize element renderer"""
        self.heading_counter = 0
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

    def render_div(self, node: Node) -> str:
        """Render div node"""
        content = self._render_div_content(node.content, 0)
        attributes = render_attributes(node.attributes)

        if attributes:
            return f"<div {attributes}>{content}</div>"
        else:
            return f"<div>{content}</div>"

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

    def render_h1(self, node: Node) -> str:
        """Render h1 heading"""
        return self.render_heading(node, 1)

    def render_h2(self, node: Node) -> str:
        """Render h2 heading"""
        return self.render_heading(node, 2)

    def render_h3(self, node: Node) -> str:
        """Render h3 heading"""
        return self.render_heading(node, 3)

    def render_h4(self, node: Node) -> str:
        """Render h4 heading"""
        return self.render_heading(node, 4)

    def render_h5(self, node: Node) -> str:
        """Render h5 heading"""
        return self.render_heading(node, 5)

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
        return f'<details{class_attr}><summary>{escape_html(summary)}</summary><div class="details-content">{content}</div></details>'

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

        return f'<span style="background-color:#ffe6e6; color:#d32f2f; padding:2px 4px; border-radius:3px;">{error_text}</span>'

    def render_toc_placeholder(self, node: Node) -> str:
        """Render table of contents marker (should be handled by TOC generator)"""
        return "<!-- TOC placeholder -->"

    def render_generic(self, node: Node) -> str:
        """Generic node renderer"""
        tag = node.type
        content = self._render_content(node.content)
        attributes = render_attributes(node.attributes)

        return create_simple_tag(tag, content, node.attributes)

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
                    parts.append(process_text_content(item))
                else:
                    parts.append(process_text_content(str(item)))
            return "".join(parts)
        else:
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
                    parts.append(process_block_content(item))
                else:
                    parts.append(process_block_content(str(item)))
            return "".join(parts)
        else:
            return process_block_content(str(content))

    def reset_counters(self) -> None:
        """Reset internal counters"""
        self.heading_counter = 0
