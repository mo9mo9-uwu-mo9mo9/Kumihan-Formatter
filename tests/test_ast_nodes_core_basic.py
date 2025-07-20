"""AST Nodes Core Basic Tests

Split from test_ast_nodes_core.py for 300-line limit compliance.
Basic tests for Node class core functionality.
Current coverage: node.py 52% → Target: 90%+
"""

import pytest

from kumihan_formatter.core.ast_nodes import Node


class TestNodeBasicCoverage:
    """Basic coverage tests for Node class"""

    def test_node_initialization_variations(self):
        """Test Node initialization with different parameters"""
        # Basic initialization
        node = Node("p", "content")
        assert node.type == "p"
        assert node.content == "content"
        assert node.attributes == {}

        # With attributes dict
        attrs = {"class": "test", "id": "node1"}
        node = Node("div", "content", attrs)
        assert node.attributes == attrs

        # With None attributes
        node = Node("span", "text", None)
        assert node.attributes == {}

    def test_node_attribute_operations_basic(self):
        """Test basic Node attribute operations"""
        node = Node("div", "content")

        # Add attribute
        node.add_attribute("class", "container")
        assert node.get_attribute("class") == "container"
        assert node.has_attribute("class")

        # Remove attribute
        node.remove_attribute("class")
        assert not node.has_attribute("class")
        assert node.get_attribute("class") is None

    def test_node_children_operations_basic(self):
        """Test basic Node children operations"""
        parent = Node("div", "parent")
        child1 = Node("p", "child1")
        child2 = Node("span", "child2")

        # Add children
        parent.add_child(child1)
        parent.add_child(child2)

        assert len(parent.children) == 2
        assert child1 in parent.children
        assert child2 in parent.children

        # Remove child
        parent.remove_child(child1)
        assert len(parent.children) == 1
        assert child1 not in parent.children
