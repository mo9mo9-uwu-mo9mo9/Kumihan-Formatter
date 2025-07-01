"""Comprehensive tests for keyword_parser.py module

Tests for Issue #351 - Phase 1 priority A (90%+ coverage target)
"""

import pytest
from typing import List, Dict, Any, Tuple

from kumihan_formatter.core.keyword_parser import KeywordParser, MarkerValidator
from kumihan_formatter.core.ast_nodes import Node


class TestKeywordParserInit:
    """Test keyword parser initialization"""

    def test_keyword_parser_init_default(self):
        """Test keyword parser initialization with default config"""
        parser = KeywordParser()
        assert parser.BLOCK_KEYWORDS is not None
        assert isinstance(parser.BLOCK_KEYWORDS, dict)
        assert len(parser.BLOCK_KEYWORDS) > 0
        # Check some default keywords exist
        assert "太字" in parser.BLOCK_KEYWORDS
        assert "イタリック" in parser.BLOCK_KEYWORDS
        assert "枠線" in parser.BLOCK_KEYWORDS

    def test_keyword_parser_init_with_config(self):
        """Test keyword parser initialization with config"""
        parser = KeywordParser(config={'test': 'value'})
        assert parser.BLOCK_KEYWORDS is not None
        assert isinstance(parser.BLOCK_KEYWORDS, dict)

    def test_default_keywords_structure(self):
        """Test that default keywords have proper structure"""
        parser = KeywordParser()
        for keyword, definition in parser.BLOCK_KEYWORDS.items():
            assert isinstance(keyword, str)
            assert isinstance(definition, dict)
            assert "tag" in definition
            assert isinstance(definition["tag"], str)


class TestNormalizeMarkerSyntax:
    """Test marker syntax normalization"""

    def test_normalize_full_width_spaces(self):
        """Test normalization of full-width spaces"""
        parser = KeywordParser()
        result = parser._normalize_marker_syntax("太字　イタリック")
        assert result == "太字 イタリック"

    def test_normalize_color_attribute(self):
        """Test normalization of color attribute"""
        parser = KeywordParser()
        result = parser._normalize_marker_syntax("ハイライトcolor=red")
        assert result == "ハイライト color=red"

    def test_normalize_alt_attribute(self):
        """Test normalization of alt attribute"""
        parser = KeywordParser()
        result = parser._normalize_marker_syntax("見出し1alt=title")
        assert result == "見出し1 alt=title"

    def test_normalize_multiple_spaces(self):
        """Test normalization of multiple spaces"""
        parser = KeywordParser()
        result = parser._normalize_marker_syntax("太字   イタリック    枠線")
        assert result == "太字 イタリック 枠線"

    def test_normalize_leading_trailing_spaces(self):
        """Test normalization of leading/trailing spaces"""
        parser = KeywordParser()
        result = parser._normalize_marker_syntax("  太字 イタリック  ")
        assert result == "太字 イタリック"

    def test_normalize_empty_string(self):
        """Test normalization of empty string"""
        parser = KeywordParser()
        result = parser._normalize_marker_syntax("")
        assert result == ""

    def test_normalize_complex_case(self):
        """Test normalization of complex case"""
        parser = KeywordParser()
        result = parser._normalize_marker_syntax("  太字　ハイライトcolor=bluealt=test  ")
        assert result == "太字 ハイライト color=blue alt=test"


