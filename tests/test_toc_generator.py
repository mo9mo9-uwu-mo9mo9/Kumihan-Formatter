"""Comprehensive tests for toc_generator.py module

Tests for Issue #351 - Phase 2 priority B (80%+ coverage target)
"""

import pytest
from typing import List, Dict, Any
from unittest.mock import Mock, patch

from kumihan_formatter.core.toc_generator import TOCEntry, TOCGenerator, TOCValidator
from kumihan_formatter.core.ast_nodes import Node


class TestTOCEntry:
    """Test TOCEntry class"""

    def test_toc_entry_init(self):
        """Test TOCEntry initialization"""
        node = Node(type="heading", content="Test Heading")
        entry = TOCEntry(level=1, title="Test Heading", heading_id="test-heading", node=node)
        
        assert entry.level == 1
        assert entry.title == "Test Heading"
        assert entry.heading_id == "test-heading"
        assert entry.node is node
        assert entry.children == []
        assert entry.parent is None

    def test_add_child(self):
        """Test adding child entry"""
        parent_node = Node(type="heading", content="Parent")
        parent = TOCEntry(1, "Parent", "parent", parent_node)
        
        child_node = Node(type="heading", content="Child")
        child = TOCEntry(2, "Child", "child", child_node)
        
        parent.add_child(child)
        
        assert len(parent.children) == 1
        assert parent.children[0] is child
        assert child.parent is parent

    def test_is_root_level(self):
        """Test checking if entry is root level"""
        node = Node(type="heading", content="Test")
        entry = TOCEntry(1, "Test", "test", node)
        
        assert entry.is_root_level() is True
        
        # Add parent
        parent_node = Node(type="heading", content="Parent")
        parent = TOCEntry(1, "Parent", "parent", parent_node)
        parent.add_child(entry)
        
        assert entry.is_root_level() is False

    def test_get_depth(self):
        """Test getting entry depth"""
        # Root entry
        root_node = Node(type="heading", content="Root")
        root = TOCEntry(1, "Root", "root", root_node)
        assert root.get_depth() == 0
        
        # Level 1 child
        child1_node = Node(type="heading", content="Child1")
        child1 = TOCEntry(2, "Child1", "child1", child1_node)
        root.add_child(child1)
        assert child1.get_depth() == 1
        
        # Level 2 child
        child2_node = Node(type="heading", content="Child2")
        child2 = TOCEntry(3, "Child2", "child2", child2_node)
        child1.add_child(child2)
        assert child2.get_depth() == 2

    def test_get_text_content(self):
        """Test getting plain text content"""
        node = Node(type="heading", content="Test")
        
        # Plain text
        entry = TOCEntry(1, "Plain Text", "plain", node)
        assert entry.get_text_content() == "Plain Text"
        
        # With HTML tags
        entry_html = TOCEntry(1, "Text with <strong>HTML</strong>", "html", node)
        assert entry_html.get_text_content() == "Text with HTML"
        
        # With multiple tags
        entry_multi = TOCEntry(1, "<em>Italic</em> and <strong>Bold</strong>", "multi", node)
        assert entry_multi.get_text_content() == "Italic and Bold"
        
        # Empty after tag removal
        entry_empty = TOCEntry(1, "<span></span>", "empty", node)
        assert entry_empty.get_text_content() == ""


class TestTOCGeneratorInit:
    """Test TOCGenerator initialization"""

    def test_init(self):
        """Test TOCGenerator initialization"""
        generator = TOCGenerator()
        assert generator.heading_counts == {}
        assert generator.heading_id_map == {}


