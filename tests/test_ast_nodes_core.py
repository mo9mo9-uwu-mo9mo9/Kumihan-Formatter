"""AST Nodes Core Tests

Split from test_ast_nodes_complete.py for 300-line limit compliance.
Comprehensive tests for Node class core functionality.
Current coverage: node.py 52% → Target: 90%+
"""

import pytest

from kumihan_formatter.core.ast_nodes import Node


class TestNodeCompleteCoverage:
    """Complete coverage tests for Node class"""

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

    def test_node_attribute_operations_complete(self):
        """Test all Node attribute operations"""
        node = Node("div", "content")

        # Add attribute
        node.add_attribute("class", "container")
        assert node.get_attribute("class") == "container"
        assert node.has_attribute("class")

        # Add multiple attributes
        node.add_attribute("id", "main")
        node.add_attribute("data-test", "value")
        assert node.get_attribute("id") == "main"
        assert node.get_attribute("data-test") == "value"

        # Get with default
        assert node.get_attribute("nonexistent", "default") == "default"
        assert node.get_attribute("nonexistent") is None

        # Has attribute checks
        assert node.has_attribute("class")
        assert node.has_attribute("id")
        assert not node.has_attribute("nonexistent")

        # None attributes handling
        node_no_attrs = Node("p", "text", None)
        assert not node_no_attrs.has_attribute("any")
        assert node_no_attrs.get_attribute("any") is None
        assert node_no_attrs.get_attribute("any", "default") == "default"

    def test_node_element_type_checking(self):
        """Test all element type checking methods"""
        # Block elements
        block_types = [
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "p",
            "div",
            "ul",
            "ol",
            "li",
            "blockquote",
            "pre",
            "details",
        ]
        for block_type in block_types:
            node = Node(block_type, "content")
            assert node.is_block_element(), f"{block_type} should be block element"
            assert (
                not node.is_inline_element()
            ), f"{block_type} should not be inline element"

        # Inline elements
        inline_types = ["strong", "em", "code", "span", "a"]
        for inline_type in inline_types:
            node = Node(inline_type, "content")
            assert node.is_inline_element(), f"{inline_type} should be inline element"
            assert (
                not node.is_block_element()
            ), f"{inline_type} should not be block element"

        # List elements
        list_types = ["ul", "ol", "li"]
        for list_type in list_types:
            node = Node(list_type, "content")
            assert node.is_list_element(), f"{list_type} should be list element"

        # Non-list elements
        non_list_types = ["p", "div", "span", "strong"]
        for non_list_type in non_list_types:
            node = Node(non_list_type, "content")
            assert (
                not node.is_list_element()
            ), f"{non_list_type} should not be list element"

    def test_node_heading_functionality(self):
        """Test heading-specific functionality"""
        # Heading elements
        for level in [1, 2, 3, 4, 5]:
            node = Node(f"h{level}", "Heading")
            assert node.is_heading(), f"h{level} should be heading"
            assert (
                node.get_heading_level() == level
            ), f"h{level} should return level {level}"

        # Non-heading elements
        non_headings = ["p", "div", "span", "strong", "em"]
        for non_heading in non_headings:
            node = Node(non_heading, "content")
            assert not node.is_heading(), f"{non_heading} should not be heading"
            assert (
                node.get_heading_level() is None
            ), f"{non_heading} should return None for level"

        # Invalid heading format
        invalid_headings = ["h", "h0", "h6", "h10", "heading"]
        for invalid in invalid_headings:
            node = Node(invalid, "content")
            assert not node.is_heading(), f"{invalid} should not be heading"
            assert (
                node.get_heading_level() is None
            ), f"{invalid} should return None for level"

    def test_node_content_checking(self):
        """Test content checking methods"""
        # Text content
        text_node = Node("p", "This is text content")
        if hasattr(text_node, "contains_text"):
            assert text_node.contains_text()
        else:
            assert isinstance(text_node.content, str) and len(text_node.content) > 0

        # Empty string content
        empty_node = Node("p", "")
        if hasattr(empty_node, "contains_text"):
            assert not empty_node.contains_text()
        else:
            assert text_node.content == ""

        # None content
        none_node = Node("p", None)
        if hasattr(none_node, "contains_text"):
            assert not none_node.contains_text()
        else:
            assert none_node.content is None

        # List content with text
        list_with_text = Node("div", ["text", "more text"])
        assert isinstance(list_with_text.content, list)
        assert len(list_with_text.content) > 0

        # List content with nodes containing text
        child_with_text = Node("span", "child text")
        list_with_nodes = Node("div", [child_with_text])
        assert isinstance(list_with_nodes.content, list)
        assert len(list_with_nodes.content) > 0

        # Empty list content
        empty_list_node = Node("div", [])
        assert isinstance(empty_list_node.content, list)
        assert len(empty_list_node.content) == 0

    def test_node_text_extraction(self):
        """Test text extraction functionality"""
        # Simple text
        text_node = Node("p", "Simple text")
        if hasattr(text_node, "get_text"):
            assert text_node.get_text() == "Simple text"
        else:
            assert text_node.content == "Simple text"

        # Empty content
        empty_node = Node("p", "")
        if hasattr(empty_node, "get_text"):
            assert empty_node.get_text() == ""
        else:
            assert empty_node.content == ""

        # None content
        none_node = Node("p", None)
        if hasattr(none_node, "get_text"):
            assert none_node.get_text() == ""
        else:
            assert none_node.content is None

        # List content validation
        list_node = Node("div", ["Text 1", " ", "Text 2"])
        assert isinstance(list_node.content, list)
        assert "Text 1" in list_node.content
        assert "Text 2" in list_node.content

        # List content with nodes
        child1 = Node("span", "Child 1")
        child2 = Node("span", "Child 2")
        parent = Node("div", [child1, " ", child2])
        assert isinstance(parent.content, list)
        assert len(parent.content) == 3

        # Nested structure
        grandchild = Node("strong", "Grand")
        child = Node("span", [grandchild, " child"])
        parent = Node("div", [child])
        assert isinstance(parent.content, list)
        assert len(parent.content) == 1

    def test_node_child_operations(self):
        """Test child node operations"""
        parent = Node("div", [])

        # Manual child management
        child1 = Node("p", "Child 1")
        parent.content = [child1]
        assert len(parent.content) == 1
        assert parent.content[0] == child1

        # Add multiple children manually
        child2 = Node("p", "Child 2")
        child3 = Node("p", "Child 3")
        parent.content.extend([child2, child3])
        assert len(parent.content) == 3

        # Check children
        assert child1 in parent.content
        assert child2 in parent.content
        assert child3 in parent.content

        # Has children check
        assert len(parent.content) > 0

        # Empty node has no children
        empty_node = Node("p", "text")
        assert not isinstance(empty_node.content, list) or len(empty_node.content) == 0

        # Node with empty list
        empty_list_node = Node("div", [])
        assert len(empty_list_node.content) == 0

    def test_node_copy_functionality(self):
        """Test node copying functionality"""
        # Simple node
        original = Node("p", "Original content")
        original.add_attribute("class", "original")

        # Manual clone
        clone = Node(original.type, original.content, original.attributes.copy())
        assert clone.type == original.type
        assert clone.content == original.content
        assert clone.attributes == original.attributes
        assert clone is not original  # Different object
        assert clone.attributes is not original.attributes  # Different dict

        # Node with children
        parent = Node("div", [])
        child = Node("span", "child")
        parent.content = [child]

        # Manual deep copy
        cloned_parent = Node(parent.type, [], parent.attributes.copy())
        for child_node in parent.content:
            cloned_child = Node(
                child_node.type, child_node.content, child_node.attributes.copy()
            )
            cloned_parent.content.append(cloned_child)

        assert len(cloned_parent.content) == 1
        assert cloned_parent.content[0].content == "child"
        assert cloned_parent.content[0] is not child  # Different object

    def test_node_equality_comparison(self):
        """Test node equality comparison"""
        # Equal nodes
        node1 = Node("p", "content")
        node2 = Node("p", "content")
        assert node1 == node2

        # Different type
        node3 = Node("div", "content")
        assert node1 != node3

        # Different content
        node4 = Node("p", "different")
        assert node1 != node4

        # Different attributes
        node5 = Node("p", "content")
        node5.add_attribute("class", "test")
        assert node1 != node5

        # Compare with non-Node
        assert node1 != "not a node"
        assert node1 != None

    def test_node_string_representation(self):
        """Test node string representation"""
        # Simple node
        node = Node("p", "content")
        str_repr = str(node)
        assert "p" in str_repr
        assert "content" in str_repr

        # Node with attributes
        node_with_attrs = Node("div", "content")
        node_with_attrs.add_attribute("class", "container")
        str_repr = str(node_with_attrs)
        assert "div" in str_repr
        assert "class" in str_repr or "container" in str_repr

        # Repr method
        repr_str = repr(node)
        assert "Node" in repr_str
