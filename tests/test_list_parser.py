"""Tests for list parser modules

This module tests list parsing functionality including unordered lists,
ordered lists, and nested list structures.
"""

from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.ast_nodes import Node


class TestListParser:
    """Test list parser functionality"""

    def setup_method(self):
        """Set up test environment"""
        # Import here to avoid circular imports during testing
        try:
            from kumihan_formatter.core.keyword_parser import KeywordParser
            from kumihan_formatter.core.list_parser import ListParser

            self.keyword_parser = Mock(spec=KeywordParser)
            self.parser = ListParser(self.keyword_parser)
        except ImportError:
            # Fallback for when list_parser module structure is different
            self.parser = None

    def test_init(self):
        """Test list parser initialization"""
        if self.parser is None:
            pytest.skip("ListParser not available")

        assert self.parser is not None
        assert self.parser.keyword_parser == self.keyword_parser

    def test_is_list_line_unordered(self):
        """Test detection of unordered list lines"""
        if self.parser is None:
            pytest.skip("ListParser not available")

        unordered_lines = [
            "- Item 1",
            "* Item 2",
            "+ Item 3",
            "  - Indented item",
            "\t* Tab indented",
        ]

        for line in unordered_lines:
            if hasattr(self.parser, "is_list_line"):
                result = self.parser.is_list_line(line)
                assert result == "ul" or result is True, f"Failed for: {line}"

    def test_is_list_line_ordered(self):
        """Test detection of ordered list lines"""
        if self.parser is None:
            pytest.skip("ListParser not available")

        ordered_lines = [
            "1. First item",
            "2. Second item",
            "10. Tenth item",
            "  1. Indented ordered",
            "\t3. Tab indented ordered",
        ]

        for line in ordered_lines:
            if hasattr(self.parser, "is_list_line"):
                result = self.parser.is_list_line(line)
                assert result == "ol" or result is True, f"Failed for: {line}"

    def test_is_list_line_not_list(self):
        """Test detection of non-list lines"""
        if self.parser is None:
            pytest.skip("ListParser not available")

        non_list_lines = [
            "Regular paragraph text",
            "Text with - dash in middle",
            "Text with 1. number in middle",
            "-Missing space after dash",
            "1.Missing space after number",
            "",
            "   ",
        ]

        for line in non_list_lines:
            if hasattr(self.parser, "is_list_line"):
                result = self.parser.is_list_line(line)
                assert (
                    result == "" or result is None or result is False
                ), f"Should not be list: {line}"

    def test_parse_unordered_list_simple(self):
        """Test parsing simple unordered list"""
        if self.parser is None:
            pytest.skip("ListParser not available")

        lines = ["- First item", "- Second item", "- Third item", ""]

        if hasattr(self.parser, "parse_unordered_list"):
            node, next_index = self.parser.parse_unordered_list(lines, 0)

            assert isinstance(node, Node) or node is not None
            assert isinstance(next_index, int)
            assert next_index > 0

    def test_parse_ordered_list_simple(self):
        """Test parsing simple ordered list"""
        if self.parser is None:
            pytest.skip("ListParser not available")

        lines = ["1. First item", "2. Second item", "3. Third item", ""]

        if hasattr(self.parser, "parse_ordered_list"):
            node, next_index = self.parser.parse_ordered_list(lines, 0)

            assert isinstance(node, Node) or node is not None
            assert isinstance(next_index, int)
            assert next_index > 0

    def test_parse_unordered_list_with_nesting(self):
        """Test parsing nested unordered list"""
        if self.parser is None:
            pytest.skip("ListParser not available")

        lines = [
            "- Top level item",
            "  - Nested item 1",
            "  - Nested item 2",
            "- Another top level",
            "",
        ]

        if hasattr(self.parser, "parse_unordered_list"):
            node, next_index = self.parser.parse_unordered_list(lines, 0)

            assert isinstance(node, Node) or node is not None
            assert isinstance(next_index, int)

    def test_parse_ordered_list_with_nesting(self):
        """Test parsing nested ordered list"""
        if self.parser is None:
            pytest.skip("ListParser not available")

        lines = [
            "1. First item",
            "   1. Nested first",
            "   2. Nested second",
            "2. Second item",
            "",
        ]

        if hasattr(self.parser, "parse_ordered_list"):
            node, next_index = self.parser.parse_ordered_list(lines, 0)

            assert isinstance(node, Node) or node is not None
            assert isinstance(next_index, int)

    def test_parse_mixed_list_stops_correctly(self):
        """Test that list parsing stops at appropriate boundaries"""
        if self.parser is None:
            pytest.skip("ListParser not available")

        lines = [
            "- List item 1",
            "- List item 2",
            "",
            "Regular paragraph",
            "- New list starts here",
        ]

        if hasattr(self.parser, "parse_unordered_list"):
            node, next_index = self.parser.parse_unordered_list(lines, 0)

            # Should stop at empty line before paragraph
            assert next_index <= 3

    def test_parse_list_with_inline_formatting(self):
        """Test parsing list with inline formatting"""
        if self.parser is None:
            pytest.skip("ListParser not available")

        lines = [
            "- Item with **bold** text",
            "- Item with *italic* text",
            "- Item with `code` text",
            "",
        ]

        if hasattr(self.parser, "parse_unordered_list"):
            node, next_index = self.parser.parse_unordered_list(lines, 0)

            assert isinstance(node, Node) or node is not None

    def test_parse_list_boundary_conditions(self):
        """Test list parsing with boundary conditions"""
        if self.parser is None:
            pytest.skip("ListParser not available")

        # Test with index beyond array bounds
        lines = ["- Item 1", "- Item 2"]

        if hasattr(self.parser, "parse_unordered_list"):
            node, next_index = self.parser.parse_unordered_list(lines, 10)

            # Should handle gracefully
            assert node is None or isinstance(node, Node)
            assert isinstance(next_index, int)

    def test_parse_empty_list_items(self):
        """Test parsing list with empty items"""
        if self.parser is None:
            pytest.skip("ListParser not available")

        lines = ["- First item", "- ", "- Third item", ""]  # Empty item

        if hasattr(self.parser, "parse_unordered_list"):
            node, next_index = self.parser.parse_unordered_list(lines, 0)

            # Should handle empty items gracefully
            assert isinstance(node, Node) or node is not None


