"""Tests for marker parser module

This module tests marker syntax parsing functionality including keyword parsing,
attribute extraction, and content normalization.
"""

from unittest.mock import Mock

import pytest

from kumihan_formatter.core.keyword_parsing.definitions import KeywordDefinitions
from kumihan_formatter.core.keyword_parsing.marker_parser import MarkerParser


class TestMarkerParser:
    """Test marker parser functionality"""

    def setup_method(self):
        """Set up test environment"""
        self.definitions = Mock(spec=KeywordDefinitions)
        self.parser = MarkerParser(self.definitions)

    def test_init(self):
        """Test marker parser initialization"""
        definitions = Mock(spec=KeywordDefinitions)
        parser = MarkerParser(definitions)
        assert isinstance(parser, MarkerParser)
        assert parser.definitions == definitions

    def test_normalize_marker_syntax_basic(self):
        """Test basic marker syntax normalization"""
        input_content = "decoration"
        result = self.parser.normalize_marker_syntax(input_content)
        assert result == "decoration"

    def test_normalize_marker_syntax_fullwidth_spaces(self):
        """Test normalization of fullwidth spaces"""
        input_content = "decoration　color=red"
        result = self.parser.normalize_marker_syntax(input_content)
        assert result == "decoration color=red"

    def test_normalize_marker_syntax_color_attribute_spacing(self):
        """Test normalization of color attribute spacing"""
        test_cases = [
            ("decorationcolor=red", "decoration color=red"),
            ("decoration+boldcolor=blue", "decoration+bold color=blue"),
            ("textcolor=#ff0000", "text color=#ff0000"),
        ]

        for input_text, expected in test_cases:
            result = self.parser.normalize_marker_syntax(input_text)
            assert result == expected

    def test_normalize_marker_syntax_alt_attribute_spacing(self):
        """Test normalization of alt attribute spacing"""
        test_cases = [
            ("imagealt=description", "image alt=description"),
            ("画像alt=説明文", "画像 alt=説明文"),
            ("photoalt=my photo", "photo alt=my photo"),
        ]

        for input_text, expected in test_cases:
            result = self.parser.normalize_marker_syntax(input_text)
            assert result == expected

    def test_normalize_marker_syntax_multiple_spaces(self):
        """Test normalization of multiple spaces"""
        input_content = "decoration    color=red     alt=description"
        result = self.parser.normalize_marker_syntax(input_content)
        assert result == "decoration color=red alt=description"

    def test_normalize_marker_syntax_leading_trailing_spaces(self):
        """Test normalization of leading and trailing spaces"""
        input_content = "   decoration color=red   "
        result = self.parser.normalize_marker_syntax(input_content)
        assert result == "decoration color=red"

    def test_normalize_marker_syntax_complex_case(self):
        """Test normalization of complex marker syntax"""
        input_content = "  decoration+bold　　color=#ff0000alt=test　image  "
        result = self.parser.normalize_marker_syntax(input_content)
        assert result == "decoration+bold color=#ff0000 alt=test image"

    def test_parse_marker_keywords_single_keyword(self):
        """Test parsing single keyword"""
        marker_content = "decoration"
        keywords, attributes, errors = self.parser.parse_marker_keywords(marker_content)

        assert keywords == ["decoration"]
        assert attributes == {}
        assert errors == []

    def test_parse_marker_keywords_compound_plus(self):
        """Test parsing compound keywords with plus"""
        marker_content = "decoration+bold+italic"
        keywords, attributes, errors = self.parser.parse_marker_keywords(marker_content)

        assert keywords == ["decoration", "bold", "italic"]
        assert attributes == {}
        assert errors == []

    def test_parse_marker_keywords_compound_fullwidth_plus(self):
        """Test parsing compound keywords with fullwidth plus"""
        marker_content = "decoration＋bold＋italic"
        keywords, attributes, errors = self.parser.parse_marker_keywords(marker_content)

        assert keywords == ["decoration", "bold", "italic"]
        assert attributes == {}
        assert errors == []

    def test_parse_marker_keywords_with_color_attribute(self):
        """Test parsing keywords with color attribute"""
        marker_content = "decoration color=red"
        keywords, attributes, errors = self.parser.parse_marker_keywords(marker_content)

        assert keywords == ["decoration"]
        assert attributes == {"color": "red"}
        assert errors == []

    def test_parse_marker_keywords_with_hex_color(self):
        """Test parsing keywords with hex color"""
        marker_content = "text color=#ff0000"
        keywords, attributes, errors = self.parser.parse_marker_keywords(marker_content)

        assert keywords == ["text"]
        assert attributes == {"color": "#ff0000"}
        assert errors == []

    def test_parse_marker_keywords_with_alt_attribute(self):
        """Test parsing keywords with alt attribute"""
        marker_content = "image alt=test description"
        keywords, attributes, errors = self.parser.parse_marker_keywords(marker_content)

        assert keywords == ["image"]
        assert attributes == {"alt": "test description"}
        assert errors == []

    def test_parse_marker_keywords_with_both_attributes(self):
        """Test parsing keywords with both color and alt attributes"""
        marker_content = "image color=blue alt=test image"
        keywords, attributes, errors = self.parser.parse_marker_keywords(marker_content)

        assert keywords == ["image"]
        assert attributes == {"color": "blue", "alt": "test image"}
        assert errors == []

    def test_parse_marker_keywords_compound_with_attributes(self):
        """Test parsing compound keywords with attributes"""
        marker_content = "decoration+bold color=#00ff00 alt=special content"
        keywords, attributes, errors = self.parser.parse_marker_keywords(marker_content)

        assert keywords == ["decoration", "bold"]
        assert attributes == {"color": "#00ff00", "alt": "special content"}
        assert errors == []

    def test_parse_marker_keywords_empty_content(self):
        """Test parsing empty marker content"""
        marker_content = ""
        keywords, attributes, errors = self.parser.parse_marker_keywords(marker_content)

        assert keywords == []
        assert attributes == {}
        assert errors == []

    def test_parse_marker_keywords_whitespace_only(self):
        """Test parsing whitespace-only marker content"""
        marker_content = "   \t   "
        keywords, attributes, errors = self.parser.parse_marker_keywords(marker_content)

        assert keywords == []
        assert attributes == {}
        assert errors == []

    def test_parse_marker_keywords_attributes_only(self):
        """Test parsing marker with only attributes"""
        marker_content = "color=red alt=description"
        keywords, attributes, errors = self.parser.parse_marker_keywords(marker_content)

        assert keywords == []
        assert attributes == {"color": "red", "alt": "description"}
        assert errors == []

    def test_extract_color_attribute_present(self):
        """Test extracting color attribute when present"""
        marker_content = "decoration color=blue other content"
        color, cleaned = self.parser.extract_color_attribute(marker_content)

        assert color == "blue"
        assert cleaned == "decoration other content"

    def test_extract_color_attribute_hex(self):
        """Test extracting hex color attribute"""
        marker_content = "text color=#ff0000 more text"
        color, cleaned = self.parser.extract_color_attribute(marker_content)

        assert color == "#ff0000"
        assert cleaned == "text more text"

    def test_extract_color_attribute_not_present(self):
        """Test extracting color attribute when not present"""
        marker_content = "decoration without color"
        color, cleaned = self.parser.extract_color_attribute(marker_content)

        assert color is None
        assert cleaned == "decoration without color"

    def test_extract_color_attribute_multiple_spaces(self):
        """Test extracting color attribute with multiple spaces"""
        marker_content = "decoration   color=green   other"
        color, cleaned = self.parser.extract_color_attribute(marker_content)

        assert color == "green"
        assert cleaned == "decoration   other"

    def test_extract_alt_attribute_present(self):
        """Test extracting alt attribute when present"""
        marker_content = "image alt=test description other content"
        alt, cleaned = self.parser.extract_alt_attribute(marker_content)

        assert alt == "test description other content"
        assert cleaned == "image"

    def test_extract_alt_attribute_not_present(self):
        """Test extracting alt attribute when not present"""
        marker_content = "image without alt"
        alt, cleaned = self.parser.extract_alt_attribute(marker_content)

        assert alt is None
        assert cleaned == "image without alt"

    def test_extract_alt_attribute_with_spaces(self):
        """Test extracting alt attribute with surrounding spaces"""
        marker_content = "image   alt=description with spaces"
        alt, cleaned = self.parser.extract_alt_attribute(marker_content)

        assert alt == "description with spaces"
        assert cleaned == "image"

    def test_split_compound_keywords_single(self):
        """Test splitting single keyword"""
        result = self.parser.split_compound_keywords("decoration")
        assert result == ["decoration"]

    def test_split_compound_keywords_plus(self):
        """Test splitting compound keywords with plus"""
        result = self.parser.split_compound_keywords("decoration+bold+italic")
        assert result == ["decoration", "bold", "italic"]

    def test_split_compound_keywords_fullwidth_plus(self):
        """Test splitting compound keywords with fullwidth plus"""
        result = self.parser.split_compound_keywords("decoration＋bold＋italic")
        assert result == ["decoration", "bold", "italic"]

    def test_split_compound_keywords_mixed_plus(self):
        """Test splitting compound keywords with mixed plus types"""
        result = self.parser.split_compound_keywords("decoration+bold＋italic")
        assert result == ["decoration", "bold", "italic"]

    def test_split_compound_keywords_with_spaces(self):
        """Test splitting compound keywords with spaces"""
        result = self.parser.split_compound_keywords("decoration + bold + italic")
        assert result == ["decoration", "bold", "italic"]

    def test_split_compound_keywords_empty_parts(self):
        """Test splitting compound keywords with empty parts"""
        result = self.parser.split_compound_keywords("decoration++bold")
        assert result == ["decoration", "bold"]

    def test_split_compound_keywords_empty_string(self):
        """Test splitting empty string"""
        result = self.parser.split_compound_keywords("")
        assert result == []

    def test_split_compound_keywords_whitespace_only(self):
        """Test splitting whitespace-only string"""
        result = self.parser.split_compound_keywords("   ")
        assert result == []

    def test_complex_marker_parsing_scenario(self):
        """Test complex marker parsing scenario"""
        marker_content = (
            "  decoration＋bold　color=#ff0000　alt=test image with spaces  "
        )
        keywords, attributes, errors = self.parser.parse_marker_keywords(marker_content)

        assert keywords == ["decoration", "bold"]
        assert attributes == {"color": "#ff0000", "alt": "test image with spaces"}
        assert errors == []

    def test_japanese_keywords(self):
        """Test parsing Japanese keywords"""
        marker_content = "見出し1＋装飾 color=red"
        keywords, attributes, errors = self.parser.parse_marker_keywords(marker_content)

        assert keywords == ["見出し1", "装飾"]
        assert attributes == {"color": "red"}
        assert errors == []

    def test_edge_case_only_plus_signs(self):
        """Test edge case with only plus signs"""
        marker_content = "+++"
        keywords, attributes, errors = self.parser.parse_marker_keywords(marker_content)

        assert keywords == []
        assert attributes == {}
        assert errors == []

    def test_edge_case_plus_with_attributes(self):
        """Test edge case with plus and attributes"""
        marker_content = "+ color=red +"
        keywords, attributes, errors = self.parser.parse_marker_keywords(marker_content)

        assert keywords == []
        assert attributes == {"color": "red"}
        assert errors == []

    def test_color_attribute_edge_cases(self):
        """Test color attribute edge cases"""
        test_cases = [
            ("text color=", ""),  # Empty color value
            (
                "text color=red color=blue",
                "red",
            ),  # Multiple color attributes - first one wins
            ("color=red text", "red"),  # Color at beginning
        ]

        for marker_content, expected_color in test_cases:
            color, _ = self.parser.extract_color_attribute(marker_content)
            if expected_color:
                assert color == expected_color
            else:
                assert color == "" or color is None

    def test_alt_attribute_edge_cases(self):
        """Test alt attribute edge cases"""
        test_cases = [
            ("image alt=", ""),  # Empty alt value
            ("alt=description", "description"),  # Alt at beginning
            ("image alt=desc1 alt=desc2", "desc1 alt=desc2"),  # Multiple alt patterns
        ]

        for marker_content, expected_pattern in test_cases:
            alt, _ = self.parser.extract_alt_attribute(marker_content)
            if expected_pattern:
                # Alt extraction takes everything after alt= until end
                assert alt is not None
                assert expected_pattern in alt or alt == expected_pattern
            else:
                assert alt == "" or alt is None


