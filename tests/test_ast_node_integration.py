"""AST Node Integration Tests

Integration tests for AST node operations.
Tests node builder workflow and nested node creation.
"""

import tempfile
from pathlib import Path

import pytest

from kumihan_formatter.core.ast_nodes import Node, NodeBuilder


class TestASTNodeIntegration:
    """Integration tests for AST node operations"""

    def test_node_builder_workflow(self):
        """Test complete node building workflow"""
        # Test creating nodes with builder
        builder = NodeBuilder("div")
        node = builder.content("Test content").css_class("test-class").build()

        assert node.type == "div"
        assert node.content == "Test content"
        assert "class" in node.attributes
        assert node.attributes["class"] == "test-class"

    def test_nested_node_creation(self):
        """Test creating nested node structures"""
        # Create parent node
        parent = NodeBuilder("div").css_class("parent").build()

        # Create child node
        child = NodeBuilder("p").content("Child content").build()

        # Test node relationships
        parent.content = [child]
        assert isinstance(parent.content, list)
        assert len(parent.content) == 1
        assert parent.content[0] == child
