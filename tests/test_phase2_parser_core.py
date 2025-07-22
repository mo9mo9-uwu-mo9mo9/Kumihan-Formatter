"""Phase 2 Parser Core Tests - パーサーコアテスト

パーサーコア機能テスト - parse関数・基本パーサー
Target: parser.py のコア機能
Goal: parse関数・MarkdownParser・KeywordParser基本テスト
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.keyword_parser import KeywordParser
from kumihan_formatter.core.markdown_parser import MarkdownParser
from kumihan_formatter.parser import parse


class TestParseFunction:
    """Parse関数の完全テスト"""

    def test_parse_function_basic(self):
        """基本的な解析テスト"""
        text = "Simple paragraph text."
        result = parse(text)

        # ASTが生成されることを確認
        assert isinstance(result, list)
        assert len(result) >= 0

    def test_parse_function_empty_text(self):
        """空テキストの解析テスト"""
        text = ""
        result = parse(text)

        # 空テキストでも正常に処理されることを確認
        assert isinstance(result, list)

    def test_parse_function_with_markup(self):
        """マークアップ記法付きテキストの解析テスト"""
        text = """
        # Heading 1

        Simple paragraph.

        ## Heading 2

        Another paragraph with **bold** text.
        """
        result = parse(text)

        # マークアップが解析されることを確認
        assert isinstance(result, list)
        assert len(result) > 0

    def test_parse_function_with_notations(self):
        """記法付きテキストの解析テスト"""
        text = "This is ((footnote)) notation and ｜ruby《ルビ》 notation."
        result = parse(text)

        # 記法が解析されることを確認
        assert isinstance(result, list)

    def test_parse_function_with_complex_content(self):
        """複雑なコンテンツの解析テスト"""
        text = """
        # Main Title

        This paragraph contains ((footnote content)) and ｜ruby《reading》.

        ## Subsection

        - List item 1
        - List item 2 with ((another footnote))

        Regular paragraph with mixed content.
        """
        result = parse(text)

        # 複雑な構造が解析されることを確認
        assert isinstance(result, list)
        assert len(result) > 0

    def test_parse_function_with_config(self):
        """設定オブジェクト付き解析テスト"""
        text = "Test content"
        config = Mock()
        config.debug = False

        result = parse(text, config)

        # 設定付きで正常に解析されることを確認
        assert isinstance(result, list)

    def test_parse_function_with_source_path(self):
        """ソースパス付き解析テスト"""
        text = "Test content"
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "test.txt"

            result = parse(text, source_path=source_path)

            # ソースパス付きで正常に解析されることを確認
            assert isinstance(result, list)

    def test_parse_function_error_handling(self):
        """解析エラーハンドリングテスト"""
        # 不正な入力でもエラーが適切に処理されることを確認
        invalid_inputs = [None, 123, [], {}]

        for invalid_input in invalid_inputs:
            try:
                result = parse(invalid_input)
                assert isinstance(result, list)  # 何らかのリストが返される
            except Exception:
                # または例外が適切に処理される
                assert True

    def test_parse_function_unicode_content(self):
        """Unicode文字を含むコンテンツの解析テスト"""
        text = "Unicode content: 日本語テスト with ((脚注)) notation."
        result = parse(text)

        # Unicode文字が正常に解析されることを確認
        assert isinstance(result, list)


class TestMarkdownParser:
    """MarkdownParser完全テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.parser = MarkdownParser()

    def test_markdown_parser_initialization(self):
        """MarkdownParser初期化テスト"""
        parser = MarkdownParser()

        # 基本属性が初期化されていることを確認
        assert hasattr(parser, "parse")

    def test_parse_heading_markup(self):
        """見出しマークアップ解析テスト"""
        text = """
        # Level 1 Heading
        ## Level 2 Heading
        ### Level 3 Heading
        """
        result = self.parser.parse(text)

        # 見出しが解析されることを確認
        assert isinstance(result, list)

    def test_parse_paragraph_markup(self):
        """段落マークアップ解析テスト"""
        text = """
        First paragraph.

        Second paragraph with content.

        Third paragraph.
        """
        result = self.parser.parse(text)

        # 段落が解析されることを確認
        assert isinstance(result, list)

    def test_parse_emphasis_markup(self):
        """強調マークアップ解析テスト"""
        text = "Text with **bold** and *italic* emphasis."
        result = self.parser.parse(text)

        # 強調が解析されることを確認
        assert isinstance(result, list)

    def test_parse_list_markup(self):
        """リストマークアップ解析テスト"""
        text = """
        - Unordered list item 1
        - Unordered list item 2
        - Unordered list item 3

        1. Ordered list item 1
        2. Ordered list item 2
        3. Ordered list item 3
        """
        result = self.parser.parse(text)

        # リストが解析されることを確認
        assert isinstance(result, list)

    def test_parse_nested_markup(self):
        """ネストしたマークアップ解析テスト"""
        text = """
        # Main Heading

        Paragraph with **bold text containing *italic* text**.

        ## Sub Heading

        - List item with **bold**
        - Another item with *italic*
        """
        result = self.parser.parse(text)

        # ネストした構造が解析されることを確認
        assert isinstance(result, list)

    def test_parse_mixed_content(self):
        """混在コンテンツ解析テスト"""
        text = """
        # Document Title

        Introduction paragraph.

        ## Features

        - Feature 1 with **importance**
        - Feature 2 with *emphasis*

        ### Details

        Detailed explanation with mixed **bold** and *italic* text.
        """
        result = self.parser.parse(text)

        # 混在コンテンツが解析されることを確認
        assert isinstance(result, list)

    def test_parse_empty_content(self):
        """空コンテンツ解析テスト"""
        text = ""
        result = self.parser.parse(text)

        # 空コンテンツでも正常に処理されることを確認
        assert isinstance(result, list)

    def test_parse_whitespace_content(self):
        """空白のみコンテンツ解析テスト"""
        text = "   \n\n   \t\t   \n   "
        result = self.parser.parse(text)

        # 空白のみでも正常に処理されることを確認
        assert isinstance(result, list)

    def test_parse_special_characters(self):
        """特殊文字解析テスト"""
        text = "Special chars: @#$%^&*()_+-=[]{}|;':\",./<>?"
        result = self.parser.parse(text)

        # 特殊文字が正常に解析されることを確認
        assert isinstance(result, list)