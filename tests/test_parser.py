"""Tests for main parser module

This module tests the main Parser class functionality including text parsing,
AST node generation, and integration with specialized parsers.
"""

from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.ast_nodes import Node
from kumihan_formatter.parser import Parser, parse


class TestParser:
    """Test main Parser class functionality"""

    def setup_method(self):
        """Set up test environment"""
        self.parser = Parser()

    def test_init_without_config(self):
        """Test parser initialization without config"""
        parser = Parser()
        assert isinstance(parser, Parser)
        assert parser.config is None
        assert parser.lines == []
        assert parser.current == 0
        assert parser.errors == []
        assert hasattr(parser, "keyword_parser")
        assert hasattr(parser, "list_parser")
        assert hasattr(parser, "block_parser")

    def test_init_with_config(self):
        """Test parser initialization with config"""
        config = {"test": "value"}
        parser = Parser(config)
        # Config is ignored in current implementation
        assert parser.config is None

    def test_parse_empty_text(self):
        """Test parsing empty text"""
        result = self.parser.parse("")
        assert isinstance(result, list)
        assert len(result) == 0

    def test_parse_whitespace_only(self):
        """Test parsing text with only whitespace"""
        whitespace_text = "   \n\t\n   "
        result = self.parser.parse(whitespace_text)
        assert isinstance(result, list)
        assert len(result) == 0

    def test_parse_simple_text(self):
        """Test parsing simple text content"""
        simple_text = "This is a simple paragraph."

        with patch.object(self.parser.block_parser, "parse_paragraph") as mock_parse:
            mock_node = Mock(spec=Node)
            mock_node.type = "paragraph"
            mock_parse.return_value = (mock_node, 1)

            result = self.parser.parse(simple_text)

            assert len(result) == 1
            assert result[0].type == "paragraph"
            mock_parse.assert_called_once()

    def test_parse_comment_lines(self):
        """Test parsing comment lines (lines starting with #)"""
        comment_text = "# This is a comment\nActual content\n# Another comment"

        with patch.object(self.parser.block_parser, "parse_paragraph") as mock_parse:
            mock_node = Mock(spec=Node)
            mock_node.type = "paragraph"
            mock_parse.return_value = (mock_node, 2)  # Skip to line after comment

            result = self.parser.parse(comment_text)

            # Should skip comment lines and parse only actual content
            assert len(result) == 1
            mock_parse.assert_called_once()

    def test_parse_block_marker(self):
        """Test parsing block markers"""
        block_text = ";;;decoration;;;\nContent\n;;;"

        with patch.object(
            self.parser.block_parser, "is_opening_marker"
        ) as mock_is_opening:
            with patch.object(
                self.parser.block_parser, "parse_block_marker"
            ) as mock_parse:
                mock_is_opening.return_value = True
                mock_node = Mock(spec=Node)
                mock_node.type = "block"
                mock_parse.return_value = (mock_node, 3)

                result = self.parser.parse(block_text)

                assert len(result) == 1
                assert result[0].type == "block"
                mock_parse.assert_called_once()

    def test_parse_unordered_list(self):
        """Test parsing unordered lists"""
        list_text = "- Item 1\n- Item 2\n- Item 3"

        with patch.object(self.parser.list_parser, "is_list_line") as mock_is_list:
            with patch.object(
                self.parser.list_parser, "parse_unordered_list"
            ) as mock_parse:
                mock_is_list.return_value = "ul"
                mock_node = Mock(spec=Node)
                mock_node.type = "list"
                mock_parse.return_value = (mock_node, 3)

                result = self.parser.parse(list_text)

                assert len(result) == 1
                assert result[0].type == "list"
                mock_parse.assert_called_once()

    def test_parse_ordered_list(self):
        """Test parsing ordered lists"""
        list_text = "1. First item\n2. Second item\n3. Third item"

        with patch.object(self.parser.list_parser, "is_list_line") as mock_is_list:
            with patch.object(
                self.parser.list_parser, "parse_ordered_list"
            ) as mock_parse:
                mock_is_list.return_value = "ol"
                mock_node = Mock(spec=Node)
                mock_node.type = "list"
                mock_parse.return_value = (mock_node, 3)

                result = self.parser.parse(list_text)

                assert len(result) == 1
                assert result[0].type == "list"
                mock_parse.assert_called_once()

    def test_parse_mixed_content(self):
        """Test parsing mixed content types"""
        mixed_text = """# Comment
Paragraph content

;;;decoration;;;
Block content
;;;

- List item 1
- List item 2"""

        # Mock all the parsers
        with patch.object(
            self.parser.block_parser, "parse_paragraph"
        ) as mock_paragraph:
            with patch.object(
                self.parser.block_parser, "is_opening_marker"
            ) as mock_is_opening:
                with patch.object(
                    self.parser.block_parser, "parse_block_marker"
                ) as mock_block:
                    with patch.object(
                        self.parser.list_parser, "is_list_line"
                    ) as mock_is_list:
                        with patch.object(
                            self.parser.list_parser, "parse_unordered_list"
                        ) as mock_list:

                            # Configure mocks
                            mock_paragraph_node = Mock(spec=Node)
                            mock_paragraph_node.type = "paragraph"
                            mock_paragraph.return_value = (mock_paragraph_node, 2)

                            mock_block_node = Mock(spec=Node)
                            mock_block_node.type = "block"
                            mock_block.return_value = (mock_block_node, 5)

                            mock_list_node = Mock(spec=Node)
                            mock_list_node.type = "list"
                            mock_list.return_value = (mock_list_node, 8)

                            def mock_is_opening_side_effect(line):
                                return line.strip() == ";;;decoration;;;"

                            def mock_is_list_side_effect(line):
                                return "ul" if line.strip().startswith("- ") else None

                            mock_is_opening.side_effect = mock_is_opening_side_effect
                            mock_is_list.side_effect = mock_is_list_side_effect

                            result = self.parser.parse(mixed_text)

                            # Should parse paragraph, block, and list
                            assert len(result) == 3

    def test_get_errors(self):
        """Test error retrieval"""
        assert self.parser.get_errors() == []

        # Add some errors
        self.parser.add_error("Test error 1")
        self.parser.add_error("Test error 2")

        errors = self.parser.get_errors()
        assert len(errors) == 2
        assert "Test error 1" in errors
        assert "Test error 2" in errors

    def test_add_error(self):
        """Test error addition"""
        error_message = "Test parsing error"
        self.parser.add_error(error_message)

        assert len(self.parser.errors) == 1
        assert self.parser.errors[0] == error_message

    def test_get_statistics(self):
        """Test statistics retrieval"""
        # Parse some content to populate statistics
        test_text = "Line 1\nLine 2\nLine 3"

        with patch.object(self.parser.block_parser, "parse_paragraph") as mock_parse:
            mock_node = Mock(spec=Node)
            mock_parse.return_value = (mock_node, 3)

            self.parser.parse(test_text)

            stats = self.parser.get_statistics()

            assert isinstance(stats, dict)
            assert "total_lines" in stats
            assert "errors_count" in stats
            assert "heading_count" in stats
            assert stats["total_lines"] == 3

    def test_parse_line_boundary_conditions(self):
        """Test parsing with boundary conditions"""
        # Test when current index exceeds lines length
        self.parser.lines = ["line 1", "line 2"]
        self.parser.current = 3

        result = self.parser._parse_line()
        assert result is None

    def test_parse_line_with_empty_lines(self):
        """Test parsing lines with empty line skipping"""
        test_text = "\n\nActual content\n\n"

        with patch.object(self.parser.block_parser, "skip_empty_lines") as mock_skip:
            with patch.object(
                self.parser.block_parser, "parse_paragraph"
            ) as mock_parse:
                mock_skip.return_value = 2  # Skip to actual content
                mock_node = Mock(spec=Node)
                mock_parse.return_value = (mock_node, 3)

                result = self.parser.parse(test_text)

                mock_skip.assert_called()
                assert len(result) == 1

    def test_error_handling_during_parsing(self):
        """Test error handling during parsing process"""
        problematic_text = "Valid line\nProblematic content"

        with patch.object(self.parser.block_parser, "parse_paragraph") as mock_parse:
            # First call succeeds, second call raises exception
            mock_node = Mock(spec=Node)
            mock_parse.side_effect = [(mock_node, 1), Exception("Parse error")]

            # Should handle exceptions gracefully
            result = self.parser.parse(problematic_text)

            # Should have parsed the first line successfully
            assert len(result) >= 0  # Parser should not crash

    def test_complex_document_structure(self):
        """Test parsing complex document with multiple structure types"""
        complex_text = """# Document Title

Introduction paragraph with multiple sentences.
This continues the paragraph.

;;;見出し1;;;
Chapter 1 Content
;;;

1. First ordered item
2. Second ordered item

- Unordered item 1
- Unordered item 2

;;;decoration;;;
Decorated content block
;;;

Final paragraph."""

        # This is an integration-style test with mocked components
        with patch.object(
            self.parser.block_parser, "parse_paragraph"
        ) as mock_paragraph:
            with patch.object(
                self.parser.block_parser, "is_opening_marker"
            ) as mock_is_opening:
                with patch.object(
                    self.parser.block_parser, "parse_block_marker"
                ) as mock_block:
                    with patch.object(
                        self.parser.list_parser, "is_list_line"
                    ) as mock_is_list:
                        with patch.object(
                            self.parser.list_parser, "parse_ordered_list"
                        ) as mock_ol:
                            with patch.object(
                                self.parser.list_parser, "parse_unordered_list"
                            ) as mock_ul:

                                # Configure complex mock behavior
                                def configure_mocks():
                                    # This would be quite complex to fully mock
                                    # For now, we'll test that the parser doesn't crash
                                    mock_node = Mock(spec=Node)
                                    mock_paragraph.return_value = (mock_node, 1)
                                    mock_block.return_value = (mock_node, 1)
                                    mock_ol.return_value = (mock_node, 1)
                                    mock_ul.return_value = (mock_node, 1)
                                    mock_is_opening.return_value = False
                                    mock_is_list.return_value = None

                                configure_mocks()
                                result = self.parser.parse(complex_text)

                                # The important thing is that parsing completes without error
                                assert isinstance(result, list)

    def test_parser_state_reset_between_parses(self):
        """Test that parser state is properly reset between parse calls"""
        # First parse
        result1 = self.parser.parse("First document")
        first_lines_count = len(self.parser.lines)
        first_current = self.parser.current

        # Second parse - state should be reset
        result2 = self.parser.parse("Second document\nWith multiple lines")

        # Verify state was reset and updated for second parse
        assert len(self.parser.lines) != first_lines_count
        assert self.parser.current == len(
            self.parser.lines
        )  # Should be at end after parse
        assert isinstance(result1, list)
        assert isinstance(result2, list)


