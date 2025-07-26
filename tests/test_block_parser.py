"""Tests for block parser module

This module tests block-level element parsing functionality including
block markers, paragraphs, and special content handling.
"""

from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.ast_nodes import Node
from kumihan_formatter.core.block_parser.block_parser import BlockParser
from kumihan_formatter.core.keyword_parser import KeywordParser, MarkerValidator


class TestBlockParser:
    """Test block parser functionality"""

    def setup_method(self):
        """Set up test environment"""
        self.keyword_parser = Mock(spec=KeywordParser)
        self.parser = BlockParser(self.keyword_parser)

    def test_init(self):
        """Test block parser initialization"""
        keyword_parser = Mock(spec=KeywordParser)
        parser = BlockParser(keyword_parser)

        assert isinstance(parser, BlockParser)
        assert parser.keyword_parser == keyword_parser
        assert isinstance(parser.marker_validator, MarkerValidator)
        assert parser.heading_counter == 0

    def test_parse_block_marker_boundary_conditions(self):
        """Test parsing block marker with boundary conditions"""
        lines = [";;;decoration;;;", "content", ";;;"]

        # Test with index beyond lines length
        result, next_index = self.parser.parse_block_marker(lines, 10)
        assert result is None
        assert next_index == 10

    def test_parse_block_marker_invalid_marker(self):
        """Test parsing invalid block marker"""
        lines = [";;;invalid", "content", ";;;"]

        with patch.object(
            self.parser.marker_validator, "validate_marker_line"
        ) as mock_validate:
            mock_validate.return_value = (False, ["Invalid marker format"])

            result, next_index = self.parser.parse_block_marker(lines, 0)

            assert result is not None
            assert result.type == "error"
            assert next_index == 1

    def test_parse_block_marker_toc_marker(self):
        """Test parsing TOC marker"""
        lines = [";;;目次;;;"]

        with patch.object(
            self.parser.marker_validator, "validate_marker_line"
        ) as mock_validate:
            mock_validate.return_value = (True, [])

            result, next_index = self.parser.parse_block_marker(lines, 0)

            assert result is not None
            assert result.type == "toc"
            assert next_index == 1

    def test_parse_block_marker_image_marker(self):
        """Test parsing image marker"""
        lines = [";;;画像;;;", "image.png", ";;;"]

        with patch.object(
            self.parser.marker_validator, "validate_marker_line"
        ) as mock_validate:
            with patch(
                "kumihan_formatter.core.block_parser.block_parser.ImageBlockParser"
            ) as mock_image_parser_class:
                mock_validate.return_value = (True, [])

                mock_image_parser = Mock()
                mock_image_node = Mock(spec=Node)
                mock_image_node.type = "image"
                mock_image_parser.parse_image_block.return_value = (mock_image_node, 3)
                mock_image_parser_class.return_value = mock_image_parser

                result, next_index = self.parser.parse_block_marker(lines, 0)

                assert result.type == "image"
                assert next_index == 3
                mock_image_parser.parse_image_block.assert_called_once_with(lines, 0)

    def test_parse_block_marker_simple_image_filename(self):
        """Test parsing simple image filename marker"""
        lines = [";;;image.png;;;"]

        with patch.object(
            self.parser.marker_validator, "validate_marker_line"
        ) as mock_validate:
            with patch(
                "kumihan_formatter.core.block_parser.block_parser.ImageBlockParser"
            ) as mock_image_parser_class:
                mock_validate.return_value = (True, [])

                mock_image_parser = Mock()
                mock_image_node = Mock(spec=Node)
                mock_image_node.type = "image"
                mock_image_parser.parse_image_block.return_value = (mock_image_node, 1)
                mock_image_parser_class.return_value = mock_image_parser

                result, next_index = self.parser.parse_block_marker(lines, 0)

                assert result.type == "image"
                assert next_index == 1

    def test_parse_block_marker_invalid_block_structure(self):
        """Test parsing block with invalid structure"""
        lines = [";;;decoration;;;", "content"]  # Missing closing marker

        with patch.object(
            self.parser.marker_validator, "validate_marker_line"
        ) as mock_validate_line:
            with patch.object(
                self.parser.marker_validator, "validate_block_structure"
            ) as mock_validate_block:
                mock_validate_line.return_value = (True, [])
                mock_validate_block.return_value = (
                    False,
                    None,
                    ["Missing closing marker"],
                )

                result, next_index = self.parser.parse_block_marker(lines, 0)

                assert result is not None
                assert result.type == "error"
                assert next_index == 1

    def test_parse_block_marker_empty_marker(self):
        """Test parsing empty marker"""
        lines = [";;;", "content", ";;;"]

        with patch.object(
            self.parser.marker_validator, "validate_marker_line"
        ) as mock_validate_line:
            with patch.object(
                self.parser.marker_validator, "validate_block_structure"
            ) as mock_validate_block:
                mock_validate_line.return_value = (True, [])
                mock_validate_block.return_value = (True, 2, [])

                result, next_index = self.parser.parse_block_marker(lines, 0)

                assert result is not None
                assert result.type == "paragraph"
                assert next_index == 3

    def test_parse_block_marker_single_keyword(self):
        """Test parsing block with single keyword"""
        lines = [";;;decoration;;;", "content", ";;;"]

        with patch.object(
            self.parser.marker_validator, "validate_marker_line"
        ) as mock_validate_line:
            with patch.object(
                self.parser.marker_validator, "validate_block_structure"
            ) as mock_validate_block:
                mock_validate_line.return_value = (True, [])
                mock_validate_block.return_value = (True, 2, [])

                # Mock keyword parser
                self.keyword_parser.parse_marker_keywords.return_value = (
                    ["decoration"],
                    {},
                    [],
                )
                mock_node = Mock(spec=Node)
                mock_node.type = "block"
                self.keyword_parser.create_single_block.return_value = mock_node

                result, next_index = self.parser.parse_block_marker(lines, 0)

                assert result.type == "block"
                assert next_index == 3
                self.keyword_parser.create_single_block.assert_called_once()

    def test_parse_block_marker_compound_keywords(self):
        """Test parsing block with compound keywords"""
        lines = [";;;decoration+bold;;;", "content", ";;;"]

        with patch.object(
            self.parser.marker_validator, "validate_marker_line"
        ) as mock_validate_line:
            with patch.object(
                self.parser.marker_validator, "validate_block_structure"
            ) as mock_validate_block:
                mock_validate_line.return_value = (True, [])
                mock_validate_block.return_value = (True, 2, [])

                # Mock keyword parser
                self.keyword_parser.parse_marker_keywords.return_value = (
                    ["decoration", "bold"],
                    {},
                    [],
                )
                mock_node = Mock(spec=Node)
                mock_node.type = "compound"
                self.keyword_parser.create_compound_block.return_value = mock_node

                result, next_index = self.parser.parse_block_marker(lines, 0)

                assert result.type == "compound"
                assert next_index == 3
                self.keyword_parser.create_compound_block.assert_called_once()

    def test_parse_block_marker_heading_with_id(self):
        """Test parsing heading block with ID assignment"""
        lines = [";;;見出し1;;;", "Chapter Title", ";;;"]

        with patch.object(
            self.parser.marker_validator, "validate_marker_line"
        ) as mock_validate_line:
            with patch.object(
                self.parser.marker_validator, "validate_block_structure"
            ) as mock_validate_block:
                mock_validate_line.return_value = (True, [])
                mock_validate_block.return_value = (True, 2, [])

                # Mock keyword parser
                self.keyword_parser.parse_marker_keywords.return_value = (
                    ["見出し1"],
                    {},
                    [],
                )
                mock_node = Mock(spec=Node)
                mock_node.type = "heading"
                mock_node.add_attribute = Mock()
                self.keyword_parser.create_single_block.return_value = mock_node

                result, next_index = self.parser.parse_block_marker(lines, 0)

                assert result.type == "heading"
                assert self.parser.heading_counter == 1
                mock_node.add_attribute.assert_called_once_with("id", "heading-1")

    def test_parse_block_marker_parse_errors(self):
        """Test parsing block with keyword parse errors"""
        lines = [";;;invalid-keyword;;;", "content", ";;;"]

        with patch.object(
            self.parser.marker_validator, "validate_marker_line"
        ) as mock_validate_line:
            with patch.object(
                self.parser.marker_validator, "validate_block_structure"
            ) as mock_validate_block:
                mock_validate_line.return_value = (True, [])
                mock_validate_block.return_value = (True, 2, [])

                # Mock keyword parser with errors
                self.keyword_parser.parse_marker_keywords.return_value = (
                    [],
                    {},
                    ["Invalid keyword"],
                )

                result, next_index = self.parser.parse_block_marker(lines, 0)

                assert result is not None
                assert result.type == "error"
                assert next_index == 3

    def test_is_simple_image_marker_various_extensions(self):
        """Test detection of simple image markers with various extensions"""
        test_cases = [
            (";;;image.png;;;", True),
            (";;;photo.jpg;;;", True),
            (";;;picture.jpeg;;;", True),
            (";;;animation.gif;;;", True),
            (";;;modern.webp;;;", True),
            (";;;vector.svg;;;", True),
            (";;;document.pdf;;;", False),
            (";;;text.txt;;;", False),
            (";;;", False),
            (";;;filename;;;", False),
        ]

        for line, expected in test_cases:
            result = self.parser._is_simple_image_marker(line)
            assert result == expected, f"Failed for {line}"

    def test_is_simple_image_marker_edge_cases(self):
        """Test edge cases for simple image marker detection"""
        edge_cases = [
            ("image.png", False),  # No markers
            (";;;image.png", False),  # Missing closing marker
            ("image.png;;;", False),  # Missing opening marker
            (";;;;;;;", False),  # Too many markers
            (";;; ;;;", False),  # Empty content
            (";;;image.PNG;;;", True),  # Uppercase extension
        ]

        for line, expected in edge_cases:
            result = self.parser._is_simple_image_marker(line)
            assert result == expected, f"Failed for {line}"

    def test_parse_paragraph_simple(self):
        """Test parsing simple paragraph"""
        lines = ["This is a paragraph.", "More content.", ""]

        result, next_index = self.parser.parse_paragraph(lines, 0)

        assert result is not None
        assert result.type == "paragraph"
        assert next_index == 2

    def test_parse_paragraph_single_line(self):
        """Test parsing single line paragraph"""
        lines = ["Single line.", ""]

        result, next_index = self.parser.parse_paragraph(lines, 0)

        assert result is not None
        assert result.type == "paragraph"
        assert next_index == 1

    def test_parse_paragraph_stops_at_list(self):
        """Test paragraph parsing stops at list items"""
        lines = ["Paragraph content.", "- List item", "More list"]

        result, next_index = self.parser.parse_paragraph(lines, 0)

        assert result is not None
        assert result.type == "paragraph"
        assert next_index == 1

    def test_parse_paragraph_stops_at_ordered_list(self):
        """Test paragraph parsing stops at ordered list"""
        lines = ["Paragraph content.", "1. First item", "2. Second item"]

        result, next_index = self.parser.parse_paragraph(lines, 0)

        assert result is not None
        assert result.type == "paragraph"
        assert next_index == 1

    def test_parse_paragraph_stops_at_block_marker(self):
        """Test paragraph parsing stops at block markers"""
        lines = ["Paragraph content.", ";;;decoration;;;", "Block content"]

        result, next_index = self.parser.parse_paragraph(lines, 0)

        assert result is not None
        assert result.type == "paragraph"
        assert next_index == 1

    def test_parse_paragraph_empty_start(self):
        """Test paragraph parsing with empty starting line"""
        lines = ["", "Content line"]

        result, next_index = self.parser.parse_paragraph(lines, 0)

        assert result is None
        assert next_index == 0

    def test_parse_paragraph_joins_lines_with_space(self):
        """Test that paragraph joins lines with spaces"""
        lines = ["First line.", "Second line.", "Third line."]

        result, next_index = self.parser.parse_paragraph(lines, 0)

        assert result is not None
        assert "First line. Second line. Third line." in str(result.content)

    def test_is_block_marker_line(self):
        """Test block marker line detection"""
        test_cases = [
            (";;;decoration;;;", True),
            (";;;", True),
            (";;;keyword", True),
            ("text ;;;", False),
            (";;; text", False),
            ("regular text", False),
            ("", False),
        ]

        for line, expected in test_cases:
            result = self.parser.is_block_marker_line(line)
            assert result == expected, f"Failed for '{line}'"

    def test_is_opening_marker(self):
        """Test opening marker detection"""
        test_cases = [
            (";;;decoration", True),
            (";;;keyword;;;", False),  # Single-line marker
            (";;;", False),  # Closing marker
            ("text;;;", False),
            (";;;decoration text", True),
            ("   ;;;keyword   ", True),
        ]

        for line, expected in test_cases:
            result = self.parser.is_opening_marker(line)
            assert result == expected, f"Failed for '{line}'"

    def test_is_closing_marker(self):
        """Test closing marker detection"""
        test_cases = [
            (";;;", True),
            ("   ;;;   ", True),
            (";;;keyword", False),
            (";;;decoration;;;", False),
            ("text", False),
        ]

        for line, expected in test_cases:
            result = self.parser.is_closing_marker(line)
            assert result == expected, f"Failed for '{line}'"

    def test_skip_empty_lines(self):
        """Test skipping empty lines"""
        lines = ["", "   ", "\t", "content", "more content"]

        result = self.parser.skip_empty_lines(lines, 0)
        assert result == 3  # Should skip to "content"

    def test_skip_empty_lines_no_empty(self):
        """Test skipping when no empty lines"""
        lines = ["content", "more content"]

        result = self.parser.skip_empty_lines(lines, 0)
        assert result == 0  # Should stay at start

    def test_skip_empty_lines_beyond_end(self):
        """Test skipping beyond end of lines"""
        lines = ["", ""]

        result = self.parser.skip_empty_lines(lines, 0)
        assert result == 2  # Should go to end

    def test_find_next_significant_line(self):
        """Test finding next significant line"""
        lines = ["", "# comment", "", "significant content", "more content"]

        result = self.parser.find_next_significant_line(lines, 0)
        assert result == 3  # Should find "significant content"

    def test_find_next_significant_line_not_found(self):
        """Test finding significant line when none exists"""
        lines = ["", "# comment", ""]

        result = self.parser.find_next_significant_line(lines, 0)
        assert result is None

    def test_is_comment_line(self):
        """Test comment line detection"""
        test_cases = [
            ("# This is a comment", True),
            ("   # Indented comment", True),
            ("Not a comment", False),
            ("Text # with hash", False),
            ("", False),
        ]

        for line, expected in test_cases:
            result = self.parser._is_comment_line(line)
            assert result == expected, f"Failed for '{line}'"


