"""要素レンダリング委譲モジュール

Issue #912 Renderer系統合リファクタリング対応
main_renderer.pyから分離された要素レンダリング処理
"""

from typing import TYPE_CHECKING, Any, Dict, cast

if TYPE_CHECKING:
    from ..main_renderer import MainRenderer

from ...ast_nodes import Node
from ...utilities.logger import get_logger


class ElementRendererDelegate:
    """要素レンダリング委譲クラス

    MainRendererから分離された要素レンダリング処理を担当
    - 各要素タイプのレンダリングメソッド (_render_* 系)
    - レンダリングメソッドキャッシュ機能
    - 最適化されたレンダリングロジック
    """

    def __init__(self, main_renderer: "MainRenderer") -> None:
        """初期化

        Args:
            main_renderer: メインレンダラーインスタンス
        """
        self.main_renderer = main_renderer
        self.logger = get_logger(__name__)
        self._renderer_method_cache: Dict[str, Any] = {}

    def render_node(self, node: Node) -> str:
        """単一ノードのレンダリング

        Args:
            node: レンダリングするASTノード

        Returns:
            str: レンダリング結果HTML
        """
        if not isinstance(node, Node):
            raise TypeError(f"Expected Node instance, got {type(node)}")

        # 委譲メソッドを動的に検索して呼び出し
        method_name = f"_render_{node.type}"
        renderer_method = getattr(self, method_name, self._render_generic)
        return renderer_method(node)

    def render_node_optimized(self, node: Node) -> str:
        """単一ノードの最適化レンダリング

        Args:
            node: レンダリングするASTノード

        Returns:
            str: レンダリング結果HTML
        """
        # 最適化: メソッド動的検索を避けるため事前キャッシュ
        renderer_method = self._get_cached_renderer_method(node.type)
        return cast(str, renderer_method(node))

    def _get_cached_renderer_method(self, node_type: str) -> Any:
        """レンダラーメソッドのキャッシュ取得（メソッド検索最適化）

        Args:
            node_type: ノードタイプ

        Returns:
            Any: レンダラーメソッド
        """
        # キャッシュから取得
        if node_type not in self._renderer_method_cache:
            method_name = f"_render_{node_type}"
            self._renderer_method_cache[node_type] = getattr(
                self, method_name, self._render_generic
            )

        return self._renderer_method_cache[node_type]

    # ==========================================
    # 各要素タイプのレンダリングメソッド
    # ==========================================

    def _render_generic(self, node: Node) -> str:
        """汎用ノードレンダラー"""
        return self.main_renderer.element_renderer.render_generic(node)

    def _render_p(self, node: Node) -> str:
        """段落ノードレンダリング"""
        return self.main_renderer.element_renderer.render_paragraph(node)

    def _render_strong(self, node: Node) -> str:
        """太字ノードレンダリング"""
        return self.main_renderer.element_renderer.render_strong(node)

    def _render_em(self, node: Node) -> str:
        """イタリックノードレンダリング"""
        return self.main_renderer.element_renderer.render_emphasis(node)

    def _render_div(self, node: Node) -> str:
        """divノードレンダリング"""
        return self.main_renderer.element_renderer.render_div(node)

    def _render_h1(self, node: Node) -> str:
        """h1見出しレンダリング"""
        return self.main_renderer.element_renderer.render_heading(node, 1)

    def _render_h2(self, node: Node) -> str:
        """h2見出しレンダリング"""
        return self.main_renderer.element_renderer.render_heading(node, 2)

    def _render_h3(self, node: Node) -> str:
        """h3見出しレンダリング"""
        return self.main_renderer.element_renderer.render_heading(node, 3)

    def _render_h4(self, node: Node) -> str:
        """h4見出しレンダリング"""
        return self.main_renderer.element_renderer.render_heading(node, 4)

    def _render_h5(self, node: Node) -> str:
        """h5見出しレンダリング"""
        return self.main_renderer.element_renderer.render_heading(node, 5)

    def _render_heading(self, node: Node, level: int) -> str:
        """ID付き見出しレンダリング"""
        return self.main_renderer.element_renderer.render_heading(node, level)

    def _render_ul(self, node: Node) -> str:
        """無順序リストレンダリング"""
        return self.main_renderer.element_renderer.render_unordered_list(node)

    def _render_ol(self, node: Node) -> str:
        """順序リストレンダリング"""
        return self.main_renderer.element_renderer.render_ordered_list(node)

    def _render_li(self, node: Node) -> str:
        """リスト項目レンダリング"""
        return self.main_renderer.element_renderer.render_list_item(node)

    def _render_details(self, node: Node) -> str:
        """詳細/サマリー要素レンダリング"""
        return self.main_renderer.element_renderer.render_details(node)

    def _render_pre(self, node: Node) -> str:
        """整形済みテキストレンダリング"""
        return self.main_renderer.element_renderer.render_preformatted(node)

    def _render_code(self, node: Node) -> str:
        """インラインコードレンダリング"""
        return self.main_renderer.element_renderer.render_code(node)

    def _render_image(self, node: Node) -> str:
        """画像要素レンダリング"""
        return self.main_renderer.element_renderer.render_image(node)

    def _render_error(self, node: Node) -> str:
        """エラーノードレンダリング"""
        return self.main_renderer.element_renderer.render_error(node)

    def _render_toc(self, node: Node) -> str:
        """目次マーカーレンダリング"""
        return self.main_renderer.element_renderer.render_toc_placeholder(node)

    def _render_ruby(self, node: Node) -> str:
        """ルビ要素レンダリング"""
        return self.main_renderer.element_renderer.render_ruby(node)

    def _render_content(self, content: Any, depth: int = 0) -> str:
        """ノードコンテンツレンダリング（再帰）"""
        return self.main_renderer.content_processor.render_content(content, depth)

    def _render_node_with_depth(self, node: Node, depth: int = 0) -> str:
        """深度追跡付き単一ノードレンダリング"""
        return self.main_renderer.content_processor.render_node_with_depth(node, depth)

    def _render_generic_with_depth(self, node: Node, depth: int = 0) -> str:
        """深度追跡付き汎用ノードレンダリング"""
        return self.main_renderer.element_renderer.render_generic(node)

    def _process_text_content(self, text: str) -> str:
        """テキストコンテンツ処理 - html_utilsに委譲"""
        return self.main_renderer._process_text_content(text)

    def _contains_html_tags(self, text: str) -> bool:
        """HTMLタグ含有チェック - html_utilsに委譲"""
        return self.main_renderer._contains_html_tags(text)

    def _render_attributes(self, attributes: Dict[str, Any]) -> str:
        """HTML属性レンダリング - html_utilsに委譲"""
        return self.main_renderer._render_attributes(attributes)