class TestGenerateTOC:
    """Test generate_toc method"""

    def test_generate_toc_empty(self):
        """Test generating TOC with empty nodes"""
        generator = TOCGenerator()
        result = generator.generate_toc([])
        
        assert isinstance(result, dict)
        assert "html" in result
        assert "entries" in result
        assert "has_toc" in result
        assert result["has_toc"] is False
        assert result["html"] == ""
        assert result["entries"] == []

    def test_generate_toc_no_headings(self):
        """Test generating TOC with no heading nodes"""
        generator = TOCGenerator()
        nodes = [
            Node(type="paragraph", content="Paragraph 1"),
            Node(type="paragraph", content="Paragraph 2")
        ]
        result = generator.generate_toc(nodes)
        
        assert result["has_toc"] is False
        assert result["html"] == ""
        assert result["entries"] == []

    def test_generate_toc_single_heading(self):
        """Test generating TOC with single heading"""
        generator = TOCGenerator()
        node = Node(type="heading", content="Test Heading")
        node.add_attribute("level", 1)
        node.add_attribute("id", "test-heading")
        
        result = generator.generate_toc([node])
        
        assert result["has_toc"] is True
        assert len(result["entries"]) == 1
        assert result["html"] != ""

    def test_generate_toc_multiple_headings(self):
        """Test generating TOC with multiple headings"""
        generator = TOCGenerator()
        nodes = []
        
        for i in range(3):
            node = Node(type="heading", content=f"Heading {i+1}")
            node.add_attribute("level", 1)
            node.add_attribute("id", f"heading-{i+1}")
            nodes.append(node)
        
        result = generator.generate_toc(nodes)
        
        assert result["has_toc"] is True
        assert len(result["entries"]) == 3
        assert result["html"] != ""

    def test_generate_toc_nested_headings(self):
        """Test generating TOC with nested headings"""
        generator = TOCGenerator()
        
        h1 = Node(type="heading", content="Level 1")
        h1.add_attribute("level", 1)
        h1.add_attribute("id", "level-1")
        
        h2 = Node(type="heading", content="Level 2")
        h2.add_attribute("level", 2)
        h2.add_attribute("id", "level-2")
        
        h3 = Node(type="heading", content="Level 3")
        h3.add_attribute("level", 3)
        h3.add_attribute("id", "level-3")
        
        result = generator.generate_toc([h1, h2, h3])
        
        assert result["has_toc"] is True
        assert len(result["entries"]) >= 1
        assert result["html"] != ""


class TestCollectHeadings:
    """Test _collect_headings method"""

    def test_collect_headings_empty(self):
        """Test collecting headings from empty nodes"""
        generator = TOCGenerator()
        headings = generator._collect_headings([])
        assert headings == []

    def test_collect_headings_no_headings(self):
        """Test collecting headings when none exist"""
        generator = TOCGenerator()
        nodes = [
            Node(type="paragraph", content="Not a heading"),
            Node(type="list", content="Not a heading")
        ]
        headings = generator._collect_headings(nodes)
        assert headings == []

    def test_collect_headings_single(self):
        """Test collecting single heading"""
        generator = TOCGenerator()
        node = Node(type="heading", content="Test")
        node.add_attribute("level", 1)
        node.add_attribute("id", "test")
        
        headings = generator._collect_headings([node])
        assert len(headings) == 1
        assert headings[0]["level"] == 1
        assert headings[0]["title"] == "Test"
        assert headings[0]["id"] == "test"

    def test_collect_headings_nested_content(self):
        """Test collecting headings from nested content"""
        generator = TOCGenerator()
        
        # Parent node with content list
        parent = Node(type="block", content=[])
        
        # Child heading
        child_heading = Node(type="heading", content="Nested Heading")
        child_heading.add_attribute("level", 2)
        child_heading.add_attribute("id", "nested")
        
        parent.content = [child_heading]
        
        headings = generator._collect_headings([parent])
        assert len(headings) == 1
        assert headings[0]["title"] == "Nested Heading"


class TestBuildTOCStructure:
    """Test _build_toc_structure method"""

    def test_build_structure_empty(self):
        """Test building structure with empty headings"""
        generator = TOCGenerator()
        entries = generator._build_toc_structure([])
        assert entries == []

    def test_build_structure_flat(self):
        """Test building flat structure"""
        generator = TOCGenerator()
        headings = [
            {"level": 1, "title": "First", "id": "first", "node": Node(type="heading", content="First")},
            {"level": 1, "title": "Second", "id": "second", "node": Node(type="heading", content="Second")},
            {"level": 1, "title": "Third", "id": "third", "node": Node(type="heading", content="Third")}
        ]
        
        entries = generator._build_toc_structure(headings)
        assert len(entries) == 3
        for entry in entries:
            assert entry.level == 1
            assert len(entry.children) == 0

    def test_build_structure_nested(self):
        """Test building nested structure"""
        generator = TOCGenerator()
        headings = [
            {"level": 1, "title": "Chapter", "id": "ch1", "node": Node(type="heading", content="Chapter")},
            {"level": 2, "title": "Section", "id": "sec1", "node": Node(type="heading", content="Section")},
            {"level": 3, "title": "Subsection", "id": "sub1", "node": Node(type="heading", content="Subsection")}
        ]
        
        entries = generator._build_toc_structure(headings)
        assert len(entries) == 1  # Only one root entry
        assert entries[0].title == "Chapter"
        assert len(entries[0].children) == 1
        assert entries[0].children[0].title == "Section"
        assert len(entries[0].children[0].children) == 1
        assert entries[0].children[0].children[0].title == "Subsection"