class TestParseMarkerKeywords:
    """Test parsing marker keywords"""

    def test_parse_simple_keyword(self):
        """Test parsing simple keyword"""
        parser = KeywordParser()
        keywords, attributes, errors = parser.parse_marker_keywords("太字")
        assert keywords == ["太字"]
        assert attributes == {}
        assert errors == []

    def test_parse_multiple_keywords(self):
        """Test parsing multiple keywords"""
        parser = KeywordParser()
        keywords, attributes, errors = parser.parse_marker_keywords("太字+イタリック")
        assert "太字" in keywords
        assert "イタリック" in keywords
        assert attributes == {}
        assert errors == []

    def test_parse_keywords_with_color(self):
        """Test parsing keywords with color attribute"""
        parser = KeywordParser()
        keywords, attributes, errors = parser.parse_marker_keywords("ハイライト color=red")
        assert keywords == ["ハイライト"]
        assert attributes == {"color": "red"}
        assert errors == []

    def test_parse_keywords_with_alt(self):
        """Test parsing keywords with alt attribute"""
        parser = KeywordParser()
        keywords, attributes, errors = parser.parse_marker_keywords("見出し1 alt=title")
        assert keywords == ["見出し1"]
        assert attributes == {"alt": "title"}
        assert errors == []

    def test_parse_keywords_with_multiple_attributes(self):
        """Test parsing keywords with multiple attributes"""
        parser = KeywordParser()
        keywords, attributes, errors = parser.parse_marker_keywords("ハイライト color=blue alt=highlight")
        assert keywords == ["ハイライト"]
        assert attributes == {"color": "blue", "alt": "highlight"}
        assert errors == []

    def test_parse_complex_case(self):
        """Test parsing complex case"""
        parser = KeywordParser()
        keywords, attributes, errors = parser.parse_marker_keywords("太字+ハイライト color=green alt=test")
        assert "太字" in keywords
        assert "ハイライト" in keywords
        assert attributes == {"color": "green", "alt": "test"}
        assert errors == []

    def test_parse_empty_content(self):
        """Test parsing empty content"""
        parser = KeywordParser()
        keywords, attributes, errors = parser.parse_marker_keywords("")
        assert keywords == []
        assert attributes == {}
        assert errors == []


class TestValidateKeywords:
    """Test keyword validation"""

    def test_validate_valid_keywords(self):
        """Test validation of valid keywords"""
        parser = KeywordParser()
        valid, invalid = parser.validate_keywords(["太字", "イタリック"])
        assert valid == ["太字", "イタリック"]
        assert invalid == []

    def test_validate_invalid_keywords(self):
        """Test validation of invalid keywords"""
        parser = KeywordParser()
        valid, invalid = parser.validate_keywords(["invalid1", "invalid2"])
        assert valid == []
        assert len(invalid) == 2
        assert "invalid1" in invalid[0]
        assert "invalid2" in invalid[1]

    def test_validate_mixed_keywords(self):
        """Test validation of mixed valid/invalid keywords"""
        parser = KeywordParser()
        valid, invalid = parser.validate_keywords(["太字", "invalid", "イタリック"])
        assert valid == ["太字", "イタリック"]
        assert len(invalid) == 1
        assert "invalid" in invalid[0]

    def test_validate_empty_list(self):
        """Test validation of empty keyword list"""
        parser = KeywordParser()
        valid, invalid = parser.validate_keywords([])
        assert valid == []
        assert invalid == []

    def test_validate_duplicate_keywords(self):
        """Test validation with duplicate keywords"""
        parser = KeywordParser()
        valid, invalid = parser.validate_keywords(["太字", "太字", "イタリック"])
        assert "太字" in valid
        assert "イタリック" in valid
        assert invalid == []


class TestCreateSingleBlock:
    """Test creating single block nodes"""

    def test_create_single_block_basic(self):
        """Test creating basic single block"""
        parser = KeywordParser()
        node = parser.create_single_block("太字", "Test content", {})
        assert isinstance(node, Node)
        # Node type matches the keyword tag
        assert node.type in ["strong", "block"]

    def test_create_single_block_with_attributes(self):
        """Test creating single block with attributes"""
        parser = KeywordParser()
        attributes = {"color": "red", "alt": "test"}
        node = parser.create_single_block("ハイライト", "Test content", attributes)
        assert isinstance(node, Node)
        # Node type matches the keyword tag
        assert node.type in ["div", "block"]

    def test_create_single_block_empty_content(self):
        """Test creating single block with empty content"""
        parser = KeywordParser()
        node = parser.create_single_block("太字", "", {})
        assert isinstance(node, Node)
        # Node type matches the keyword tag
        assert node.type in ["strong", "block"]

    def test_create_single_block_invalid_keyword(self):
        """Test creating single block with invalid keyword"""
        parser = KeywordParser()
        node = parser.create_single_block("invalid", "Test content", {})
        # Should return error node or handle gracefully
        assert isinstance(node, Node)


