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
    create_render_context,
    create_render_result,
)
from .components.content_processor_delegate import ContentProcessorDelegate

# 委譲コンポーネントのインポート
from .components.element_renderer_delegate import ElementRendererDelegate
from .components.output_formatter_delegate import OutputFormatterDelegate
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

        # 委譲コンポーネントの初期化
        self._element_delegate = ElementRendererDelegate(self)
        self._content_delegate = ContentProcessorDelegate(self)
        self._output_delegate = OutputFormatterDelegate(self)

        # Issue #700: graceful error handling support
        self.graceful_errors: list[Any] = []
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
            def format(self, nodes: list[Node]) -> str:
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
    def render_nodes(self, nodes: list[Node], format: str = "html") -> str:
        """ノードリストレンダリング処理（統合版）- 名前変更

        Args:
            nodes: レンダリングするASTノードリスト
            format: 出力形式 ("html" または "markdown")

        Returns:
            str: 指定形式でレンダリングされた出力
        """
        self.logger.debug(f"Rendering {len(nodes)} nodes to {format}")

        if format.lower() == "html":
            return cast(str, self.html_formatter.format(nodes))
        elif format.lower() == "markdown":
            return cast(str, self.markdown_formatter.format(nodes))
        else:
            raise ValueError(f"Unsupported format: {format}")

    def render_to_file(
        self, nodes: list[Node], output_path: Union[str, Path], format: str = "html"
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
        return self._content_delegate.render_nodes_optimized(nodes)

    def render_node_optimized(self, node: Node) -> str:
        """
        単一ノードの最適化HTML生成

        Args:
            node: AST node to render

        Returns:
            str: Generated HTML for the node (optimized)
        """
        return self._element_delegate.render_node_optimized(node)

    def render_nodes_with_errors_optimized(self, nodes: list[Node]) -> str:
        """Issue #700: 最適化されたエラー情報埋め込みレンダリング"""
        return self._content_delegate.render_nodes_with_errors_optimized(nodes)

    def _render_error_summary_optimized(self) -> str:
        """最適化されたエラーサマリーHTML生成"""
        return self._content_delegate._render_error_summary_optimized()

    def _render_single_error_optimized(self, error: Any, error_number: int) -> str:
        """単一エラーの最適化レンダリング"""
        return self._content_delegate._render_single_error_optimized(
            error, error_number
        )

    def _embed_error_markers_optimized(self, html: str) -> str:
        """最適化されたエラーマーカー埋め込み"""
        return self._content_delegate._embed_error_markers_optimized(html)

    def _create_error_marker_optimized(self, error: Any) -> str:
        """最適化されたエラーマーカー作成"""
        return self._content_delegate._create_error_marker_optimized(error)

    def get_rendering_metrics(self) -> dict[str, Any]:
        """レンダリングメトリクスを取得"""
        return self._output_delegate.get_rendering_metrics()

    def render_node(self, node: Node, context: Optional[RenderContext] = None) -> str:
        """
        Render a single node to HTML (BaseRendererProtocol準拠)

        Args:
            node: AST node to render
            context: レンダリングコンテキスト（オプション）

        Returns:
            str: Generated HTML for the node
        """
        return self._element_delegate.render_node(node)

    # ==========================================
    # 委譲メソッド（要素レンダリング）
    # ==========================================

    def _render_generic(self, node: Node) -> str:
        """Generic node renderer"""
        return self._element_delegate._render_generic(node)

    def _render_p(self, node: Node) -> str:
        """Render paragraph node"""
        return self._element_delegate._render_p(node)

    def _render_strong(self, node: Node) -> str:
        """Render strong (bold) node"""
        return self._element_delegate._render_strong(node)

    def _render_em(self, node: Node) -> str:
        """Render emphasis (italic) node"""
        return self._element_delegate._render_em(node)

    def _render_div(self, node: Node) -> str:
        """Render div node"""
        return self._element_delegate._render_div(node)

    def _render_h1(self, node: Node) -> str:
        """Render h1 heading"""
        return self._element_delegate._render_h1(node)

    def _render_h2(self, node: Node) -> str:
        """Render h2 heading"""
        return self._element_delegate._render_h2(node)

    def _render_h3(self, node: Node) -> str:
        """Render h3 heading"""
        return self._element_delegate._render_h3(node)

    def _render_h4(self, node: Node) -> str:
        """Render h4 heading"""
        return self._element_delegate._render_h4(node)

    def _render_h5(self, node: Node) -> str:
        """Render h5 heading"""
        return self._element_delegate._render_h5(node)

    def _render_heading(self, node: Node, level: int) -> str:
        """Render heading with ID"""
        return self._element_delegate._render_heading(node, level)

    def _render_ul(self, node: Node) -> str:
        """Render unordered list"""
        return self._element_delegate._render_ul(node)

    def _render_ol(self, node: Node) -> str:
        """Render ordered list"""
        return self._element_delegate._render_ol(node)

    def _render_li(self, node: Node) -> str:
        """Render list item"""
        return self._element_delegate._render_li(node)

    def _render_details(self, node: Node) -> str:
        """Render details/summary element"""
        return self._element_delegate._render_details(node)

    def _render_pre(self, node: Node) -> str:
        """Render preformatted text"""
        return self._element_delegate._render_pre(node)

    def _render_code(self, node: Node) -> str:
        """Render inline code"""
        return self._element_delegate._render_code(node)

    def _render_image(self, node: Node) -> str:
        """Render image element"""
        return self._element_delegate._render_image(node)

    def _render_error(self, node: Node) -> str:
        """Render error node"""
        return self._element_delegate._render_error(node)

    def _render_toc(self, node: Node) -> str:
        """Render table of contents marker"""
        return self._element_delegate._render_toc(node)

    def _render_ruby(self, node: Node) -> str:
        """Render ruby (ルビ) element"""
        return self._element_delegate._render_ruby(node)

    def _render_content(self, content: Any, depth: int = 0) -> str:
        """Render node content (recursive)"""
        return self._element_delegate._render_content(content, depth)

    def _render_node_with_depth(self, node: Node, depth: int = 0) -> str:
        """Render a single node with depth tracking"""
        return self._element_delegate._render_node_with_depth(node, depth)

    def _render_generic_with_depth(self, node: Node, depth: int = 0) -> str:
        """Generic node renderer with depth tracking"""
        return self._element_delegate._render_generic_with_depth(node, depth)

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
    ) -> list[dict[str, Any]]:
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
        return self._output_delegate.render_nodes_with_errors(nodes)

    def _render_error_summary(self) -> str:
        """エラーサマリーをHTMLで生成"""
        return self._output_delegate._render_error_summary()

    def _embed_error_markers(self, html: str) -> str:
        """HTML内のエラー発生箇所にマーカーを埋め込み"""
        return self._output_delegate._embed_error_markers(html)

    # ==========================================
    # プロトコル準拠メソッド（BaseRendererProtocol実装）
    # ==========================================

    def render_to_html(self, nodes: list[Node]) -> str:
        """HTMLレンダリング（互換性メソッド）"""
        return cast(str, self.render_nodes(nodes, format="html"))

    def render_to_markdown(self, nodes: list[Node]) -> str:
        """Markdownレンダリング（互換性メソッド）"""
        return cast(str, self.render_nodes(nodes, format="markdown"))

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
                context = create_render_context(output_format="html")
                return self.render([node], context)
            elif output_format == "markdown":
                context = create_render_context(output_format="markdown")
                return self.render([node], context)
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
    ) -> list[str]:
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

    def get_renderer_info(self) -> dict[str, Any]:
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
        self, nodes: List[Node], context: Optional[RenderContext] = None
    ) -> RenderResult:
        """統一レンダリングインターフェース（BaseRendererProtocol準拠）"""
        try:
            if not nodes:
                return create_render_result(content="", success=True)

            # 複数ノードを順次処理
            output_format = context.output_format if context else "html"
            result_content = self.render_nodes(nodes, output_format)
            return create_render_result(content=result_content, success=True)
        except Exception as e:
            result = create_render_result(success=False)
            result.add_error(f"レンダリング失敗: {e}")
            return result

    def _render_original(self, nodes: list[Node], format: str = "html") -> str:
        """元のrenderメソッド実装（統合版）"""
        return cast(str, self.render_nodes(nodes, format))

    def get_supported_formats(self) -> list[str]:
        """サポートする出力形式のリストを返す（抽象メソッド実装）"""
        return ["html", "markdown"]

    def validate_options(self, options: Dict[str, Any]) -> List[str]:
        """オプションの妥当性をチェック（BaseRendererProtocol準拠）"""
        errors = []

        if not isinstance(options, dict):
            errors.append("オプションは辞書形式で指定してください")
            return errors

        # 有効なオプションキーの定義
        valid_keys = {
            "title",
            "template",
            "include_toc",
            "source_text",
            "source_filename",
            "navigation_html",
            "graceful_errors",
            "embed_errors_in_html",
            "format",
        }

        # 不明なキーがないかチェック
        for key in options.keys():
            if key not in valid_keys:
                errors.append(f"不明なオプションキー: {key}")

        return errors


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
