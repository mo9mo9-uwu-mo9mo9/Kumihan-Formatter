"""Renderer Module Integration Coverage Tests

モジュールレベル関数、後方互換性、エラーハンドリング、統合シナリオのテスト。
"""

from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.ast_nodes import Node
from kumihan_formatter.core.rendering.main_renderer import (
    HTMLRenderer,
    render_single_node,
)


class TestModuleLevelFunctions:
    """モジュールレベル関数のテスト"""

    def test_render_single_node(self):
        """render_single_node関数のテスト"""
        node = Mock(spec=Node)
        node.type = "p"

        with patch(
            "kumihan_formatter.core.rendering.main_renderer.HTMLRenderer"
        ) as mock_renderer_class:
            mock_renderer = Mock()
            mock_renderer_class.return_value = mock_renderer
            mock_renderer._render_node_with_depth.return_value = "<p>test</p>"

            result = render_single_node(node, 2)

            assert result == "<p>test</p>"
            mock_renderer_class.assert_called_once()
            mock_renderer._render_node_with_depth.assert_called_once_with(node, 2)

    def test_render_single_node_default_depth(self):
        """デフォルト深度でのrender_single_node"""
        node = Mock(spec=Node)

        with patch(
            "kumihan_formatter.core.rendering.main_renderer.HTMLRenderer"
        ) as mock_renderer_class:
            mock_renderer = Mock()
            mock_renderer_class.return_value = mock_renderer
            mock_renderer._render_node_with_depth.return_value = "<div>test</div>"

            result = render_single_node(node)

            assert result == "<div>test</div>"
            mock_renderer._render_node_with_depth.assert_called_once_with(node, 0)


class TestBackwardCompatibility:
    """後方互換性のテスト"""

    def test_compound_element_renderer_alias(self):
        """CompoundElementRendererエイリアスの確認"""
        from kumihan_formatter.core.rendering.compound_renderer import (
            CompoundElementRenderer as OriginalRenderer,
        )
        from kumihan_formatter.core.rendering.main_renderer import (
            CompoundElementRenderer,
        )

        assert CompoundElementRenderer is OriginalRenderer

    def test_module_exports(self):
        """__all__エクスポートの確認"""
        from kumihan_formatter.core.rendering.main_renderer import __all__

        expected_exports = [
            "HTMLRenderer",
            "CompoundElementRenderer",
            "render_single_node",
        ]
        assert __all__ == expected_exports


class TestErrorHandling:
    """エラーハンドリングのテスト"""

    def test_render_node_with_exception(self):
        """レンダリング中の例外処理"""
        renderer = HTMLRenderer()

        node = Mock(spec=Node)
        node.type = "p"

        # _render_pが例外を発生させる場合
        with patch.object(renderer, "_render_p") as mock_render:
            mock_render.side_effect = Exception("Render error")

            # 例外が適切に伝播されることを確認
            with pytest.raises(Exception, match="Render error"):
                renderer.render_node(node)

    def test_render_nodes_with_exception(self):
        """ノードリストレンダリング中の例外処理"""
        renderer = HTMLRenderer()

        node1 = Mock(spec=Node)
        node2 = Mock(spec=Node)

        with patch.object(renderer, "render_node") as mock_render:
            # 最初のノードで例外が発生
            mock_render.side_effect = [Exception("Error"), "<p>Success</p>"]

            # 例外が適切に伝播されることを確認
            with pytest.raises(Exception, match="Error"):
                renderer.render_nodes([node1, node2])


class TestIntegrationScenarios:
    """統合シナリオのテスト"""

    def test_full_rendering_workflow(self):
        """完全なレンダリングワークフローのテスト"""
        renderer = HTMLRenderer()

        # 複数の異なるタイプのノードを作成
        nodes = []

        # 見出しノード
        h1_node = Mock(spec=Node)
        h1_node.type = "h1"
        nodes.append(h1_node)

        # 段落ノード
        p_node = Mock(spec=Node)
        p_node.type = "p"
        nodes.append(p_node)

        # リストノード
        ul_node = Mock(spec=Node)
        ul_node.type = "ul"
        nodes.append(ul_node)

        # 各レンダリングメソッドをモック
        with (
            patch.object(
                renderer.heading_renderer, "render_h1", return_value="<h1>Title</h1>"
            ),
            patch.object(
                renderer.element_renderer,
                "render_paragraph",
                return_value="<p>Text</p>",
            ),
            patch.object(
                renderer.element_renderer,
                "render_unordered_list",
                return_value="<ul><li>Item</li></ul>",
            ),
        ):
            result = renderer.render_nodes(nodes)

            expected = "<h1>Title</h1>\n<p>Text</p>\n<ul><li>Item</li></ul>"
            assert result == expected

    def test_counter_synchronization(self):
        """カウンタ同期のテスト"""
        renderer = HTMLRenderer()

        # カウンタを設定
        renderer.heading_counter = 15

        # 両方のコンポーネントに同期されることを確認
        assert renderer.heading_renderer.heading_counter == 15
        assert renderer.heading_collector.heading_counter == 15

        # リセット後の確認
        renderer.reset_counters()

        # リセットメソッドが呼ばれたことを確認