class TestCreateCompoundBlock:
    """Test creating compound block nodes"""

    def test_create_compound_block_single_keyword(self):
        """Test creating compound block with single keyword"""
        parser = KeywordParser()
        node = parser.create_compound_block(["太字"], "Test content", {})
        assert isinstance(node, Node)

    def test_create_compound_block_multiple_keywords(self):
        """Test creating compound block with multiple keywords"""
        parser = KeywordParser()
        node = parser.create_compound_block(["太字", "イタリック"], "Test content", {})
        assert isinstance(node, Node)

    def test_create_compound_block_with_attributes(self):
        """Test creating compound block with attributes"""
        parser = KeywordParser()
        attributes = {"color": "blue"}
        node = parser.create_compound_block(["ハイライト"], "Test content", attributes)
        assert isinstance(node, Node)

    def test_create_compound_block_empty_keywords(self):
        """Test creating compound block with empty keywords"""
        parser = KeywordParser()
        node = parser.create_compound_block([], "Test content", {})
        assert isinstance(node, Node)

    def test_create_compound_block_complex_nesting(self):
        """Test creating compound block with complex nesting"""
        parser = KeywordParser()
        keywords = ["枠線", "太字", "イタリック"]
        node = parser.create_compound_block(keywords, "Test content", {})
        assert isinstance(node, Node)


class TestProcessInlineKeywords:
    """Test processing inline keywords"""

    def test_process_inline_simple(self):
        """Test processing simple inline keywords"""
        parser = KeywordParser()
        result = parser._process_inline_keywords("This is [太字:bold text] normal text")
        assert isinstance(result, str)
        assert "bold text" in result

    def test_process_inline_no_keywords(self):
        """Test processing text without inline keywords"""
        parser = KeywordParser()
        result = parser._process_inline_keywords("Normal text without keywords")
        assert result == "Normal text without keywords"

    def test_process_inline_multiple(self):
        """Test processing multiple inline keywords"""
        parser = KeywordParser()
        result = parser._process_inline_keywords("[太字:bold] and [イタリック:italic]")
        assert isinstance(result, str)

    def test_process_inline_empty_string(self):
        """Test processing empty string"""
        parser = KeywordParser()
        result = parser._process_inline_keywords("")
        assert result == ""

    def test_process_inline_malformed(self):
        """Test processing malformed inline keywords"""
        parser = KeywordParser()
        result = parser._process_inline_keywords("[太字:unclosed")
        assert isinstance(result, str)


class TestSortKeywordsByNestingOrder:
    """Test sorting keywords by nesting order"""

    def test_sort_simple_keywords(self):
        """Test sorting simple keywords"""
        parser = KeywordParser()
        keywords = ["太字", "イタリック"]
        sorted_keywords = parser._sort_keywords_by_nesting_order(keywords)
        assert isinstance(sorted_keywords, list)
        assert len(sorted_keywords) == 2

    def test_sort_complex_keywords(self):
        """Test sorting complex keywords"""
        parser = KeywordParser()
        keywords = ["太字", "枠線", "見出し1", "イタリック"]
        sorted_keywords = parser._sort_keywords_by_nesting_order(keywords)
        assert isinstance(sorted_keywords, list)
        assert len(sorted_keywords) == 4

    def test_sort_empty_list(self):
        """Test sorting empty keyword list"""
        parser = KeywordParser()
        sorted_keywords = parser._sort_keywords_by_nesting_order([])
        assert sorted_keywords == []

    def test_sort_single_keyword(self):
        """Test sorting single keyword"""
        parser = KeywordParser()
        sorted_keywords = parser._sort_keywords_by_nesting_order(["太字"])
        assert sorted_keywords == ["太字"]


