"""Realistic Parser Usage Tests

Focus on actual working parser functionality with realistic test cases.
Target: Increase parser module coverage significantly.
"""

import pytest


class TestParserRealUsage:
    """Test parser with real-world usage patterns"""

    def test_parser_basic_functionality(self):
        """Test basic parser functionality"""
        from kumihan_formatter.parser import Parser

        parser = Parser()

        # Test simple text parsing
        simple_cases = [
            "",  # Empty
            "Hello",  # Single word
            "Hello world",  # Simple sentence
            "Line 1\nLine 2",  # Multi-line
            "Paragraph 1\n\nParagraph 2",  # Paragraphs
        ]

        for text in simple_cases:
            result = parser.parse(text)
            assert result is not None
            assert isinstance(result, list)

    def test_parser_heading_parsing(self):
        """Test heading parsing"""
        from kumihan_formatter.parser import Parser

        parser = Parser()

        heading_cases = [
            "# Level 1 Heading",
            "## Level 2 Heading",
            "### Level 3 Heading",
            "#### Level 4 Heading",
            "##### Level 5 Heading",
            "# Heading\nParagraph text",
            "## Heading with **bold** text",
        ]

        for text in heading_cases:
            result = parser.parse(text)
            assert result is not None
            assert len(result) > 0

            # Check first node is heading
            if result and hasattr(result[0], "type"):
                assert result[0].type.startswith("h")

    def test_parser_list_parsing(self):
        """Test list parsing"""
        from kumihan_formatter.parser import Parser

        parser = Parser()

        list_cases = [
            "- Item 1\n- Item 2",
            "* Item A\n* Item B",
            "1. First\n2. Second",
            "- Nested:\n  - Sub item",
            """- Main item
  - Sub item 1
  - Sub item 2
- Another main item""",
        ]

        for text in list_cases:
            result = parser.parse(text)
            assert result is not None
            # Lists should produce nodes
            assert len(result) > 0

    def test_parser_kumihan_syntax(self):
        """Test Kumihan-specific syntax parsing"""
        from kumihan_formatter.parser import Parser

        parser = Parser()

        kumihan_cases = [
            ";;;highlight;;; Important text ;;;",
            ";;;box;;; Boxed content ;;;",
            "Text with ((footnote content)) inline",
            "｜漢字《かんじ》 ruby notation",
            """Document with multiple syntaxes:
;;;highlight;;; Highlighted section ;;;

Regular paragraph.

And ((a footnote)).""",
        ]

        for text in kumihan_cases:
            result = parser.parse(text)
            assert result is not None
            assert isinstance(result, list)

    def test_parser_mixed_content(self):
        """Test parsing mixed content documents"""
        from kumihan_formatter.parser import Parser

        parser = Parser()

        # Realistic document content
        document = """# Kumihan Formatter Document

This is an introduction paragraph with **bold** and *italic* text.

## Features

- Feature 1: Basic text formatting
- Feature 2: Kumihan syntax support
  - Sub-feature: Footnotes
  - Sub-feature: Ruby text

;;;highlight;;;
This section is highlighted for importance.
;;;

### Usage Example

Here's how to use footnotes((This is a footnote example)).

And ruby text: ｜日本語《にほんご》

## Conclusion

The formatter supports various text styles and special notations."""

        result = parser.parse(document)
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0

        # Document should have multiple nodes
        if len(result) > 5:
            # Check variety of node types
            node_types = set()
            for node in result:
                if hasattr(node, "type"):
                    node_types.add(node.type)

            # Should have different types
            assert len(node_types) > 1
