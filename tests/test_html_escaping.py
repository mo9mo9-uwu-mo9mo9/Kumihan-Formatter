"""
HTML Escaping セキュリティテストスイート

Issue #594 Phase 2-2対応 - レンダリング機能安定化
HTMLセキュリティ、XSS防止、エスケープ処理の体系的テスト
"""

import pytest

from kumihan_formatter.core.rendering.html_escaping import (
    contains_html_tags,
    escape_html,
    render_attributes,
)


class TestHTMLEscaping:
    """HTMLエスケープ機能のセキュリティテストクラス"""

    def test_escape_html_basic_characters(self):
        """基本的なHTML特殊文字のエスケープテスト"""
        # Given
        test_cases = [
            ("Hello World", "Hello World"),
            ("<script>", "&lt;script&gt;"),
            ("&", "&amp;"),
            ('"', "&quot;"),
            ("'", "&#x27;"),
            ("A & B", "A &amp; B"),
            ("<>", "&lt;&gt;"),
        ]

        # When/Then
        for input_text, expected_output in test_cases:
            result = escape_html(input_text)
            assert result == expected_output

    def test_escape_html_xss_prevention(self):
        """XSS攻撃防止テスト"""
        # Given
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<iframe src='data:text/html,<script>alert(1)</script>'></iframe>",
            "<svg onload=alert('XSS')>",
            "<input onfocus=alert('XSS') autofocus>",
            "<select onfocus=alert('XSS') autofocus>",
            "<textarea onfocus=alert('XSS') autofocus>",
            "<keygen onfocus=alert('XSS') autofocus>",
            "<video><source onerror='alert(1)'>",
            "<audio src=x onerror=alert('XSS')>",
            "<object data='data:text/html,<script>alert(1)</script>'>",
            "<embed src='data:text/html,<script>alert(1)</script>'>",
            "<details open ontoggle=alert('XSS')>",
            "<summary>Click me<style>*{color:red}</style></summary>",
        ]

        # When/Then
        for payload in xss_payloads:
            result = escape_html(payload)

            # 危険なタグがエスケープされていることを確認
            assert "<script>" not in result
            assert "<iframe" not in result
            assert "<svg" not in result
            assert "<object" not in result
            assert "<embed" not in result

            # イベントハンドラーが実行可能な形で残っていないことを確認
            # エスケープされても文字列として残る場合があるが、実行はされない
            assert "<img src=x onerror=" not in result  # 実行可能な形ではない
            assert "<svg onload=" not in result
            assert "<input onfocus=" not in result

            # javascriptプロトコルが無効化されていることを確認
            assert "javascript:" not in result or "&" in result

    def test_escape_html_unicode_characters(self):
        """Unicode文字のエスケープテスト"""
        # Given
        unicode_texts = [
            "日本語テキスト",
            "中文文本",
            "العربية",
            "Русский текст",
            "🎉 Emoji 🚀",
            "数学記号: ∑∆∞",
            "特殊文字: ©®™",
        ]

        # When/Then
        for text in unicode_texts:
            result = escape_html(text)
            # Unicode文字は保持される（エスケープされない）
            assert result == text

    def test_escape_html_mixed_content(self):
        """混合コンテンツのエスケープテスト"""
        # Given
        mixed_content = 'Normal text <script>alert("XSS")</script> 日本語 & more'

        # When
        result = escape_html(mixed_content)

        # Then
        assert "&lt;script&gt;" in result
        assert "&quot;XSS&quot;" in result
        assert "日本語" in result
        assert "&amp;" in result
        assert "<script>" not in result

    def test_escape_html_empty_and_none(self):
        """空文字列とNone値のテスト"""
        # Given/When/Then
        assert escape_html("") == ""

        # Noneは渡されない想定だが、str変換でカバー
        with pytest.raises(AttributeError):
            escape_html(None)

    def test_render_attributes_basic(self):
        """基本的な属性レンダリングテスト"""
        # Given
        attributes = {"class": "highlight", "id": "main-content", "data-value": "123"}

        # When
        result = render_attributes(attributes)

        # Then
        assert 'class="highlight"' in result
        assert 'id="main-content"' in result
        assert 'data-value="123"' in result

    def test_render_attributes_empty_or_none(self):
        """空またはNone属性のテスト"""
        # Given/When/Then
        assert render_attributes(None) == ""
        assert render_attributes({}) == ""

    def test_render_attributes_xss_prevention(self):
        """属性値でのXSS防止テスト"""
        # Given
        malicious_attributes = {
            "onclick": "alert('XSS')",
            "src": "javascript:alert('XSS')",
            "style": "background:url('javascript:alert(1)')",
            "href": "javascript:void(0)",
            "title": '<script>alert("XSS")</script>',
        }

        # When
        result = render_attributes(malicious_attributes)

        # Then
        # イベントハンドラーがエスケープされることを確認
        assert 'onclick="alert' in result and "&" in result
        assert "javascript:alert" in result and "&" in result
        assert "&lt;script&gt;" in result
        assert "<script>" not in result

    def test_render_attributes_special_values(self):
        """特殊値の属性レンダリングテスト"""
        # Given
        attributes = {
            "data-number": 42,
            "data-float": 3.14,
            "data-bool": True,
            "data-none": None,  # None値は除外される
            "data-empty": "",
            "data-quotes": 'He said "Hello"',
        }

        # When
        result = render_attributes(attributes)

        # Then
        assert 'data-number="42"' in result
        assert 'data-float="3.14"' in result
        assert 'data-bool="True"' in result
        assert "data-none=" not in result  # None値は除外
        assert 'data-empty=""' in result
        assert 'data-quotes="He said &quot;Hello&quot;"' in result

    def test_render_attributes_order_consistency(self):
        """属性順序の一貫性テスト"""
        # Given
        attributes = {"z": "last", "a": "first", "m": "middle"}

        # When
        result1 = render_attributes(attributes)
        result2 = render_attributes(attributes)

        # Then
        # 順序は辞書の順序に依存するが、結果は一貫している
        assert result1 == result2
        assert len(result1.split()) == 3  # 3つの属性

    def test_contains_html_tags_detection(self):
        """HTMLタグ検出テスト"""
        # Given
        test_cases = [
            # (入力, 期待値)
            ("Normal text", False),
            ("<p>Paragraph</p>", True),
            ("<script>alert('XSS')</script>", True),
            ("<img src='test.jpg'>", True),
            (
                "Text with < and > symbols",
                True,
            ),  # < と > の間に文字があるとタグとして検出される
            ("<", False),  # 不完全なタグ
            (">", False),  # 不完全なタグ
            ("<>", False),  # 空のタグ（<[^>]+>なので+により1文字以上必要）
            ("<<script>", True),  # 複数の<
            ("<p><strong>Bold</strong></p>", True),  # ネストされたタグ
            ("<!-- Comment -->", True),  # コメント
            ("<br/>", True),  # 自己完結タグ
            ('<input type="text">', True),  # 属性付きタグ
        ]

        # When/Then
        for text, expected in test_cases:
            result = contains_html_tags(text)
            assert result == expected, f"Failed for: {text}"

    def test_contains_html_tags_edge_cases(self):
        """HTMLタグ検出エッジケーステスト"""
        # Given
        edge_cases = [
            "",  # 空文字列
            "   ",  # 空白のみ
            "Math: 2 &lt; 3 &gt; 1",  # 数学記号（エスケープ済み）
            "Email: user@domain.com",  # @記号
            "Angle brackets in <quotes>",  # クォート内
            "Multiple < symbols < here",  # 複数の<
            "HTML entities: &lt;p&gt;",  # HTMLエンティティ
        ]

        # When/Then
        safe_cases = edge_cases[:2] + edge_cases[3:4]  # 空文字列、空白、@記号
        for text in safe_cases:
            result = contains_html_tags(text)
            assert result is False, f"Should be False for: {text}"

        # HTMLエンティティは検出されない（適切な動作）
        assert not contains_html_tags("HTML entities: &lt;p&gt;")
        assert not contains_html_tags("Math: 2 &lt; 3 &gt; 1")

        # 以下は実際にタグパターンとして検出される
        assert contains_html_tags(
            "Angle brackets in <quotes>"
        )  # <quotes>がタグとして検出
        # "Multiple < symbols < here" は実際にはFalseになる（< と > の間に適切な文字がない）
        assert not contains_html_tags("Multiple < symbols < here")

    def test_html_security_integration(self):
        """HTML セキュリティ統合テスト"""
        # Given
        malicious_input = '<script>alert("XSS")</script>'
        malicious_attributes = {"onclick": 'alert("XSS")', "class": "safe-class"}

        # When
        escaped_content = escape_html(malicious_input)
        rendered_attrs = render_attributes(malicious_attributes)
        has_tags = contains_html_tags(malicious_input)

        # Then
        # コンテンツがエスケープされている
        assert "&lt;script&gt;" in escaped_content
        assert "<script>" not in escaped_content

        # 属性がエスケープされている
        assert "&quot;XSS&quot;" in rendered_attrs
        assert 'class="safe-class"' in rendered_attrs

        # タグが検出されている
        assert has_tags is True

    def test_performance_large_content(self):
        """大量コンテンツのパフォーマンステスト"""
        # Given
        large_content = "Normal text " * 10000 + "<script>alert('XSS')</script>"
        large_attributes = {f"data-{i}": f"value-{i}" for i in range(100)}

        # When
        import time

        start_time = time.time()
        escaped = escape_html(large_content)
        escape_time = time.time() - start_time

        start_time = time.time()
        attrs = render_attributes(large_attributes)
        attr_time = time.time() - start_time

        start_time = time.time()
        has_tags = contains_html_tags(large_content)
        detection_time = time.time() - start_time

        # Then
        # パフォーマンス要件（通常の処理時間内）
        assert escape_time < 1.0  # 1秒以内
        assert attr_time < 1.0  # 1秒以内
        assert detection_time < 1.0  # 1秒以内

        # 結果の正確性
        assert "&lt;script&gt;" in escaped
        assert len(attrs.split()) == 100  # 100個の属性
        assert has_tags is True

    def test_memory_safety(self):
        """メモリ安全性テスト"""
        # Given
        inputs = [
            "x" * 1000000,  # 1MB文字列
            "<" * 100000,  # 大量の<文字
            "&" * 100000,  # 大量の&文字
        ]

        # When/Then
        for test_input in inputs:
            # メモリリークやクラッシュが発生しないことを確認
            result = escape_html(test_input)
            assert len(result) >= len(test_input)  # エスケープ後は長くなる可能性

    def test_regex_security(self):
        """正規表現セキュリティテスト（ReDoS防止）"""
        # Given
        # ReDoS（Regular Expression Denial of Service）攻撃パターン
        redos_patterns = [
            "<" + "a" * 100000 + ">",  # 長いタグ名
            "<" + "x" * 50000,  # 閉じられていない長いタグ
            ">" * 100000,  # 大量の>文字
        ]

        # When/Then
        import time

        for pattern in redos_patterns:
            start_time = time.time()
            result = contains_html_tags(pattern)
            execution_time = time.time() - start_time

            # 1秒以内に処理が完了すること（ReDoS防止）
            assert (
                execution_time < 1.0
            ), f"ReDoS detected with pattern length: {len(pattern)}"
            # 結果の正確性も確認
            assert isinstance(result, bool)
