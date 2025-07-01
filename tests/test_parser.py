"""Comprehensive tests for parser.py module

Tests for Issue #351 - Phase 1 priority A (90%+ coverage target)
"""

import pytest
from typing import List

from kumihan_formatter.parser import Parser, parse
from kumihan_formatter.core.ast_nodes import Node


class TestParserInit:
    """Test parser initialization"""

    def test_parser_init_default(self):
        """Test parser initialization with default parameters"""
        parser = Parser()
        assert parser.config is None
        assert parser.lines == []
        assert parser.current == 0
        assert parser.errors == []
        assert parser.keyword_parser is not None
        assert parser.list_parser is not None
        assert parser.block_parser is not None

    def test_parser_init_with_config(self):
        """Test parser initialization with config parameter"""
        parser = Parser(config={'test': 'value'})
        assert parser.config is None  # Config is ignored in current implementation
        assert parser.lines == []
        assert parser.current == 0
        assert parser.errors == []


class TestParserBasicParsing:
    """Test basic parsing functionality"""

    def test_parse_empty_string(self):
        """Test parsing empty string"""
        parser = Parser()
        result = parser.parse("")
        assert isinstance(result, list)
        assert len(result) == 0

    def test_parse_single_line(self):
        """Test parsing single line of text"""
        parser = Parser()
        result = parser.parse("Hello world")
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Node)

    def test_parse_multiple_lines(self):
        """Test parsing multiple lines"""
        parser = Parser()
        text = "Line 1\nLine 2\nLine 3"
        result = parser.parse(text)
        assert isinstance(result, list)
        assert len(result) >= 1  # May be combined into paragraphs

    def test_parse_with_empty_lines(self):
        """Test parsing text with empty lines"""
        parser = Parser()
        text = "Line 1\n\nLine 2\n\n\nLine 3"
        result = parser.parse(text)
        assert isinstance(result, list)
        # Empty lines should be skipped

    def test_parse_only_empty_lines(self):
        """Test parsing text with only empty lines"""
        parser = Parser()
        text = "\n\n\n"
        result = parser.parse(text)
        assert isinstance(result, list)
        assert len(result) == 0

    def test_parse_only_whitespace(self):
        """Test parsing text with only whitespace"""
        parser = Parser()
        text = "   \n  \t  \n   "
        result = parser.parse(text)
        assert isinstance(result, list)


class TestParserCommentHandling:
    """Test comment line handling"""

    def test_parse_comment_lines(self):
        """Test parsing lines with comments"""
        parser = Parser()
        text = "# This is a comment\nNormal line\n# Another comment"
        result = parser.parse(text)
        assert isinstance(result, list)
        # Comments should be ignored, only normal line should be parsed

    def test_parse_only_comments(self):
        """Test parsing text with only comments"""
        parser = Parser()
        text = "# Comment 1\n# Comment 2\n# Comment 3"
        result = parser.parse(text)
        assert isinstance(result, list)
        assert len(result) == 0

    def test_parse_mixed_comments_and_content(self):
        """Test parsing mixed comments and content"""
        parser = Parser()
        text = "# Header comment\nContent line 1\n# Middle comment\nContent line 2"
        result = parser.parse(text)
        assert isinstance(result, list)
        # Should parse only content lines


class TestParserListParsing:
    """Test list parsing functionality"""

    def test_parse_unordered_list(self):
        """Test parsing unordered list"""
        parser = Parser()
        text = "- Item 1\n- Item 2\n- Item 3"
        result = parser.parse(text)
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_parse_ordered_list(self):
        """Test parsing ordered list"""
        parser = Parser()
        text = "1. Item 1\n2. Item 2\n3. Item 3"
        result = parser.parse(text)
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_parse_nested_lists(self):
        """Test parsing nested lists"""
        parser = Parser()
        text = "- Item 1\n  - Subitem 1\n  - Subitem 2\n- Item 2"
        result = parser.parse(text)
        assert isinstance(result, list)

    def test_parse_mixed_list_types(self):
        """Test parsing mixed list types"""
        parser = Parser()
        text = "- Unordered item\n1. Ordered item\n- Another unordered"
        result = parser.parse(text)
        assert isinstance(result, list)


class TestParserBlockParsing:
    """Test block parsing functionality"""

    def test_parse_paragraph(self):
        """Test parsing regular paragraph"""
        parser = Parser()
        text = "This is a regular paragraph with multiple words."
        result = parser.parse(text)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_parse_multiple_paragraphs(self):
        """Test parsing multiple paragraphs separated by empty lines"""
        parser = Parser()
        text = "Paragraph 1\n\nParagraph 2\n\nParagraph 3"
        result = parser.parse(text)
        assert isinstance(result, list)
        assert len(result) >= 3

    def test_parse_block_markers(self):
        """Test parsing with block markers"""
        parser = Parser()
        # Test basic block structure
        text = "Normal text before block"
        result = parser.parse(text)
        assert isinstance(result, list)


class TestParserErrorHandling:
    """Test error handling functionality"""

    def test_get_errors_empty(self):
        """Test getting errors when no errors exist"""
        parser = Parser()
        parser.parse("Valid content")
        errors = parser.get_errors()
        assert isinstance(errors, list)
        assert len(errors) == 0

    def test_add_error(self):
        """Test adding error manually"""
        parser = Parser()
        parser.add_error("Test error message")
        errors = parser.get_errors()
        assert len(errors) == 1
        assert errors[0] == "Test error message"

    def test_multiple_errors(self):
        """Test adding multiple errors"""
        parser = Parser()
        parser.add_error("Error 1")
        parser.add_error("Error 2")
        parser.add_error("Error 3")
        errors = parser.get_errors()
        assert len(errors) == 3
        assert "Error 1" in errors
        assert "Error 2" in errors
        assert "Error 3" in errors