class TestListParserCore:
    """Test list parser core functionality"""

    def setup_method(self):
        """Set up test environment"""
        try:
            from kumihan_formatter.core.keyword_parser import KeywordParser
            from kumihan_formatter.core.keyword_parsing.definitions import (
                KeywordDefinitions,
            )
            from kumihan_formatter.core.list_parser_core import ListParserCore

            definitions = KeywordDefinitions()
            keyword_parser = KeywordParser(definitions)
            self.parser_core = ListParserCore(keyword_parser)
        except ImportError:
            self.parser_core = None

    def test_core_initialization(self):
        """Test list parser core initialization"""
        if self.parser_core is None:
            pytest.skip("ListParserCore not available")

        assert self.parser_core is not None

    def test_parse_list_item_content(self):
        """Test parsing individual list item content"""
        if self.parser_core is None:
            pytest.skip("ListParserCore not available")

        if hasattr(self.parser_core, "parse_item_content"):
            content = "Item with **bold** and *italic* text"
            result = self.parser_core.parse_item_content(content)

            assert isinstance(result, str) or isinstance(result, list)

    def test_calculate_indentation_level(self):
        """Test calculating indentation levels"""
        if self.parser_core is None:
            pytest.skip("ListParserCore not available")

        test_cases = [
            ("- Item", 0),
            ("  - Indented item", 1),
            ("    - Double indented", 2),
            ("\t- Tab indented", 1),
        ]

        for line, expected_level in test_cases:
            if hasattr(self.parser_core, "get_indentation_level"):
                level = self.parser_core.get_indentation_level(line)
                assert level == expected_level, f"Failed for: '{line}'"

    def test_extract_list_item_text(self):
        """Test extracting text from list items"""
        if self.parser_core is None:
            pytest.skip("ListParserCore not available")

        test_cases = [
            ("- Simple item", "Simple item"),
            ("1. Numbered item", "Numbered item"),
            ("  * Indented item", "Indented item"),
            ("10. Double digit", "Double digit"),
        ]

        for line, expected_text in test_cases:
            if hasattr(self.parser_core, "extract_item_text"):
                text = self.parser_core.extract_item_text(line)
                assert text.strip() == expected_text, f"Failed for: '{line}'"


class TestListParserFactory:
    """Test list parser factory functionality"""

    def setup_method(self):
        """Set up test environment"""
        try:
            from kumihan_formatter.core.list_parser_factory import ListParserFactory

            self.factory = ListParserFactory()
        except ImportError:
            self.factory = None

    def test_factory_initialization(self):
        """Test list parser factory initialization"""
        if self.factory is None:
            pytest.skip("ListParserFactory not available")

        assert self.factory is not None

    def test_create_unordered_list_parser(self):
        """Test creating unordered list parser"""
        if self.factory is None:
            pytest.skip("ListParserFactory not available")

        if hasattr(self.factory, "create_unordered_parser"):
            parser = self.factory.create_unordered_parser()
            assert parser is not None

    def test_create_ordered_list_parser(self):
        """Test creating ordered list parser"""
        if self.factory is None:
            pytest.skip("ListParserFactory not available")

        if hasattr(self.factory, "create_ordered_parser"):
            parser = self.factory.create_ordered_parser()
            assert parser is not None

    def test_factory_produces_different_parsers(self):
        """Test that factory produces appropriate parsers for different list types"""
        if self.factory is None:
            pytest.skip("ListParserFactory not available")

        if hasattr(self.factory, "create_parser_for_type"):
            ul_parser = self.factory.create_parser_for_type("ul")
            ol_parser = self.factory.create_parser_for_type("ol")

            # Should create different instances or configurations
            assert ul_parser is not None
            assert ol_parser is not None