class TestBlockParserIntegration:
    """Integration tests for block parser"""

    def test_parser_with_real_dependencies(self):
        """Test block parser with real dependencies"""
        from kumihan_formatter.core.keyword_parser import KeywordParser

        keyword_parser = KeywordParser()
        parser = BlockParser(keyword_parser)

        # Verify initialization with real dependencies
        assert parser.keyword_parser is not None
        assert parser.marker_validator is not None
        assert parser.logger is not None

    def test_complex_block_parsing_scenario(self):
        """Test complex block parsing scenario"""
        lines = [
            ";;;decoration+bold;;;",
            "This is decorated content",
            "with multiple lines",
            ";;;",
        ]

        keyword_parser = Mock(spec=KeywordParser)
        keyword_parser.parse_marker_keywords.return_value = (
            ["decoration", "bold"],
            {},
            [],
        )

        mock_node = Mock(spec=Node)
        mock_node.type = "compound"
        keyword_parser.create_compound_block.return_value = mock_node

        parser = BlockParser(keyword_parser)

        with patch.object(
            parser.marker_validator, "validate_marker_line"
        ) as mock_validate_line:
            with patch.object(
                parser.marker_validator, "validate_block_structure"
            ) as mock_validate_block:
                mock_validate_line.return_value = (True, [])
                mock_validate_block.return_value = (True, 3, [])

                result, next_index = parser.parse_block_marker(lines, 0)

                assert result.type == "compound"
                assert next_index == 4

    def test_paragraph_parsing_with_various_content(self):
        """Test paragraph parsing with various content types"""
        test_paragraphs = [
            ["Simple paragraph."],
            ["Multi-line", "paragraph", "content."],
            ["Paragraph with", "Japanese content 日本語"],
            ["Paragraph with", "special characters !@#$%^&*()"],
        ]

        keyword_parser = Mock(spec=KeywordParser)
        parser = BlockParser(keyword_parser)

        for paragraph_lines in test_paragraphs:
            # Add empty line at end to stop paragraph
            lines = paragraph_lines + [""]

            result, next_index = parser.parse_paragraph(lines, 0)

            assert result is not None
            assert result.type == "paragraph"
            assert next_index == len(paragraph_lines)

    def test_error_handling_in_block_parsing(self):
        """Test error handling during block parsing"""
        lines = [";;;invalid-marker", "content", ";;;"]

        keyword_parser = Mock(spec=KeywordParser)
        parser = BlockParser(keyword_parser)

        # Force validation to fail
        with patch.object(
            parser.marker_validator, "validate_marker_line"
        ) as mock_validate:
            mock_validate.return_value = (False, ["Invalid marker syntax"])

            result, next_index = parser.parse_block_marker(lines, 0)

            # Should handle error gracefully
            assert result is not None
            assert result.type == "error"
            assert isinstance(next_index, int)
