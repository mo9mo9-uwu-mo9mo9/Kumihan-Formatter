"""ElementRenderer包括的テストスイート

Issue #594 Phase 2-2対応 - レンダリング機能安定化
統合ElementRendererの完全テスト（実際のNodeオブジェクト使用）
"""

from unittest.mock import Mock

import pytest

from kumihan_formatter.core.ast_nodes import Node
from kumihan_formatter.core.rendering.element_renderer import ElementRenderer


class TestElementRenderer:
    """統合ElementRendererの包括的テストクラス"""

    def test_init(self):
        """初期化テスト"""
        # When
        renderer = ElementRenderer()

        # Then
        assert renderer._main_renderer is None
        assert renderer.heading_counter == 0

    def test_set_main_renderer(self):
        """メインレンダラー設定テスト"""
        # Given
        renderer = ElementRenderer()
        main_renderer = Mock()

        # When
        renderer.set_main_renderer(main_renderer)

        # Then
        assert renderer._main_renderer == main_renderer

    def test_render_paragraph(self):
        """段落レンダリングテスト"""
        # Given
        renderer = ElementRenderer()
        node = Node(type="p", content="This is a paragraph.")

        # When
        result = renderer.render_paragraph(node)

        # Then
        assert result == "<p>This is a paragraph.</p>"

    def test_render_strong(self):
        """太字レンダリングテスト"""
        # Given
        renderer = ElementRenderer()
        node = Node(type="strong", content="Bold text")

        # When
        result = renderer.render_strong(node)

        # Then
        assert result == "<strong>Bold text</strong>"

    def test_render_emphasis(self):
        """斜体レンダリングテスト"""
        # Given
        renderer = ElementRenderer()
        node = Node(type="em", content="Italic text")

        # When
        result = renderer.render_emphasis(node)

        # Then
        assert result == "<em>Italic text</em>"

    def test_render_preformatted(self):
        """整形済みテキストレンダリングテスト"""
        # Given
        renderer = ElementRenderer()
        node = Node(
            type="pre",
            content="def hello():\n    print('Hello, World!')",
            attributes={"class": "code-block"},
        )

        # When
        result = renderer.render_preformatted(node)

        # Then
        assert '<pre class="code-block">' in result
        assert "def hello():" in result
        assert "Hello, World!" in result
        assert "</pre>" in result

    def test_render_preformatted_no_attributes(self):
        """属性なし整形済みテキストレンダリングテスト"""
        # Given
        renderer = ElementRenderer()
        node = Node(type="pre", content="Simple code")

        # When
        result = renderer.render_preformatted(node)

        # Then
        assert result == "<pre>Simple code</pre>"

    def test_render_code(self):
        """インラインコードレンダリングテスト"""
        # Given
        renderer = ElementRenderer()
        node = Node(type="code", content="var x = 42;")

        # When
        result = renderer.render_code(node)

        # Then
        assert result == "<code>var x = 42;</code>"

    def test_render_code_with_attributes(self):
        """属性付きインラインコードレンダリングテスト"""
        # Given
        renderer = ElementRenderer()
        node = Node(
            type="code",
            content="console.log('test');",
            attributes={"class": "javascript"},
        )

        # When
        result = renderer.render_code(node)

        # Then
        assert '<code class="javascript">' in result
        assert "console.log" in result
        assert "</code>" in result

    def test_render_image(self):
        """画像レンダリングテスト"""
        # Given
        renderer = ElementRenderer()
        node = Node(type="image", content="test.jpg", attributes={"alt": "Test Image"})

        # When
        result = renderer.render_image(node)

        # Then
        assert '<img src="images/test.jpg"' in result
        assert 'alt="Test Image"' in result
        assert "/>" in result

    def test_render_image_no_alt(self):
        """alt属性なし画像レンダリングテスト"""
        # Given
        renderer = ElementRenderer()
        node = Node(type="image", content="photo.png")

        # When
        result = renderer.render_image(node)

        # Then
        assert '<img src="images/photo.png" />' in result

    def test_render_error(self):
        """エラーレンダリングテスト"""
        # Given
        renderer = ElementRenderer()
        node = Node(type="error", content="Syntax error", attributes={"line": 10})

        # When
        result = renderer.render_error(node)

        # Then
        assert "[ERROR (Line 10): Syntax error]" in result
        assert "background-color:#ffe6e6" in result
        assert "color:#d32f2f" in result

    def test_render_error_no_line(self):
        """行番号なしエラーレンダリングテスト"""
        # Given
        renderer = ElementRenderer()
        node = Node(type="error", content="General error")

        # When
        result = renderer.render_error(node)

        # Then
        assert "[ERROR: General error]" in result

    def test_render_toc_placeholder(self):
        """目次プレースホルダーレンダリングテスト"""
        # Given
        renderer = ElementRenderer()
        node = Node(type="toc", content="")

        # When
        result = renderer.render_toc_placeholder(node)

        # Then
        assert result == "<!-- TOC placeholder -->"

    def test_render_heading_with_id(self):
        """ID付き見出しレンダリングテスト"""
        # Given
        renderer = ElementRenderer()
        node = Node(type="h1", content="Chapter 1", attributes={"id": "chapter-1"})

        # When
        result = renderer.render_heading(node, 1)

        # Then
        assert '<h1 id="chapter-1">Chapter 1</h1>' in result

    def test_render_heading_generate_id(self):
        """ID自動生成見出しレンダリングテスト"""
        # Given
        renderer = ElementRenderer()
        node = Node(type="h2", content="Section Title")

        # When
        result = renderer.render_heading(node, 2)

        # Then
        assert '<h2 id="heading-1">Section Title</h2>' in result
        assert renderer.heading_counter == 1
        assert node.get_attribute("id") == "heading-1"

    def test_render_heading_level_bounds(self):
        """見出しレベル境界テスト"""
        # Given
        renderer = ElementRenderer()
        node = Node(type="h7", content="Invalid level")

        # When - レベル7（無効）を渡す
        result = renderer.render_heading(node, 7)

        # Then - h6に制限される
        assert "<h6" in result
        assert "</h6>" in result

        # Given - レベル0（無効）
        result2 = renderer.render_heading(node, 0)

        # Then - h1に制限される
        assert "<h1" in result2
        assert "</h1>" in result2

    def test_render_unordered_list(self):
        """順序なしリストレンダリングテスト"""
        # Given
        renderer = ElementRenderer()
        list_items = [
            Node(type="li", content="Item 1"),
            Node(type="li", content="Item 2"),
        ]
        node = Node(type="ul", content=list_items)

        # When
        result = renderer.render_unordered_list(node)

        # Then
        assert "<ul>" in result
        assert "</ul>" in result

    def test_render_ordered_list(self):
        """順序付きリストレンダリングテスト"""
        # Given
        renderer = ElementRenderer()
        list_items = [
            Node(type="li", content="First"),
            Node(type="li", content="Second"),
        ]
        node = Node(type="ol", content=list_items, attributes={"start": "5"})

        # When
        result = renderer.render_ordered_list(node)

        # Then
        assert '<ol start="5">' in result
        assert "</ol>" in result

    def test_render_list_item(self):
        """リスト項目レンダリングテスト"""
        # Given
        renderer = ElementRenderer()
        node = Node(type="li", content="List item content")

        # When
        result = renderer.render_list_item(node)

        # Then
        assert result == "<li>List item content</li>"

    def test_render_div(self):
        """divレンダリングテスト"""
        # Given
        renderer = ElementRenderer()
        node = Node(
            type="div",
            content="Div content",
            attributes={"class": "container", "id": "main"},
        )

        # When
        result = renderer.render_div(node)

        # Then
        assert '<div class="container" id="main">' in result
        assert "Div content" in result
        assert "</div>" in result

    def test_render_details(self):
        """detailsレンダリングテスト"""
        # Given
        renderer = ElementRenderer()
        node = Node(
            type="details",
            content="Hidden content here",
            attributes={"summary": "Click to expand", "open": True},
        )

        # When
        result = renderer.render_details(node)

        # Then
        assert '<details open="True">' in result
        assert "<summary>Click to expand</summary>" in result
        assert "Hidden content here" in result
        assert "</details>" in result

    def test_render_details_default_summary(self):
        """デフォルトsummary付きdetailsレンダリングテスト"""
        # Given
        renderer = ElementRenderer()
        node = Node(type="details", content="Content")

        # When
        result = renderer.render_details(node)

        # Then
        assert "<summary>詳細</summary>" in result

    def test_render_summary(self):
        """summaryレンダリングテスト"""
        # Given
        renderer = ElementRenderer()
        node = Node(type="summary", content="Summary text")

        # When
        result = renderer.render_summary(node)

        # Then
        assert result == "<summary>Summary text</summary>"

    def test_render_element_type_dispatch(self):
        """要素タイプ別ディスパッチテスト"""
        # Given
        renderer = ElementRenderer()
        test_cases = [
            ("paragraph", "Test content", "<p>Test content</p>"),
            ("strong", "Bold", "<strong>Bold</strong>"),
            ("emphasis", "Italic", "<em>Italic</em>"),
            ("code", "code", "<code>code</code>"),
        ]

        # When/Then
        for element_type, content, expected in test_cases:
            node = Node(type=element_type, content=content)
            result = renderer.render_element(node)
            assert expected in result

    def test_render_element_heading_types(self):
        """見出し要素タイプテスト"""
        # Given
        renderer = ElementRenderer()

        # When/Then
        for level in range(1, 6):
            node = Node(type=f"heading{level}", content=f"Heading {level}")
            result = renderer.render_element(node)
            assert f"<h{level}" in result
            assert f"</h{level}>" in result

    def test_render_element_invalid_heading(self):
        """無効な見出し要素テスト"""
        # Given
        renderer = ElementRenderer()
        node = Node(type="headingXYZ", content="Invalid")

        # When
        result = renderer.render_element(node)

        # Then - デフォルトでh1として扱われる
        assert "<h1" in result

    def test_render_generic_fallback(self):
        """汎用レンダリングフォールバックテスト"""
        # Given
        renderer = ElementRenderer()
        node = Node(type="paragraph", content="Test")

        # When
        result = renderer.render_generic(node)

        # Then
        assert result == renderer.render_element(node)

    def test_render_unknown_element(self):
        """未知要素レンダリングテスト"""
        # Given
        renderer = ElementRenderer()
        node = Node(
            type="custom-element",
            content="Custom content",
            attributes={"data-value": "123"},
        )

        # When
        result = renderer.render_element(node)

        # Then
        assert "Custom content" in result

    def test_render_content_string(self):
        """文字列コンテンツレンダリングテスト"""
        # Given
        renderer = ElementRenderer()
        node = Node(type="p", content="Simple text")

        # When
        result = renderer._render_content("Simple text", 0)

        # Then
        assert "Simple text" in result

    def test_render_content_none(self):
        """Noneコンテンツレンダリングテスト"""
        # Given
        renderer = ElementRenderer()

        # When
        result = renderer._render_content(None, 0)

        # Then
        assert result == ""

    def test_render_content_node_without_main_renderer(self):
        """メインレンダラーなしNodeコンテンツレンダリングテスト"""
        # Given
        renderer = ElementRenderer()
        child_node = Node(type="span", content="child")

        # When
        result = renderer._render_content(child_node, 0)

        # Then
        assert result == "{NODE:span}"

    def test_render_content_list(self):
        """リストコンテンツレンダリングテスト"""
        # Given
        renderer = ElementRenderer()
        content_list = ["Text part ", Node(type="strong", content="bold"), " more text"]

        # When
        result = renderer._render_content(content_list, 0)

        # Then
        assert "Text part " in result
        assert "{NODE:strong}" in result
        assert " more text" in result

    def test_render_content_max_depth(self):
        """最大再帰深度テスト"""
        # Given
        renderer = ElementRenderer()

        # When - 最大深度を超える
        result = renderer._render_content("test", 101)

        # Then
        assert result == "[ERROR: Maximum recursion depth reached]"

    def test_render_content_with_main_renderer(self):
        """メインレンダラー付きコンテンツレンダリングテスト"""
        # Given
        renderer = ElementRenderer()
        main_renderer_mock = Mock()
        main_renderer_mock._render_node_with_depth.return_value = "<span>mocked</span>"
        renderer.set_main_renderer(main_renderer_mock)

        child_node = Node(type="span", content="child")

        # When
        result = renderer._render_content(child_node, 0)

        # Then
        assert result == "<span>mocked</span>"
        main_renderer_mock._render_node_with_depth.assert_called_once_with(
            child_node, 1
        )

    def test_html_escaping_in_content(self):
        """HTMLエスケープテスト"""
        # Given
        renderer = ElementRenderer()
        node = Node(type="p", content="<script>alert('XSS')</script>")

        # When
        result = renderer.render_paragraph(node)

        # Then
        assert "&lt;script&gt;" in result
        assert "&lt;/script&gt;" in result
        assert "<script>" not in result

    def test_attribute_rendering(self):
        """属性レンダリングテスト"""
        # Given
        renderer = ElementRenderer()
        node = Node(
            type="div",
            content="Content",
            attributes={"class": "test-class", "id": "test-id", "data-value": "123"},
        )

        # When
        result = renderer.render_div(node)

        # Then
        assert 'class="test-class"' in result
        assert 'id="test-id"' in result
        assert 'data-value="123"' in result

    def test_xss_prevention_attributes(self):
        """属性でのXSS防止テスト"""
        # Given
        renderer = ElementRenderer()
        node = Node(
            type="div",
            content="Safe content",
            attributes={
                "onclick": "alert('XSS')",
                "title": '<script>alert("XSS")</script>',
            },
        )

        # When
        result = renderer.render_div(node)

        # Then
        assert "&quot;" in result  # クォートがエスケープされている
        assert "&lt;script&gt;" in result  # スクリプトタグがエスケープされている
        assert "<script>" not in result

    def test_performance_large_content(self):
        """大量コンテンツのパフォーマンステスト"""
        # Given
        renderer = ElementRenderer()
        large_content = "x" * 10000  # 10KB
        node = Node(type="p", content=large_content)

        # When
        import time

        start_time = time.time()
        result = renderer.render_paragraph(node)
        elapsed_time = time.time() - start_time

        # Then
        assert len(result) > 10000
        assert elapsed_time < 1.0  # 1秒以内

    def test_memory_efficiency(self):
        """メモリ効率テスト"""
        # Given
        renderer = ElementRenderer()
        nodes = [Node(type="p", content=f"Paragraph {i}") for i in range(100)]

        # When
        results = []
        for node in nodes:
            result = renderer.render_paragraph(node)
            results.append(result)

        # Then
        assert len(results) == 100
        assert all("Paragraph" in r for r in results)

    def test_unicode_support(self):
        """Unicode文字サポートテスト"""
        # Given
        renderer = ElementRenderer()
        unicode_texts = ["日本語テキスト", "Русский текст", "🎉 Emoji 🚀", "العربية"]

        # When/Then
        for text in unicode_texts:
            node = Node(type="p", content=text)
            result = renderer.render_paragraph(node)
            assert text in result

    def test_backward_compatibility_aliases(self):
        """後方互換性エイリアステスト"""
        # Given/When/Then
        from kumihan_formatter.core.rendering.element_renderer import (
            BasicElementRenderer,
            DivRenderer,
            HeadingRenderer,
            ListRenderer,
        )

        # 全て同じElementRendererクラスを指している
        assert BasicElementRenderer == ElementRenderer
        assert HeadingRenderer == ElementRenderer
        assert ListRenderer == ElementRenderer
        assert DivRenderer == ElementRenderer
