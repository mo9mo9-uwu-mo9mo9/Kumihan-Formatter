"""Main HTML renderer for Kumihan-Formatter

This module provides the main HTMLRenderer class that coordinates
all specialized renderers and maintains backward compatibility.
"""

from html import escape
from typing import Any, List

from ..ast_nodes import Node
from .compound_renderer import CompoundElementRenderer
from .content_processor import ContentProcessor
from .element_renderer import ElementRenderer
from .heading_collector import HeadingCollector
from .heading_renderer import HeadingRenderer
from .html_formatter import HTMLFormatter
from .html_utils import process_text_content


class HTMLRenderer:
    """
    HTML出力のメインレンダラー（特化レンダラーを統括）

    設計ドキュメント:
    - 記法仕様: /SPEC.md#Kumihan記法基本構文
    - アーキテクチャ: /CONTRIBUTING.md#アーキテクチャ概要
    - 依存関係: /docs/CLASS_DEPENDENCY_MAP.md

    関連クラス:
    - ElementRenderer: 基本要素のレンダリング
    - CompoundElementRenderer: 複合要素のレンダリング
    - HTMLFormatter: HTML出力フォーマット調整
    - Node: 入力となるASTノード
    - Renderer: このクラスを使用する上位レンダラー

    責務:
    - NodeからHTMLへの変換統括
    - ネスト順序の制御（NESTING_ORDER準拠）
    - 特化レンダラーの調整
    - HTMLエスケープとセキュリティ対応
    """

    # Maintain the original nesting order for backward compatibility
    NESTING_ORDER = [
        "details",  # 折りたたみ, ネタバレ
        "div",  # 枠線, ハイライト
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",  # 見出し
        "strong",  # 太字
        "em",  # イタリック
    ]

    def __init__(self) -> None:
        """Initialize HTML renderer with specialized renderers"""
        self.element_renderer = ElementRenderer()
        self.compound_renderer = CompoundElementRenderer()
        self.formatter = HTMLFormatter()

        # Initialize specialized processors
        self.heading_renderer = HeadingRenderer(self.element_renderer)
        self.content_processor = ContentProcessor(self)
        self.heading_collector = HeadingCollector()

        # Inject this main renderer into element renderer for content processing
        self.element_renderer._main_renderer = self

    def render_nodes(self, nodes: list[Node]) -> str:
        """
        Render a list of nodes to HTML

        Args:
            nodes: List of AST nodes to render

        Returns:
            str: Generated HTML
        """
        html_parts = []

        for node in nodes:
            html = self.render_node(node)
            if html:
                html_parts.append(html)

        return "\n".join(html_parts)

    def render_node(self, node: Node) -> str:
        """
        Render a single node to HTML

        Args:
            node: AST node to render

        Returns:
            str: Generated HTML for the node
        """
        if not isinstance(node, Node):
            return escape(str(node))  # type: ignore

        # Route to specific rendering method
        renderer_method = getattr(self, f"_render_{node.type}", self._render_generic)
        return renderer_method(node)

    def _render_generic(self, node: Node) -> str:
        """Generic node renderer"""
        return self.element_renderer.render_generic(node)

    def _render_p(self, node: Node) -> str:
        """Render paragraph node"""
        return self.element_renderer.render_paragraph(node)

    def _render_strong(self, node: Node) -> str:
        """Render strong (bold) node"""
        return self.element_renderer.render_strong(node)

    def _render_em(self, node: Node) -> str:
        """Render emphasis (italic) node"""
        return self.element_renderer.render_emphasis(node)

    def _render_div(self, node: Node) -> str:
        """Render div node"""
        return self.element_renderer.render_div(node)

    def _render_h1(self, node: Node) -> str:
        """Render h1 heading"""
        return self.heading_renderer.render_h1(node)

    def _render_h2(self, node: Node) -> str:
        """Render h2 heading"""
        return self.heading_renderer.render_h2(node)

    def _render_h3(self, node: Node) -> str:
        """Render h3 heading"""
        return self.heading_renderer.render_h3(node)

    def _render_h4(self, node: Node) -> str:
        """Render h4 heading"""
        return self.heading_renderer.render_h4(node)

    def _render_h5(self, node: Node) -> str:
        """Render h5 heading"""
        return self.heading_renderer.render_h5(node)

    def _render_heading(self, node: Node, level: int) -> str:
        """Render heading with ID"""
        return self.heading_renderer.render_heading(node, level)

    def _render_ul(self, node: Node) -> str:
        """Render unordered list"""
        return self.element_renderer.render_unordered_list(node)

    def _render_ol(self, node: Node) -> str:
        """Render ordered list"""
        return self.element_renderer.render_ordered_list(node)

    def _render_li(self, node: Node) -> str:
        """Render list item"""
        return self.element_renderer.render_list_item(node)

    def _render_details(self, node: Node) -> str:
        """Render details/summary element"""
        return self.element_renderer.render_details(node)

    def _render_pre(self, node: Node) -> str:
        """Render preformatted text"""
        return self.element_renderer.render_preformatted(node)

    def _render_code(self, node: Node) -> str:
        """Render inline code"""
        return self.element_renderer.render_code(node)

    def _render_image(self, node: Node) -> str:
        """Render image element"""
        return self.element_renderer.render_image(node)

    def _render_error(self, node: Node) -> str:
        """Render error node"""
        return self.element_renderer.render_error(node)

    def _render_toc(self, node: Node) -> str:
        """Render table of contents marker"""
        return self.element_renderer.render_toc_placeholder(node)

    def _render_content(self, content: Any, depth: int = 0) -> str:
        """Render node content (recursive)"""
        return self.content_processor.render_content(content, depth)

    def _render_node_with_depth(self, node: Node, depth: int = 0) -> str:
        """Render a single node with depth tracking"""
        return self.content_processor.render_node_with_depth(node, depth)

    def _render_generic_with_depth(self, node: Node, depth: int = 0) -> str:
        """Generic node renderer with depth tracking"""
        return self.element_renderer.render_generic(node)

    def _process_text_content(self, text: str) -> str:
        """Process text content - delegate to html_utils"""
        return process_text_content(text)

    def _contains_html_tags(self, text: str) -> bool:
        """Check if text contains HTML tags - delegate to html_utils"""
        from .html_utils import contains_html_tags

        return contains_html_tags(text)

    def _render_attributes(self, attributes: dict[str, Any]) -> str:
        """Render HTML attributes - delegate to html_utils"""
        from .html_utils import render_attributes

        return render_attributes(attributes)

    def collect_headings(
        self, nodes: list[Node], depth: int = 0
    ) -> List[dict[str, Any]]:
        """
        Collect all headings from nodes for TOC generation

        Args:
            nodes: List of nodes to search
            depth: Current recursion depth (prevents infinite recursion)

        Returns:
            list[Dict]: List of heading information
        """
        return self.heading_collector.collect_headings(nodes, depth)

    def reset_counters(self) -> None:
        """Reset internal counters"""
        self.heading_renderer.reset_counters()
        self.heading_collector.reset_counters()
        self.element_renderer.reset_counters()

    @property
    def heading_counter(self) -> int:
        """Get current heading counter"""
        return self.heading_renderer.heading_counter

    @heading_counter.setter
    def heading_counter(self, value: int) -> None:
        """Set heading counter"""
        self.heading_renderer.heading_counter = value
        self.heading_collector.heading_counter = value


# Module-level function for backward compatibility
def render_single_node(node: Node, depth: int = 0) -> str:
    """
    Render a single node (used by element_renderer for recursive calls)

    Args:
        node: Node to render
        depth: Current recursion depth

    Returns:
        str: Rendered HTML
    """
    # Create a temporary renderer instance for recursive calls
    renderer = HTMLRenderer()
    return renderer._render_node_with_depth(node, depth)


# Maintain the original CompoundElementRenderer class for backward compatibility
CompoundElementRenderer = CompoundElementRenderer

__all__ = ["HTMLRenderer", "CompoundElementRenderer", "render_single_node"]