class TestParserStatistics:
    """Test statistics functionality"""

    def test_get_statistics_empty(self):
        """Test getting statistics for empty content"""
        parser = Parser()
        parser.parse("")
        stats = parser.get_statistics()
        assert isinstance(stats, dict)
        assert "total_lines" in stats
        assert "errors_count" in stats
        assert "heading_count" in stats
        assert stats["total_lines"] == 1  # Empty string becomes one empty line
        assert stats["errors_count"] == 0

    def test_get_statistics_with_content(self):
        """Test getting statistics for real content"""
        parser = Parser()
        text = "Line 1\nLine 2\nLine 3"
        parser.parse(text)
        stats = parser.get_statistics()
        assert stats["total_lines"] == 3
        assert stats["errors_count"] == 0
        assert "heading_count" in stats

    def test_get_statistics_with_errors(self):
        """Test getting statistics when errors exist"""
        parser = Parser()
        parser.parse("Some content")
        parser.add_error("Test error")
        stats = parser.get_statistics()
        assert stats["errors_count"] == 1


class TestParserInternalMethods:
    """Test internal parsing methods"""

    def test_parse_line_empty_position(self):
        """Test _parse_line when current position is at end"""
        parser = Parser()
        parser.lines = ["line1", "line2"]
        parser.current = 2  # Beyond end
        result = parser._parse_line()
        assert result is None

    def test_parse_line_comment(self):
        """Test _parse_line with comment line"""
        parser = Parser()
        parser.lines = ["# This is a comment"]
        parser.current = 0
        result = parser._parse_line()
        assert result is None
        assert parser.current == 1

    def test_parse_line_normal_content(self):
        """Test _parse_line with normal content"""
        parser = Parser()
        parser.lines = ["Normal content line"]
        parser.current = 0
        result = parser._parse_line()
        assert result is not None
        assert isinstance(result, Node)


class TestParseFunction:
    """Test module-level parse function"""

    def test_parse_function_basic(self):
        """Test module-level parse function with basic input"""
        result = parse("Hello world")
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_parse_function_with_config(self):
        """Test module-level parse function with config"""
        result = parse("Hello world", config={'test': 'value'})
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_parse_function_empty(self):
        """Test module-level parse function with empty input"""
        result = parse("")
        assert isinstance(result, list)
        assert len(result) == 0

    def test_parse_function_complex(self):
        """Test module-level parse function with complex input"""
        text = """# Header
        
Regular paragraph

- List item 1
- List item 2

Another paragraph"""
        result = parse(text)
        assert isinstance(result, list)
        assert len(result) >= 2


class TestParserEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_parse_very_long_line(self):
        """Test parsing very long line"""
        parser = Parser()
        long_line = "a" * 10000
        result = parser.parse(long_line)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_parse_unicode_content(self):
        """Test parsing unicode content"""
        parser = Parser()
        text = "こんにちは世界\n日本語のテスト\n絵文字 🚀 ⭐"
        result = parser.parse(text)
        assert isinstance(result, list)

    def test_parse_special_characters(self):
        """Test parsing with special characters"""
        parser = Parser()
        text = "Line with @#$%^&*()_+-={}[]|\\:;\"'<>?,./"
        result = parser.parse(text)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_parse_whitespace_only_lines(self):
        """Test parsing lines with only whitespace"""
        parser = Parser()
        text = "Content\n   \t   \nMore content"
        result = parser.parse(text)
        assert isinstance(result, list)

    def test_parse_mixed_line_endings(self):
        """Test parsing with mixed line endings"""
        parser = Parser()
        text = "Line 1\nLine 2\rLine 3\r\nLine 4"
        result = parser.parse(text)
        assert isinstance(result, list)


class TestParserStateManagement:
    """Test parser state management"""

    def test_parser_state_reset_on_new_parse(self):
        """Test that parser state resets properly on new parse"""
        parser = Parser()
        
        # First parse
        parser.parse("First content")
        parser.add_error("First error")
        first_errors = len(parser.get_errors())
        first_lines = len(parser.lines)
        
        # Second parse should reset state
        parser.parse("Second content")
        second_errors = len(parser.get_errors())
        second_lines = len(parser.lines)
        
        assert second_errors == 0  # Errors should be reset
        assert parser.current == 0 or parser.current == second_lines  # Current should be reset

    def test_parser_lines_property(self):
        """Test parser lines property after parsing"""
        parser = Parser()
        text = "Line 1\nLine 2\nLine 3"
        parser.parse(text)
        assert len(parser.lines) == 3
        assert parser.lines[0] == "Line 1"
        assert parser.lines[1] == "Line 2"
        assert parser.lines[2] == "Line 3"

    def test_parser_current_position_tracking(self):
        """Test parser current position tracking"""
        parser = Parser()
        text = "Line 1\nLine 2"
        parser.parse(text)
        # After parsing, current should be at end or properly positioned
        assert parser.current >= 0
        assert parser.current <= len(parser.lines)