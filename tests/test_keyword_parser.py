"""Tests for keyword parser module

This module tests keyword parsing functionality including keyword validation,
block creation, and compound keyword handling.
"""

from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.ast_nodes import Node
from kumihan_formatter.core.keyword_parser import KeywordParser, MarkerValidator


class TestKeywordParser:
    """Test keyword parser functionality"""

    def setup_method(self):
        """Set up test environment"""
        self.parser = KeywordParser()

    def test_init_without_config(self):
        """Test keyword parser initialization without config"""
        parser = KeywordParser()
        assert isinstance(parser, KeywordParser)
        assert parser.definitions is not None
        assert parser.marker_parser is not None
        assert parser.validator is not None
        assert parser.BLOCK_KEYWORDS is not None

    def test_init_with_config(self):
        """Test keyword parser initialization with config"""
        config = {"test": "value"}
        parser = KeywordParser(config)
        assert isinstance(parser, KeywordParser)

    def test_default_block_keywords(self):
        """Test default block keywords are properly defined"""
        expected_keywords = [
            "太字",
            "イタリック",
            "枠線",
            "ハイライト",
            "見出し1",
            "見出し2",
            "見出し3",
            "見出し4",
            "見出し5",
            "折りたたみ",
            "ネタバレ",
        ]

        for keyword in expected_keywords:
            assert keyword in self.parser.DEFAULT_BLOCK_KEYWORDS
            assert "tag" in self.parser.DEFAULT_BLOCK_KEYWORDS[keyword]

    def test_nesting_order_defined(self):
        """Test nesting order is properly defined"""
        expected_tags = ["details", "div", "h1", "h2", "h3", "h4", "h5", "strong", "em"]

        assert self.parser.NESTING_ORDER == expected_tags

    def test_normalize_marker_syntax_delegation(self):
        """Test that normalize_marker_syntax delegates to marker_parser"""
        test_input = "decoration color=red"

        with patch.object(
            self.parser.marker_parser, "normalize_marker_syntax"
        ) as mock_normalize:
            mock_normalize.return_value = "decoration color=red"

            result = self.parser._normalize_marker_syntax(test_input)

            mock_normalize.assert_called_once_with(test_input)
            assert result == "decoration color=red"

    def test_parse_marker_keywords_delegation(self):
        """Test that parse_marker_keywords delegates to marker_parser"""
        test_input = "decoration+bold color=red"
        expected_result = (["decoration", "bold"], {"color": "red"}, [])

        with patch.object(
            self.parser.marker_parser, "parse_marker_keywords"
        ) as mock_parse:
            mock_parse.return_value = expected_result

            result = self.parser.parse_marker_keywords(test_input)

            mock_parse.assert_called_once_with(test_input)
            assert result == expected_result

    def test_validate_keywords_delegation(self):
        """Test that validate_keywords delegates to validator"""
        test_keywords = ["decoration", "invalid"]
        expected_result = (["decoration"], ["Invalid keyword: invalid"])

        with patch.object(self.parser.validator, "validate_keywords") as mock_validate:
            mock_validate.return_value = expected_result

            result = self.parser.validate_keywords(test_keywords)

            mock_validate.assert_called_once_with(test_keywords)
            assert result == expected_result

    def test_get_keyword_suggestions_delegation(self):
        """Test that _get_keyword_suggestions delegates to validator"""
        test_keyword = "invalid"
        expected_result = ["太字", "枠線", "見出し1"]

        with patch.object(
            self.parser.validator, "get_keyword_suggestions"
        ) as mock_suggest:
            mock_suggest.return_value = expected_result

            result = self.parser._get_keyword_suggestions(test_keyword)

            mock_suggest.assert_called_once_with(test_keyword, 3)
            assert result == expected_result

    def test_create_single_block_valid_keyword(self):
        """Test creating single block with valid keyword"""
        keyword = "太字"
        content = "Bold text content"
        attributes = {}

        result = self.parser.create_single_block(keyword, content, attributes)

        assert isinstance(result, Node)
        assert result.type == "strong"

    def test_create_single_block_invalid_keyword(self):
        """Test creating single block with invalid keyword"""
        keyword = "invalid_keyword"
        content = "Some content"
        attributes = {}

        result = self.parser.create_single_block(keyword, content, attributes)

        assert isinstance(result, Node)
        assert result.type == "error"

    def test_create_single_block_empty_content(self):
        """Test creating single block with empty content"""
        keyword = "太字"
        content = ""
        attributes = {}

        result = self.parser.create_single_block(keyword, content, attributes)

        assert isinstance(result, Node)
        assert result.type == "strong"

    def test_create_single_block_with_class(self):
        """Test creating single block with class attribute"""
        keyword = "枠線"
        content = "Boxed content"
        attributes = {}

        result = self.parser.create_single_block(keyword, content, attributes)

        assert isinstance(result, Node)
        assert result.type == "div"
        assert hasattr(result, "css_class")

    def test_create_single_block_with_summary(self):
        """Test creating single block with summary attribute"""
        keyword = "折りたたみ"
        content = "Collapsible content"
        attributes = {}

        result = self.parser.create_single_block(keyword, content, attributes)

        assert isinstance(result, Node)
        assert result.type == "details"

    def test_create_single_block_highlight_with_color(self):
        """Test creating highlight block with color attribute"""
        keyword = "ハイライト"
        content = "Highlighted text"
        attributes = {"color": "red"}

        result = self.parser.create_single_block(keyword, content, attributes)

        assert isinstance(result, Node)
        assert result.type == "div"

    def test_create_single_block_highlight_with_hex_color(self):
        """Test creating highlight block with hex color"""
        keyword = "ハイライト"
        content = "Highlighted text"
        attributes = {"color": "#ff0000"}

        result = self.parser.create_single_block(keyword, content, attributes)

        assert isinstance(result, Node)
        assert result.type == "div"

    def test_create_single_block_with_custom_attributes(self):
        """Test creating single block with custom attributes"""
        keyword = "太字"
        content = "Bold text"
        attributes = {"id": "custom-id", "data-test": "value"}

        result = self.parser.create_single_block(keyword, content, attributes)

        assert isinstance(result, Node)
        assert result.type == "strong"

    def test_create_compound_block_empty_keywords(self):
        """Test creating compound block with empty keywords"""
        keywords = []
        content = "Some content"
        attributes = {}

        result = self.parser.create_compound_block(keywords, content, attributes)

        assert isinstance(result, Node)
        assert result.type == "error"

    def test_create_compound_block_invalid_keywords(self):
        """Test creating compound block with invalid keywords"""
        keywords = ["invalid", "also_invalid"]
        content = "Some content"
        attributes = {}

        with patch.object(self.parser, "validate_keywords") as mock_validate:
            mock_validate.return_value = ([], ["Invalid keywords"])

            result = self.parser.create_compound_block(keywords, content, attributes)

            assert isinstance(result, Node)
            assert result.type == "error"

    def test_create_compound_block_valid_keywords(self):
        """Test creating compound block with valid keywords"""
        keywords = ["枠線", "太字"]
        content = "Nested content"
        attributes = {}

        with patch.object(self.parser, "validate_keywords") as mock_validate:
            mock_validate.return_value = (keywords, [])

            result = self.parser.create_compound_block(keywords, content, attributes)

            assert isinstance(result, Node)
            # Should create nested structure with outer div and inner strong

    def test_create_compound_block_with_attributes(self):
        """Test creating compound block with attributes"""
        keywords = ["ハイライト", "太字"]
        content = "Highlighted bold text"
        attributes = {"color": "blue", "id": "test-id"}

        with patch.object(self.parser, "validate_keywords") as mock_validate:
            mock_validate.return_value = (keywords, [])

            result = self.parser.create_compound_block(keywords, content, attributes)

            assert isinstance(result, Node)

    def test_parse_block_content_empty(self):
        """Test parsing empty block content"""
        content = ""
        result = self.parser._parse_block_content(content)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == ""

    def test_parse_block_content_whitespace_only(self):
        """Test parsing whitespace-only block content"""
        content = "   \t   "
        result = self.parser._parse_block_content(content)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == ""

    def test_parse_block_content_normal_text(self):
        """Test parsing normal text content"""
        content = "This is normal text content."
        result = self.parser._parse_block_content(content)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == content

    def test_process_inline_keywords(self):
        """Test processing inline keywords"""
        content = "Text with inline keywords"
        result = self.parser._process_inline_keywords(content)

        # Currently just returns the content as-is
        assert result == content

    def test_sort_keywords_by_nesting_order(self):
        """Test sorting keywords by nesting order"""
        keywords = ["太字", "枠線", "見出し1"]
        result = self.parser._sort_keywords_by_nesting_order(keywords)

        # Should sort by nesting order: div (枠線), h1 (見出し1), strong (太字)
        expected_order = ["枠線", "見出し1", "太字"]
        assert result == expected_order

    def test_sort_keywords_by_nesting_order_unknown_keywords(self):
        """Test sorting with unknown keywords"""
        keywords = ["太字", "unknown_keyword"]

        # Mock BLOCK_KEYWORDS to include only known keywords
        with patch.object(
            self.parser, "BLOCK_KEYWORDS", self.parser.DEFAULT_BLOCK_KEYWORDS
        ):
            result = self.parser._sort_keywords_by_nesting_order(keywords)

            # Known keywords should come first, unknown last
            assert "太字" in result
            assert "unknown_keyword" in result

    def test_sort_keywords_by_nesting_order_empty_list(self):
        """Test sorting empty keyword list"""
        keywords = []
        result = self.parser._sort_keywords_by_nesting_order(keywords)

        assert result == []

    def test_heading_keywords_mapping(self):
        """Test that heading keywords map to correct tags"""
        heading_keywords = ["見出し1", "見出し2", "見出し3", "見出し4", "見出し5"]
        expected_tags = ["h1", "h2", "h3", "h4", "h5"]

        for keyword, expected_tag in zip(heading_keywords, expected_tags):
            block_def = self.parser.DEFAULT_BLOCK_KEYWORDS[keyword]
            assert block_def["tag"] == expected_tag

    def test_details_keywords_have_summary(self):
        """Test that details keywords have summary attribute"""
        details_keywords = ["折りたたみ", "ネタバレ"]

        for keyword in details_keywords:
            block_def = self.parser.DEFAULT_BLOCK_KEYWORDS[keyword]
            assert block_def["tag"] == "details"
            assert "summary" in block_def

    def test_styled_keywords_have_class(self):
        """Test that styled keywords have class attribute"""
        styled_keywords = ["枠線", "ハイライト"]

        for keyword in styled_keywords:
            block_def = self.parser.DEFAULT_BLOCK_KEYWORDS[keyword]
            assert "class" in block_def