class TestUtilityMethods:
    """Test utility methods"""

    def test_get_all_keywords(self):
        """Test getting all available keywords"""
        parser = KeywordParser()
        keywords = parser.get_all_keywords()
        assert isinstance(keywords, list)
        assert len(keywords) > 0
        assert "太字" in keywords
        assert "イタリック" in keywords

    def test_is_valid_keyword(self):
        """Test checking if keyword is valid"""
        parser = KeywordParser()
        assert parser.is_valid_keyword("太字") is True
        assert parser.is_valid_keyword("invalid") is False
        assert parser.is_valid_keyword("") is False

    def test_get_keyword_info(self):
        """Test getting keyword information"""
        parser = KeywordParser()
        info = parser.get_keyword_info("太字")
        assert info is not None
        assert isinstance(info, dict)
        assert "tag" in info

        # Test invalid keyword
        assert parser.get_keyword_info("invalid") is None

    def test_add_custom_keyword(self):
        """Test adding custom keyword"""
        parser = KeywordParser()
        initial_count = len(parser.get_all_keywords())
        
        parser.add_custom_keyword("custom", {"tag": "span", "class": "custom"})
        
        assert len(parser.get_all_keywords()) == initial_count + 1
        assert parser.is_valid_keyword("custom") is True
        assert parser.get_keyword_info("custom") is not None

    def test_remove_keyword(self):
        """Test removing keyword"""
        parser = KeywordParser()
        
        # Add a custom keyword first
        parser.add_custom_keyword("removeme", {"tag": "span"})
        assert parser.is_valid_keyword("removeme") is True
        
        # Remove it
        result = parser.remove_keyword("removeme")
        assert result is True
        assert parser.is_valid_keyword("removeme") is False
        
        # Try to remove non-existent keyword
        result = parser.remove_keyword("nonexistent")
        assert result is False


class TestMarkerValidator:
    """Test MarkerValidator class"""

    def test_marker_validator_init(self):
        """Test MarkerValidator initialization"""
        parser = KeywordParser()
        validator = MarkerValidator(parser)
        assert validator.keyword_parser is parser

    def test_validate_marker_line_valid(self):
        """Test validating valid marker line"""
        parser = KeywordParser()
        validator = MarkerValidator(parser)
        
        is_valid, errors = validator.validate_marker_line("《太字》")
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)

    def test_validate_marker_line_invalid(self):
        """Test validating invalid marker line"""
        parser = KeywordParser()
        validator = MarkerValidator(parser)
        
        is_valid, errors = validator.validate_marker_line("《invalid》")
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)

    def test_validate_marker_line_empty(self):
        """Test validating empty marker line"""
        parser = KeywordParser()
        validator = MarkerValidator(parser)
        
        is_valid, errors = validator.validate_marker_line("")
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)

    def test_validate_marker_line_malformed(self):
        """Test validating malformed marker line"""
        parser = KeywordParser()
        validator = MarkerValidator(parser)
        
        is_valid, errors = validator.validate_marker_line("《太字")
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_parse_marker_with_special_characters(self):
        """Test parsing marker with special characters"""
        parser = KeywordParser()
        keywords, attributes, errors = parser.parse_marker_keywords("太字 color=red123")
        assert isinstance(keywords, list)
        assert isinstance(attributes, dict)
        assert isinstance(errors, list)

    def test_parse_marker_with_unicode(self):
        """Test parsing marker with unicode characters"""
        parser = KeywordParser()
        keywords, attributes, errors = parser.parse_marker_keywords("太字 color=red")
        assert isinstance(keywords, list)
        assert isinstance(attributes, dict)
        assert isinstance(errors, list)

    def test_create_block_with_very_long_content(self):
        """Test creating block with very long content"""
        parser = KeywordParser()
        long_content = "a" * 10000
        node = parser.create_single_block("太字", long_content, {})
        assert isinstance(node, Node)

    def test_validate_very_long_keyword_list(self):
        """Test validating very long keyword list"""
        parser = KeywordParser()
        long_list = ["太字"] * 1000
        valid, invalid = parser.validate_keywords(long_list)
        assert isinstance(valid, list)
        assert isinstance(invalid, list)

    def test_process_inline_with_nested_brackets(self):
        """Test processing inline with nested brackets"""
        parser = KeywordParser()
        result = parser._process_inline_keywords("[太字:[nested brackets]]")
        assert isinstance(result, str)

    def test_normalize_with_mixed_encoding(self):
        """Test normalization with mixed encoding issues"""
        parser = KeywordParser()
        result = parser._normalize_marker_syntax("太字\u3000イタリック")  # Full-width space
        assert "太字 イタリック" in result