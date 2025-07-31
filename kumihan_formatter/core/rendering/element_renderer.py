"""Element renderer for Kumihan-Formatter - 完全統合版 (Issue #590 - Phase 0-2完了)

全てのHTML要素レンダリング機能を統合実装。
人為的分割を解消し、開発効率を向上。

統合前:
- basic_element_renderer.py (139行)
- heading_renderer.py (119行)
- list_renderer.py (96行)
- div_renderer.py (156行)
- element_renderer.py (141行)
合計: 651行 (5ファイル)

統合後: 1ファイル（Important Tier: 500行制限内）
"""

from typing import Any

from ..ast_nodes import Node
from .html_utils import (
    create_simple_tag,
    escape_html,
    process_text_content,
    render_attributes,
    render_attributes_with_enhancements,
)


class ElementRenderer:
    """統合要素レンダラー - 完全統合版

    統合された機能:
    - 基本要素レンダリング（paragraph, strong, emphasis, code等）
    - 見出し要素レンダリング（h1-h6, ID生成）
    - リスト要素レンダリング（ul, ol, li）
    - Div・Details要素レンダリング
    """

    def __init__(self) -> None:
        """統合要素レンダラーを初期化"""
        self._main_renderer: Any | None = None  # Will be set by main renderer
        self.heading_counter = 0  # 見出しID生成用

        # Phase 4: HTMLFormatter for accessibility and CSS class generation
        from .html_formatter import HTMLFormatter

        self.formatter = HTMLFormatter()

    def set_main_renderer(self, renderer: Any) -> None:
        """メインレンダラーを設定（コンポーネント間通信用）"""
        self._main_renderer = renderer

    # === 基本要素レンダリング機能 ===

    def render_paragraph(self, node: Node) -> str:
        """段落要素をレンダリング（Phase 4: 統合機能適用）"""
        content = self._render_content(node.content, 0)

        # Phase 4: Always apply enhanced attribute rendering
        attr_str = render_attributes_with_enhancements(
            "p", node.attributes, content, self.formatter
        )

        if attr_str:
            return f"<p {attr_str}>{content}</p>"
        return f"<p>{content}</p>"

    def render_strong(self, node: Node) -> str:
        """太字要素をレンダリング（Phase 4: 統合機能適用）"""
        content = self._render_content(node.content, 0)

        # Phase 4: Always apply enhanced attribute rendering
        attr_str = render_attributes_with_enhancements(
            "strong", node.attributes, content, self.formatter
        )

        if attr_str:
            return f"<strong {attr_str}>{content}</strong>"
        return f"<strong>{content}</strong>"

    def render_emphasis(self, node: Node) -> str:
        """斜体要素をレンダリング（Phase 4: 統合機能適用）"""
        content = self._render_content(node.content, 0)

        # Phase 4: Always apply enhanced attribute rendering
        attr_str = render_attributes_with_enhancements(
            "em", node.attributes, content, self.formatter
        )

        if attr_str:
            return f"<em {attr_str}>{content}</em>"
        return f"<em>{content}</em>"

    def render_preformatted(self, node: Node) -> str:
        """整形済みテキストをレンダリング"""
        if isinstance(node.content, str):
            content = escape_html(node.content)
        else:
            content = self._render_content(node.content, 0)

        attributes = render_attributes(node.attributes)

        # キーワード属性に基づく特別処理の判定
        keyword = node.get_attribute("keyword")
        should_wrap_with_code = False
        
        if keyword:
            # KeywordDefinitionsから設定を取得
            from kumihan_formatter.core.keyword_parsing.definitions import KeywordDefinitions
            keyword_defs = KeywordDefinitions()
            keyword_info = keyword_defs.get_keyword_info(keyword)
            
            if keyword_info and keyword_info.get("wrap_with_code", False):
                should_wrap_with_code = True
        
        if should_wrap_with_code:
            content = f"<code>{content}</code>"

        if attributes:
            return f"<pre {attributes}>{content}</pre>"
        else:
            return f"<pre>{content}</pre>"

    def render_code(self, node: Node) -> str:
        """インラインコードをレンダリング"""
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
        """画像要素をレンダリング（Phase 4: アクセシビリティ改善）"""
        filename = node.content if isinstance(node.content, str) else str(node.content)
        src = f"images/{filename}"

        # Phase 4: Enhanced accessibility and CSS class handling
        attributes = node.attributes.copy() if node.attributes else {}
        attributes["src"] = src

        # Generate alt text if not provided
        if "alt" not in attributes:
            attributes["alt"] = self.formatter._generate_alt_text(filename)

        # Use enhanced attribute rendering with accessibility features
        attr_str = render_attributes_with_enhancements(
            "img", attributes, filename, self.formatter
        )

        return f"<img {attr_str} />"

    def render_error(self, node: Node) -> str:
        """エラー要素をレンダリング"""
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
        """目次プレースホルダーをレンダリング"""
        return "<!-- TOC placeholder -->"

    # === 見出し要素レンダリング機能 ===

    def render_heading(self, node: Node, level: int) -> str:
        """見出し要素をIDと共にレンダリング（Phase 4: アクセシビリティ改善）

        Args:
            node: 見出しノード
            level: 見出しレベル (1-6)

        Returns:
            str: HTML見出し要素
        """
        content = self._render_content(node.content, 0)
        tag = f"h{min(max(level, 1), 6)}"  # h1-h6に制限

        # 見出しIDを生成（存在しない場合）
        attributes = node.attributes.copy() if node.attributes else {}
        if "id" not in attributes:
            self.heading_counter += 1
            attributes["id"] = f"heading-{self.heading_counter}"

        # Phase 4: Enhanced accessibility and CSS class handling
        attr_str = render_attributes_with_enhancements(
            tag, attributes, content, self.formatter
        )

        return f"<{tag} {attr_str}>{content}</{tag}>"

    # === リスト要素レンダリング機能 ===

    def render_unordered_list(self, node: Node) -> str:
        """順序なしリストをレンダリング（Phase 4: 統合機能適用）"""
        content = self._render_content(node.content, 0)

        # Phase 4: Enhanced attribute rendering
        attr_str = render_attributes_with_enhancements(
            "ul", node.attributes, content, self.formatter
        )

        return f"<ul {attr_str}>{content}</ul>"

    def render_ordered_list(self, node: Node) -> str:
        """順序ありリストをレンダリング（Phase 4: 統合機能適用）"""
        content = self._render_content(node.content, 0)

        # Phase 4: Enhanced attribute rendering
        attr_str = render_attributes_with_enhancements(
            "ol", node.attributes, content, self.formatter
        )

        return f"<ol {attr_str}>{content}</ol>"

    def render_list_item(self, node: Node) -> str:
        """リスト項目をレンダリング（Phase 4: 統合機能適用）"""
        content = self._render_content(node.content, 0)

        # Phase 4: Enhanced attribute rendering
        attr_str = render_attributes_with_enhancements(
            "li", node.attributes, content, self.formatter
        )

        return f"<li {attr_str}>{content}</li>"

    # === Div・Details要素レンダリング機能 ===

    def render_div(self, node: Node) -> str:
        """div要素をレンダリング（Phase 4: 統合機能適用）"""
        content = self._render_content(node.content, 0)

        # Phase 4: Always apply enhanced attribute rendering with
        # accessibility and CSS classes
        attr_str = render_attributes_with_enhancements(
            "div", node.attributes, content, self.formatter
        )

        if attr_str:
            return f"<div {attr_str}>{content}</div>"
        return f"<div>{content}</div>"

    def render_details(self, node: Node) -> str:
        """details要素をレンダリング（Phase 4: アクセシビリティ改善）"""
        # summaryとcontentを分離
        summary_text = node.get_attribute("summary", "詳細")
        content = self._render_content(node.content, 0)

        # 他の属性を処理（summaryを除く）
        attributes = {k: v for k, v in node.attributes.items() if k != "summary"}

        # Phase 4: Enhanced accessibility and CSS class handling
        attr_str = render_attributes_with_enhancements(
            "details", attributes, summary_text, self.formatter
        )

        summary_html = f"<summary>{escape_html(summary_text)}</summary>"

        return f"<details {attr_str}>{summary_html}{content}</details>"

    def render_summary(self, node: Node) -> str:
        """summary要素をレンダリング"""
        content = self._render_content(node.content, 0)
        attributes = render_attributes(node.attributes)

        if attributes:
            return f"<summary {attributes}>{content}</summary>"
        else:
            return f"<summary>{content}</summary>"

    # === 汎用要素レンダリング ===

    def render_element(self, node: Node) -> str:
        """汎用要素をレンダリング"""
        element_type = node.type

        # 要素タイプ別の分岐
        element_handlers = {
            "paragraph": self.render_paragraph,
            "strong": self.render_strong,
            "emphasis": self.render_emphasis,
            "preformatted": self.render_preformatted,
            "code": self.render_code,
            "image": self.render_image,
            "error": self.render_error,
            "toc_placeholder": self.render_toc_placeholder,
            "unordered_list": self.render_unordered_list,
            "ordered_list": self.render_ordered_list,
            "list_item": self.render_list_item,
            "div": self.render_div,
            "details": self.render_details,
            "summary": self.render_summary,
        }

        # 見出し要素の処理
        if element_type.startswith("heading"):
            try:
                level = int(element_type.replace("heading", ""))
                return self.render_heading(node, level)
            except (ValueError, AttributeError):
                level = 1
                return self.render_heading(node, level)

        # 登録されたハンドラーの実行
        handler = element_handlers.get(element_type)
        if handler:
            return handler(node)

        # 未知の要素タイプの処理
        return self._render_unknown_element(node)

    def render_generic(self, node: Node) -> str:
        """汎用ノードレンダリング（後方互換性のため）"""
        return self.render_element(node)

    def _render_unknown_element(self, node: Node) -> str:
        """未知の要素タイプをレンダリング（Phase 4: 統一機能適用）"""
        content = self._render_content(node.content, 0)
        return create_simple_tag(
            node.type, content, node.attributes, formatter=self.formatter
        )

    # === ヘルパーメソッド ===

    def _render_content(self, content: Any, depth: int = 0) -> str:
        """ノードコンテンツをレンダリング（再帰的）

        Args:
            content: レンダリングするコンテンツ
            depth: 現在の再帰深度

        Returns:
            str: レンダリング結果
        """
        max_depth = 100  # 無限再帰を防止

        if depth > max_depth:
            return "[ERROR: Maximum recursion depth reached]"

        if content is None:
            return ""
        elif isinstance(content, str):
            return process_text_content(content)
        elif isinstance(content, Node):
            # メインレンダラーを使用してノードをレンダリング
            if self._main_renderer:
                result = self._main_renderer._render_node_with_depth(content, depth + 1)
                return str(result)
            else:
                return f"{{NODE:{content.type}}}"
        elif isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, Node):
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


# 後方互換性のため、分割されていたクラスもエクスポート（廃止予定）
BasicElementRenderer = ElementRenderer  # 廃止予定
HeadingRenderer = ElementRenderer  # 廃止予定
ListRenderer = ElementRenderer  # 廃止予定
DivRenderer = ElementRenderer  # 廃止予定

__all__ = [
    "ElementRenderer",
    "BasicElementRenderer",  # 廃止予定
    "HeadingRenderer",  # 廃止予定
    "ListRenderer",  # 廃止予定
    "DivRenderer",  # 廃止予定
]
