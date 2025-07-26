"""Tests for document validator module

This module tests the main document validator that coordinates
all validation components.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.ast_nodes import Node
from kumihan_formatter.core.validators.document_validator import DocumentValidator
from kumihan_formatter.core.validators.validation_issue import ValidationIssue


class TestDocumentValidator:
    """Test document validator functionality"""

    def setup_method(self):
        """Set up test environment"""
        self.validator = DocumentValidator()

    def test_init_without_config(self):
        """Test validator initialization without config"""
        validator = DocumentValidator()
        assert isinstance(validator, DocumentValidator)
        assert validator.config is None
        assert len(validator.issues) == 0

    def test_init_with_config(self):
        """Test validator initialization with config"""
        config = {"test": "value"}
        validator = DocumentValidator(config)
        assert validator.config == config

    def test_validate_text_valid_content(self):
        """Test validation of valid text content"""
        valid_text = "# Header\n\nValid content with no issues."

        # Mock all validators to return no issues
        with (
            patch.object(
                self.validator.syntax_validator, "validate_encoding", return_value=[]
            ),
            patch.object(
                self.validator.syntax_validator,
                "validate_marker_syntax",
                return_value=[],
            ),
            patch.object(
                self.validator.syntax_validator, "validate_list_syntax", return_value=[]
            ),
            patch.object(
                self.validator.syntax_validator,
                "validate_block_syntax",
                return_value=[],
            ),
            patch.object(
                self.validator.structure_validator,
                "validate_document_structure",
                return_value=[],
            ),
            patch.object(
                self.validator.performance_validator,
                "validate_memory_usage",
                return_value=[],
            ),
        ):

            issues = self.validator.validate_text(valid_text)
            assert len(issues) == 0

    def test_validate_text_with_issues(self):
        """Test validation of text with various issues"""
        problematic_text = "Invalid ;;; marker\n\ufffd Unicode issue"

        # Mock validators to return issues
        syntax_issues = [
            ValidationIssue("error", "syntax", "Invalid marker", code="INVALID_MARKER"),
            ValidationIssue(
                "error", "syntax", "Invalid Unicode", code="INVALID_UNICODE"
            ),
        ]

        with (
            patch.object(
                self.validator.syntax_validator,
                "validate_encoding",
                return_value=syntax_issues[:1],
            ),
            patch.object(
                self.validator.syntax_validator,
                "validate_marker_syntax",
                return_value=syntax_issues[1:],
            ),
            patch.object(
                self.validator.syntax_validator, "validate_list_syntax", return_value=[]
            ),
            patch.object(
                self.validator.syntax_validator,
                "validate_block_syntax",
                return_value=[],
            ),
            patch.object(
                self.validator.structure_validator,
                "validate_document_structure",
                return_value=[],
            ),
            patch.object(
                self.validator.performance_validator,
                "validate_memory_usage",
                return_value=[],
            ),
        ):

            issues = self.validator.validate_text(problematic_text)
            assert len(issues) == 2
            assert all(issue.level == "error" for issue in issues)

    def test_validate_ast_valid(self):
        """Test validation of valid AST"""
        mock_ast = [Mock(spec=Node)]

        with (
            patch.object(
                self.validator.structure_validator,
                "validate_ast_structure",
                return_value=[],
            ),
            patch.object(
                self.validator.structure_validator,
                "validate_toc_structure",
                return_value=[],
            ),
            patch.object(
                self.validator.performance_validator,
                "validate_ast_performance",
                return_value=[],
            ),
        ):

            issues = self.validator.validate_ast(mock_ast)
            assert len(issues) == 0

    def test_validate_ast_with_issues(self):
        """Test validation of AST with issues"""
        mock_ast = [Mock(spec=Node)]

        structure_issues = [
            ValidationIssue(
                "warning", "structure", "Missing header", code="MISSING_HEADER"
            )
        ]
        performance_issues = [
            ValidationIssue(
                "warning", "performance", "Deep nesting", code="DEEP_NESTING"
            )
        ]

        with (
            patch.object(
                self.validator.structure_validator,
                "validate_ast_structure",
                return_value=structure_issues,
            ),
            patch.object(
                self.validator.structure_validator,
                "validate_toc_structure",
                return_value=[],
            ),
            patch.object(
                self.validator.performance_validator,
                "validate_ast_performance",
                return_value=performance_issues,
            ),
        ):

            issues = self.validator.validate_ast(mock_ast)
            assert len(issues) == 2
            assert issues[0].category == "structure"
            assert issues[1].category == "performance"

    def test_validate_file_valid(self):
        """Test validation of valid file"""
        with tempfile.NamedTemporaryFile(
            suffix=".txt", mode="w", encoding="utf-8", delete=False
        ) as temp_file:
            temp_file.write("# Valid Content\n\nThis is valid content.")
            temp_file.flush()

            try:
                file_path = Path(temp_file.name)

                # Mock all validators to return no issues
                with (
                    patch.object(
                        self.validator.file_validator,
                        "validate_file_path",
                        return_value=[],
                    ),
                    patch.object(
                        self.validator.performance_validator,
                        "validate_file_size",
                        return_value=[],
                    ),
                    patch.object(self.validator, "validate_text", return_value=[]),
                ):

                    issues = self.validator.validate_file(file_path)
                    assert len(issues) == 0
            finally:
                os.unlink(temp_file.name)

    def test_validate_file_not_found(self):
        """Test validation of non-existent file"""
        non_existent_file = Path("/non/existent/file.txt")

        file_not_found_issue = ValidationIssue(
            "error", "file", "File not found", code="FILE_NOT_FOUND"
        )

        with patch.object(
            self.validator.file_validator,
            "validate_file_path",
            return_value=[file_not_found_issue],
        ):
            issues = self.validator.validate_file(non_existent_file)

            assert len(issues) == 1
            assert issues[0].code == "FILE_NOT_FOUND"

    def test_validate_file_read_error(self):
        """Test validation when file read fails"""
        with tempfile.NamedTemporaryFile(
            suffix=".txt", mode="w", encoding="utf-8", delete=False
        ) as temp_file:
            temp_file.write("Content")
            temp_file.flush()

            try:
                file_path = Path(temp_file.name)

                # Mock file validator to return no issues, but simulate read error
                with (
                    patch.object(
                        self.validator.file_validator,
                        "validate_file_path",
                        return_value=[],
                    ),
                    patch.object(
                        self.validator.performance_validator,
                        "validate_file_size",
                        return_value=[],
                    ),
                    patch("builtins.open", side_effect=IOError("Simulated read error")),
                ):

                    issues = self.validator.validate_file(file_path)

                    read_errors = [
                        issue for issue in issues if issue.code == "FILE_READ_ERROR"
                    ]
                    assert len(read_errors) == 1
                    assert "Simulated read error" in read_errors[0].message
            finally:
                os.unlink(temp_file.name)

    def test_validate_output_path(self):
        """Test output path validation delegation"""
        output_path = Path("/tmp/output.html")
        expected_issues = [
            ValidationIssue("warning", "file", "Output warning", code="OUTPUT_WARNING")
        ]

        with patch.object(
            self.validator.file_validator,
            "validate_output_path",
            return_value=expected_issues,
        ):
            issues = self.validator.validate_output_path(output_path)

            assert issues == expected_issues

    def test_get_error_count(self):
        """Test error count calculation"""
        self.validator.issues = [
            ValidationIssue("error", "test", "Error 1"),
            ValidationIssue("warning", "test", "Warning 1"),
            ValidationIssue("error", "test", "Error 2"),
            ValidationIssue("info", "test", "Info 1"),
        ]

        assert self.validator.get_error_count() == 2

    def test_get_warning_count(self):
        """Test warning count calculation"""
        self.validator.issues = [
            ValidationIssue("error", "test", "Error 1"),
            ValidationIssue("warning", "test", "Warning 1"),
            ValidationIssue("warning", "test", "Warning 2"),
            ValidationIssue("info", "test", "Info 1"),
        ]

        assert self.validator.get_warning_count() == 2

    def test_get_info_count(self):
        """Test info count calculation"""
        self.validator.issues = [
            ValidationIssue("error", "test", "Error 1"),
            ValidationIssue("warning", "test", "Warning 1"),
            ValidationIssue("info", "test", "Info 1"),
            ValidationIssue("info", "test", "Info 2"),
        ]

        assert self.validator.get_info_count() == 2

    def test_has_errors(self):
        """Test error detection"""
        # No errors
        self.validator.issues = [
            ValidationIssue("warning", "test", "Warning 1"),
            ValidationIssue("info", "test", "Info 1"),
        ]
        assert not self.validator.has_errors()

        # With errors
        self.validator.issues = [
            ValidationIssue("error", "test", "Error 1"),
            ValidationIssue("warning", "test", "Warning 1"),
        ]
        assert self.validator.has_errors()

    def test_clear_issues(self):
        """Test clearing validation issues"""
        self.validator.issues = [
            ValidationIssue("error", "test", "Error 1"),
            ValidationIssue("warning", "test", "Warning 1"),
        ]

        assert len(self.validator.issues) == 2

        self.validator.clear_issues()
        assert len(self.validator.issues) == 0

    def test_validate_text_clears_previous_issues(self):
        """Test that validate_text clears previous issues"""
        # Add some existing issues
        self.validator.issues = [
            ValidationIssue("error", "test", "Old error"),
        ]

        valid_text = "Valid content"

        # Mock all validators to return no issues
        with (
            patch.object(
                self.validator.syntax_validator, "validate_encoding", return_value=[]
            ),
            patch.object(
                self.validator.syntax_validator,
                "validate_marker_syntax",
                return_value=[],
            ),
            patch.object(
                self.validator.syntax_validator, "validate_list_syntax", return_value=[]
            ),
            patch.object(
                self.validator.syntax_validator,
                "validate_block_syntax",
                return_value=[],
            ),
            patch.object(
                self.validator.structure_validator,
                "validate_document_structure",
                return_value=[],
            ),
            patch.object(
                self.validator.performance_validator,
                "validate_memory_usage",
                return_value=[],
            ),
        ):

            issues = self.validator.validate_text(valid_text)

            # Should have cleared previous issues
            assert len(issues) == 0
            assert len(self.validator.issues) == 0

    def test_validate_ast_clears_previous_issues(self):
        """Test that validate_ast clears previous issues"""
        # Add some existing issues
        self.validator.issues = [
            ValidationIssue("error", "test", "Old error"),
        ]

        mock_ast = [Mock(spec=Node)]

        with (
            patch.object(
                self.validator.structure_validator,
                "validate_ast_structure",
                return_value=[],
            ),
            patch.object(
                self.validator.structure_validator,
                "validate_toc_structure",
                return_value=[],
            ),
            patch.object(
                self.validator.performance_validator,
                "validate_ast_performance",
                return_value=[],
            ),
        ):

            issues = self.validator.validate_ast(mock_ast)

            # Should have cleared previous issues
            assert len(issues) == 0
            assert len(self.validator.issues) == 0

    def test_validate_file_clears_previous_issues(self):
        """Test that validate_file clears previous issues"""
        # Add some existing issues
        self.validator.issues = [
            ValidationIssue("error", "test", "Old error"),
        ]

        with tempfile.NamedTemporaryFile(
            suffix=".txt", mode="w", encoding="utf-8", delete=False
        ) as temp_file:
            temp_file.write("Valid content")
            temp_file.flush()

            try:
                file_path = Path(temp_file.name)

                with (
                    patch.object(
                        self.validator.file_validator,
                        "validate_file_path",
                        return_value=[],
                    ),
                    patch.object(
                        self.validator.performance_validator,
                        "validate_file_size",
                        return_value=[],
                    ),
                    patch.object(self.validator, "validate_text", return_value=[]),
                ):

                    issues = self.validator.validate_file(file_path)

                    # Should have cleared previous issues
                    assert len(issues) == 0
                    assert len(self.validator.issues) == 0
            finally:
                os.unlink(temp_file.name)

    def test_integration_with_all_validators(self):
        """Test integration between all validator components"""
        test_text = "# Test Document\n\n;;;decoration;;; content ;;;\n\n1. List item"

        # This test verifies that all validators are called in the correct order
        with (
            patch.object(
                self.validator.syntax_validator, "validate_encoding"
            ) as mock_encoding,
            patch.object(
                self.validator.syntax_validator, "validate_marker_syntax"
            ) as mock_marker,
            patch.object(
                self.validator.syntax_validator, "validate_list_syntax"
            ) as mock_list,
            patch.object(
                self.validator.syntax_validator, "validate_block_syntax"
            ) as mock_block,
            patch.object(
                self.validator.structure_validator, "validate_document_structure"
            ) as mock_structure,
            patch.object(
                self.validator.performance_validator, "validate_memory_usage"
            ) as mock_memory,
        ):

            # Configure mocks to return empty lists
            mock_encoding.return_value = []
            mock_marker.return_value = []
            mock_list.return_value = []
            mock_block.return_value = []
            mock_structure.return_value = []
            mock_memory.return_value = []

            self.validator.validate_text(test_text)

            # Verify all validators were called
            mock_encoding.assert_called_once_with(test_text)
            mock_marker.assert_called_once()
            mock_list.assert_called_once()
            mock_block.assert_called_once()
            mock_structure.assert_called_once()
            mock_memory.assert_called_once_with(test_text)