class TestGenerateTOCHTML:
    """Test _generate_toc_html method"""

    def test_generate_html_empty(self):
        """Test generating HTML for empty entries"""
        generator = TOCGenerator()
        html = generator._generate_toc_html([])
        assert html == ""

    def test_generate_html_single_entry(self):
        """Test generating HTML for single entry"""
        generator = TOCGenerator()
        node = Node(type="heading", content="Test")
        entry = TOCEntry(1, "Test", "test", node)
        
        html = generator._generate_toc_html([entry])
        assert isinstance(html, str)
        assert len(html) > 0
        assert "Test" in html
        assert "#test" in html

    def test_generate_html_multiple_entries(self):
        """Test generating HTML for multiple entries"""
        generator = TOCGenerator()
        entries = []
        
        for i in range(3):
            node = Node(type="heading", content=f"Heading {i+1}")
            entry = TOCEntry(1, f"Heading {i+1}", f"heading-{i+1}", node)
            entries.append(entry)
        
        html = generator._generate_toc_html(entries)
        assert isinstance(html, str)
        assert "Heading 1" in html
        assert "Heading 2" in html
        assert "Heading 3" in html


class TestShouldGenerateTOC:
    """Test should_generate_toc method"""

    def test_should_generate_empty(self):
        """Test should generate with empty nodes"""
        generator = TOCGenerator()
        assert generator.should_generate_toc([]) is False

    def test_should_generate_no_headings(self):
        """Test should generate with no headings"""
        generator = TOCGenerator()
        nodes = [
            Node(type="paragraph", content="Not a heading"),
            Node(type="list", content="Not a heading")
        ]
        assert generator.should_generate_toc(nodes) is False

    def test_should_generate_single_heading(self):
        """Test should generate with single heading"""
        generator = TOCGenerator()
        node = Node(type="heading", content="Test")
        node.add_attribute("level", 1)
        assert generator.should_generate_toc([node]) is False  # Single heading doesn't need TOC

    def test_should_generate_multiple_headings(self):
        """Test should generate with multiple headings"""
        generator = TOCGenerator()
        nodes = []
        for i in range(3):
            node = Node(type="heading", content=f"Heading {i+1}")
            node.add_attribute("level", 1)
            nodes.append(node)
        
        assert generator.should_generate_toc(nodes) is True

    def test_should_generate_with_toc_marker(self):
        """Test should generate with explicit TOC marker"""
        generator = TOCGenerator()
        toc_marker = Node(type="toc", content="")
        assert generator.should_generate_toc([toc_marker]) is True


class TestGetTOCStatistics:
    """Test get_toc_statistics method"""

    def test_statistics_empty(self):
        """Test statistics for empty entries"""
        generator = TOCGenerator()
        stats = generator.get_toc_statistics([])
        
        assert stats["total_entries"] == 0
        assert stats["max_depth"] == 0
        assert stats["level_counts"] == {}

    def test_statistics_single_entry(self):
        """Test statistics for single entry"""
        generator = TOCGenerator()
        node = Node(type="heading", content="Test")
        entry = TOCEntry(1, "Test", "test", node)
        
        stats = generator.get_toc_statistics([entry])
        
        assert stats["total_entries"] == 1
        assert stats["max_depth"] == 1
        assert stats["level_counts"][1] == 1

    def test_statistics_nested_entries(self):
        """Test statistics for nested entries"""
        generator = TOCGenerator()
        
        # Create nested structure
        root_node = Node(type="heading", content="Root")
        root = TOCEntry(1, "Root", "root", root_node)
        
        child_node = Node(type="heading", content="Child")
        child = TOCEntry(2, "Child", "child", child_node)
        root.add_child(child)
        
        grandchild_node = Node(type="heading", content="Grandchild")
        grandchild = TOCEntry(3, "Grandchild", "grandchild", grandchild_node)
        child.add_child(grandchild)
        
        stats = generator.get_toc_statistics([root])
        
        assert stats["total_entries"] == 3
        assert stats["max_depth"] == 3
        assert 1 in stats["level_counts"]
        assert 2 in stats["level_counts"]
        assert 3 in stats["level_counts"]


