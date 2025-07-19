"""AST Nodes Builder Tests

Split from test_ast_nodes_complete.py for 300-line limit compliance.
Comprehensive tests for NodeBuilder class functionality.
"""

import pytest

from kumihan_formatter.core.ast_nodes import Node, NodeBuilder


class TestNodeBuilderCompleteCoverage:
    """Complete coverage tests for NodeBuilder class"""

    def test_node_builder_all_methods(self):
        """Test all NodeBuilder methods"""
        builder = NodeBuilder("section")

        # Method chaining
        node = (
            builder.content("Test content")
            .css_class("section-class")
            .id("section-1")
            .style("color: red;")
            .attribute("data-test", "value")
            .attribute("role", "main")
            .build()
        )

        assert node.type == "section"
        assert node.content == "Test content"
        assert node.get_attribute("class") == "section-class"
        assert node.get_attribute("id") == "section-1"
        assert node.get_attribute("style") == "color: red;"
        assert node.get_attribute("data-test") == "value"
        assert node.get_attribute("role") == "main"

    def test_node_builder_different_content_types(self):
        """Test NodeBuilder with different content types"""
        # String content
        builder = NodeBuilder("p")
        node = builder.content("String content").build()
        assert node.content == "String content"

        # List content
        builder = NodeBuilder("div")
        list_content = ["item1", "item2"]
        node = builder.content(list_content).build()
        assert node.content == list_content

        # Node content
        child_node = Node("span", "child")
        builder = NodeBuilder("div")
        node = builder.content(child_node).build()
        assert node.content == child_node

        # None content
        builder = NodeBuilder("br")
        node = builder.content(None).build()
        assert node.content is None

    def test_node_builder_attribute_overwrites(self):
        """Test NodeBuilder attribute overwrite behavior"""
        builder = NodeBuilder("div")

        # Overwrite same attribute
        node = (
            builder.css_class("first-class")
            .css_class("second-class")  # Should overwrite
            .build()
        )

        assert node.get_attribute("class") == "second-class"

        # Overwrite with attribute method
        builder = NodeBuilder("span")
        node = (
            builder.id("first-id")
            .attribute("id", "second-id")  # Should overwrite
            .build()
        )

        assert node.get_attribute("id") == "second-id"

    def test_node_builder_edge_cases(self):
        """Test NodeBuilder edge cases"""
        # Empty type
        builder = NodeBuilder("")
        node = builder.content("content").build()
        assert node.type == ""

        # Very long type
        long_type = "very_long_element_type_name_for_testing"
        builder = NodeBuilder(long_type)
        node = builder.build()
        assert node.type == long_type

        # Build without setting anything
        builder = NodeBuilder("div")
        node = builder.build()
        assert node.type == "div"
        assert node.content is None
        assert node.attributes == {}

        # Multiple builds from same builder
        builder = NodeBuilder("p").content("text")
        node1 = builder.build()
        node2 = builder.build()
        assert node1.content == node2.content
        assert node1 is not node2  # Different objects