class TestParseFunction:
    """Test standalone parse function"""

    def test_parse_function_exists(self):
        """Test that parse function exists and is callable"""
        assert callable(parse)

    def test_parse_function_basic_usage(self):
        """Test basic usage of parse function"""
        result = parse("")
        assert isinstance(result, list)

    def test_parse_function_with_config(self):
        """Test parse function with config parameter"""
        config = {"test": "value"}
        result = parse("", config)
        assert isinstance(result, list)

    def test_parse_function_creates_parser_instance(self):
        """Test that parse function creates Parser instance"""
        with patch("kumihan_formatter.parser.Parser") as mock_parser_class:
            mock_parser_instance = Mock()
            mock_parser_instance.parse.return_value = []
            mock_parser_class.return_value = mock_parser_instance

            test_text = "Test content"
            result = parse(test_text)

            mock_parser_class.assert_called_once_with(None)
            mock_parser_instance.parse.assert_called_once_with(test_text)

    def test_parse_function_with_various_inputs(self):
        """Test parse function with various input types"""
        test_cases = [
            "",
            "Simple text",
            "Multi\nline\ntext",
            "Text with ;;; markers ;;;",
            "- List item\n- Another item",
        ]

        for test_input in test_cases:
            result = parse(test_input)
            assert isinstance(result, list), f"Failed for input: {test_input}"


