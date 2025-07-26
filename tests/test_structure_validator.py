"""Tests for structure validator module

This module tests document structure validation including AST validation,
TOC structure, and document organization.
"""

from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.ast_nodes import Node
from kumihan_formatter.core.validators.structure_validator import StructureValidator
from kumihan_formatter.core.validators.validation_issue import ValidationIssue


class TestStructureValidator:
    """Test structure validator functionality"""

    def setup_method(self):
        """Set up test environment"""
        self.validator = StructureValidator()

    def test_init(self):
        """Test validator initialization"""
        validator = StructureValidator()
        assert isinstance(validator, StructureValidator)
        assert hasattr(validator, "toc_validator")

    def test_validate_ast_structure_valid(self):
        """Test validation of valid AST structure"""
        mock_ast = [Mock(spec=Node)]

        with patch(
            "kumihan_formatter.core.validators.structure_validator.validate_ast"
        ) as mock_validate:
            mock_validate.return_value = []

            issues = self.validator.validate_ast_structure(mock_ast)
            assert len(issues) == 0

    def test_validate_ast_structure_invalid(self):
        """Test validation of invalid AST structure"""
        mock_ast = [Mock(spec=Node)]

        with patch(
            "kumihan_formatter.core.validators.structure_validator.validate_ast"
        ) as mock_validate:
            mock_validate.return_value = [
                "Invalid node structure",
                "Missing required field",
            ]

            issues = self.validator.validate_ast_structure(mock_ast)

            assert len(issues) == 2
            assert all(issue.level == "error" for issue in issues)
            assert all(issue.category == "structure" for issue in issues)
            assert all(issue.code == "INVALID_AST_STRUCTURE" for issue in issues)

    def test_validate_toc_structure_valid(self):
        """Test validation of valid TOC structure"""
        # Create mock nodes with heading structure
        mock_nodes = []
        for i, level in enumerate([1, 2, 3]):
            mock_node = Mock(spec=Node)
            mock_node.type = "heading"
            mock_node.level = level
            mock_node.content = f"Heading {level}"
            mock_node.id = f"heading-{i}"
            mock_nodes.append(mock_node)

        with patch.object(
            self.validator.toc_validator, "validate_toc_structure"
        ) as mock_validate:
            mock_validate.return_value = []

            issues = self.validator.validate_toc_structure(mock_nodes)
            assert len(issues) == 0

    def test_validate_toc_structure_invalid(self):
        """Test validation of invalid TOC structure"""
        mock_nodes = [Mock(spec=Node)]
        mock_nodes[0].type = "heading"
        mock_nodes[0].level = 1
        mock_nodes[0].content = "Heading"

        with patch.object(
            self.validator.toc_validator, "validate_toc_structure"
        ) as mock_validate:
            mock_validate.return_value = ["Invalid TOC hierarchy"]

            issues = self.validator.validate_toc_structure(mock_nodes)

            assert len(issues) == 1
            assert issues[0].level == "warning"
            assert issues[0].category == "structure"
            assert issues[0].code == "INVALID_TOC_STRUCTURE"

    def test_validate_document_structure_empty_document(self):
        """Test validation of empty document"""
        empty_lines = []
        issues = self.validator.validate_document_structure(empty_lines)

        assert len(issues) == 1
        assert issues[0].level == "warning"
        assert issues[0].code == "EMPTY_DOCUMENT"

    def test_validate_document_structure_whitespace_only(self):
        """Test validation of document with only whitespace"""
        whitespace_lines = ["   ", "\t\t", "", "  \n  "]
        issues = self.validator.validate_document_structure(whitespace_lines)

        assert len(issues) == 1
        assert issues[0].level == "warning"
        assert issues[0].code == "EMPTY_DOCUMENT"

    def test_validate_document_structure_very_long_document(self):
        """Test validation of very long document"""
        long_lines = [f"Line {i}" for i in range(10001)]
        issues = self.validator.validate_document_structure(long_lines)

        long_doc_issues = [
            issue for issue in issues if issue.code == "VERY_LONG_DOCUMENT"
        ]
        assert len(long_doc_issues) == 1
        assert long_doc_issues[0].level == "warning"
        assert "10001 lines" in long_doc_issues[0].message

    def test_validate_document_structure_valid_headings(self):
        """Test validation of document with valid heading hierarchy"""
        valid_lines = [
            "# Introduction",
            "Content here",
            ";;;見出し1;;; Main Section ;;;",
            "More content",
            ";;;見出し2;;; Subsection ;;;",
            "Subsection content",
        ]

        issues = self.validator.validate_document_structure(valid_lines)

        # Should not have heading hierarchy issues
        heading_issues = [
            issue for issue in issues if issue.code == "SKIPPED_HEADING_LEVEL"
        ]
        assert len(heading_issues) == 0

    def test_validate_document_structure_skipped_heading_levels(self):
        """Test validation of document with skipped heading levels"""
        invalid_lines = [
            "Content here",
            ";;;見出し1;;; Main Section ;;;",
            "More content",
            ";;;見出し3;;; Skipped level 2 ;;;",  # Skips level 2
            "Content",
        ]

        issues = self.validator.validate_document_structure(invalid_lines)

        # Should have heading hierarchy issue
        heading_issues = [
            issue for issue in issues if issue.code == "SKIPPED_HEADING_LEVEL"
        ]
        assert len(heading_issues) == 1
        assert heading_issues[0].level == "warning"
        assert heading_issues[0].line_number == 4

    def test_extract_toc_entries_with_headings(self):
        """Test extraction of TOC entries from AST with headings"""
        mock_nodes = []

        # Create heading nodes
        for i, (level, content) in enumerate([(1, "Main"), (2, "Sub"), (1, "Another")]):
            mock_node = Mock(spec=Node)
            mock_node.type = "heading"
            mock_node.level = level
            mock_node.content = content
            mock_node.id = f"heading-{i}"
            mock_nodes.append(mock_node)

        # Create non-heading node
        text_node = Mock(spec=Node)
        text_node.type = "paragraph"
        mock_nodes.append(text_node)

        entries = self.validator._extract_toc_entries(mock_nodes)

        assert len(entries) == 3  # Only heading nodes
        assert entries[0]["level"] == 1
        assert entries[0]["text"] == "Main"
        assert entries[1]["level"] == 2
        assert entries[1]["text"] == "Sub"

    def test_extract_toc_entries_no_headings(self):
        """Test extraction of TOC entries from AST without headings"""
        mock_nodes = [Mock(spec=Node)]
        mock_nodes[0].type = "paragraph"

        entries = self.validator._extract_toc_entries(mock_nodes)
        assert len(entries) == 0

    def test_extract_toc_entries_missing_attributes(self):
        """Test extraction with nodes missing required attributes"""
        mock_node = Mock(spec=Node)
        mock_node.type = "heading"
        # Missing level and content attributes

        entries = self.validator._extract_toc_entries([mock_node])
        assert len(entries) == 0

    def test_extract_heading_level_valid(self):
        """Test extraction of heading level from valid lines"""
        test_cases = [
            (";;;見出し1;;; Title ;;;", 1),
            (";;;見出し2;;; Subtitle ;;;", 2),
            (";;;見出し3;;; Sub-subtitle ;;;", 3),
            ("   ;;;見出し2;;; Indented ;;;", 2),
        ]

        for line, expected_level in test_cases:
            level = self.validator._extract_heading_level(line)
            assert level == expected_level

    def test_extract_heading_level_invalid(self):
        """Test extraction of heading level from invalid lines"""
        invalid_lines = [
            "Regular text",
            ";;;decoration;;; Not a heading ;;;",
            ";;;見出し;;; Missing level ;;;",
            ";;;見出しa;;; Non-numeric ;;;",
        ]

        for line in invalid_lines:
            level = self.validator._extract_heading_level(line)
            assert level is None

        # Special case: level 0 is technically extracted but might be considered invalid
        level_0_line = ";;;見出し0;;; Invalid level ;;;"
        level = self.validator._extract_heading_level(level_0_line)
        # The function extracts 0, but this might be considered invalid in context
        assert level == 0  # The function does extract 0

    def test_validate_heading_hierarchy_valid(self):
        """Test validation of valid heading hierarchy"""
        valid_hierarchy = [(1, 1), (2, 2), (3, 2), (4, 3), (5, 1)]

        issues = self.validator._validate_heading_hierarchy(valid_hierarchy)
        assert len(issues) == 0

    def test_validate_heading_hierarchy_skipped_levels(self):
        """Test validation of heading hierarchy with skipped levels"""
        invalid_hierarchy = [(1, 1), (2, 3), (3, 2)]  # Skips level 2 initially

        issues = self.validator._validate_heading_hierarchy(invalid_hierarchy)

        assert len(issues) == 1
        assert issues[0].level == "warning"
        assert issues[0].code == "SKIPPED_HEADING_LEVEL"
        assert issues[0].line_number == 2
        assert "from 1 to 3" in issues[0].message

    def test_validate_heading_hierarchy_multiple_skips(self):
        """Test validation with multiple heading level skips"""
        invalid_hierarchy = [(1, 2), (2, 4), (3, 1)]  # Skip from 0 to 2, then 2 to 4

        issues = self.validator._validate_heading_hierarchy(invalid_hierarchy)

        assert len(issues) == 2
        skip_issues = [
            issue for issue in issues if issue.code == "SKIPPED_HEADING_LEVEL"
        ]
        assert len(skip_issues) == 2

    def test_validate_heading_hierarchy_empty(self):
        """Test validation of empty heading hierarchy"""
        empty_hierarchy = []

        issues = self.validator._validate_heading_hierarchy(empty_hierarchy)
        assert len(issues) == 0

    def test_integration_document_with_headings_and_content(self):
        """Test integration with realistic document structure"""
        document_lines = [
            "# Document Title",
            "",
            "Introduction paragraph.",
            "",
            ";;;見出し1;;; Chapter 1 ;;;",
            "Chapter content here.",
            "",
            ";;;見出し2;;; Section 1.1 ;;;",
            "Section content.",
            "",
            ";;;見出し2;;; Section 1.2 ;;;",
            "More section content.",
            "",
            ";;;見出し1;;; Chapter 2 ;;;",
            "Second chapter content.",
        ]

        issues = self.validator.validate_document_structure(document_lines)

        # Should have no structural issues
        structural_issues = [
            issue
            for issue in issues
            if issue.code in ["SKIPPED_HEADING_LEVEL", "EMPTY_DOCUMENT"]
        ]
        assert len(structural_issues) == 0

    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        # Single line document
        single_line = ["Only one line"]
        issues = self.validator.validate_document_structure(single_line)
        empty_issues = [issue for issue in issues if issue.code == "EMPTY_DOCUMENT"]
        assert len(empty_issues) == 0

        # Document with exactly 10000 lines (boundary)
        boundary_lines = [f"Line {i}" for i in range(10000)]
        issues = self.validator.validate_document_structure(boundary_lines)
        long_doc_issues = [
            issue for issue in issues if issue.code == "VERY_LONG_DOCUMENT"
        ]
        assert len(long_doc_issues) == 0

    def test_extract_toc_entries_with_node_without_id(self):
        """Test TOC extraction when nodes don't have id attribute"""
        mock_node = Mock(spec=Node)
        mock_node.type = "heading"
        mock_node.level = 1
        mock_node.content = "Heading"
        # No id attribute

        entries = self.validator._extract_toc_entries([mock_node])

        assert len(entries) == 1
        assert entries[0]["id"] is None
