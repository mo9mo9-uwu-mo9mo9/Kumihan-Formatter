"""Syntax validation for Kumihan documents

This module handles syntax-level validation including markers, lists,
and basic text structure.
"""

from typing import Any, Union

from ..list_parser import ListParser
from ..list_validator import ListValidator
from ..parsing.block import BlockParser, BlockValidator
from ..parsing.keyword.keyword_parser import KeywordParser
from ..parsing.keyword.validator import KeywordValidator
from .validation_issue import ValidationIssue


class SyntaxValidator:
    """Validator for Kumihan syntax"""

    def __init__(self, config: Union[dict[str, Any], None] = None) -> None:
        """Initialize syntax validator"""
        self.config = config

        # Initialize specialized validators
        from ..parsing.keyword.definitions import KeywordDefinitions

        definitions = KeywordDefinitions()
        self.keyword_parser = KeywordParser(definitions)
        self.list_parser = ListParser()
        self.block_parser = BlockParser(self.keyword_parser)
        self.marker_validator = KeywordValidator(definitions)
        self.list_validator = ListValidator(self.list_parser)
        self.block_validator = BlockValidator(self.block_parser)

    def validate_encoding(self, text: str) -> list[ValidationIssue]:
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

    def validate_marker_syntax(self, lines: list[str]) -> list[ValidationIssue]:
        """Validate marker syntax in lines"""
        # ;;;記法は削除されました（Phase 1完了）
        return []

    def validate_list_syntax(self, lines: list[str]) -> list[ValidationIssue]:
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

    def validate_block_syntax(self, lines: list[str]) -> list[ValidationIssue]:
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
