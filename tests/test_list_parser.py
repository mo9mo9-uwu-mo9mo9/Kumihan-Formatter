"""Comprehensive tests for list_parser.py module

Tests for Issue #351 - Phase 1 priority A (90%+ coverage target)
"""

import pytest
from typing import List, Tuple

from kumihan_formatter.core.list_parser import ListParser, NestedListParser, ListValidator
from kumihan_formatter.core.keyword_parser import KeywordParser
from kumihan_formatter.core.ast_nodes import Node


class TestListParserInit:
    """Test list parser initialization"""

    def test_list_parser_init(self):
        """Test list parser initialization"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        assert list_parser.keyword_parser is keyword_parser


class TestListTypeDetection:
    """Test list type detection"""

    def test_is_list_line_unordered_dash(self):
        """Test detection of unordered list with dash"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        
        result = list_parser.is_list_line("- Item 1")
        assert result == "ul"

    def test_is_list_line_unordered_bullet(self):
        """Test detection of unordered list with bullet"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        
        result = list_parser.is_list_line("・ Item 1")
        assert result == "ul"

    def test_is_list_line_ordered(self):
        """Test detection of ordered list"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        
        result = list_parser.is_list_line("1. Item 1")
        assert result == "ol"

    def test_is_list_line_not_list(self):
        """Test detection of non-list line"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        
        result = list_parser.is_list_line("Normal paragraph")
        assert result == ""

    def test_is_list_line_empty(self):
        """Test detection of empty line"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        
        result = list_parser.is_list_line("")
        assert result == ""

    def test_is_list_line_whitespace_only(self):
        """Test detection of whitespace-only line"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        
        result = list_parser.is_list_line("   ")
        assert result == ""


class TestUnorderedListParsing:
    """Test unordered list parsing"""

    def test_parse_unordered_list_single_item(self):
        """Test parsing single-item unordered list"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        
        lines = ["- Item 1"]
        node, next_index = list_parser.parse_unordered_list(lines, 0)
        
        assert isinstance(node, Node)
        assert next_index == 1

    def test_parse_unordered_list_multiple_items(self):
        """Test parsing multi-item unordered list"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        
        lines = ["- Item 1", "- Item 2", "- Item 3"]
        node, next_index = list_parser.parse_unordered_list(lines, 0)
        
        assert isinstance(node, Node)
        assert next_index == 3

    def test_parse_unordered_list_with_content_after(self):
        """Test parsing unordered list with content after"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        
        lines = ["- Item 1", "- Item 2", "Regular paragraph"]
        node, next_index = list_parser.parse_unordered_list(lines, 0)
        
        assert isinstance(node, Node)
        assert next_index == 2

    def test_parse_unordered_list_bullet_style(self):
        """Test parsing unordered list with bullet style"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        
        lines = ["・ Item 1", "・ Item 2"]
        node, next_index = list_parser.parse_unordered_list(lines, 0)
        
        assert isinstance(node, Node)
        assert next_index == 2


class TestOrderedListParsing:
    """Test ordered list parsing"""

    def test_parse_ordered_list_single_item(self):
        """Test parsing single-item ordered list"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        
        lines = ["1. Item 1"]
        node, next_index = list_parser.parse_ordered_list(lines, 0)
        
        assert isinstance(node, Node)
        assert next_index == 1

    def test_parse_ordered_list_multiple_items(self):
        """Test parsing multi-item ordered list"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        
        lines = ["1. Item 1", "2. Item 2", "3. Item 3"]
        node, next_index = list_parser.parse_ordered_list(lines, 0)
        
        assert isinstance(node, Node)
        assert next_index == 3

    def test_parse_ordered_list_with_content_after(self):
        """Test parsing ordered list with content after"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        
        lines = ["1. Item 1", "2. Item 2", "Regular paragraph"]
        node, next_index = list_parser.parse_ordered_list(lines, 0)
        
        assert isinstance(node, Node)
        assert next_index == 2

    def test_parse_ordered_list_non_sequential(self):
        """Test parsing ordered list with non-sequential numbers"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        
        lines = ["1. Item 1", "5. Item 2", "10. Item 3"]
        node, next_index = list_parser.parse_ordered_list(lines, 0)
        
        assert isinstance(node, Node)
        assert next_index == 3


class TestListItemParsing:
    """Test individual list item parsing"""

    def test_parse_list_item_simple(self):
        """Test parsing simple list item"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        
        item_node = list_parser._parse_list_item("Simple item text", {})
        assert isinstance(item_node, Node)

    def test_parse_list_item_with_keywords(self):
        """Test parsing list item with keywords"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        
        item_node = list_parser._parse_list_item(";;;太字;;; Text with keywords", {})
        assert isinstance(item_node, Node)

    def test_parse_list_item_empty(self):
        """Test parsing empty list item"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        
        item_node = list_parser._parse_list_item("", {})
        assert isinstance(item_node, Node)

    def test_parse_keyword_list_item(self):
        """Test parsing keyword list item"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        
        node = list_parser._parse_keyword_list_item(";;;太字;;; Bold text")
        assert isinstance(node, Node)

    def test_parse_keyword_list_item_no_keywords(self):
        """Test parsing list item without keywords"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        
        node = list_parser._parse_keyword_list_item("Normal text")
        assert isinstance(node, Node)


