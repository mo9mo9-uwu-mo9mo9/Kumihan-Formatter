"""Main document validator for Kumihan-Formatter

This module coordinates all validation components to provide
comprehensive document validation.
"""

from pathlib import Path

from ..ast_nodes import Node
from .file_validator import FileValidator
from .performance_validator import PerformanceValidator
from .structure_validator import StructureValidator
from .syntax_validator import SyntaxValidator
from .validation_issue import ValidationIssue


class DocumentValidator:
    """Main validator that coordinates all validation components"""

    def __init__(self, config=None):
        """Initialize document validator with all sub-validators"""
        self.config = config

        # Initialize all validators
        self.syntax_validator = SyntaxValidator(config)
        self.structure_validator = StructureValidator()
        self.performance_validator = PerformanceValidator(config)
        self.file_validator = FileValidator()

        self.issues: list[ValidationIssue] = []

    def validate_text(self, text: str) -> list[ValidationIssue]:
        """
        Validate raw text input

        Args:
            text: Raw text to validate

        Returns:
            list[ValidationIssue]: List of validation issues
        """
        self.issues = []
        lines = text.split("\n")

        # Syntax validation
        self.issues.extend(self.syntax_validator.validate_encoding(text))
        self.issues.extend(self.syntax_validator.validate_marker_syntax(lines))
        self.issues.extend(self.syntax_validator.validate_list_syntax(lines))
        self.issues.extend(self.syntax_validator.validate_block_syntax(lines))

        # Structure validation
        self.issues.extend(self.structure_validator.validate_document_structure(lines))

        # Performance validation
        self.issues.extend(self.performance_validator.validate_memory_usage(text))

        return self.issues

    def validate_ast(self, ast: list[Node]) -> list[ValidationIssue]:
        """
        Validate parsed AST

        Args:
            ast: Parsed AST to validate

        Returns:
            list[ValidationIssue]: List of validation issues
        """
        self.issues = []

        # Structure validation
        self.issues.extend(self.structure_validator.validate_ast_structure(ast))
        self.issues.extend(self.structure_validator.validate_toc_structure(ast))

        # Performance validation
        self.issues.extend(self.performance_validator.validate_ast_performance(ast))

        return self.issues

    def validate_file(self, file_path: Path) -> list[ValidationIssue]:
        """
        Validate a file

        Args:
            file_path: Path to file to validate

        Returns:
            list[ValidationIssue]: List of validation issues
        """
        self.issues = []

        # File validation
        file_issues = self.file_validator.validate_file_path(file_path)
        self.issues.extend(file_issues)

        # If file is not accessible, stop here
        if any(issue.code == "FILE_NOT_FOUND" for issue in file_issues):
            return self.issues

        # Content validation
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            self.issues.extend(self.validate_text(text))
        except Exception as e:
            self.issues.append(
                ValidationIssue(
                    level="error",
                    category="file",
                    message=f"Error reading file: {str(e)}",
                    code="FILE_READ_ERROR",
                )
            )

        return self.issues

    def validate_output_path(self, output_path: Path) -> list[ValidationIssue]:
        """
        Validate output path

        Args:
            output_path: Path to output file

        Returns:
            list[ValidationIssue]: List of validation issues
        """
        return self.file_validator.validate_output_path(output_path)

    def get_error_count(self) -> int:
        """Get count of error-level issues"""
        return sum(1 for issue in self.issues if issue.is_error())

    def get_warning_count(self) -> int:
        """Get count of warning-level issues"""
        return sum(1 for issue in self.issues if issue.is_warning())

    def get_info_count(self) -> int:
        """Get count of info-level issues"""
        return sum(1 for issue in self.issues if issue.is_info())

    def has_errors(self) -> bool:
        """Check if there are any error-level issues"""
        return any(issue.is_error() for issue in self.issues)

    def clear_issues(self) -> None:
        """Clear all validation issues"""
        self.issues = []
