"""AST Nodes Factories Tests

Split from test_ast_nodes_complete.py for 300-line limit compliance.
Comprehensive tests for Node factory functions.
"""

import pytest

from kumihan_formatter.core.ast_nodes import Node
from kumihan_formatter.core.ast_nodes.factories import (
    div_box,
    emphasis,
    heading,
    highlight,
    paragraph,
    strong,
)


class TestNodeFactoriesComplete:
    """Complete coverage tests for Node factory functions"""

    def test_paragraph_factory(self):
        """Test paragraph factory function"""
        # Simple paragraph
        p = paragraph("Text content")
        assert p.type == "p"
        assert p.content == "Text content"

        # Paragraph with attributes
        p_with_class = paragraph("Styled text", {"class": "intro"})
        assert p_with_class.get_attribute("class") == "intro"

    def test_heading_factory(self):
        """Test heading factory function"""
        # Different heading levels
        for level in [1, 2, 3, 4, 5]:
            h = heading(level, "Heading text")
            assert h.type == f"h{level}"
            assert h.content == "Heading text"

        # Heading with attributes
        h_with_id = heading(1, "Title", {"id": "main-title"})
        assert h_with_id.get_attribute("id") == "main-title"

        # Invalid level handling
        try:
            h_invalid = heading(0, "Invalid")
            # Should handle gracefully or raise appropriate error
        except (ValueError, AssertionError):
            pass  # Expected behavior

    def test_container_factories(self):
        """Test container factory functions"""
        # Div box factory
        d = div_box("Div content")
        assert d.type == "div"
        assert d.content == "Div content"
        assert d.get_attribute("class") == "box"

        # Highlight div factory
        h = highlight("Highlighted content")
        assert h.type == "div"
        assert h.content == "Highlighted content"
        assert h.get_attribute("class") == "highlight"

        # Highlight with color
        h_colored = highlight("Colored content", "yellow")
        assert "background-color:yellow" in h_colored.get_attribute("style", "")

    def test_formatting_factories(self):
        """Test formatting factory functions"""
        # Strong (bold)
        strong_node = strong("Bold text")
        assert strong_node.type == "strong"
        assert strong_node.content == "Bold text"

        # Emphasis (italic)
        em_node = emphasis("Italic text")
        assert em_node.type == "em"
        assert em_node.content == "Italic text"

    def test_manual_node_creation(self):
        """Test manual node creation for missing factories"""
        # List item (manual creation)
        li = Node("li", "Item content")
        assert li.type == "li"
        assert li.content == "Item content"

        # Unordered list (manual creation)
        item1 = Node("li", "Item 1")
        item2 = Node("li", "Item 2")
        ul = Node("ul", [item1, item2])
        assert ul.type == "ul"
        assert len(ul.content) == 2

        # Ordered list (manual creation)
        ol = Node("ol", [item1, item2])
        assert ol.type == "ol"
        assert len(ol.content) == 2

        # Error node (manual creation)
        error = Node("error", "Error message")
        assert error.type == "error"
        assert "Error message" in error.content
