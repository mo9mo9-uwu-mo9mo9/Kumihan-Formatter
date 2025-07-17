"""
markdown_converter.py分割のためのテスト

TDD: 分割後の新しいモジュール構造のテスト
Issue #492 Phase 5A - markdown_converter.py分割
"""

from pathlib import Path
from unittest.mock import Mock

import pytest


class TestMarkdownParser:
    """マークダウンパーサーのテスト"""

    def test_markdown_parser_import(self):
        """RED: パーサーモジュールインポートテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.markdown_parser import MarkdownParser

    def test_markdown_parser_initialization(self):
        """RED: パーサー初期化テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.markdown_parser import MarkdownParser

            parser = MarkdownParser()

    def test_compile_patterns_method(self):
        """RED: パターンコンパイルメソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.markdown_parser import MarkdownParser

            parser = MarkdownParser()
            patterns = parser._compile_patterns()

    def test_convert_headings_method(self):
        """RED: 見出し変換メソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.markdown_parser import MarkdownParser

            parser = MarkdownParser()
            result = parser._convert_headings("# Test Heading")

    def test_convert_lists_method(self):
        """RED: リスト変換メソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.markdown_parser import MarkdownParser

            parser = MarkdownParser()
            result = parser._convert_lists("- Item 1\n- Item 2")

    def test_convert_inline_elements_method(self):
        """RED: インライン要素変換メソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.markdown_parser import MarkdownParser

            parser = MarkdownParser()
            result = parser._convert_inline_elements("**bold** *italic*")


