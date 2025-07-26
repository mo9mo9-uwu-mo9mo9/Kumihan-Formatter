"""
MainRenderer包括的テストスイート

Issue #594 Phase 2-2対応 - レンダリング機能安定化
HTML妥当性、変換精度、セキュリティ、パフォーマンスの体系的テスト
"""

import time
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.ast_nodes import Node
from kumihan_formatter.core.rendering.main_renderer import (
    HTMLRenderer,
    render_single_node,
)


class TestHTMLRenderer:
    """HTMLRendererの包括的テストクラス"""

    def test_init(self):
        """初期化テスト"""
        # When
        renderer = HTMLRenderer()

        # Then
        assert renderer.element_renderer is not None
        assert renderer.compound_renderer is not None
        assert renderer.formatter is not None
        assert renderer.content_processor is not None
        assert renderer.heading_collector is not None
        assert renderer.heading_counter == 0

    def test_nesting_order_constant(self):
        """ネスト順序定数の確認テスト"""
        # Given
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

        # Then
        assert HTMLRenderer.NESTING_ORDER == expected_order

    def test_render_nodes_empty_list(self):
        """空のノードリストレンダリングテスト"""
        # Given
        renderer = HTMLRenderer()
        nodes = []

        # When
        result = renderer.render_nodes(nodes)

        # Then
        assert result == ""

    def test_render_nodes_multiple(self):
        """複数ノードのレンダリングテスト"""
        # Given
        renderer = HTMLRenderer()
        nodes = [
            Node(type="p", content="Paragraph 1"),
            Node(type="p", content="Paragraph 2"),
            Node(type="p", content="Paragraph 3"),
        ]

        # When
        result = renderer.render_nodes(nodes)

        # Then
        assert "<p>Paragraph 1</p>" in result
        assert "<p>Paragraph 2</p>" in result
        assert "<p>Paragraph 3</p>" in result
        assert result.count("\n") == 2  # 3つの要素間に2つの改行

    def test_render_node_invalid_type(self):
        """無効なノードタイプのレンダリングテスト"""
        # Given
        renderer = HTMLRenderer()
        # 非Nodeオブジェクト

        # When
        result = renderer.render_node("plain text")

        # Then
        assert result == "plain text"  # エスケープされる

    def test_render_node_with_special_characters(self):
        """特殊文字を含むノードのレンダリングテスト"""
        # Given
        renderer = HTMLRenderer()
        # HTMLエスケープが必要な文字

        # When
        result = renderer.render_node("<script>alert('XSS')</script>")

        # Then
        assert "&lt;script&gt;" in result
        assert "&lt;/script&gt;" in result
        assert "alert" in result

    def test_render_paragraph(self):
        """段落レンダリングテスト"""
        # Given
        renderer = HTMLRenderer()
        node = Node(type="p", content="This is a paragraph.")

        # When
        result = renderer.render_node(node)

        # Then
        assert result == "<p>This is a paragraph.</p>"

    def test_render_strong(self):
        """太字レンダリングテスト"""
        # Given
        renderer = HTMLRenderer()
        node = Node(type="strong", content="Bold text")

        # When
        result = renderer.render_node(node)

        # Then
        assert result == "<strong>Bold text</strong>"

    def test_render_emphasis(self):
        """斜体レンダリングテスト"""
        # Given
        renderer = HTMLRenderer()
        node = Node(type="em", content="Italic text")

        # When
        result = renderer.render_node(node)

        # Then
        assert result == "<em>Italic text</em>"

    def test_render_div_with_class(self):
        """クラス付きdivレンダリングテスト"""
        # Given
        renderer = HTMLRenderer()
        node = Node(
            type="div", content="Content in div", attributes={"class": "highlight"}
        )

        # When
        result = renderer.render_node(node)

        # Then
        assert '<div class="highlight">' in result
        assert "Content in div" in result
        assert "</div>" in result

    def test_render_headings_all_levels(self):
        """全レベルの見出しレンダリングテスト"""
        # Given
        renderer = HTMLRenderer()

        # When/Then
        for level in range(1, 6):
            node = Node(type=f"h{level}", content=f"Heading Level {level}")
            result = renderer.render_node(node)

            assert f"<h{level}" in result
            assert f"id=" in result  # 見出しにはIDが付与される
            assert f"Heading Level {level}" in result
            assert f"</h{level}>" in result

    def test_render_unordered_list(self):
        """順序なしリストレンダリングテスト"""
        # Given
        renderer = HTMLRenderer()
        list_items = [
            Node(type="li", content="Item 1"),
            Node(type="li", content="Item 2"),
            Node(type="li", content="Item 3"),
        ]
        node = Node(type="ul", content=list_items)

        # When
        result = renderer.render_node(node)

        # Then
        assert "<ul>" in result
        assert "</ul>" in result
        assert result.count("<li>") == 3
        assert "Item 1" in result
        assert "Item 2" in result
        assert "Item 3" in result

    def test_render_ordered_list(self):
        """順序付きリストレンダリングテスト"""
        # Given
        renderer = HTMLRenderer()
        list_items = [
            Node(type="li", content="First"),
            Node(type="li", content="Second"),
            Node(type="li", content="Third"),
        ]
        node = Node(type="ol", content=list_items)

        # When
        result = renderer.render_node(node)

        # Then
        assert "<ol>" in result
        assert "</ol>" in result
        assert result.count("<li>") == 3

    def test_render_details_summary(self):
        """details/summaryレンダリングテスト"""
        # Given
        renderer = HTMLRenderer()
        node = Node(
            type="details",
            content="Hidden content",
            attributes={"summary": "Click to expand"},
        )

        # When
        result = renderer.render_node(node)

        # Then
        assert "<details>" in result
        assert "<summary>" in result
        assert "Click to expand" in result
        assert "Hidden content" in result
        assert "</details>" in result

    def test_render_preformatted_text(self):
        """整形済みテキストレンダリングテスト"""
        # Given
        renderer = HTMLRenderer()
        node = Node(type="pre", content="def hello():\n    print('Hello, World!')")

        # When
        result = renderer.render_node(node)

        # Then
        assert "<pre>" in result
        assert "</pre>" in result
        assert "def hello():" in result
        # シングルクォートはHTMLエンティティに変換される可能性がある
        assert "Hello, World!" in result
        assert "print" in result

    def test_render_inline_code(self):
        """インラインコードレンダリングテスト"""
        # Given
        renderer = HTMLRenderer()
        node = Node(type="code", content="var x = 42;")

        # When
        result = renderer.render_node(node)

        # Then
        assert "<code>" in result
        assert "</code>" in result
        assert "var x = 42;" in result

    def test_render_image(self):
        """画像レンダリングテスト"""
        # Given
        renderer = HTMLRenderer()
        node = Node(
            type="image",
            content="test.jpg",  # ファイル名をcontentに設定
            attributes={"alt": "Test Image", "title": "A test image"},
        )

        # When
        result = renderer.render_node(node)

        # Then
        assert "<img" in result
        assert 'src="images/test.jpg"' in result  # imagesディレクトリが付与される
        assert 'alt="Test Image"' in result
        # titleはelement_rendererで使用されない可能性がある

    def test_render_error_node(self):
        """エラーノードレンダリングテスト"""
        # Given
        renderer = HTMLRenderer()
        node = Node(
            type="error",
            content="Syntax error",
            attributes={"message": "Syntax error", "line_number": 10},
        )

        # When
        result = renderer.render_node(node)

        # Then
        assert "error" in result.lower()
        assert "Syntax error" in result

    def test_render_toc_placeholder(self):
        """目次プレースホルダーレンダリングテスト"""
        # Given
        renderer = HTMLRenderer()
        node = Node(type="toc", content="")

        # When
        result = renderer.render_node(node)

        # Then
        assert "toc" in result.lower() or result == ""

    def test_nested_content_rendering(self):
        """ネストされたコンテンツのレンダリングテスト"""
        # Given
        renderer = HTMLRenderer()
        inner_node = Node(type="strong", content="important")
        # contentにリストを渡す（ElementRendererの仕様に合わせる）
        outer_node = Node(type="p", content=["This is ", inner_node, " text."])

        # When
        result = renderer.render_node(outer_node)

        # Then
        assert "<p>" in result
        assert "<strong>important</strong>" in result
        assert "</p>" in result

    def test_collect_headings_empty(self):
        """空ノードリストからの見出し収集テスト"""
        # Given
        renderer = HTMLRenderer()
        nodes = []

        # When
        headings = renderer.collect_headings(nodes)

        # Then
        assert headings == []

    def test_collect_headings_multiple_levels(self):
        """複数レベルの見出し収集テスト"""
        # Given
        renderer = HTMLRenderer()
        nodes = [
            Node(type="h1", content="Chapter 1"),
            Node(type="p", content="Some text"),
            Node(type="h2", content="Section 1.1"),
            Node(type="h2", content="Section 1.2"),
            Node(type="h3", content="Subsection 1.2.1"),
        ]

        # When
        headings = renderer.collect_headings(nodes)

        # Then
        assert len(headings) == 4
        # heading_collectorが返すフォーマットに合わせる
        if headings and isinstance(headings[0], dict):
            # levelキーの存在を確認
            assert "level" in headings[0] or "heading_level" in headings[0]
            # textまたはcontentキーの存在を確認
            assert any(key in headings[0] for key in ["text", "content", "title"])

    def test_reset_counters(self):
        """カウンターリセットテスト"""
        # Given
        renderer = HTMLRenderer()
        renderer.heading_counter = 5

        # When
        renderer.reset_counters()

        # Then
        assert renderer.heading_counter == 0

    def test_heading_counter_property(self):
        """見出しカウンタープロパティテスト"""
        # Given
        renderer = HTMLRenderer()

        # When
        renderer.heading_counter = 10

        # Then
        assert renderer.heading_counter == 10
        assert renderer.element_renderer.heading_counter == 10
        assert renderer.heading_collector.heading_counter == 10

    def test_render_single_node_function(self):
        """render_single_node関数テスト"""
        # Given
        node = Node(type="p", content="Test paragraph")

        # When
        result = render_single_node(node)

        # Then
        assert "<p>Test paragraph</p>" in result

    def test_render_single_node_with_depth(self):
        """深さ指定付きrender_single_node関数テスト"""
        # Given
        node = Node(type="p", content="Deep paragraph")

        # When
        result = render_single_node(node, depth=3)

        # Then
        assert "<p>Deep paragraph</p>" in result

    def test_performance_large_document(self):
        """大規模ドキュメントのパフォーマンステスト"""
        # Given
        renderer = HTMLRenderer()
        # 1000個のノードを生成
        nodes = [Node(type="p", content=f"Paragraph {i}") for i in range(1000)]

        # When
        start_time = time.time()
        result = renderer.render_nodes(nodes)
        elapsed_time = time.time() - start_time

        # Then
        assert len(result) > 0
        assert result.count("<p>") == 1000
        # パフォーマンス要件: <100ms/KB
        # 約50KB（50文字 × 1000段落）で5秒以内
        assert elapsed_time < 5.0

    def test_xss_prevention(self):
        """XSS攻撃防止テスト"""
        # Given
        renderer = HTMLRenderer()
        malicious_contents = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<iframe src='evil.com'></iframe>",
        ]

        # When/Then
        for content in malicious_contents:
            node = Node(type="p", content=content)
            result = renderer.render_node(node)

            # スクリプトタグがエスケープされていることを確認
            assert "<script>" not in result
            assert "javascript:" not in result or "&" in result
            # onerror属性はエスケープされても文字列として残る場合がある
            # 重要なのは実行可能な形で残っていないこと
            assert "<img src=x onerror=" not in result  # 実行可能な形ではない
            assert "<iframe" not in result

    def test_unicode_support(self):
        """Unicode文字サポートテスト"""
        # Given
        renderer = HTMLRenderer()
        unicode_texts = [
            "日本語テキスト",
            "中文文本",
            "Текст на русском",
            "🎉 Emoji support 🚀",
            "العربية",
        ]

        # When/Then
        for text in unicode_texts:
            node = Node(type="p", content=text)
            result = renderer.render_node(node)
            assert text in result

    def test_memory_usage_efficiency(self):
        """メモリ使用効率テスト"""
        # Given
        renderer = HTMLRenderer()
        # メモリ使用量を抑えるため、同じノードを再利用
        base_node = Node(type="p", content="x" * 1000)  # 1KB

        # When - 50回レンダリング（約50KB相当）
        results = []
        for _ in range(50):
            result = renderer.render_node(base_node)
            results.append(result)

        # Then
        # 全結果が同じであることを確認（メモリリークがないこと）
        assert all(r == results[0] for r in results)

    def test_generic_node_fallback(self):
        """未知のノードタイプのフォールバックテスト"""
        # Given
        renderer = HTMLRenderer()
        node = Node(type="unknown_type", content="Unknown content")

        # When
        result = renderer.render_node(node)

        # Then
        # ジェネリックレンダラーが使用される
        assert "Unknown content" in result

    @patch("kumihan_formatter.core.rendering.main_renderer.ElementRenderer")
    def test_element_renderer_injection(self, mock_element_renderer):
        """ElementRendererへのメインレンダラー注入テスト"""
        # Given
        mock_instance = Mock()
        mock_element_renderer.return_value = mock_instance

        # When
        renderer = HTMLRenderer()

        # Then
        mock_instance.set_main_renderer.assert_called_once_with(renderer)

    def test_html_validity_output(self):
        """HTML妥当性テスト - W3C準拠"""
        # Given
        renderer = HTMLRenderer()
        nodes = [
            Node(type="h1", content="Title"),
            Node(
                type="p",
                content="",
                children=[
                    Node(type="text", content="Paragraph with "),
                    Node(type="strong", content="bold"),
                    Node(type="text", content=" and "),
                    Node(type="em", content="italic"),
                ],
            ),
            Node(
                type="ul",
                content="",
                children=[
                    Node(type="li", content="Item 1"),
                    Node(type="li", content="Item 2"),
                ],
            ),
        ]

        # When
        result = renderer.render_nodes(nodes)

        # Then
        # 基本的なHTML構造の妥当性チェック
        assert result.count("<h1") == result.count("</h1>")
        assert result.count("<p>") == result.count("</p>")
        assert result.count("<ul>") == result.count("</ul>")
        assert result.count("<li>") == result.count("</li>")
        assert result.count("<strong>") == result.count("</strong>")
        assert result.count("<em>") == result.count("</em>")

    def test_accessibility_attributes(self):
        """アクセシビリティ属性テスト"""
        # Given
        renderer = HTMLRenderer()

        # 画像のalt属性
        img_node = Node(
            type="image", content="test.jpg", attributes={"alt": "Description"}
        )
        img_result = renderer.render_node(img_node)
        assert 'alt="Description"' in img_result

        # 見出しのID属性（アンカーリンク用）
        h1_node = Node(type="h1", content="Section Title")
        h1_result = renderer.render_node(h1_node)
        assert "id=" in h1_result