class TestListUtilities:
    """Test list utility methods"""

    def test_contains_list_true(self):
        """Test contains_list returns true for list content"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        
        content = "Some text\n- List item\nMore text"
        result = list_parser.contains_list(content)
        assert result is True

    def test_contains_list_false(self):
        """Test contains_list returns false for non-list content"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        
        content = "Just normal text\nAnother paragraph"
        result = list_parser.contains_list(content)
        assert result is False

    def test_extract_list_items_unordered(self):
        """Test extracting unordered list items"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        
        content = "- Item 1\n- Item 2\n- Item 3"
        items = list_parser.extract_list_items(content)
        assert isinstance(items, list)
        assert len(items) == 3

    def test_extract_list_items_ordered(self):
        """Test extracting ordered list items"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        
        content = "1. Item 1\n2. Item 2\n3. Item 3"
        items = list_parser.extract_list_items(content)
        assert isinstance(items, list)
        assert len(items) == 3

    def test_extract_list_items_mixed_content(self):
        """Test extracting list items from mixed content"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        
        content = "Paragraph\n- Item 1\n- Item 2\nAnother paragraph"
        items = list_parser.extract_list_items(content)
        assert isinstance(items, list)
        assert len(items) == 2

    def test_extract_list_items_no_lists(self):
        """Test extracting from content without lists"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        
        content = "Just normal paragraphs\nNo lists here"
        items = list_parser.extract_list_items(content)
        assert isinstance(items, list)
        assert len(items) == 0


class TestNestedListParser:
    """Test nested list parser"""

    def test_nested_list_parser_init(self):
        """Test nested list parser initialization"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        nested_parser = NestedListParser(list_parser)
        assert nested_parser.list_parser is list_parser

    def test_parse_nested_lists_simple(self):
        """Test parsing simple nested lists"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        nested_parser = NestedListParser(list_parser)
        
        lines = ["- Item 1", "  - Subitem 1", "- Item 2"]
        result = nested_parser.parse_nested_lists(lines)
        assert isinstance(result, list)

    def test_calculate_indent_level(self):
        """Test calculating indent level"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        nested_parser = NestedListParser(list_parser)
        
        assert nested_parser._calculate_indent_level("- Item") == 0
        assert nested_parser._calculate_indent_level("  - Item") == 2
        assert nested_parser._calculate_indent_level("    - Item") == 4

    def test_group_by_indent_level(self):
        """Test grouping by indent level"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        nested_parser = NestedListParser(list_parser)
        
        lines = ["- Item 1", "  - Subitem", "- Item 2"]
        groups = nested_parser._group_by_indent_level(lines)
        assert isinstance(groups, list)


class TestListValidator:
    """Test list validator"""

    def test_list_validator_init(self):
        """Test list validator initialization"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        validator = ListValidator(list_parser)
        assert validator.list_parser is list_parser

    def test_validate_list_structure_valid(self):
        """Test validating valid list structure"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        validator = ListValidator(list_parser)
        
        lines = ["- Item 1", "- Item 2", "- Item 3"]
        errors = validator.validate_list_structure(lines)
        assert isinstance(errors, list)

    def test_validate_list_structure_mixed(self):
        """Test validating mixed list structure"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        validator = ListValidator(list_parser)
        
        lines = ["- Item 1", "1. Item 2", "- Item 3"]
        errors = validator.validate_list_structure(lines)
        assert isinstance(errors, list)

    def test_validate_keyword_list_item(self):
        """Test validating keyword list item"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        validator = ListValidator(list_parser)
        
        errors = validator._validate_keyword_list_item(";;;太字;;; Valid item", 1)
        assert isinstance(errors, list)

    def test_validate_keyword_list_item_invalid(self):
        """Test validating invalid keyword list item"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        validator = ListValidator(list_parser)
        
        errors = validator._validate_keyword_list_item(";;;invalid;;; Invalid item", 1)
        assert isinstance(errors, list)


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_parse_list_from_middle(self):
        """Test parsing list starting from middle of lines"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        
        lines = ["Paragraph", "- Item 1", "- Item 2"]
        node, next_index = list_parser.parse_unordered_list(lines, 1)
        
        assert isinstance(node, Node)
        assert next_index == 3

    def test_parse_list_at_end(self):
        """Test parsing list at end of document"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        
        lines = ["- Item 1", "- Item 2"]
        node, next_index = list_parser.parse_unordered_list(lines, 0)
        
        assert isinstance(node, Node)
        assert next_index == 2

    def test_parse_empty_lines_array(self):
        """Test parsing with empty lines array"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        
        lines = []
        node, next_index = list_parser.parse_unordered_list(lines, 0)
        
        assert isinstance(node, Node)
        assert next_index == 0

    def test_parse_list_with_unicode(self):
        """Test parsing list with unicode content"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        
        lines = ["- 日本語アイテム", "- 絵文字 🚀", "- Special chars ♪♫"]
        node, next_index = list_parser.parse_unordered_list(lines, 0)
        
        assert isinstance(node, Node)
        assert next_index == 3

    def test_parse_list_with_very_long_items(self):
        """Test parsing list with very long items"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        
        long_item = "a" * 10000
        lines = [f"- {long_item}"]
        node, next_index = list_parser.parse_unordered_list(lines, 0)
        
        assert isinstance(node, Node)
        assert next_index == 1

    def test_list_detection_edge_cases(self):
        """Test list detection edge cases"""
        keyword_parser = KeywordParser()
        list_parser = ListParser(keyword_parser)
        
        # Almost list but not quite
        assert list_parser.is_list_line("-Not a list") == ""
        assert list_parser.is_list_line("1.Not a list") == ""
        assert list_parser.is_list_line("・Not a list") == ""
        
        # Valid lists with edge formatting
        assert list_parser.is_list_line("- ") != ""
        assert list_parser.is_list_line("1. ") != ""