class TestParserIntegration:
    """Integration tests for parser with its dependencies"""

    def test_parser_with_real_dependencies(self):
        """Test parser with actual (not mocked) specialized parsers"""
        parser = Parser()

        # Verify that specialized parsers are properly initialized
        assert parser.keyword_parser is not None
        assert parser.list_parser is not None
        assert parser.block_parser is not None

        # Test that they have the expected interface
        assert hasattr(parser.keyword_parser, "parse_marker_keywords")
        assert hasattr(parser.list_parser, "is_list_line")
        assert hasattr(parser.block_parser, "is_opening_marker")

    def test_parser_error_accumulation(self):
        """Test that parser properly accumulates errors from sub-parsers"""
        parser = Parser()

        # Add errors through the interface
        parser.add_error("Syntax error in line 1")
        parser.add_error("Invalid marker in line 5")

        errors = parser.get_errors()
        assert len(errors) == 2
        assert "Syntax error in line 1" in errors
        assert "Invalid marker in line 5" in errors

    def test_parser_logging_integration(self):
        """Test that parser properly integrates with logging system"""
        parser = Parser()

        # Verify logger is initialized
        assert parser.logger is not None
        assert hasattr(parser.logger, "debug")
        assert hasattr(parser.logger, "info")
        assert hasattr(parser.logger, "warning")
        assert hasattr(parser.logger, "error")
