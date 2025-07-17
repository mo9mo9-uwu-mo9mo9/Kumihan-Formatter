"""Phase 2 Core Function Tests - Issue #499

This test suite covers the core functionality tests for Phase 2:
- Parser tests
- Renderer tests
- Keyword parser tests
"""

from pathlib import Path

import pytest

from kumihan_formatter.core.ast_nodes import Node
from kumihan_formatter.core.ast_nodes.factories import heading, paragraph
from kumihan_formatter.core.keyword_parser import KeywordParser
from kumihan_formatter.parser import Parser, parse
from kumihan_formatter.renderer import Renderer, render


class TestParserCore:
    """Core parser functionality tests"""

    def test_parser_basic_functionality(self):
        """Test basic parser functionality"""
        parser = Parser()
        text = "Hello World"
        nodes = parser.parse(text)
        assert len(nodes) == 1
        assert isinstance(nodes[0], Node)
        assert nodes[0].type == "p"

    def test_parser_multiple_paragraphs(self):
        """Test parsing multiple paragraphs"""
        parser = Parser()
        text = "First paragraph\n\nSecond paragraph"
        nodes = parser.parse(text)
        assert len(nodes) >= 2
        assert all(isinstance(node, Node) for node in nodes)

    def test_parser_comment_handling(self):
        """Test comment line handling"""
        parser = Parser()
        text = "# This is a comment\n\nActual content"
        nodes = parser.parse(text)
        assert len(nodes) == 1  # Comment should be skipped
        assert nodes[0].type == "p"

    def test_parser_error_handling(self):
        """Test parser error handling"""
        parser = Parser()
        parser.add_error("Test error")
        errors = parser.get_errors()
        assert len(errors) == 1
        assert "Test error" in errors


class TestRendererCore:
    """Core renderer functionality tests"""

    def test_renderer_basic_functionality(self):
        """Test basic renderer functionality"""
        renderer = Renderer()
        ast = [paragraph("Hello World")]
        result = renderer.render(ast)
        assert isinstance(result, str)
        assert "Hello World" in result
        assert len(result) > 0

    def test_renderer_with_headings(self):
        """Test renderer with headings"""
        renderer = Renderer()
        ast = [heading(1, "Main Title"), paragraph("Content under heading")]
        result = renderer.render(ast)
        assert isinstance(result, str)
        assert "Main Title" in result
        assert "Content under heading" in result

    def test_renderer_toc_generation(self):
        """Test TOC generation"""
        renderer = Renderer()
        ast = [
            heading(1, "Title 1"),
            paragraph("Content 1"),
            heading(2, "Title 2"),
            paragraph("Content 2"),
        ]
        toc_data = renderer.get_toc_data(ast)
        assert isinstance(toc_data, dict)
        assert "has_toc" in toc_data
        assert "html" in toc_data

    def test_renderer_template_validation(self):
        """Test template validation"""
        renderer = Renderer()
        is_valid, error = renderer.validate_template("nonexistent.html")
        assert isinstance(is_valid, bool)
        assert isinstance(error, (str, type(None)))


class TestKeywordParserCore:
    """Core keyword parser functionality tests"""

    def test_keyword_parser_initialization(self):
        """Test keyword parser initialization"""
        parser = KeywordParser()
        assert parser.definitions is not None
        assert parser.marker_parser is not None
        assert parser.validator is not None
        assert parser.BLOCK_KEYWORDS is not None
        assert isinstance(parser.BLOCK_KEYWORDS, dict)

    def test_keyword_parser_default_keywords(self):
        """Test default keyword definitions"""
        parser = KeywordParser()

        # Check that default keywords exist
        assert "太字" in parser.BLOCK_KEYWORDS
        assert "イタリック" in parser.BLOCK_KEYWORDS
        assert "枠線" in parser.BLOCK_KEYWORDS
        assert "ハイライト" in parser.BLOCK_KEYWORDS

        # Check keyword definitions
        assert parser.BLOCK_KEYWORDS["太字"]["tag"] == "strong"
        assert parser.BLOCK_KEYWORDS["イタリック"]["tag"] == "em"
        assert parser.BLOCK_KEYWORDS["枠線"]["tag"] == "div"
        assert parser.BLOCK_KEYWORDS["枠線"]["class"] == "box"

    def test_keyword_parser_validation(self):
        """Test keyword validation"""
        parser = KeywordParser()

        # Test valid keywords
        valid_keywords, invalid_keywords = parser.validate_keywords(
            ["太字", "イタリック"]
        )
        assert isinstance(valid_keywords, list)
        assert isinstance(invalid_keywords, list)
        assert "太字" in valid_keywords
        assert "イタリック" in valid_keywords

        # Test invalid keywords
        valid_keywords, invalid_keywords = parser.validate_keywords(
            ["無効なキーワード"]
        )
        assert isinstance(valid_keywords, list)
        assert isinstance(invalid_keywords, list)
        assert len(invalid_keywords) > 0

    def test_keyword_parser_marker_parsing(self):
        """Test marker parsing"""
        parser = KeywordParser()

        # Test basic parsing
        keywords, attributes, errors = parser.parse_marker_keywords("太字")
        assert isinstance(keywords, list)
        assert isinstance(attributes, dict)
        assert isinstance(errors, list)

        # Test with compound keywords
        keywords, attributes, errors = parser.parse_marker_keywords("太字+イタリック")
        assert isinstance(keywords, list)
        assert isinstance(attributes, dict)
        assert isinstance(errors, list)


class TestIntegrationCore:
    """Integration tests for core components"""

    def test_parser_renderer_integration(self):
        """Test parser and renderer integration"""
        # Parse text
        parser = Parser()
        text = "# Main Title\n\nThis is content\n\n## Sub Title\n\nMore content"
        ast = parser.parse(text)

        # Render AST
        renderer = Renderer()
        result = renderer.render(ast, title="Test Document")

        # Verify results
        assert isinstance(result, str)
        assert "Test Document" in result
        assert len(result) > 0

    def test_keyword_parser_integration(self):
        """Test keyword parser integration"""
        parser = KeywordParser()

        # Test that all components work together
        keywords, attributes, errors = parser.parse_marker_keywords("太字[red]")
        assert isinstance(keywords, list)
        assert isinstance(attributes, dict)
        assert isinstance(errors, list)

        # Test validation
        valid, invalid = parser.validate_keywords(keywords)
        assert isinstance(valid, list)
        assert isinstance(invalid, list)

    def test_full_pipeline(self):
        """Test complete processing pipeline"""
        # Parse
        parser = Parser()
        text = "Hello **World**"
        ast = parser.parse(text)

        # Render
        renderer = Renderer()
        result = renderer.render(ast)

        # Verify
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Hello" in result


@pytest.mark.unit
class TestCoreUnitTests:
    """Unit tests for core functionality"""

    def test_node_creation(self):
        """Test AST node creation"""
        node = paragraph("Test content")
        assert isinstance(node, Node)
        assert node.type == "p"
        assert node.content == "Test content"

    def test_heading_creation(self):
        """Test heading node creation"""
        node = heading(1, "Test heading")
        assert isinstance(node, Node)
        assert node.type == "h1"
        assert node.content == "Test heading"

    def test_parse_function_compatibility(self):
        """Test parse function compatibility"""
        result = parse("Hello World")
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Node)

    def test_render_function_compatibility(self):
        """Test render function compatibility"""
        ast = [paragraph("Hello World")]
        result = render(ast)
        assert isinstance(result, str)
        assert "Hello World" in result


if __name__ == "__main__":
    pytest.main([__file__])