class TestMarkerValidator:
    """Test marker validator functionality"""

    def test_validate_marker_line_valid(self):
        """Test validating valid marker line"""
        valid_lines = [
            ";;;decoration;;;",
            ";;;keyword;;;",
            ";;; spaced ;;;",
            ";;;complex+keyword color=red;;;",
        ]

        for line in valid_lines:
            is_valid, warnings = MarkerValidator.validate_marker_line(line)
            assert is_valid, f"Failed for line: {line}"
            assert len(warnings) == 0

    def test_validate_marker_line_invalid(self):
        """Test validating invalid marker line"""
        invalid_lines = [
            "decoration",
            ";;;missing end",
            "missing start;;;",
            "no markers at all",
            "",
        ]

        for line in invalid_lines:
            is_valid, warnings = MarkerValidator.validate_marker_line(line)
            assert not is_valid, f"Should be invalid: {line}"
            assert len(warnings) > 0

    def test_validate_block_structure_valid(self):
        """Test validating valid block structure"""
        lines = [
            ";;;decoration;;;",
            "Content line 1",
            "Content line 2",
            ";;;",
        ]

        is_valid, end_index, warnings = MarkerValidator.validate_block_structure(
            lines, 0
        )

        assert is_valid
        assert end_index == 3
        assert len(warnings) == 0

    def test_validate_block_structure_missing_end(self):
        """Test validating block structure with missing end marker"""
        lines = [
            ";;;decoration;;;",
            "Content line 1",
            "Content line 2",
        ]

        is_valid, end_index, warnings = MarkerValidator.validate_block_structure(
            lines, 0
        )

        assert not is_valid
        assert end_index is None
        assert len(warnings) > 0
        assert "終了マーカー" in warnings[0]

    def test_validate_block_structure_immediate_end(self):
        """Test validating block structure with immediate end marker"""
        lines = [
            ";;;decoration;;;",
            ";;;",
        ]

        is_valid, end_index, warnings = MarkerValidator.validate_block_structure(
            lines, 0
        )

        assert is_valid
        assert end_index == 1
        assert len(warnings) == 0

    def test_validate_block_structure_nested_markers(self):
        """Test validating block structure with nested markers"""
        lines = [
            ";;;outer;;;",
            "Content",
            ";;;inner;;;",
            "Nested content",
            ";;;",
            "More content",
            ";;;",
        ]

        is_valid, end_index, warnings = MarkerValidator.validate_block_structure(
            lines, 0
        )

        # Should find the first closing marker
        assert is_valid
        assert end_index == 4

    def test_validate_block_structure_empty_lines(self):
        """Test validating block structure with empty lines"""
        lines = []

        is_valid, end_index, warnings = MarkerValidator.validate_block_structure(
            lines, 0
        )

        assert not is_valid
        assert end_index is None
        assert len(warnings) > 0


