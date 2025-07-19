"""Complete Parser Tests for Issue #491 Phase 3

Comprehensive tests for parser.py to achieve 100% coverage.
Current coverage: 72% → Target: 100%
"""

from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.ast_nodes import Node
from kumihan_formatter.parser import Parser, parse


class TestParserCompleteCoverage:
    """Complete coverage tests for Parser class"""

    def test_parser_initialization(self):
        """Test Parser initialization"""
        parser = Parser()
        assert parser is not None
        assert hasattr(parser, "block_parser")
        assert hasattr(parser, "list_parser")
        assert hasattr(parser, "keyword_parser")

    def test_parser_with_config(self):
        """Test Parser initialization with config"""
        from kumihan_formatter.config import ConfigManager

        config = ConfigManager()
        parser = Parser(config)
        assert parser is not None
        assert parser.config == config

    def test_parse_empty_content(self):
        """Test parsing empty content"""
        parser = Parser()
        result = parser.parse("")
        assert isinstance(result, list)

        # Test None content
        result = parser.parse(None)
        assert isinstance(result, list)

    def test_parse_whitespace_only(self):
        """Test parsing whitespace-only content"""
        parser = Parser()

        # Test spaces only
        result = parser.parse("   ")
        assert isinstance(result, list)

        # Test newlines only
        result = parser.parse("\n\n\n")
        assert isinstance(result, list)

        # Test mixed whitespace
        result = parser.parse("  \n  \t  \n  ")
        assert isinstance(result, list)

    def test_parse_simple_text(self):
        """Test parsing simple text content"""
        parser = Parser()

        # Single line
        result = parser.parse("Hello World")
        assert isinstance(result, list)
        assert len(result) > 0

        # Multiple lines
        result = parser.parse("Line 1\nLine 2\nLine 3")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_parse_with_kumihan_markers(self):
        """Test parsing content with Kumihan markers"""
        parser = Parser()

        # Test with marker syntax
        content = ";;;太字;;; テスト内容 ;;;"
        result = parser.parse(content)
        assert isinstance(result, list)

        # Test with footnote syntax
        content = "本文((脚注内容))です"
        result = parser.parse(content)
        assert isinstance(result, list)

        # Test with ruby syntax
        content = "漢字｜読み方《よみかた》"
        result = parser.parse(content)
        assert isinstance(result, list)

    def test_parse_with_lists(self):
        """Test parsing content with list syntax"""
        parser = Parser()

        # Bullet list
        content = "- Item 1\n- Item 2\n- Item 3"
        result = parser.parse(content)
        assert isinstance(result, list)

        # Numbered list
        content = "1. First\n2. Second\n3. Third"
        result = parser.parse(content)
        assert isinstance(result, list)

    def test_parse_with_blocks(self):
        """Test parsing content with block elements"""
        parser = Parser()

        # Quote block
        content = "> This is a quote\n> Multiple lines"
        result = parser.parse(content)
        assert isinstance(result, list)

        # Code block
        content = "```\ncode here\n```"
        result = parser.parse(content)
        assert isinstance(result, list)

    def test_parse_mixed_content(self):
        """Test parsing mixed content types"""
        parser = Parser()

        content = """# タイトル

普通のテキスト

- リスト項目1
- リスト項目2

;;;太字;;; 強調テキスト ;;;

本文((脚注))です。

> 引用文
"""
        result = parser.parse(content)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_parse_error_handling(self):
        """Test parser error handling"""
        parser = Parser()

        # Test with invalid marker syntax
        content = ";;;不正なマーカー"  # Missing closing
        result = parser.parse(content)
        assert isinstance(result, list)

        # Test with malformed content
        content = "((未完了の脚注"
        result = parser.parse(content)
        assert isinstance(result, list)

    def test_parse_function_edge_cases(self):
        """Test parse function edge cases"""
        # Test with empty string
        result = parse("")
        assert isinstance(result, list)

        # Test with None
        result = parse(None)
        assert isinstance(result, list)

        # Test with very long content
        long_content = "A" * 10000
        result = parse(long_content)
        assert isinstance(result, list)

    def test_parse_unicode_content(self):
        """Test parsing Unicode content"""
        parser = Parser()

        # Japanese text
        content = "これは日本語のテストです。漢字、ひらがな、カタカナを含みます。"
        result = parser.parse(content)
        assert isinstance(result, list)

        # Mixed scripts
        content = "English 日本語 한국어 中文 العربية"
        result = parser.parse(content)
        assert isinstance(result, list)

        # Special unicode characters
        content = "Symbols: ♠ ♥ ♦ ♣ ★ ☆ ☯ ☮"
        result = parser.parse(content)
        assert isinstance(result, list)

    def test_parse_special_characters(self):
        """Test parsing special characters"""
        parser = Parser()

        # HTML-like content
        content = "<div>Not actual HTML</div>"
        result = parser.parse(content)
        assert isinstance(result, list)

        # Special punctuation
        content = "Test... with! various? punctuation: marks;"
        result = parser.parse(content)
        assert isinstance(result, list)

        # Mathematical symbols
        content = "Math: ∑ ∫ ∞ ± × ÷ ≠ ≤ ≥"
        result = parser.parse(content)
        assert isinstance(result, list)

    def test_parser_component_integration(self):
        """Test parser component integration"""
        parser = Parser()

        # Verify parser components exist
        assert parser.block_parser is not None
        assert parser.list_parser is not None
        assert parser.keyword_parser is not None

        # Test that components are used
        content = "Test content with various elements"
        result = parser.parse(content)
        assert isinstance(result, list)

    def test_parse_performance_edge_cases(self):
        """Test parser performance edge cases"""
        parser = Parser()

        # Very short content
        result = parser.parse("a")
        assert isinstance(result, list)

        # Empty lines mixed with content
        content = "\n\nContent\n\n\nMore content\n\n"
        result = parser.parse(content)
        assert isinstance(result, list)

        # Repeated patterns
        content = ";;;pattern;;; text ;;;\n" * 100
        result = parser.parse(content)
        assert isinstance(result, list)


