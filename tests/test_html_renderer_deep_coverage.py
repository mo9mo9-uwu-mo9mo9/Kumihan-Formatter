"""HTML Renderer Deep Coverage Tests

main_renderer.py 48%→90%+の深度カバレッジ向上テスト。
"""

from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.ast_nodes import Node
from kumihan_formatter.core.rendering.main_renderer import (
    HTMLRenderer,
    render_single_node,
)


class TestHTMLRendererDeepCoverage:
    """HTMLRenderer深度テスト - 48%→90%+目標"""

    def test_html_renderer_initialization(self):
        """HTMLRenderer初期化テスト"""
        renderer = HTMLRenderer()

        # 必要なコンポーネントが初期化されていることを確認
        assert renderer.element_renderer is not None
        assert renderer.compound_renderer is not None
        assert renderer.formatter is not None
        assert renderer.heading_renderer is not None
        assert renderer.content_processor is not None
        assert renderer.heading_collector is not None

        # 相互参照が正しく設定されていることを確認
        assert renderer.element_renderer._main_renderer == renderer
        assert renderer.heading_renderer._main_renderer == renderer

    def test_nesting_order_constant(self):
        """NESTING_ORDER定数の確認"""
        renderer = HTMLRenderer()

        expected_order = [
            "details",
            "div",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "strong",
            "em",
        ]

        assert renderer.NESTING_ORDER == expected_order

    def test_render_nodes_empty(self):
        """空のノードリストのレンダリング"""
        renderer = HTMLRenderer()
        result = renderer.render_nodes([])
        assert result == ""

    def test_render_nodes_multiple(self):
        """複数ノードのレンダリング"""
        renderer = HTMLRenderer()

        # モックノードを作成
        node1 = Mock(spec=Node)
        node1.type = "p"
        node1.content = "Test1"

        node2 = Mock(spec=Node)
        node2.type = "p"
        node2.content = "Test2"

        with patch.object(renderer, "render_node") as mock_render:
            mock_render.side_effect = ["<p>Test1</p>", "<p>Test2</p>"]

            result = renderer.render_nodes([node1, node2])

            assert result == "<p>Test1</p>\n<p>Test2</p>"
            assert mock_render.call_count == 2

    def test_render_nodes_with_empty_results(self):
        """空の結果を含むノードリストのレンダリング"""
        renderer = HTMLRenderer()

        node1 = Mock(spec=Node)
        node2 = Mock(spec=Node)

        with patch.object(renderer, "render_node") as mock_render:
            mock_render.side_effect = ["<p>Test</p>", ""]  # 2番目は空

            result = renderer.render_nodes([node1, node2])

            assert result == "<p>Test</p>"

    def test_render_node_non_node_object(self):
        """Node以外のオブジェクトのレンダリング"""
        renderer = HTMLRenderer()

        # 文字列をレンダリング
        result = renderer.render_node("plain text")
        assert result == "plain text"

        # HTMLエスケープが必要な文字列
        result = renderer.render_node("<script>alert('xss')</script>")
        assert "&lt;script&gt;" in result

    def test_render_node_with_specific_type(self):
        """特定タイプのノードレンダリング"""
        renderer = HTMLRenderer()

        node = Mock(spec=Node)
        node.type = "p"

        with patch.object(renderer, "_render_p") as mock_render_p:
            mock_render_p.return_value = "<p>test</p>"

            result = renderer.render_node(node)

            assert result == "<p>test</p>"
            mock_render_p.assert_called_once_with(node)

    def test_render_node_generic_fallback(self):
        """汎用レンダラーへのフォールバック"""
        renderer = HTMLRenderer()

        node = Mock(spec=Node)
        node.type = "unknown_type"

        with patch.object(renderer, "_render_generic") as mock_render_generic:
            mock_render_generic.return_value = "<div>unknown</div>"

            result = renderer.render_node(node)

            assert result == "<div>unknown</div>"
            mock_render_generic.assert_called_once_with(node)

    def test_all_specific_render_methods(self):
        """全ての特定レンダリングメソッドのテスト"""
        renderer = HTMLRenderer()
        node = Mock(spec=Node)

        # 各メソッドが正しいレンダラーに委譲することを確認
        test_cases = [
            ("_render_generic", "element_renderer", "render_generic"),
            ("_render_p", "element_renderer", "render_paragraph"),
            ("_render_strong", "element_renderer", "render_strong"),
            ("_render_em", "element_renderer", "render_emphasis"),
            ("_render_div", "element_renderer", "render_div"),
            ("_render_h1", "heading_renderer", "render_h1"),
            ("_render_h2", "heading_renderer", "render_h2"),
            ("_render_h3", "heading_renderer", "render_h3"),
            ("_render_h4", "heading_renderer", "render_h4"),
            ("_render_h5", "heading_renderer", "render_h5"),
            ("_render_ul", "element_renderer", "render_unordered_list"),
            ("_render_ol", "element_renderer", "render_ordered_list"),
            ("_render_li", "element_renderer", "render_list_item"),
            ("_render_details", "element_renderer", "render_details"),
            ("_render_pre", "element_renderer", "render_preformatted"),
            ("_render_code", "element_renderer", "render_code"),
            ("_render_image", "element_renderer", "render_image"),
            ("_render_error", "element_renderer", "render_error"),
            ("_render_toc", "element_renderer", "render_toc_placeholder"),
        ]

        for method_name, renderer_attr, target_method in test_cases:
            with patch.object(
                getattr(renderer, renderer_attr), target_method
            ) as mock_method:
                mock_method.return_value = f"<{method_name}>test</{method_name}>"

                method = getattr(renderer, method_name)
                result = method(node)

                assert f"<{method_name}>test</{method_name}>" in result
                mock_method.assert_called_once_with(node)

    def test_render_heading_with_level(self):
        """レベル指定見出しレンダリング"""
        renderer = HTMLRenderer()
        node = Mock(spec=Node)

        with patch.object(renderer.heading_renderer, "render_heading") as mock_render:
            mock_render.return_value = "<h2 id='test'>Test</h2>"

            result = renderer._render_heading(node, 2)

            assert result == "<h2 id='test'>Test</h2>"
            mock_render.assert_called_once_with(node, 2)

    def test_content_processing_methods(self):
        """コンテンツ処理メソッド群のテスト"""
        renderer = HTMLRenderer()

        # _render_content
        with patch.object(renderer.content_processor, "render_content") as mock_render:
            mock_render.return_value = "processed content"

            result = renderer._render_content("content", 1)

            assert result == "processed content"
            mock_render.assert_called_once_with("content", 1)

        # _render_node_with_depth
        node = Mock(spec=Node)
        with patch.object(
            renderer.content_processor, "render_node_with_depth"
        ) as mock_render:
            mock_render.return_value = "<div>depth content</div>"

            result = renderer._render_node_with_depth(node, 2)

            assert result == "<div>depth content</div>"
            mock_render.assert_called_once_with(node, 2)

        # _render_generic_with_depth
        with patch.object(renderer.element_renderer, "render_generic") as mock_render:
            mock_render.return_value = "<span>generic</span>"

            result = renderer._render_generic_with_depth(node, 1)

            assert result == "<span>generic</span>"
            mock_render.assert_called_once_with(node)

    def test_html_utility_methods(self):
        """HTMLユーティリティメソッドのテスト"""
        renderer = HTMLRenderer()

        # _process_text_content
        with patch(
            "kumihan_formatter.core.rendering.main_renderer.process_text_content"
        ) as mock_process:
            mock_process.return_value = "processed text"

            result = renderer._process_text_content("raw text")

            assert result == "processed text"
            mock_process.assert_called_once_with("raw text")

        # _contains_html_tags
        with patch(
            "kumihan_formatter.core.rendering.html_utils.contains_html_tags"
        ) as mock_contains:
            mock_contains.return_value = True

            result = renderer._contains_html_tags("<p>test</p>")

            assert result is True
            mock_contains.assert_called_once_with("<p>test</p>")

        # _render_attributes
        with patch(
            "kumihan_formatter.core.rendering.html_utils.render_attributes"
        ) as mock_render:
            mock_render.return_value = 'class="test" id="test"'

            attrs = {"class": "test", "id": "test"}
            result = renderer._render_attributes(attrs)

            assert result == 'class="test" id="test"'
            mock_render.assert_called_once_with(attrs)

    def test_heading_collection(self):
        """見出し収集機能のテスト"""
        renderer = HTMLRenderer()
        nodes = [Mock(spec=Node)]

        with patch.object(
            renderer.heading_collector, "collect_headings"
        ) as mock_collect:
            mock_collect.return_value = [{"level": 1, "text": "Test", "id": "test"}]

            result = renderer.collect_headings(nodes, 1)

            assert result == [{"level": 1, "text": "Test", "id": "test"}]
            mock_collect.assert_called_once_with(nodes, 1)

    def test_counter_management(self):
        """カウンタ管理機能のテスト"""
        renderer = HTMLRenderer()

        # reset_counters
        with (
            patch.object(renderer.heading_renderer, "reset_counters") as mock_heading,
            patch.object(
                renderer.heading_collector, "reset_counters"
            ) as mock_collector,
            patch.object(renderer.element_renderer, "reset_counters") as mock_element,
        ):
            renderer.reset_counters()

            mock_heading.assert_called_once()
            mock_collector.assert_called_once()
            mock_element.assert_called_once()

    def test_heading_counter_property(self):
        """heading_counterプロパティのテスト"""
        renderer = HTMLRenderer()

        # ゲッター
        renderer.heading_renderer.heading_counter = 5
        assert renderer.heading_counter == 5

        # セッター
        renderer.heading_counter = 10
        assert renderer.heading_renderer.heading_counter == 10
        assert renderer.heading_collector.heading_counter == 10

    def test_dynamic_method_resolution(self):
        """動的メソッド解決のテスト"""
        renderer = HTMLRenderer()

        # 存在するメソッド
        node = Mock(spec=Node)
        node.type = "p"

        method = getattr(renderer, f"_render_{node.type}", renderer._render_generic)
        assert method == renderer._render_p

        # 存在しないメソッド
        node.type = "nonexistent"
        method = getattr(renderer, f"_render_{node.type}", renderer._render_generic)
        assert method == renderer._render_generic