class TestMarkerParserIntegration:
    """Integration tests for marker parser"""

    def test_real_world_markers(self):
        """Test parsing real-world marker examples"""
        definitions = KeywordDefinitions()
        parser = MarkerParser(definitions)

        real_world_cases = [
            "見出し1",
            "装飾 color=red",
            "画像 alt=サンプル画像",
            "強調＋太字 color=#ff0000",
            "引用+斜体　color=blue alt=引用文",
        ]

        for marker in real_world_cases:
            keywords, attributes, errors = parser.parse_marker_keywords(marker)

            # Should parse without errors
            assert isinstance(keywords, list)
            assert isinstance(attributes, dict)
            assert isinstance(errors, list)

            # Should have at least some meaningful output
            assert len(keywords) > 0 or len(attributes) > 0

    def test_parser_consistency(self):
        """Test that parser produces consistent results"""
        definitions = KeywordDefinitions()
        parser = MarkerParser(definitions)

        marker_content = "decoration+bold color=red alt=test"

        # Parse the same content multiple times
        results = []
        for _ in range(3):
            result = parser.parse_marker_keywords(marker_content)
            results.append(result)

        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result == first_result

    def test_normalization_preserves_meaning(self):
        """Test that normalization preserves semantic meaning"""
        definitions = KeywordDefinitions()
        parser = MarkerParser(definitions)

        # Test various ways to write the same thing
        equivalent_markers = [
            "decoration color=red",
            "decoration　color=red",
            "decorationcolor=red",
            "  decoration   color=red  ",
        ]

        results = []
        for marker in equivalent_markers:
            result = parser.parse_marker_keywords(marker)
            results.append(result)

        # All should produce the same result
        first_result = results[0]
        for result in results[1:]:
            assert result[0] == first_result[0]  # Same keywords
            assert result[1] == first_result[1]  # Same attributes