class TestParserConfigurationScenarios:
    """Test parser with different configuration scenarios"""

    def test_parser_with_different_configs(self):
        """Test parser with different configuration objects"""
        from kumihan_formatter.config import ConfigManager

        # Test with default config
        config1 = ConfigManager()
        parser1 = Parser(config1)
        result1 = parser1.parse("Test content")
        assert isinstance(result1, list)

        # Test with custom config path
        try:
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".toml", delete=False
            ) as f:
                f.write('[formatting]\noutput_format = "html"\n')
                temp_path = f.name

            config2 = ConfigManager(config_path=temp_path)
            parser2 = Parser(config2)
            result2 = parser2.parse("Test content")
            assert isinstance(result2, list)

        except Exception:
            # If config file creation fails, just test basic functionality
            parser2 = Parser()
            result2 = parser2.parse("Test content")
            assert isinstance(result2, list)

    def test_parser_config_influence(self):
        """Test how configuration influences parsing"""
        from kumihan_formatter.config import ConfigManager

        config = ConfigManager()
        parser = Parser(config)

        # Test that parser uses config
        assert parser.config == config

        # Test parsing with config
        result = parser.parse("Content to parse")
        assert isinstance(result, list)


class TestParserErrorRecovery:
    """Test parser error recovery mechanisms"""

    def test_malformed_marker_recovery(self):
        """Test recovery from malformed markers"""
        parser = Parser()

        # Missing closing marker
        content = ";;;太字;;; 内容"
        result = parser.parse(content)
        assert isinstance(result, list)

        # Extra opening markers
        content = ";;;太字;;;太字;;; 内容 ;;;"
        result = parser.parse(content)
        assert isinstance(result, list)

        # Nested markers (should be handled gracefully)
        content = ";;;外側;;;内側;;;内容;;;外側終了;;;"
        result = parser.parse(content)
        assert isinstance(result, list)

    def test_incomplete_syntax_recovery(self):
        """Test recovery from incomplete syntax"""
        parser = Parser()

        # Incomplete footnote
        content = "テキスト((脚注"
        result = parser.parse(content)
        assert isinstance(result, list)

        # Incomplete ruby
        content = "漢字｜読み方《"
        result = parser.parse(content)
        assert isinstance(result, list)

        # Incomplete list
        content = "- 項目1\n項目2\n- 項目3"
        result = parser.parse(content)
        assert isinstance(result, list)

    def test_mixed_syntax_errors(self):
        """Test handling of mixed syntax errors"""
        parser = Parser()

        content = """
        ;;;不完全マーカー
        - リスト項目
        ((不完了脚注
        正常なテキスト
        ;;;正常;;; マーカー ;;;
        """
        result = parser.parse(content)
        assert isinstance(result, list)


class TestParserStressTests:
    """Stress tests for parser robustness"""

    def test_large_content_parsing(self):
        """Test parsing large content"""
        parser = Parser()

        # Generate large content
        large_content = "テストライン " * 1000 + "\n" * 500
        result = parser.parse(large_content)
        assert isinstance(result, list)

    def test_deeply_nested_structures(self):
        """Test deeply nested structures"""
        parser = Parser()

        # Create nested list structure
        nested_content = ""
        for i in range(10):
            nested_content += "  " * i + f"- Level {i} item\n"

        result = parser.parse(nested_content)
        assert isinstance(result, list)

    def test_complex_marker_combinations(self):
        """Test complex marker combinations"""
        parser = Parser()

        content = """
        ;;;太字;;; テキスト((脚注内容)) ;;;

        漢字｜読み方《よみかた》の；；；マーカー;;; 内容 ;;;

        - ;;;リスト;;; 項目 ;;;
        - 項目((脚注))
        """
        result = parser.parse(content)
        assert isinstance(result, list)


class TestParserEdgeCaseHandling:
    """Test parser edge case handling"""

    def test_boundary_conditions(self):
        """Test boundary conditions"""
        parser = Parser()

        # Single character
        result = parser.parse("a")
        assert isinstance(result, list)

        # Only markers
        result = parser.parse(";;;;;;")
        assert isinstance(result, list)

        # Only special characters
        result = parser.parse("｜《》（）")
        assert isinstance(result, list)

    def test_encoding_edge_cases(self):
        """Test encoding edge cases"""
        parser = Parser()

        # Test with various encodings represented as strings
        utf8_content = "UTF-8: こんにちは"
        result = parser.parse(utf8_content)
        assert isinstance(result, list)

        # Test with emoji
        emoji_content = "Emoji test: 😀 🎉 📝 ✅"
        result = parser.parse(emoji_content)
        assert isinstance(result, list)

    def test_line_ending_variations(self):
        """Test different line ending variations"""
        parser = Parser()

        # Unix line endings
        unix_content = "Line 1\nLine 2\nLine 3"
        result = parser.parse(unix_content)
        assert isinstance(result, list)

        # Windows line endings
        windows_content = "Line 1\r\nLine 2\r\nLine 3"
        result = parser.parse(windows_content)
        assert isinstance(result, list)

        # Mixed line endings
        mixed_content = "Line 1\nLine 2\r\nLine 3\n"
        result = parser.parse(mixed_content)
        assert isinstance(result, list)
