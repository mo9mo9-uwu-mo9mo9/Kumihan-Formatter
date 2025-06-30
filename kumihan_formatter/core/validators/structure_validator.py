"""Structure validation for Kumihan documents

This module validates document structure including AST validation,
TOC structure, and document organization.
"""

from typing import Any, Dict, List, Optional

from ..ast_nodes import Node, validate_ast
from ..toc_generator import TOCValidator
from .validation_issue import ValidationIssue


class StructureValidator:
    """Validator for document structure"""

    def __init__(self):
        """Initialize structure validator"""
        self.toc_validator = TOCValidator()

    def validate_ast_structure(self, ast: List[Node]) -> List[ValidationIssue]:
        """Validate AST structure"""
        issues = []

        # AST structure validation
        ast_issues = validate_ast(ast)
        for issue in ast_issues:
            issues.append(
                ValidationIssue(
                    level="error",
                    category="structure",
                    message=issue,
                    code="INVALID_AST_STRUCTURE",
                )
            )

        return issues

    def validate_toc_structure(self, ast: List[Node]) -> List[ValidationIssue]:
        """Validate TOC structure"""
        issues = []

        # Extract TOC entries
        toc_entries = self._extract_toc_entries(ast)

        # Validate TOC structure
        toc_issues = self.toc_validator.validate_toc_structure(toc_entries)
        for issue in toc_issues:
            issues.append(
                ValidationIssue(
                    level="warning",
                    category="structure",
                    message=issue,
                    code="INVALID_TOC_STRUCTURE",
                )
            )

        return issues

    def validate_document_structure(self, lines: List[str]) -> List[ValidationIssue]:
        """Validate overall document structure"""
        issues = []

        # Check for empty document
        if not lines or all(not line.strip() for line in lines):
            issues.append(
                ValidationIssue(
                    level="warning",
                    category="structure",
                    message="Document is empty",
                    code="EMPTY_DOCUMENT",
                )
            )
            return issues

        # Check document length
        if len(lines) > 10000:
            issues.append(
                ValidationIssue(
                    level="warning",
                    category="structure",
                    message=f"Document is very long ({len(lines)} lines)",
                    suggestion="Consider splitting into multiple files",
                    code="VERY_LONG_DOCUMENT",
                )
            )

        # Check for proper heading structure
        heading_levels = []
        for i, line in enumerate(lines):
            if line.strip().startswith(";;;見出し"):
                level = self._extract_heading_level(line)
                if level:
                    heading_levels.append((i + 1, level))

        # Validate heading hierarchy
        if heading_levels:
            issues.extend(self._validate_heading_hierarchy(heading_levels))

        return issues

    def _extract_toc_entries(self, ast: List[Node]) -> List[Dict[str, Any]]:
        """Extract TOC entries from AST"""
        entries = []
        for node in ast:
            if hasattr(node, "type") and node.type == "heading":
                if hasattr(node, "level") and hasattr(node, "content"):
                    entries.append(
                        {
                            "level": node.level,
                            "text": node.content,
                            "id": getattr(node, "id", None),
                        }
                    )
        return entries

    def _extract_heading_level(self, line: str) -> Optional[int]:
        """Extract heading level from line"""
        import re

        match = re.match(r";;;見出し(\d)", line.strip())
        if match:
            return int(match.group(1))
        return None

    def _validate_heading_hierarchy(
        self, heading_levels: List[tuple]
    ) -> List[ValidationIssue]:
        """Validate heading hierarchy"""
        issues = []

        # Check for skipped levels
        prev_level = 0
        for line_num, level in heading_levels:
            if level > prev_level + 1:
                issues.append(
                    ValidationIssue(
                        level="warning",
                        category="structure",
                        message=f"Heading level skipped (from {prev_level} to {level})",
                        line_number=line_num,
                        suggestion="Use consecutive heading levels",
                        code="SKIPPED_HEADING_LEVEL",
                    )
                )
            prev_level = level

        return issues