class TestMarkdownRenderer:
    """マークダウンレンダラーのテスト"""

    def test_markdown_renderer_import(self):
        """RED: レンダラーモジュールインポートテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.markdown_renderer import MarkdownRenderer

    def test_markdown_renderer_initialization(self):
        """RED: レンダラー初期化テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.markdown_renderer import MarkdownRenderer

            renderer = MarkdownRenderer()

    def test_convert_paragraphs_method(self):
        """RED: 段落変換メソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.markdown_renderer import MarkdownRenderer

            renderer = MarkdownRenderer()
            result = renderer._convert_paragraphs("Paragraph text\n\nAnother paragraph")

    def test_create_full_html_method(self):
        """RED: 完全HTML作成メソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.markdown_renderer import MarkdownRenderer

            renderer = MarkdownRenderer()
            result = renderer._create_full_html("Title", "<p>Content</p>", "test.md")

    def test_extract_title_from_content_method(self):
        """RED: タイトル抽出メソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.markdown_renderer import MarkdownRenderer

            renderer = MarkdownRenderer()
            result = renderer._extract_title_from_content("# Main Title\nContent")


class TestMarkdownProcessor:
    """マークダウンプロセッサーのテスト"""

    def test_markdown_processor_import(self):
        """RED: プロセッサーモジュールインポートテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.markdown_processor import MarkdownProcessor

    def test_markdown_processor_initialization(self):
        """RED: プロセッサー初期化テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.markdown_processor import MarkdownProcessor

            processor = MarkdownProcessor()

    def test_convert_code_blocks_method(self):
        """RED: コードブロック変換メソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.markdown_processor import MarkdownProcessor

            processor = MarkdownProcessor()
            result = processor._convert_code_blocks("```python\nprint('hello')\n```")

    def test_generate_heading_id_method(self):
        """RED: 見出しID生成メソッドテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.markdown_processor import MarkdownProcessor

            processor = MarkdownProcessor()
            result = processor._generate_heading_id("Test Heading")


class TestMarkdownFactory:
    """マークダウンファクトリーのテスト"""

    def test_markdown_factory_import(self):
        """RED: ファクトリーモジュールインポートテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.markdown_factory import (
                create_markdown_converter,
            )

    def test_create_markdown_converter_function(self):
        """RED: マークダウン変換器作成関数テスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.markdown_factory import (
                create_markdown_converter,
            )

            converter = create_markdown_converter()

    def test_markdown_converter_components(self):
        """RED: 変換器コンポーネントテスト"""
        with pytest.raises(ImportError):
            from kumihan_formatter.core.markdown_factory import MarkdownFactory

            factory = MarkdownFactory()


class TestOriginalMarkdownConverter:
    """元のmarkdown_converterモジュールとの互換性テスト"""

    def test_original_converter_still_works(self):
        """元のmarkdown_converterが正常動作することを確認"""
        from kumihan_formatter.core.markdown_converter import (
            SimpleMarkdownConverter,
            convert_markdown_file,
            convert_markdown_text,
        )

        # 基本クラスが存在することを確認
        assert SimpleMarkdownConverter is not None

        # ファクトリー関数が存在することを確認
        assert callable(convert_markdown_file)
        assert callable(convert_markdown_text)

    def test_simple_markdown_converter_initialization(self):
        """元のSimpleMarkdownConverter初期化テスト"""
        from kumihan_formatter.core.markdown_converter import SimpleMarkdownConverter

        converter = SimpleMarkdownConverter()
        assert converter is not None
        assert hasattr(converter, "patterns")

    def test_convert_text_method(self):
        """convert_textメソッドテスト"""
        from kumihan_formatter.core.markdown_converter import SimpleMarkdownConverter

        converter = SimpleMarkdownConverter()
        result = converter.convert_text("# Test\nThis is a test.")
        assert isinstance(result, str)
        assert "<h1" in result
        assert "<p>" in result

    def test_convert_file_method(self):
        """convert_fileメソッドテスト"""
        from kumihan_formatter.core.markdown_converter import SimpleMarkdownConverter

        converter = SimpleMarkdownConverter()
        assert hasattr(converter, "convert_file")
        assert callable(converter.convert_file)

    def test_core_methods_exist(self):
        """コアメソッドが存在することを確認"""
        from kumihan_formatter.core.markdown_converter import SimpleMarkdownConverter

        converter = SimpleMarkdownConverter()

        # パターン関連
        assert hasattr(converter, "_compile_patterns")
        assert hasattr(converter, "patterns")

        # 変換メソッド系
        assert hasattr(converter, "_convert_headings")
        assert hasattr(converter, "_convert_lists")
        assert hasattr(converter, "_convert_inline_elements")
        assert hasattr(converter, "_convert_paragraphs")
        assert hasattr(converter, "_convert_code_blocks")

        # HTML生成系
        assert hasattr(converter, "_create_full_html")
        assert hasattr(converter, "_extract_title_from_content")
        assert hasattr(converter, "_generate_heading_id")

    def test_helper_functions(self):
        """ヘルパー関数のテスト"""
        from kumihan_formatter.core.markdown_converter import convert_markdown_text

        result = convert_markdown_text("# Test Title\nTest content")
        assert isinstance(result, str)
        assert "<!DOCTYPE html>" in result
        assert "<title>" in result
        assert "<h1" in result

    def test_markdown_patterns(self):
        """マークダウンパターンのテスト"""
        from kumihan_formatter.core.markdown_converter import SimpleMarkdownConverter

        converter = SimpleMarkdownConverter()
        patterns = converter.patterns

        # 主要パターンが存在することを確認
        assert "h1" in patterns
        assert "h2" in patterns
        assert "strong" in patterns
        assert "em" in patterns
        assert "link" in patterns
        assert "code" in patterns
        assert "ul_item" in patterns
        assert "ol_item" in patterns

    def test_text_conversion_functionality(self):
        """テキスト変換機能のテスト"""
        from kumihan_formatter.core.markdown_converter import SimpleMarkdownConverter

        converter = SimpleMarkdownConverter()

        # 見出し変換
        result = converter.convert_text("# Main Title")
        assert '<h1 id="main-title">Main Title</h1>' in result

        # 強調変換
        result = converter.convert_text("**bold** *italic*")
        assert "<strong>bold</strong>" in result
        assert "<em>italic</em>" in result

        # リンク変換
        result = converter.convert_text("[link text](http://example.com)")
        assert '<a href="http://example.com">link text</a>' in result
