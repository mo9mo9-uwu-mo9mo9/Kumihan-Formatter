"""
統合メインレンダラー
分割されたモジュールを統合する新しいMainRenderer
"""

import logging
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from ..ast_nodes.node import Node
from .output_formatter import OutputFormatter


class MainRenderer:
    """統合メインレンダラー（分割版統合）"""

    # ネスティング順序定義（互換性維持）
    NESTING_ORDER = [
        "div",
        "section",
        "article",
        "main",
        "aside",
        "header",
        "footer",
        "nav",
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None, container: Any = None):
        """統合レンダラー初期化"""
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        self.container = container

        # 分割されたコンポーネントを初期化
        self.rendering_engine = RenderingEngine(config)
        self.content_processor = ContentProcessor(config)
        self.template_manager = TemplateManager(config)
        self.output_formatter = OutputFormatter(config)

        # 互換性維持のための属性
        self.graceful_errors: List[Dict[str, Any]] = []
        self.embed_errors_in_html = True
        self.footnotes_data: Optional[Dict[str, Any]] = None

        # レンダラー初期化
        self._initialize_renderers()

    def _initialize_renderers(self) -> None:
        """レンダラー初期化（互換性維持）"""
        try:
            # 基本的なレンダラー属性を設定
            self.html_formatter = None
            self.markdown_formatter = None

            self.logger.debug("レンダラー初期化完了")

        except Exception as e:
            self.logger.error(f"レンダラー初期化エラー: {e}")

    # 主要レンダリングメソッド（委譲）
    def render_nodes(self, nodes: List[Node], format: str = "html") -> str:
        """ノードリストレンダリング"""
        return self.rendering_engine.render_nodes(nodes, format)

    def render_to_file(
        self,
        nodes: List[Node],
        output_path: Union[str, Path],
        format: str = "html",
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """ファイル出力レンダリング"""
        return self.output_formatter.render_to_file(nodes, output_path, format, context)

    def render_nodes_to_html(self, nodes: List[Node]) -> str:
        """ノードリストをHTMLにレンダリング"""
        return self.rendering_engine.render_nodes_to_html(nodes)

    def render_nodes_optimized(self, nodes: List[Node]) -> str:
        """最適化されたノードレンダリング"""
        return self.rendering_engine.render_nodes_optimized(nodes)

    def render_node_optimized(self, node: Node) -> str:
        """最適化された単一ノードレンダリング"""
        return self.rendering_engine.render_node_optimized(node)

    def render_nodes_with_errors(self, nodes: List[Node]) -> str:
        """エラー付きノードレンダリング"""
        return self.rendering_engine.render_nodes_with_errors(nodes)

    def render_node(self, node: Node, context: Optional[Dict[str, Any]] = None) -> str:
        """単一ノードレンダリング"""
        return self.rendering_engine.render_node(node, context)

    def render_node_protocol(
        self, node: Node, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """プロトコル準拠ノードレンダリング"""
        return self.rendering_engine.render_node_protocol(node, context)

    # コンテンツ処理メソッド（委譲）
    def _process_text_content(self, text: str) -> str:
        """テキストコンテンツ処理"""
        return self.content_processor.process_text_content(text)

    def _contains_html_tags(self, text: str) -> bool:
        """HTMLタグ含有チェック"""
        return self.content_processor.contains_html_tags(text)

    def _render_content(self, content: str, depth: int = 0) -> str:
        """深度付きコンテンツレンダリング"""
        return self.content_processor.render_content_with_depth(content, depth)

    def _render_node_with_depth(self, node: Node, depth: int = 0) -> str:
        """深度付きノードレンダリング"""
        return self.content_processor.render_node_with_depth(node, depth)

    def _render_generic_with_depth(self, node: Node, depth: int = 0) -> str:
        """深度付き汎用レンダリング"""
        return self.content_processor.render_generic_with_depth(node, depth)

    def collect_headings(
        self, nodes: List[Node], depth: int = 0
    ) -> List[Dict[str, Any]]:
        """見出し収集"""
        return self.content_processor.collect_headings(nodes, depth)

    # テンプレート管理メソッド（委譲）
    def render_with_template(
        self,
        nodes: List[Node],
        template_path: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """テンプレート使用レンダリング"""
        return self.template_manager.render_with_template(nodes, template_path, context)

    # 出力フォーマットメソッド（委譲）
    def render_to_html(self, nodes: List[Node]) -> str:
        """HTMLレンダリング"""
        return self.output_formatter.render_to_html(nodes)

    def render_to_markdown(self, nodes: List[Node]) -> str:
        """Markdownレンダリング"""
        return self.output_formatter.render_to_markdown(nodes)

    def render_to_text(self, nodes: List[Node]) -> str:
        """テキストレンダリング"""
        return self.output_formatter.render_to_text(nodes)

    def render_to_json(self, nodes: List[Node]) -> str:
        """JSONレンダリング"""
        return self.output_formatter.render_to_json(nodes)

    # 設定・管理メソッド
    def set_footnote_data(self, footnotes_data: Dict[str, Any]) -> None:
        """脚注データ設定"""
        try:
            self.footnotes_data = footnotes_data
            self.logger.debug(
                f"脚注データを設定: {len(footnotes_data) if footnotes_data else 0}個"
            )

        except Exception as e:
            self.logger.error(f"脚注データ設定エラー: {e}")

    def set_graceful_errors(
        self, errors: List[Dict[str, Any]], embed_in_html: bool = True
    ) -> None:
        """グレースフルエラー設定"""
        self.graceful_errors = errors
        self.embed_errors_in_html = embed_in_html

        # サブコンポーネントにも設定
        self.rendering_engine.set_graceful_errors(errors, embed_in_html)

    def reset_counters(self) -> None:
        """カウンターリセット"""
        self.rendering_engine.reset_counters()

    def heading_counter(self, value: Optional[int] = None) -> int:
        """見出しカウンター"""
        return self.rendering_engine.heading_counter(value)

    # レンダラー情報・メタデータ
    def get_renderer_info(self) -> Dict[str, Any]:
        """レンダラー情報"""
        return {
            "name": "MainRenderer (Integrated)",
            "version": "2.0.0",
            "components": {
                "rendering_engine": self.rendering_engine.get_renderer_info(),
                "content_processor": self.content_processor.get_processor_info(),
                "template_manager": self.template_manager.get_manager_info(),
                "output_formatter": self.output_formatter.get_formatter_info(),
            },
            "formats": self.get_supported_formats(),
            "features": [
                "integrated_rendering",
                "content_processing",
                "template_management",
                "multi_format_output",
                "error_handling",
                "optimization",
            ],
        }

    def supports_format(self, format_hint: str) -> bool:
        """フォーマット対応確認"""
        return self.output_formatter.supports_format(format_hint)

    def get_supported_formats(self) -> List[str]:
        """対応フォーマット一覧"""
        return self.output_formatter.get_supported_formats()

    def validate(
        self, node: Node, context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """ノード検証"""
        try:
            context = context or {}
            errors = []

            # 基本検証
            if not hasattr(node, "tag"):
                errors.append("ノードにtagプロパティがありません")

            if not hasattr(node, "content"):
                errors.append("ノードにcontentプロパティがありません")

            return errors

        except Exception as e:
            self.logger.error(f"検証エラー: {e}")
            return [f"検証処理エラー: {str(e)}"]

    def validate_options(self, options: Dict[str, Any]) -> List[str]:
        """オプション検証"""
        return self.output_formatter.validate_output_options(options)

    def render(
        self, nodes: List[Node], context: Optional[Dict[str, Any]] = None
    ) -> str:
        """汎用レンダリング（プロトコル対応）"""
        try:
            if not nodes:
                return ""

            context = context or {}

            # フォーマット指定がある場合
            if "format" in context:
                output_format = context["format"]
                result_content = self.output_formatter.render_to_format(
                    nodes, output_format, context
                )
                return result_content

            # デフォルトはHTML
            return self.render_nodes_to_html(nodes)

        except Exception as e:
            self.logger.error(f"レンダリングエラー: {e}")
            result = f'<div class="error">レンダリングエラー: {str(e)}</div>'
            return result

    def get_rendering_metrics(self) -> Dict[str, Any]:
        """レンダリングメトリクス取得"""
        return self.rendering_engine.get_rendering_metrics()

    # 互換性維持のための個別レンダリングメソッド
    def _render_generic(self, node: Node) -> str:
        return self.rendering_engine._render_generic(node)

    def _render_p(self, node: Node) -> str:
        return self.rendering_engine._render_p(node)

    def _render_strong(self, node: Node) -> str:
        return self.rendering_engine._render_strong(node)

    def _render_em(self, node: Node) -> str:
        return self.rendering_engine._render_em(node)

    def _render_div(self, node: Node) -> str:
        return self.rendering_engine._render_div(node)

    def _render_h1(self, node: Node) -> str:
        return self.rendering_engine._render_h1(node)

    def _render_h2(self, node: Node) -> str:
        return self.rendering_engine._render_h2(node)

    def _render_h3(self, node: Node) -> str:
        return self.rendering_engine._render_h3(node)

    def _render_h4(self, node: Node) -> str:
        return self.rendering_engine._render_h4(node)

    def _render_h5(self, node: Node) -> str:
        return self.rendering_engine._render_h5(node)

    def _render_heading(self, node: Node, level: int) -> str:
        return self.rendering_engine._render_heading(node, level)

    def _render_ul(self, node: Node) -> str:
        return self.rendering_engine._render_ul(node)

    def _render_ol(self, node: Node) -> str:
        return self.rendering_engine._render_ol(node)

    def _render_li(self, node: Node) -> str:
        return self.rendering_engine._render_li(node)

    def _render_details(self, node: Node) -> str:
        return self.rendering_engine._render_details(node)

    def _render_pre(self, node: Node) -> str:
        return self.rendering_engine._render_pre(node)

    def _render_code(self, node: Node) -> str:
        return self.rendering_engine._render_code(node)

    def _render_image(self, node: Node) -> str:
        return self.rendering_engine._render_image(node)

    def _render_error(self, node: Node) -> str:
        return self.rendering_engine._render_error(node)

    def _render_toc(self, node: Node) -> str:
        return self.rendering_engine._render_toc(node)

    def _render_ruby(self, node: Node) -> str:
        return self.rendering_engine._render_ruby(node)

    def _render_attributes(self, attributes: Dict[str, Any]) -> str:
        return self.rendering_engine._render_attributes(attributes)

    # エラー処理メソッド（簡易版）
    def render_nodes_with_errors_optimized(self, nodes: List[Node]) -> str:
        """最適化エラー処理レンダリング"""
        return self.render_nodes_with_errors(nodes)

    def _render_error_summary(self) -> str:
        """エラーサマリーレンダリング"""
        return ""

    def _render_error_summary_optimized(self) -> str:
        """最適化エラーサマリーレンダリング"""
        return self._render_error_summary()

    def _render_single_error_optimized(
        self, error: Dict[str, Any], error_number: int
    ) -> str:
        """最適化単一エラーレンダリング"""
        return f'<div class="error">エラー {error_number}: {error.get("message", "")}</div>'

    def _embed_error_markers(self, html: str) -> str:
        """エラーマーカー埋め込み"""
        return html

    def _embed_error_markers_optimized(self, html: str) -> str:
        """最適化エラーマーカー埋め込み"""
        return self._embed_error_markers(html)

    def _create_error_marker_optimized(self, error: Dict[str, Any]) -> str:
        """最適化エラーマーカー作成"""
        return f'<span class="error-marker">{error.get("message", "エラー")}</span>'

    # レガシー互換性メソッド
    def _render_original(self, nodes: List[Node], format: str) -> str:
        """オリジナルレンダリング（互換性）"""
        return self.render_nodes(nodes, format)


# HTMLRendererエイリアス（互換性維持）
HTMLRenderer = MainRenderer


# 独立関数（互換性維持）
def render_single_node(node: Node, renderer: Optional[MainRenderer] = None) -> str:
    """単一ノードレンダリング関数"""
    if renderer is None:
        renderer = MainRenderer()

    return renderer.render_node(node)
