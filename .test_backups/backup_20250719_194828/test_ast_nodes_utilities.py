"""AST Nodes Utilities Tests

Split from test_ast_nodes_complete.py for 300-line limit compliance.
Comprehensive tests for Node utility operations.
"""

import json

import pytest

from kumihan_formatter.core.ast_nodes import Node
from kumihan_formatter.core.ast_nodes.factories import paragraph


class TestNodeUtilitiesComplete:
    """Complete coverage tests for Node utilities"""

    def test_node_tree_traversal(self):
        """Test node tree traversal utilities"""
        # Create tree structure manually
        root = Node("div", [])
        root.content = []
        child1 = paragraph("Child 1")
        child2 = Node("div", [])
        grandchild = Node("span", "Grandchild")

        # Build tree structure
        child2.content = [grandchild]
        root.content = [child1, child2]

        # Basic tree structure validation
        assert isinstance(root.content, list)
        assert len(root.content) == 2
        assert root.content[0] == child1
        assert root.content[1] == child2

        # Child content validation
        assert isinstance(child2.content, list)
        assert len(child2.content) == 1
        assert child2.content[0] == grandchild

        # Attribute testing
        child1.add_attribute("class", "special")
        assert child1.get_attribute("class") == "special"

    def test_node_transformation_utilities(self):
        """Test node transformation utilities"""
        # Manual type conversion
        p_node = paragraph("Text")
        div_node = Node("div", p_node.content)
        div_node.attributes = p_node.attributes.copy()
        assert div_node.type == "div"
        assert div_node.content == "Text"

        # Manual wrapping
        text_node = Node("span", "Text")
        wrapped = Node("div", [text_node])
        wrapped.add_attribute("class", "wrapper")
        assert wrapped.type == "div"
        assert wrapped.get_attribute("class") == "wrapper"
        assert wrapped.content == [text_node]

        # Manual unwrapping
        container = Node("div", [Node("span", "Content")])
        unwrapped = container.content
        assert len(unwrapped) == 1
        assert unwrapped[0].type == "span"
        assert unwrapped[0].content == "Content"

    def test_node_validation_utilities(self):
        """Test node validation utilities"""
        # Basic node validation
        valid_node = paragraph("Valid content")
        assert valid_node.type == "p"
        assert valid_node.content == "Valid content"

        # Edge case node
        edge_node = Node("", None)
        assert edge_node.type == ""
        assert edge_node.content is None

        # Check attributes existence
        node_with_attrs = Node("div", "Content")
        node_with_attrs.add_attribute("id", "required-id")

        # Attribute validation
        assert node_with_attrs.has_attribute("id")
        assert not node_with_attrs.has_attribute("class")
        assert node_with_attrs.get_attribute("id") == "required-id"

    def test_node_serialization_utilities(self):
        """Test node serialization utilities"""
        # Manual dictionary creation
        node = paragraph("Content")
        node.add_attribute("class", "test")

        node_dict = {
            "type": node.type,
            "content": node.content,
            "attributes": node.attributes,
        }
        assert node_dict["type"] == "p"
        assert node_dict["content"] == "Content"
        assert node_dict["attributes"]["class"] == "test"

        # Manual reconstruction
        reconstructed = Node(
            node_dict["type"], node_dict["content"], node_dict["attributes"]
        )
        assert reconstructed.type == node.type
        assert reconstructed.content == node.content
        assert reconstructed.attributes == node.attributes

        # JSON compatibility test
        json_str = json.dumps(node_dict)
        parsed_dict = json.loads(json_str)
        json_node = Node(
            parsed_dict["type"], parsed_dict["content"], parsed_dict["attributes"]
        )
        assert json_node.type == node.type
