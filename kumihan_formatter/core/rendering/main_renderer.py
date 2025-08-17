"""統合メインレンダラー - Issue #912 Renderer系統合リファクタリング

Renderer系統合版：全体統括レンダラー
- 元々のHTMLRenderer機能を統合
- HtmlFormatter、MarkdownFormatterを統括
- 既存API完全互換性維持
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union, cast

if TYPE_CHECKING:
    from ..patterns.dependency_injection import DIContainer
    from ..patterns.factories import RendererFactory

from ..ast_nodes import Node
from ..mixins.event_mixin import EventEmitterMixin, with_events
from ..utilities.logger import get_logger
from .base.renderer_protocols import (
    BaseRendererProtocol,
    RenderContext,
    RenderResult,
    create_render_result,
)
from .compound_renderer import CompoundElementRenderer
from .content_processor import ContentProcessor
from .element_renderer import ElementRenderer
from .formatters.html_formatter import HtmlFormatter
from .formatters.markdown_formatter import MarkdownFormatter
from .heading_collector import HeadingCollector

# HeadingRenderer is now part of ElementRenderer
from .html_formatter import HTMLFormatter
from .html_utils import process_text_content


class MainRenderer(BaseRendererProtocol, EventEmitterMixin):
    """統合メインレンダラー（全Rendererシステム統括）

    Issue #912 Renderer系統合リファクタリング対応

    統合された機能:
    - HTML出力（HtmlFormatter統括）
    - Markdown出力（MarkdownFormatter統括）
    - 既存HTMLRenderer機能完全継承
    - 後方互換性完全維持

    設計ドキュメント:
    - 記法仕様: /SPEC.md#Kumihan記法基本構文
    - アーキテクチャ: /CONTRIBUTING.md#アーキテクチャ概要
    - 依存関係: /docs/CLASS_DEPENDENCY_MAP.md

    関連クラス:
    - HtmlFormatter: HTML出力専用フォーマッター
    - MarkdownFormatter: Markdown出力専用フォーマッター
    - ElementRenderer: 基本要素のレンダリング
    - CompoundElementRenderer: 複合要素のレンダリング
    - HTMLFormatter: HTML出力フォーマット調整（既存）
    - Node: 入力となるASTノード

    責務:
    - 全出力形式の統括管理
    - フォーマット選択と処理委譲
    - 既存API完全互換性維持
    - セキュリティ・エラーハンドリング統括
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

    def __init__(
        self, config: Optional[Any] = None, container: Optional["DIContainer"] = None
    ) -> None:
        """統合メインレンダラーを初期化

        Args:
            config: 設定オブジェクト（オプショナル）
            container: DIコンテナ（オプショナル）- Issue #914 Phase 2
        """
        self.logger = get_logger(__name__)
        self.config = config

        # EventEmitterMixin初期化
        self._source_name = self.__class__.__name__

        # DIコンテナ設定（Issue #914 Phase 2）
        self.container = container
        if self.container is None:
            try:
                from ..patterns.dependency_injection import get_container

                self.container = get_container()
                self.logger.debug("Using global DI container")
            except ImportError:
                self.logger.debug(
                    "DI container not available, using direct instantiation"
                )
                self.container = None

        # ファクトリー設定（Issue #914 Phase 2）
        self.renderer_factory: Optional["RendererFactory"] = None
        if self.container is not None:
            try:
                from ..patterns.factories import get_renderer_factory

                self.renderer_factory = get_renderer_factory()
                self.logger.debug("Renderer factory initialized with DI support")
            except ImportError:
                self.logger.debug(
                    "Renderer factory not available, falling back to direct instantiation"
                )

        # レンダラーの初期化
        self._initialize_renderers()

        # 既存コンポーネント（後方互換性のため維持）
        self.element_renderer = ElementRenderer()
        self.compound_renderer = CompoundElementRenderer()
        self.formatter = HTMLFormatter()

        # Initialize specialized processors
        self.content_processor = ContentProcessor(self)
        self.heading_collector = HeadingCollector()

        # Inject this main renderer into element renderer for content processing
        self.element_renderer.set_main_renderer(self)

        # Issue #700: graceful error handling support
        self.graceful_errors: List[Any] = []
        self.embed_errors_in_html = False

        # Footnote integration support
        self.footnotes_data: Optional[dict[str, Any]] = None

        self.logger.debug("MainRenderer initialized with config support")

    def _initialize_renderers(self) -> None:
        """レンダラーの初期化（DI対応 - Issue #914 Phase 2）"""
        try:
            # DIパターンによる初期化を試行
            if self.renderer_factory is not None and self.container is not None:
                self.logger.debug("Initializing renderers using DI pattern")
                self.html_formatter = self._create_renderer_with_fallback("html")
                self.markdown_formatter = self._create_renderer_with_fallback(
                    "markdown"
                )
            else:
                # 従来の直接インスタンス化（フォールバック）
                self.logger.debug("Initializing renderers using direct instantiation")
                self.html_formatter = HtmlFormatter(self.config)
                self.markdown_formatter = MarkdownFormatter(self.config)

            self.logger.info("All specialized renderers initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize renderers: {e}")
            # フォールバック: 直接インスタンス化
            self._initialize_fallback_renderers()

    def _create_renderer_with_fallback(self, renderer_type: str) -> Any:
        """DI失敗時のフォールバック付きレンダラー生成（Issue #914 Phase 2）"""
        try:
            # 1. DIコンテナ経由で解決を試行
            if self.container is not None:
                try:
                    # 型マッピング
                    renderer_class_map = {
                        "html": HtmlFormatter,
                        "markdown": MarkdownFormatter,
                    }

                    if renderer_type in renderer_class_map:
                        renderer_class = renderer_class_map[renderer_type]
                        instance = self.container.resolve(renderer_class)
                        self.logger.debug(
                            f"DI resolution successful for {renderer_type}"
                        )
                        return instance
                except Exception as di_error:
                    self.logger.warning(
                        f"DI creation failed for {renderer_type}: {di_error}"
                    )

            # 2. ファクトリー経由での生成を試行
            if self.renderer_factory is not None:
                try:
                    instance = self.renderer_factory.create(
                        renderer_type, config=self.config
                    )
                    self.logger.debug(
                        f"Factory creation successful for {renderer_type}"
                    )
                    return instance
                except Exception as factory_error:
                    self.logger.warning(
                        f"Factory creation failed for {renderer_type}: {factory_error}"
                    )

            # 3. 直接インスタンス化（最終フォールバック）
            return self._create_direct_renderer_instance(renderer_type)

        except Exception as e:
            self.logger.error(
                f"All renderer creation methods failed for {renderer_type}: {e}"
            )
            return self._create_direct_renderer_instance(renderer_type)

    def _create_direct_renderer_instance(self, renderer_type: str) -> Any:
        """直接レンダラーインスタンス化（最終フォールバック）"""
        try:
            renderer_class_map = {
                "html": HtmlFormatter,
                "markdown": MarkdownFormatter,
            }

            if renderer_type in renderer_class_map:
                renderer_class = renderer_class_map[renderer_type]
                instance = renderer_class(self.config)
                self.logger.debug(
                    f"Direct instantiation successful for {renderer_type}"
                )
                return instance
            else:
                raise ValueError(f"Unknown renderer type: {renderer_type}")

        except Exception as e:
            self.logger.error(f"Direct instantiation failed for {renderer_type}: {e}")
            # 最小限の汎用レンダラーを返す
            return self._create_minimal_renderer()

    def _create_minimal_renderer(self) -> Any:
        """最小限の汎用レンダラー生成"""

        class MinimalRenderer:
            def format(self, nodes: List[Node]) -> str:
                if not nodes:
                    return ""
                return "\n".join(
                    str(node.content) for node in nodes if hasattr(node, "content")
                )

        return MinimalRenderer()

    def _initialize_fallback_renderers(self) -> None:
        """フォールバック用レンダラー初期化"""
        self.logger.warning("Using fallback renderer initialization")
        try:
            self.html_formatter = HtmlFormatter(self.config)
            self.markdown_formatter = MarkdownFormatter(self.config)
        except Exception as e:
            self.logger.error(f"Fallback renderer initialization failed: {e}")
            self.html_formatter = self._create_minimal_renderer()
            self.markdown_formatter = self._create_minimal_renderer()

    @with_events("main_render")
    def render_nodes(self, nodes: List[Node], format: str = "html") -> str:
        """ノードリストレンダリング処理（統合版）- 名前変更

        Args:
            nodes: レンダリングするASTノードリスト
            format: 出力形式 ("html" または "markdown")

        Returns:
            str: 指定形式でレンダリングされた出力
        """
        self.logger.debug(f"Rendering {len(nodes)} nodes to {format}")

        if format.lower() == "html":
            return self.html_formatter.format(nodes)
        elif format.lower() == "markdown":
            return self.markdown_formatter.format(nodes)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def render_to_file(
        self, nodes: List[Node], output_path: Union[str, Path], format: str = "html"
    ) -> None:
        """ファイル出力

        Args:
            nodes: レンダリングするASTノードリスト
            output_path: 出力ファイルパス
            format: 出力形式 ("html" または "markdown")
        """
        output_path = Path(output_path)
        content = self.render_nodes(nodes, format)

        # 出力ディレクトリが存在しない場合は作成
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        self.logger.info(f"Rendered content saved to {output_path}")

    def set_footnote_data(self, footnotes_data: dict[str, Any]) -> None:
        """
        脚注データを設定（Rendererからの統合用）

        Args:
            footnotes_data: 脚注データ辞書 {footnotes, clean_text, manager}
        """
        try:
            self.footnotes_data = footnotes_data
            self.logger.debug(
                f"Set footnote data: {len(footnotes_data.get('footnotes', []))} footnotes"
            )
        except Exception as e:
            self.logger.error(f"Failed to set footnote data: {e}")
            self.footnotes_data = None

    def render_nodes_to_html(self, nodes: list[Node]) -> str:
        """
        Render a list of nodes to HTML (旧render_nodesメソッド)

        Args:
            nodes: List of AST nodes to render

        Returns:
            str: Generated HTML
        """
        # Issue #700: graceful errors対応
        if self.graceful_errors and self.embed_errors_in_html:
            return self.render_nodes_with_errors(nodes)

        html_parts = []
        for node in nodes:
            html = self.render_node(node)
            html_parts.append(html)

        # Generate main content HTML
        main_html = "\n".join(html_parts)

        # Process footnote placeholders if footnote data is available
        if self.footnotes_data:
            try:
                footnotes = self.footnotes_data.get("footnotes", [])

                if footnotes:
                    # Replace footnote placeholders with actual HTML links
                    # import re removed - unused import (F401)

                    for footnote in footnotes:
                        placeholder = f"[FOOTNOTE_REF_{footnote['number']}]"
                        footnote_link = (
                            f'<sup><a href="#footnote-{footnote["number"]}" '
                            f'id="footnote-ref-{footnote["number"]}">'
                            f'[{footnote["number"]}]</a></sup>'
                        )
                        main_html = main_html.replace(placeholder, footnote_link)

                    self.logger.debug(
                        f"Replaced {len(footnotes)} footnote placeholders with HTML links"
                    )

            except Exception as e:
                self.logger.warning(f"Failed to process footnote placeholders: {e}")
                # Continue with original HTML if footnote processing fails

        # 新記法脚注システム：文書末尾に脚注セクションを追加
        footnote_manager = (
            self.footnotes_data.get("manager") if self.footnotes_data else None
        )
        if footnote_manager and footnote_manager.get_footnotes():
            footnotes_html = footnote_manager.generate_footnotes_html(
                footnote_manager.get_footnotes()
            )
            if footnotes_html[0]:  # エラーがない場合
                main_html += "\n" + footnotes_html[0]
            elif footnotes_html[1]:  # エラーがある場合はログ出力
                self.logger.warning(f"Footnote generation errors: {footnotes_html[1]}")

        return main_html

    def render_nodes_optimized(self, nodes: list[Node]) -> str:
        """
        最適化されたノードリストのHTML生成（Issue #727 パフォーマンス最適化対応）

        改善点:
        - StringBuilder パターンでガベージコレクション負荷軽減
        - HTML文字列結合の最適化
        - メモリ効率向上
        - 処理速度75%改善目標

        Args:
            nodes: List of AST nodes to render

        Returns:
            str: Generated HTML (optimized)
        """
        # Issue #700: graceful errors対応
        if self.graceful_errors and self.embed_errors_in_html:
            return self.render_nodes_with_errors_optimized(nodes)

        html_parts: list[str] = []
        html_parts_append = html_parts.append
        for node in nodes:
            html = self.render_node(node)
            html_parts_append(html)

        # 高速文字列結合（join最適化）
        return "\n".join(html_parts)

    def render_node_optimized(self, node: Node) -> str:
        """
        単一ノードの最適化HTML生成

        Args:
            node: AST node to render

        Returns:
            str: Generated HTML for the node (optimized)
        """
        # 最適化: メソッド動的検索を避けるため事前キャッシュ
        renderer_method = self._get_cached_renderer_method(node.type)
        return cast(str, renderer_method(node))

    def _get_cached_renderer_method(self, node_type: str) -> Any:
        """レンダラーメソッドのキャッシュ取得（メソッド検索最適化）"""

        # レンダラーメソッドキャッシュが未初期化なら作成
        if not hasattr(self, "_renderer_method_cache"):
            self._renderer_method_cache: dict[str, Any] = {}

        # キャッシュから取得
        if node_type not in self._renderer_method_cache:
            method_name = f"_render_{node_type}"
            self._renderer_method_cache[node_type] = getattr(
                self, method_name, self._render_generic
            )

        return self._renderer_method_cache[node_type]

    def render_nodes_with_errors_optimized(self, nodes: list[Node]) -> str:
        """Issue #700: 最適化されたエラー情報埋め込みレンダリング"""

        # StringBuilder パターン
        html_parts: list[str] = []
        html_parts_append = html_parts.append

        for node in nodes:
            html = self.render_node_optimized(node)
            if html:
                html_parts_append(html)

        # エラー情報をHTML前に効率的に挿入
        if self.embed_errors_in_html and self.graceful_errors:
            error_summary_html = self._render_error_summary_optimized()
            html_parts.insert(0, error_summary_html)

            # 効率的なエラーマーカー埋め込み
            html_with_markers = self._embed_error_markers_optimized(
                "\n".join(html_parts)
            )
            return html_with_markers

        return "\n".join(html_parts)

    def _render_error_summary_optimized(self) -> str:
        """最適化されたエラーサマリーHTML生成"""
        if not self.graceful_errors:
            return ""

        error_count = 0
        warning_count = 0

        for error in self.graceful_errors:
            if error.severity == "error":
                error_count += 1
            elif error.severity == "warning":
                warning_count += 1

        total_count = len(self.graceful_errors)

        # StringBuilder パターンでHTML構築
        html_parts = [
            '<div class="kumihan-error-summary" id="error-summary">',
            "    <h3>🔍 記法エラーレポート</h3>",
            '    <div class="error-stats">',
            f'        <span class="error-count">❌ エラー: {error_count}件</span>',
            f'        <span class="warning-count">⚠️ 警告: {warning_count}件</span>',
            f'        <span class="total-count">📊 合計: {total_count}件</span>',
            "    </div>",
            '    <details class="error-details">',
            "        <summary>詳細を表示</summary>",
            '        <div class="error-list">',
        ]

        # 各エラーの詳細を効率的に追加
        for i, error in enumerate(self.graceful_errors, 1):
            error_html = self._render_single_error_optimized(error, i)
            html_parts.append(error_html)

        html_parts.extend(["        </div>", "    </details>", "</div>"])

        return "\n".join(html_parts)

    def _render_single_error_optimized(self, error: Any, error_number: int) -> str:
        """単一エラーの最適化レンダリング"""
        from .html_escaping import escape_html

        # XSS対策: エラー情報のエスケープ処理（最適化）
        safe_title = escape_html(error.display_title)
        safe_severity = escape_html(error.severity.upper())
        safe_content = error.html_content  # 既にエスケープ済み

        # 文字列テンプレート最適化
        return f"""
            <div class="error-item {error.html_class}" data-line="{error.line_number}">
                <div class="error-header">
                    <span class="error-number">#{error_number}</span>
                    <span class="error-title">{safe_title}</span>
                    <span class="error-severity">{safe_severity}</span>
                </div>
                <div class="error-content">
                    {safe_content}
                </div>
            </div>"""

    def _embed_error_markers_optimized(self, html: str) -> str:
        """最適化されたエラーマーカー埋め込み"""
        if not self.graceful_errors:
            return html

        lines = html.split("\n")
        error_by_line: dict[int, list[Any]] = {}
        modified_lines = []

        # エラーを行番号でグループ化
        for error in self.graceful_errors:
            line_no = getattr(error, "line_number", 1)
            if line_no not in error_by_line:
                error_by_line[line_no] = []
            error_by_line[line_no].append(error)

        # 効率的な行処理
        for line_no, line in enumerate(lines, 1):
            modified_lines.append(line)

            # エラーマーカー挿入（最適化）
            if line_no in error_by_line:
                for error in error_by_line[line_no]:
                    error_marker = self._create_error_marker_optimized(error)
                    modified_lines.append(error_marker)

        return "\n".join(modified_lines)

    def _create_error_marker_optimized(self, error: Any) -> str:
        """最適化されたエラーマーカー作成"""
        from .html_escaping import escape_html

        safe_message = escape_html(error.message)
        safe_suggestion = escape_html(error.suggestion) if error.suggestion else ""
        error_icon = "❌" if error.severity == "error" else "⚠️"

        # f-string最適化
        suggestion_html = (
            f'<div class="error-suggestion">💡 {safe_suggestion}</div>'
            if safe_suggestion
            else ""
        )

        return (
            f"""<div class="kumihan-error-marker {error.html_class}" """
            f"""data-line="{error.line_number}">
    <div class="error-indicator">
        <span class="error-icon">{error_icon}</span>
        <span class="error-message">{safe_message}</span>
        {suggestion_html}
    </div>
</div>"""
        )

    def get_rendering_metrics(self) -> dict[str, Any]:
        """レンダリングメトリクスを取得"""
        return {
            "renderer_cache_size": len(getattr(self, "_renderer_method_cache", {})),
            "graceful_errors_count": len(self.graceful_errors),
            "embed_errors_enabled": self.embed_errors_in_html,
            "heading_counter": self.heading_counter,
        }

    def render_node(self, node: Node) -> str:
        """
        Render a single node to HTML

        Args:
            node: AST node to render

        Returns:
            str: Generated HTML for the node
        """
        if not isinstance(node, Node):
            raise TypeError(f"Expected Node instance, got {type(node)}")

        # Delegateメソッドを動的に検索して呼び出し
        method_name = f"_render_{node.type}"
        renderer_method = getattr(self, method_name, self._render_generic)
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
        return self.element_renderer.render_heading(node, 1)

    def _render_h2(self, node: Node) -> str:
        """Render h2 heading"""
        return self.element_renderer.render_heading(node, 2)

    def _render_h3(self, node: Node) -> str:
        """Render h3 heading"""
        return self.element_renderer.render_heading(node, 3)

    def _render_h4(self, node: Node) -> str:
        """Render h4 heading"""
        return self.element_renderer.render_heading(node, 4)

    def _render_h5(self, node: Node) -> str:
        """Render h5 heading"""
        return self.element_renderer.render_heading(node, 5)

    def _render_heading(self, node: Node, level: int) -> str:
        """Render heading with ID"""
        return self.element_renderer.render_heading(node, level)

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

    def _render_ruby(self, node: Node) -> str:
        """Render ruby (ルビ) element"""
        return self.element_renderer.render_ruby(node)

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
        self.heading_collector.reset_counters()
        self.element_renderer.heading_counter = 0

    @property
    def heading_counter(self) -> int:
        """Get current heading counter"""
        return self.element_renderer.heading_counter

    @heading_counter.setter
    def heading_counter(self, value: int) -> None:
        """Set heading counter"""
        self.element_renderer.heading_counter = value
        self.heading_collector.heading_counter = value

    def set_graceful_errors(
        self, errors: list[Any], embed_in_html: bool = True
    ) -> None:
        """Issue #700: graceful error handlingのエラー情報を設定"""

        self.graceful_errors = errors
        self.embed_errors_in_html = embed_in_html

    def render_nodes_with_errors(self, nodes: list[Node]) -> str:
        """Issue #700: エラー情報を埋め込みながらノードをレンダリング"""
        html_parts = []

        for node in nodes:
            html = self.render_node(node)
            if html:
                html_parts.append(html)

        # エラー情報をHTMLに埋め込み
        if self.embed_errors_in_html and self.graceful_errors:
            error_summary_html = self._render_error_summary()
            html_parts.insert(0, error_summary_html)

            # 各エラー箇所にマーカーを挿入
            html_with_markers = self._embed_error_markers("\n".join(html_parts))
            return html_with_markers

        return "\n".join(html_parts)

    def _render_error_summary(self) -> str:
        """エラーサマリーをHTMLで生成"""
        if not self.graceful_errors:
            return ""

        # エラーサマリーのヘッダー部分
        error_count = len(self.graceful_errors)
        summary_html = f"""
<div class="kumihan-error-summary">
    <details open>
        <summary class="error-summary-header">
            <span class="error-count-badge">{error_count}</span>
            <span class="error-summary-title">構文エラー・警告一覧</span>
        </summary>
        <div class="error-list">
"""

        # 各エラーの詳細を追加
        for i, error in enumerate(self.graceful_errors, 1):
            from .html_escaping import escape_html

            # XSS対策: エラー情報のエスケープ処理
            safe_title = escape_html(error.display_title)
            safe_severity = escape_html(error.severity.upper())
            safe_content = (
                error.html_content
            )  # html_contentプロパティ内で既にエスケープ済み

            # ハイライト付きコンテキストと修正提案を追加
            highlighted_context = error.get_highlighted_context()
            correction_suggestions_html = error.get_correction_suggestions_html()

            error_html = f"""
            <div class="error-item {error.html_class}" data-line="{error.line_number}">
                <div class="error-header">
                    <span class="error-number">#{i}</span>
                    <span class="error-title">{safe_title}</span>
                    <span class="error-severity">{safe_severity}</span>
                </div>
                <div class="error-content">
                    {safe_content}
                    {(f'<div class="error-context-highlighted">{highlighted_context}</div>'
                      if highlighted_context != error.context else '')}
                    {correction_suggestions_html
                     and f'<div class="correction-suggestions">'
                         f'<h4>修正提案:</h4>{correction_suggestions_html}</div>' or ''}
                </div>
            </div>
"""
            summary_html += error_html

        summary_html += """
        </div>
    </details>
</div>
"""
        return summary_html

    def _embed_error_markers(self, html: str) -> str:
        """HTML内のエラー発生箇所にマーカーを埋め込み"""
        if not self.graceful_errors:
            return html

        modified_lines = html.split("\n")

        for error in self.graceful_errors:
            if error.line_number and error.line_number <= len(modified_lines):
                from .html_escaping import escape_html

                # XSS対策: エラー情報のエスケープ処理
                safe_message = escape_html(error.message)
                safe_suggestion = (
                    escape_html(error.suggestion) if error.suggestion else ""
                )
                error_icon = "❌" if error.severity == "error" else "⚠️"

                error_marker = f"""
<div class="kumihan-error-marker {error.html_class}" data-line="{error.line_number}">
    <div class="error-indicator">
        <span class="error-icon">{error_icon}</span>
        <span class="error-message">{safe_message}</span>
        {f'<div class="error-suggestion">💡 {safe_suggestion}</div>' if safe_suggestion else ''}
    </div>
</div>"""
                modified_lines.insert(error.line_number - 1, error_marker)

        return "\n".join(modified_lines)

    # ==========================================
    # プロトコル準拠メソッド（BaseRendererProtocol実装）
    # ==========================================

    def render_to_html(self, nodes: List[Node]) -> str:
        """HTMLレンダリング（互換性メソッド）"""
        return self.render_nodes(nodes, format="html")

    def render_to_markdown(self, nodes: List[Node]) -> str:
        """Markdownレンダリング（互換性メソッド）"""
        return self.render_nodes(nodes, format="markdown")

    def render_node_protocol(
        self, node: Node, context: Optional[RenderContext] = None
    ) -> RenderResult:
        """プロトコル準拠レンダリングインターフェース"""
        try:
            # デフォルトでHTML形式でレンダリング
            output_format = (
                context.output_format
                if context and hasattr(context, "output_format")
                else "html"
            )

            if output_format == "html":
                html_content = self.render([node], format="html")
                return create_render_result(content=html_content, success=True)
            elif output_format == "markdown":
                md_content = self.render([node], format="markdown")
                return create_render_result(content=md_content, success=True)
            else:
                result = create_render_result(success=False)
                result.add_error(f"未対応の出力形式: {output_format}")
                return result

        except Exception as e:
            result = create_render_result(success=False)
            result.add_error(f"レンダリング失敗: {e}")
            return result

    def validate(
        self, node: Node, context: Optional[RenderContext] = None
    ) -> List[str]:
        """バリデーション実装（プロトコル準拠）"""
        errors = []
        try:
            # ノードの基本検証
            if not node:
                errors.append("ノードが空です")
            elif not hasattr(node, "node_type"):
                errors.append("ノードタイプが設定されていません")
        except Exception as e:
            errors.append(f"バリデーションエラー: {e}")
        return errors

    def get_renderer_info(self) -> Dict[str, Any]:
        """レンダラー情報（プロトコル準拠）"""
        return {
            "name": "MainRenderer",
            "version": "2.0.0",
            "supported_formats": ["html", "markdown"],
            "capabilities": ["html_rendering", "markdown_rendering", "error_recovery"],
            "formatters": ["html", "markdown"],
        }

    def supports_format(self, format_hint: str) -> bool:
        """フォーマット対応判定（プロトコル準拠）"""
        return format_hint in ["html", "markdown", "text"]

    # プロトコル準拠のためのエイリアス
    def render(
        self,
        node_or_nodes: Union[Node, List[Node]],
        context: Optional[RenderContext] = None,
        format: str = "html",
    ) -> Union[str, RenderResult]:
        """プロトコル準拠および既存API互換レンダリング"""
        if isinstance(node_or_nodes, Node):
            # プロトコル準拠モード：単一ノード -> RenderResult
            return self.render_node_protocol(node_or_nodes, context)
        else:
            # 既存API互換モード：ノードリスト -> str
            return self._render_original(node_or_nodes, format)

    def _render_original(self, nodes: List[Node], format: str = "html") -> str:
        """元のrenderメソッド実装（統合版）"""
        return self.render_nodes(nodes, format)


# 後方互換性：既存の HTMLRenderer エイリアス
HTMLRenderer = MainRenderer


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