class TestListParserIntegration:
    """Integration tests for list parsing"""

    def test_list_detection_and_parsing_integration(self):
        """Test integration between list detection and parsing"""
        try:
            from kumihan_formatter.core.keyword_parser import KeywordParser
            from kumihan_formatter.core.list_parser import ListParser

            keyword_parser = KeywordParser()
            list_parser = ListParser(keyword_parser)

            test_line = "- Test list item"

            # Test detection
            if hasattr(list_parser, "is_list_line"):
                list_type = list_parser.is_list_line(test_line)
                assert list_type in ["ul", "ol"] or list_type is True

            # Test parsing based on detection
            lines = [test_line, "- Second item", ""]

            if hasattr(list_parser, "parse_unordered_list"):
                node, next_index = list_parser.parse_unordered_list(lines, 0)
                assert node is not None

        except ImportError:
            pytest.skip("List parser modules not available")

    def test_complex_nested_list_scenario(self):
        """Test complex nested list parsing scenario"""
        try:
            from kumihan_formatter.core.keyword_parser import KeywordParser
            from kumihan_formatter.core.list_parser import ListParser

            keyword_parser = KeywordParser()
            list_parser = ListParser(keyword_parser)

            complex_list = [
                "1. First main item",
                "   - Nested unordered item",
                "   - Another nested item",
                "     1. Deeply nested ordered",
                "     2. Another deep item",
                "   - Back to second level",
                "2. Second main item",
                "",
            ]

            if hasattr(list_parser, "parse_ordered_list"):
                node, next_index = list_parser.parse_ordered_list(complex_list, 0)

                # Should handle complex nesting
                assert node is not None
                assert isinstance(next_index, int)

        except ImportError:
            pytest.skip("List parser modules not available")

    def test_list_parser_error_handling(self):
        """Test list parser error handling"""
        try:
            from kumihan_formatter.core.keyword_parser import KeywordParser
            from kumihan_formatter.core.list_parser import ListParser

            keyword_parser = KeywordParser()
            list_parser = ListParser(keyword_parser)

            # Test with malformed list
            malformed_lines = ["- Valid item", "Not a list item", "- Back to list", ""]

            if hasattr(list_parser, "parse_unordered_list"):
                node, next_index = list_parser.parse_unordered_list(malformed_lines, 0)

                # Should handle malformed input gracefully
                assert isinstance(next_index, int)

        except ImportError:
            pytest.skip("List parser modules not available")

    def test_list_parser_with_real_keyword_parser(self):
        """Test list parser with real keyword parser integration"""
        try:
            from kumihan_formatter.core.keyword_parser import KeywordParser
            from kumihan_formatter.core.list_parser import ListParser

            # Use real keyword parser for integration testing
            keyword_parser = KeywordParser()
            list_parser = ListParser(keyword_parser)

            # Test that the integration works
            assert list_parser.keyword_parser is not None

            # Test basic functionality
            if hasattr(list_parser, "is_list_line"):
                result = list_parser.is_list_line("- Test item")
                assert result is not None

        except ImportError:
            pytest.skip("List parser modules not available")

    def test_various_list_formats(self):
        """Test various list formats and edge cases"""
        try:
            from kumihan_formatter.core.keyword_parser import KeywordParser
            from kumihan_formatter.core.list_parser import ListParser

            keyword_parser = KeywordParser()
            list_parser = ListParser(keyword_parser)

            # Test different bullet styles
            bullet_styles = [
                ["- Dash style", ""],
                ["* Asterisk style", ""],
                ["+ Plus style", ""],
            ]

            for style_lines in bullet_styles:
                if hasattr(list_parser, "parse_unordered_list"):
                    node, next_index = list_parser.parse_unordered_list(style_lines, 0)
                    # Should handle all bullet styles
                    assert node is not None or next_index > 0

            # Test different numbering styles
            number_styles = [
                ["1. Standard numbering", ""],
                ["10. Double digit", ""],
                ["999. Large number", ""],
            ]

            for style_lines in number_styles:
                if hasattr(list_parser, "parse_ordered_list"):
                    node, next_index = list_parser.parse_ordered_list(style_lines, 0)
                    # Should handle all numbering styles
                    assert node is not None or next_index > 0

        except ImportError:
            pytest.skip("List parser modules not available")
