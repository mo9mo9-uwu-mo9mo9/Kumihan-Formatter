"""Node Coverage Tests

Split from test_additional_coverage.py for 300-line limit compliance.
Coverage booster tests for AST nodes modules.
"""

import pytest

from kumihan_formatter.core.ast_nodes import Node, NodeBuilder


class TestNodeBuilderAdvanced:
    """Advanced tests for NodeBuilder"""

    def test_node_builder_chaining(self):
        """Test NodeBuilder method chaining"""
        builder = NodeBuilder("section")
        node = (
            builder.content("Test content")
            .css_class("test-class")
            .id("test-id")
            .attribute("data-test", "value")
            .build()
        )

        assert node.type == "section"
        assert node.content == "Test content"
        assert node.get_attribute("class") == "test-class"
        assert node.get_attribute("id") == "test-id"
        assert node.get_attribute("data-test") == "value"

    def test_node_multiple_classes(self):
        """Test Node with multiple CSS classes"""
        node = NodeBuilder("div").css_class("class1").css_class("class2").build()

        # Should handle multiple class additions
        assert "class" in node.attributes

    def test_node_complex_content(self):
        """Test Node with complex nested content"""
        child1 = Node("span", "Child 1")
        child2 = Node("span", "Child 2")

        parent = NodeBuilder("div").content([child1, child2]).build()
        assert isinstance(parent.content, list)
        assert len(parent.content) == 2
        assert parent.content[0] == child1
        assert parent.content[1] == child2


class TestNodeAttributeOperations:
    """Comprehensive Node attribute tests"""

    def test_node_attribute_edge_cases(self):
        """Test Node attribute edge cases"""
        node = Node("div", "content")

        # Test setting None attribute
        node.add_attribute("empty", None)
        assert node.get_attribute("empty") is None

        # Test setting empty string attribute
        node.add_attribute("empty_string", "")
        assert node.get_attribute("empty_string") == ""

        # Test overwriting attribute
        node.add_attribute("test", "value1")
        node.add_attribute("test", "value2")
        assert node.get_attribute("test") == "value2"

    def test_node_has_attribute(self):
        """Test Node has_attribute method"""
        node = Node("div", "content")

        # Test with no attributes
        assert not node.has_attribute("nonexistent")

        # Test with existing attribute
        node.add_attribute("test", "value")
        assert node.has_attribute("test")
        assert not node.has_attribute("other")

    def test_node_attribute_manipulation(self):
        """Test Node attribute manipulation methods"""
        node = Node("div", "content")

        # Add and check attribute
        node.add_attribute("test", "value")
        assert node.has_attribute("test")
        assert node.get_attribute("test") == "value"

        # Test attribute overwriting
        node.add_attribute("test", "new_value")
        assert node.get_attribute("test") == "new_value"

        # Test Node element type checking methods
        assert node.is_block_element()  # div is a block element
        assert not node.is_inline_element()