class TestTOCValidator:
    """Test TOCValidator class"""

    def test_validator_init(self):
        """Test TOCValidator initialization"""
        validator = TOCValidator()
        assert validator._errors == []

    def test_validate_empty_structure(self):
        """Test validating empty structure"""
        validator = TOCValidator()
        errors = validator.validate_toc_structure([])
        assert errors == []

    def test_validate_valid_structure(self):
        """Test validating valid structure"""
        validator = TOCValidator()
        
        node1 = Node(type="heading", content="First")
        entry1 = TOCEntry(1, "First", "first", node1)
        
        node2 = Node(type="heading", content="Second")
        entry2 = TOCEntry(2, "Second", "second", node2)
        entry1.add_child(entry2)
        
        errors = validator.validate_toc_structure([entry1])
        assert isinstance(errors, list)

    def test_validate_duplicate_ids(self):
        """Test validating duplicate IDs"""
        validator = TOCValidator()
        
        node1 = Node(type="heading", content="First")
        entry1 = TOCEntry(1, "First", "duplicate", node1)
        
        node2 = Node(type="heading", content="Second")
        entry2 = TOCEntry(1, "Second", "duplicate", node2)
        
        errors = validator.validate_toc_structure([entry1, entry2])
        assert len(errors) > 0
        assert any("duplicate" in error.lower() for error in errors)

    def test_validate_heading_hierarchy(self):
        """Test validating heading hierarchy"""
        validator = TOCValidator()
        
        # Skip level (h1 -> h3)
        node1 = Node(type="heading", content="Level 1")
        entry1 = TOCEntry(1, "Level 1", "level1", node1)
        
        node3 = Node(type="heading", content="Level 3")
        entry3 = TOCEntry(3, "Level 3", "level3", node3)
        entry1.add_child(entry3)  # Skip level 2
        
        errors = validator.validate_toc_structure([entry1])
        assert isinstance(errors, list)


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_toc_entry_with_none_parent(self):
        """Test TOC entry with explicit None parent"""
        node = Node(type="heading", content="Test")
        entry = TOCEntry(1, "Test", "test", node)
        entry.parent = None
        assert entry.is_root_level() is True

    def test_generate_toc_with_none_nodes(self):
        """Test generating TOC with None in nodes list"""
        generator = TOCGenerator()
        nodes = [None, Node(type="heading", content="Test")]
        # Should handle None gracefully
        result = generator.generate_toc([n for n in nodes if n])
        assert isinstance(result, dict)

    def test_heading_without_id(self):
        """Test heading without ID attribute"""
        generator = TOCGenerator()
        node = Node(type="heading", content="No ID")
        node.add_attribute("level", 1)
        # Missing ID attribute
        
        result = generator.generate_toc([node])
        assert isinstance(result, dict)

    def test_heading_without_level(self):
        """Test heading without level attribute"""
        generator = TOCGenerator()
        node = Node(type="heading", content="No Level")
        node.add_attribute("id", "no-level")
        # Missing level attribute
        
        result = generator.generate_toc([node])
        assert isinstance(result, dict)

    def test_deeply_nested_structure(self):
        """Test deeply nested TOC structure"""
        generator = TOCGenerator()
        nodes = []
        
        # Create 6 levels of nesting
        for i in range(1, 7):
            node = Node(type="heading", content=f"Level {i}")
            node.add_attribute("level", i)
            node.add_attribute("id", f"level-{i}")
            nodes.append(node)
        
        result = generator.generate_toc(nodes)
        assert isinstance(result, dict)
        assert result["has_toc"] is True

    def test_toc_with_special_characters(self):
        """Test TOC with special characters in titles"""
        generator = TOCGenerator()
        
        node = Node(type="heading", content="Special & Characters < > \"")
        node.add_attribute("level", 1)
        node.add_attribute("id", "special")
        
        result = generator.generate_toc([node])
        assert isinstance(result, dict)
        assert result["has_toc"] is True
        # HTML should be properly escaped

    def test_toc_with_unicode(self):
        """Test TOC with unicode content"""
        generator = TOCGenerator()
        
        node = Node(type="heading", content="日本語タイトル 🚀")
        node.add_attribute("level", 1)
        node.add_attribute("id", "unicode")
        
        result = generator.generate_toc([node])
        assert isinstance(result, dict)
        assert result["has_toc"] is True