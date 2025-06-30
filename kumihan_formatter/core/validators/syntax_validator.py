"""Syntax validation for Kumihan documents

This module handles syntax-level validation including markers, lists,
and basic text structure.
"""

from typing import List, Optional

from ..block_parser import BlockParser, BlockValidator
from ..keyword_parser import KeywordParser, MarkerValidator
from ..list_parser import ListParser, ListValidator
from .validation_issue import ValidationIssue


class SyntaxValidator:
    """Validator for Kumihan syntax"""

    def __init__(self, config=None):
        """Initialize syntax validator"""
        self.config = config
        self.keyword_parser = KeywordParser(config)
        self.list_parser = ListParser(self.keyword_parser)
        self.block_parser = BlockParser(self.keyword_parser)

        # Initialize specialized validators
        self.marker_validator = MarkerValidator(self.keyword_parser)
        self.list_validator = ListValidator(self.list_parser)
        self.block_validator = BlockValidator(self.block_parser)

    def validate_encoding(self, text: str) -> List[ValidationIssue]:
        """Validate text encoding"""
        issues = []

        # Check for common encoding issues
        if "\ufffd" in text:  # Unicode replacement character
            issues.append(
                ValidationIssue(
                    level="error",
                    category="syntax",
                    message="Text contains invalid Unicode characters",
                    suggestion="Check file encoding (should be UTF-8)",
                    code="INVALID_UNICODE",
                )
            )

        # Check for mixed line endings
        if "\r\n" in text and "\n" in text.replace("\r\n", ""):
            issues.append(
                ValidationIssue(
                    level="warning",
                    category="syntax",
                    message="Mixed line endings detected",
                    suggestion="Use consistent line endings (LF or CRLF)",
                    code="MIXED_LINE_ENDINGS",
                )
            )

        return issues

    def validate_marker_syntax(self, lines: List[str]) -> List[ValidationIssue]:
        """Validate marker syntax in lines"""
        issues = []

        for i, line in enumerate(lines):
            # Check for invalid marker usage
            if ";;;" in line and not line.strip().startswith(";;;"):
                issues.append(
                    ValidationIssue(
                        level="error",
                        category="syntax",
                        message="Marker ;;; must be at the beginning of the line",
                        line_number=i + 1,
                        suggestion="Move ;;; to the start of the line",
                        code="INVALID_MARKER_POSITION",
                    )
                )

            # Validate marker syntax
            if line.strip().startswith(";;;"):
                is_valid, error_messages = self.marker_validator.validate_marker_line(
                    line.strip()
                )
                if not is_valid:
                    for error_msg in error_messages:
                        issues.append(
                            ValidationIssue(
                                level="error",
                                category="syntax",
                                message=error_msg,
                                line_number=i + 1,
                                code="INVALID_MARKER",
                            )
                        )

        return issues

    def validate_list_syntax(self, lines: List[str]) -> List[ValidationIssue]:
        """Validate list syntax in lines"""
        issues = []
        list_issue_messages = self.list_validator.validate_list_structure(lines)
        for msg in list_issue_messages:
            issues.append(
                ValidationIssue(
                    level="warning",
                    category="syntax",
                    message=msg,
                    code="LIST_STRUCTURE",
                )
            )
        return issues

    def validate_block_syntax(self, lines: List[str]) -> List[ValidationIssue]:
        """Validate block syntax in lines"""
        issues = []
        block_issue_messages = self.block_validator.validate_document_structure(lines)
        for msg in block_issue_messages:
            issues.append(
                ValidationIssue(
                    level="error",
                    category="syntax",
                    message=msg,
                    code="BLOCK_STRUCTURE",
                )
            )
        return issues