class TestKeywordParserIntegration:
    """Integration tests for keyword parser"""

    def test_full_parsing_workflow(self):
        """Test full parsing workflow from marker to node"""
        parser = KeywordParser()

        # Test single keyword workflow
        marker_content = "太字"
        keywords, attributes, errors = parser.parse_marker_keywords(marker_content)

        assert keywords == ["太字"]
        assert attributes == {}
        assert errors == []

        # Create block from parsed keywords
        if len(keywords) == 1:
            node = parser.create_single_block(keywords[0], "Bold content", attributes)
        else:
            node = parser.create_compound_block(keywords, "Bold content", attributes)

        assert isinstance(node, Node)
        assert node.type == "strong"

    def test_compound_keyword_workflow(self):
        """Test compound keyword workflow"""
        parser = KeywordParser()

        marker_content = "枠線+太字"
        keywords, attributes, errors = parser.parse_marker_keywords(marker_content)

        # Assuming successful parsing
        if not errors:
            node = parser.create_compound_block(keywords, "Nested content", attributes)
            assert isinstance(node, Node)

    def test_error_handling_workflow(self):
        """Test error handling throughout the workflow"""
        parser = KeywordParser()

        # Test with invalid keyword
        marker_content = "invalid_keyword"
        keywords, attributes, errors = parser.parse_marker_keywords(marker_content)

        if keywords:
            node = parser.create_single_block(keywords[0], "Content", attributes)
            # Should create error node for invalid keyword
            assert isinstance(node, Node)

    def test_complex_marker_parsing(self):
        """Test parsing complex marker with attributes"""
        parser = KeywordParser()

        marker_content = "ハイライト+太字 color=#ff0000 id=test"
        keywords, attributes, errors = parser.parse_marker_keywords(marker_content)

        if not errors:
            node = parser.create_compound_block(keywords, "Complex content", attributes)
            assert isinstance(node, Node)

    def test_parser_consistency_across_calls(self):
        """Test that parser produces consistent results across multiple calls"""
        parser = KeywordParser()

        marker_content = "太字"
        content = "Test content"
        attributes = {}

        # Create same block multiple times
        results = []
        for _ in range(3):
            node = parser.create_single_block(marker_content, content, attributes)
            results.append(node.type)

        # All results should be the same
        assert all(result == results[0] for result in results)

    def test_backward_compatibility(self):
        """Test backward compatibility of delegated methods"""
        parser = KeywordParser()

        # Test that all delegated methods work
        normalized = parser._normalize_marker_syntax("test content")
        assert isinstance(normalized, str)

        keywords, attrs, errs = parser.parse_marker_keywords("太字")
        assert isinstance(keywords, list)
        assert isinstance(attrs, dict)
        assert isinstance(errs, list)

        valid, invalid = parser.validate_keywords(["太字", "invalid"])
        assert isinstance(valid, list)
        assert isinstance(invalid, list)

        suggestions = parser._get_keyword_suggestions("invalid")
        assert isinstance(suggestions, list)
