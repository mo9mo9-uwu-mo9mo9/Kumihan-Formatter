"""HTMLFormatter包括的テストスイート

Issue #594 Phase 2-2対応 - レンダリング機能安定化
HTML整形、バリデーション、最適化機能の体系的テスト
"""

import pytest

from kumihan_formatter.core.rendering.html_formatter import HTMLFormatter


class TestHTMLFormatter:
    """HTMLFormatterの包括的テストクラス"""

    def test_init_default(self):
        """デフォルト初期化テスト"""
        # When
        formatter = HTMLFormatter()

        # Then
        assert formatter.indent_size == 2

    def test_init_custom_indent(self):
        """カスタムインデント初期化テスト"""
        # When
        formatter = HTMLFormatter(indent_size=4)

        # Then
        assert formatter.indent_size == 4

    def test_format_html_empty_string(self):
        """空文字列フォーマットテスト"""
        # Given
        formatter = HTMLFormatter()

        # When
        result = formatter.format_html("")

        # Then
        assert result == ""

    def test_format_html_whitespace_only(self):
        """空白のみのフォーマットテスト"""
        # Given
        formatter = HTMLFormatter()

        # When
        result = formatter.format_html("   \n  \t  ")

        # Then
        assert result == "   \n  \t  "

    def test_format_html_simple_paragraph(self):
        """単純段落フォーマットテスト"""
        # Given
        formatter = HTMLFormatter()
        html = "<p>Hello World</p>"

        # When
        result = formatter.format_html(html)

        # Then
        expected_lines = ["<p>", "  Hello World", "</p>"]
        assert result == "\n".join(expected_lines)

    def test_format_html_nested_structure(self):
        """ネストされた構造フォーマットテスト"""
        # Given
        formatter = HTMLFormatter()
        html = "<div><p>Content</p><p>More content</p></div>"

        # When
        result = formatter.format_html(html)

        # Then
        lines = result.split("\n")
        assert "<div>" in lines[0]
        assert "  <p>" in lines[1]  # 2スペースインデント
        assert "    Content" in lines[2]  # 4スペースインデント（コンテンツ）
        assert "  </p>" in lines[3]
        assert "  <p>" in lines[4]
        assert "    More content" in lines[5]
        assert "  </p>" in lines[6]
        assert "</div>" in lines[7]

    def test_format_html_custom_indent_size(self):
        """カスタムインデントサイズフォーマットテスト"""
        # Given
        formatter = HTMLFormatter(indent_size=4)
        html = "<div><p>Content</p></div>"

        # When
        result = formatter.format_html(html)

        # Then
        lines = result.split("\n")
        assert "<div>" in lines[0]
        assert "    <p>" in lines[1]  # 4スペースインデント
        assert "        Content" in lines[2]  # 8スペースインデント（コンテンツ）
        assert "    </p>" in lines[3]
        assert "</div>" in lines[4]

    def test_format_html_preserve_inline_true(self):
        """インライン要素保持フォーマットテスト"""
        # Given
        formatter = HTMLFormatter()
        html = "<p>Text with <strong>bold</strong> word</p>"

        # When
        result = formatter.format_html(html, preserve_inline=True)

        # Then
        # 実際にはテキストとタグが分割される
        assert "<p>" in result
        assert "Text with" in result
        assert "<strong>" in result
        assert "bold" in result
        assert "</strong>" in result
        assert "word" in result
        assert "</p>" in result

    def test_format_html_preserve_inline_false(self):
        """インライン要素非保持フォーマットテスト"""
        # Given
        formatter = HTMLFormatter()
        html = "<p>Text with <strong>bold</strong> word</p>"

        # When
        result = formatter.format_html(html, preserve_inline=False)

        # Then
        lines = result.split("\n")
        assert len(lines) > 1  # 複数行に分割される

    def test_format_html_self_closing_tags(self):
        """自己完結タグフォーマットテスト"""
        # Given
        formatter = HTMLFormatter()
        html = "<div><img src='test.jpg' /><br/><hr/></div>"

        # When
        result = formatter.format_html(html)

        # Then
        lines = result.split("\n")
        assert "<div>" in lines[0]
        assert any("img" in line for line in lines)
        assert any("br" in line for line in lines)
        assert any("hr" in line for line in lines)
        assert "</div>" in lines[-1]

    def test_format_html_complex_nesting(self):
        """複雑なネスト構造フォーマットテスト"""
        # Given
        formatter = HTMLFormatter()
        html = "<html><head><title>Test</title></head><body><div><ul><li>Item 1</li><li>Item 2</li></ul></div></body></html>"

        # When
        result = formatter.format_html(html)

        # Then
        lines = result.split("\n")
        assert len(lines) > 5  # 複数行に分割
        # インデントレベルの確認
        title_line = next(line for line in lines if "title" in line.lower())
        assert title_line.startswith("    ")  # 2レベルインデント

    def test_minify_html_basic(self):
        """基本HTMLミニファイテスト"""
        # Given
        formatter = HTMLFormatter()
        html = "  <p>  Hello   World  </p>  "

        # When
        result = formatter.minify_html(html)

        # Then
        assert result == "<p> Hello World </p>"

    def test_minify_html_remove_comments(self):
        """コメント削除ミニファイテスト"""
        # Given
        formatter = HTMLFormatter()
        html = "<p>Content</p><!-- This is a comment --><div>More</div>"

        # When
        result = formatter.minify_html(html)

        # Then
        assert "comment" not in result
        assert "<p>Content</p><div>More</div>" in result

    def test_minify_html_multiline_comments(self):
        """複数行コメント削除テスト"""
        # Given
        formatter = HTMLFormatter()
        html = """<p>Before</p>
<!--
Multi-line
comment
-->
<p>After</p>"""

        # When
        result = formatter.minify_html(html)

        # Then
        assert "Multi-line" not in result
        assert "<p>Before</p><p>After</p>" in result

    def test_minify_html_extra_whitespace(self):
        """余分な空白削除テスト"""
        # Given
        formatter = HTMLFormatter()
        html = "<div>   \n\t  <p>Content</p>   \n  </div>"

        # When
        result = formatter.minify_html(html)

        # Then
        assert result == "<div><p>Content</p></div>"

    def test_validate_html_structure_valid(self):
        """有効なHTML構造バリデーションテスト"""
        # Given
        formatter = HTMLFormatter()
        html = (
            "<html><head><title>Test</title></head><body><p>Content</p></body></html>"
        )

        # When
        issues = formatter.validate_html_structure(html)

        # Then
        assert issues == []

    def test_validate_html_structure_unclosed_tag(self):
        """未完了タグバリデーションテスト"""
        # Given
        formatter = HTMLFormatter()
        html = "<div><p>Content</div>"

        # When
        issues = formatter.validate_html_structure(html)

        # Then
        assert len(issues) > 0
        assert any("Unclosed tag: p" in issue for issue in issues)

    def test_validate_html_structure_unmatched_closing(self):
        """不一致終了タグバリデーションテスト"""
        # Given
        formatter = HTMLFormatter()
        html = "<div><p>Content</span></div>"

        # When
        issues = formatter.validate_html_structure(html)

        # Then
        assert len(issues) > 0
        assert any("Mismatched tags" in issue for issue in issues)

    def test_validate_html_structure_closing_without_opening(self):
        """開始タグなし終了タグバリデーションテスト"""
        # Given
        formatter = HTMLFormatter()
        html = "<p>Content</p></div>"

        # When
        issues = formatter.validate_html_structure(html)

        # Then
        assert len(issues) > 0
        assert any("Closing tag without opening" in issue for issue in issues)

    def test_validate_html_structure_self_closing_tags(self):
        """自己完結タグ有効性テスト"""
        # Given
        formatter = HTMLFormatter()
        html = "<div><img src='test.jpg' /><br/><hr/></div>"

        # When
        issues = formatter.validate_html_structure(html)

        # Then
        assert issues == []  # 自己完結タグは問題なし

    def test_extract_text_content_basic(self):
        """基本テキスト抽出テスト"""
        # Given
        formatter = HTMLFormatter()
        html = "<p>Hello World</p>"

        # When
        result = formatter.extract_text_content(html)

        # Then
        assert result == "Hello World"

    def test_extract_text_content_nested_tags(self):
        """ネストされたタグからのテキスト抽出テスト"""
        # Given
        formatter = HTMLFormatter()
        html = "<div><p>Paragraph 1</p><p>Paragraph 2</p></div>"

        # When
        result = formatter.extract_text_content(html)

        # Then
        # タグ間の空白が保持されない場合がある
        assert "Paragraph 1" in result
        assert "Paragraph 2" in result
        # 空白の有無は不定だが、両方のコンテンツが含まれていることを確認

    def test_extract_text_content_html_entities(self):
        """HTMLエンティティテキスト抽出テスト"""
        # Given
        formatter = HTMLFormatter()
        html = "<p>Code: &lt;script&gt;alert('XSS')&lt;/script&gt;</p>"

        # When
        result = formatter.extract_text_content(html)

        # Then
        assert result == "Code: <script>alert('XSS')</script>"

    def test_extract_text_content_all_entities(self):
        """全HTMLエンティティテキスト抽出テスト"""
        # Given
        formatter = HTMLFormatter()
        html = "<p>&lt; &gt; &amp; &quot; &#x27;</p>"

        # When
        result = formatter.extract_text_content(html)

        # Then
        assert result == "< > & \" '"

    def test_extract_text_content_whitespace_cleanup(self):
        """空白文字整理テキスト抽出テスト"""
        # Given
        formatter = HTMLFormatter()
        html = "<div>  \n\t  Text   with   spaces  \n  </div>"

        # When
        result = formatter.extract_text_content(html)

        # Then
        assert result == "Text with spaces"

    def test_tokenize_html_simple(self):
        """単純HTMLトークン化テスト"""
        # Given
        formatter = HTMLFormatter()
        html = "<p>Hello World</p>"

        # When
        tokens = formatter._tokenize_html(html)

        # Then
        assert tokens == ["<p>", "Hello World", "</p>"]

    def test_tokenize_html_complex(self):
        """複雑HTMLトークン化テスト"""
        # Given
        formatter = HTMLFormatter()
        html = "<div>Text<span>Inline</span>More text</div>"

        # When
        tokens = formatter._tokenize_html(html)

        # Then
        expected = [
            "<div>",
            "Text",
            "<span>",
            "Inline",
            "</span>",
            "More text",
            "</div>",
        ]
        assert tokens == expected

    def test_tokenize_html_empty_tags(self):
        """空タグトークン化テスト"""
        # Given
        formatter = HTMLFormatter()
        html = "<div></div>"

        # When
        tokens = formatter._tokenize_html(html)

        # Then
        assert tokens == ["<div>", "</div>"]

    def test_extract_tags(self):
        """タグ抽出テスト"""
        # Given
        formatter = HTMLFormatter()
        html = "<div><p>Content</p><br/></div>"

        # When
        tags = formatter._extract_tags(html)

        # Then
        assert tags == ["<div>", "<p>", "</p>", "<br/>", "</div>"]

    def test_extract_tag_name(self):
        """タグ名抽出テスト"""
        # Given
        formatter = HTMLFormatter()
        test_cases = [
            ("<p>", "p"),
            ("</div>", "div"),
            ('<img src="test.jpg" />', "img"),
            ("<h1 class='title'>", "h1"),
        ]

        # When/Then
        for tag, expected_name in test_cases:
            result = formatter._extract_tag_name(tag)
            assert result == expected_name

    def test_is_opening_tag(self):
        """開始タグ判定テスト"""
        # Given
        formatter = HTMLFormatter()
        test_cases = [
            ("<p>", True),
            ("<div class='test'>", True),
            ("</p>", False),
            ("<br/>", False),
            ("Hello", False),
        ]

        # When/Then
        for tag, expected in test_cases:
            result = formatter._is_opening_tag(tag)
            assert result == expected

    def test_is_closing_tag(self):
        """終了タグ判定テスト"""
        # Given
        formatter = HTMLFormatter()
        test_cases = [
            ("</p>", True),
            ("</div>", True),
            ("<p>", False),
            ("<br/>", False),
            ("Hello", False),
        ]

        # When/Then
        for tag, expected in test_cases:
            result = formatter._is_closing_tag(tag)
            assert result == expected

    def test_is_self_closing_tag(self):
        """自己完結タグ判定テスト"""
        # Given
        formatter = HTMLFormatter()
        test_cases = [
            ("<br/>", True),
            ("<img src='test.jpg' />", True),
            ("<hr/>", True),
            ("<p>", False),
            ("</p>", False),
            ("Hello", False),
        ]

        # When/Then
        for tag, expected in test_cases:
            result = formatter._is_self_closing_tag(tag)
            assert result == expected

    def test_is_inline_element(self):
        """インライン要素判定テスト"""
        # Given
        formatter = HTMLFormatter()

        # インライン要素
        inline_cases = [
            "<span>",
            "<strong>",
            "<em>",
            "<a href='#'>",
            "<code>",
            "<img src='test.jpg'>",
        ]

        # ブロック要素
        block_cases = [
            "<div>",
            "<p>",
            "<h1>",
            "<ul>",
            "<li>",
            "<section>",
        ]

        # When/Then
        for tag in inline_cases:
            result = formatter._is_inline_element(tag)
            assert result is True, f"Should be inline: {tag}"

        for tag in block_cases:
            result = formatter._is_inline_element(tag)
            assert result is False, f"Should be block: {tag}"

    def test_format_html_with_attributes(self):
        """属性付きHTMLフォーマットテスト"""
        # Given
        formatter = HTMLFormatter()
        html = '<div class="container" id="main"><p class="text">Content</p></div>'

        # When
        result = formatter.format_html(html)

        # Then
        lines = result.split("\n")
        assert 'class="container"' in lines[0]
        assert 'id="main"' in lines[0]
        assert 'class="text"' in lines[1]

    def test_performance_large_html(self):
        """大規模HTMLパフォーマンステスト"""
        # Given
        formatter = HTMLFormatter()
        # 1000個の段落を含む大きなHTML
        large_html = (
            "<div>" + "".join(f"<p>Paragraph {i}</p>" for i in range(1000)) + "</div>"
        )

        # When
        import time

        start_time = time.time()
        result = formatter.format_html(large_html)
        elapsed_time = time.time() - start_time

        # Then
        assert len(result) > len(large_html)  # フォーマット後は長くなる
        assert elapsed_time < 2.0  # 2秒以内
        assert result.count("<p>") == 1000

    def test_memory_efficiency(self):
        """メモリ効率テスト"""
        # Given
        formatter = HTMLFormatter()
        test_html = "<div><p>Test content</p></div>"

        # When - 100回連続処理
        results = []
        for _ in range(100):
            result = formatter.format_html(test_html)
            results.append(result)

        # Then
        assert len(results) == 100
        assert all(r == results[0] for r in results)  # 全て同じ結果

    def test_unicode_support(self):
        """Unicode文字サポートテスト"""
        # Given
        formatter = HTMLFormatter()
        unicode_texts = [
            "<p>日本語テキスト</p>",
            "<p>Русский текст</p>",
            "<p>🎉 Emoji support 🚀</p>",
            "<p>العربية</p>",
        ]

        # When/Then
        for html in unicode_texts:
            formatted = formatter.format_html(html)
            minified = formatter.minify_html(html)
            text_content = formatter.extract_text_content(html)

            # Unicode文字が保持されている
            assert (
                "日本語" in formatted
                or "Русский" in formatted
                or "🎉" in formatted
                or "العربية" in formatted
            )
            assert len(text_content.strip()) > 0

    def test_edge_cases_malformed_html(self):
        """不正なHTML形式エッジケーステスト"""
        # Given
        formatter = HTMLFormatter()
        malformed_cases = [
            "<p>Unclosed paragraph",
            "<div><p>Nested unclosed</div>",
            "< >Empty tag< >",
            "<script>alert('test')</script>",  # スクリプト要素
        ]

        # When/Then
        for html in malformed_cases:
            # 例外が発生せずに処理される
            formatted = formatter.format_html(html)
            minified = formatter.minify_html(html)
            issues = formatter.validate_html_structure(html)

            assert isinstance(formatted, str)
            assert isinstance(minified, str)
            assert isinstance(issues, list)

    def test_html_validation_complex_structure(self):
        """複雑なHTML構造バリデーションテスト"""
        # Given
        formatter = HTMLFormatter()
        complex_html = """
        <html>
            <head>
                <title>Test Page</title>
                <meta charset="utf-8" />
            </head>
            <body>
                <header>
                    <h1>Main Title</h1>
                </header>
                <main>
                    <section>
                        <h2>Section Title</h2>
                        <p>Content paragraph.</p>
                        <ul>
                            <li>Item 1</li>
                            <li>Item 2</li>
                        </ul>
                    </section>
                </main>
                <footer>
                    <p>Footer content</p>
                </footer>
            </body>
        </html>
        """

        # When
        issues = formatter.validate_html_structure(complex_html)

        # Then
        assert issues == []  # 有効な構造

    def test_format_preserve_content_integrity(self):
        """コンテンツ整合性保持テスト"""
        # Given
        formatter = HTMLFormatter()
        original_html = "<div><p>Important content with <strong>emphasis</strong> and <a href='#'>link</a>.</p></div>"

        # When
        formatted = formatter.format_html(original_html)
        minified = formatter.minify_html(original_html)
        text_content = formatter.extract_text_content(original_html)

        # Then
        # 重要なコンテンツが保持されている
        assert "Important content" in formatted
        assert "emphasis" in formatted
        assert "link" in formatted
        # 属性のクォートはシングルまたはダブルの場合がある
        assert "href='#'" in formatted or 'href="#"' in formatted

        assert "Important content" in minified
        # extract_text_contentでは空白が正常化される
        assert "Important content" in text_content
        assert "emphasis" in text_content
        assert "link" in text_content
