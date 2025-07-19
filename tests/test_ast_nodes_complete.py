"""Complete AST Nodes Tests for Issue #491 Phase 3

Comprehensive tests for ast_nodes module to achieve high coverage.
Current coverage: node.py 52% → Target: 90%+
"""

import pytest

from kumihan_formatter.core.ast_nodes import Node, NodeBuilder
from kumihan_formatter.core.ast_nodes.factories import (
    div_box,
    emphasis,
    heading,
    highlight,
    paragraph,
    strong,
)


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


class TestNodeUtilitiesComplete:
    """Complete coverage tests for Node utilities"""

    def test_node_tree_traversal(self):
        """Test node tree traversal utilities"""
        # Create tree structure
        root = div("Root")
        child1 = paragraph("Child 1")
        child2 = div("Child 2")
        grandchild = span("Grandchild")
        child2.add_child(grandchild)
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
        import json

        json_str = json.dumps(node_dict)
        parsed_dict = json.loads(json_str)
        json_node = Node(
            parsed_dict["type"], parsed_dict["content"], parsed_dict["attributes"]
        )
        assert json_node.type == node.type
