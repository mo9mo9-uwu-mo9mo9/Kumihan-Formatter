"""Element renderer for Kumihan-Formatter - integration of split components

This module provides a unified interface for rendering all HTML elements by
integrating specialized renderer components.

Issue #490対応 - ファイルサイズ制限遵守により分割統合:
- basic_element_renderer.py: 基本要素レンダリング
- heading_renderer.py: 見出し要素レンダリング
- list_renderer.py: リスト要素レンダリング
- div_renderer.py: div・details要素レンダリング
"""

from typing import Any

from ..ast_nodes import Node
from .basic_element_renderer import BasicElementRenderer
from .div_renderer import DivRenderer
from .heading_renderer import HeadingRenderer
from .html_utils import create_simple_tag
from .list_renderer import ListRenderer


class ElementRenderer:
    """Unified element renderer integrating specialized components"""

    def __init__(self) -> None:
        """Initialize element renderer with component instances"""
        self._main_renderer: Any | None = None  # Will be set by main renderer

        # Initialize component renderers
        self.basic_renderer = BasicElementRenderer()
        self.heading_renderer = HeadingRenderer()
        self.list_renderer = ListRenderer()
        self.div_renderer = DivRenderer()

        # Legacy property for backward compatibility
        self.heading_counter = 0

    # Basic element methods - delegate to basic_renderer
    def render_paragraph(self, node: Node) -> str:
        """Render paragraph node"""
        self.basic_renderer._main_renderer = self._main_renderer
        return self.basic_renderer.render_paragraph(node)

    def render_strong(self, node: Node) -> str:
        """Render strong (bold) node"""
        self.basic_renderer._main_renderer = self._main_renderer
        return self.basic_renderer.render_strong(node)

    def render_emphasis(self, node: Node) -> str:
        """Render emphasis (italic) node"""
        self.basic_renderer._main_renderer = self._main_renderer
        return self.basic_renderer.render_emphasis(node)

    def render_preformatted(self, node: Node) -> str:
        """Render preformatted text"""
        self.basic_renderer._main_renderer = self._main_renderer
        return self.basic_renderer.render_preformatted(node)

    def render_code(self, node: Node) -> str:
        """Render inline code"""
        self.basic_renderer._main_renderer = self._main_renderer
        return self.basic_renderer.render_code(node)

    def render_image(self, node: Node) -> str:
        """Render image element"""
        self.basic_renderer._main_renderer = self._main_renderer
        return self.basic_renderer.render_image(node)

    def render_error(self, node: Node) -> str:
        """Render error node"""
        self.basic_renderer._main_renderer = self._main_renderer
        return self.basic_renderer.render_error(node)

    def render_toc_placeholder(self, node: Node) -> str:
        """Render table of contents marker"""
        self.basic_renderer._main_renderer = self._main_renderer
        return self.basic_renderer.render_toc_placeholder(node)

    # Div and details methods - delegate to div_renderer
    def render_div(self, node: Node) -> str:
        """Render div node"""
        self.div_renderer._main_renderer = self._main_renderer
        return self.div_renderer.render_div(node)

    def render_details(self, node: Node) -> str:
        """Render details/summary element"""
        self.div_renderer._main_renderer = self._main_renderer
        return self.div_renderer.render_details(node)

    # Heading methods - delegate to heading_renderer
    def render_heading(self, node: Node, level: int) -> str:
        """Render heading with ID"""
        self.heading_renderer._main_renderer = self._main_renderer
        # Sync heading counter
        self.heading_counter = self.heading_renderer.heading_counter
        result = self.heading_renderer.render_heading(node, level)
        self.heading_counter = self.heading_renderer.heading_counter
        return result

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

    # List methods - delegate to list_renderer
    def render_unordered_list(self, node: Node) -> str:
        """Render unordered list"""
        self.list_renderer._main_renderer = self._main_renderer
        return self.list_renderer.render_unordered_list(node)

    def render_ordered_list(self, node: Node) -> str:
        """Render ordered list"""
        self.list_renderer._main_renderer = self._main_renderer
        return self.list_renderer.render_ordered_list(node)

    def render_list_item(self, node: Node) -> str:
        """Render list item"""
        self.list_renderer._main_renderer = self._main_renderer
        return self.list_renderer.render_list_item(node)

    def render_generic(self, node: Node) -> str:
        """Generic node renderer"""
        tag = node.type
        content = self.basic_renderer._render_content(node.content)
        return create_simple_tag(tag, content, node.attributes)

    def reset_counters(self) -> None:
        """Reset internal counters"""
        self.heading_counter = 0
        self.heading_renderer.reset_counters()
