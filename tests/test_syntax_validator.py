"""Tests for syntax validator module

This module tests syntax validation functionality including encoding,
markers, lists, and block structure validation.
"""

from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.core.validators.syntax_validator import SyntaxValidator
from kumihan_formatter.core.validators.validation_issue import ValidationIssue


class TestSyntaxValidator:
    """Test syntax validator functionality"""

    def setup_method(self):
        """Set up test environment"""
        self.validator = SyntaxValidator()

    def test_init_without_config(self):
        """Test validator initialization without config"""
        validator = SyntaxValidator()
        assert isinstance(validator, SyntaxValidator)
        assert validator.config is None

    def test_init_with_config(self):
        """Test validator initialization with config"""
        config = {"test": "value"}
        validator = SyntaxValidator(config)
        assert validator.config == config

    def test_validate_encoding_valid_text(self):
        """Test validation of text with valid encoding"""
        valid_text = "This is valid UTF-8 text\nWith multiple lines"
        issues = self.validator.validate_encoding(valid_text)
        assert len(issues) == 0

    def test_validate_encoding_invalid_unicode(self):
        """Test validation of text with invalid Unicode characters"""
        invalid_text = "This text contains \ufffd replacement character"
        issues = self.validator.validate_encoding(invalid_text)

        assert len(issues) == 1
        assert issues[0].level == "error"
        assert issues[0].category == "syntax"
        assert issues[0].code == "INVALID_UNICODE"
        assert "Unicode" in issues[0].message

    def test_validate_encoding_mixed_line_endings(self):
        """Test validation of text with mixed line endings"""
        mixed_text = "Line 1\r\nLine 2\nLine 3"
        issues = self.validator.validate_encoding(mixed_text)

        assert len(issues) == 1
        assert issues[0].level == "warning"
        assert issues[0].category == "syntax"
        assert issues[0].code == "MIXED_LINE_ENDINGS"
        assert "line endings" in issues[0].message.lower()

    def test_validate_marker_syntax_valid_markers(self):
        """Test validation of valid marker syntax"""
        valid_lines = [
            ";;;decoration;;; content ;;;",
            "Regular text line",
            ";;;another;;; more content ;;;",
        ]

        with patch.object(
            self.validator.marker_validator, "validate_marker_line"
        ) as mock_validate:
            mock_validate.return_value = (True, [])
            issues = self.validator.validate_marker_syntax(valid_lines)

        # Should have no issues for valid markers
        marker_errors = [
            issue
            for issue in issues
            if issue.code in ["INVALID_MARKER_POSITION", "INVALID_MARKER"]
        ]
        assert len(marker_errors) == 0

    def test_validate_marker_syntax_invalid_position(self):
        """Test validation of markers in invalid positions"""
        invalid_lines = [
            "Some text ;;; marker not at start",
            "Regular text line",
        ]

        issues = self.validator.validate_marker_syntax(invalid_lines)

        # Should have error for invalid marker position
        position_errors = [
            issue for issue in issues if issue.code == "INVALID_MARKER_POSITION"
        ]
        assert len(position_errors) == 1
        assert position_errors[0].level == "error"
        assert position_errors[0].line_number == 1

    def test_validate_marker_syntax_invalid_marker_format(self):
        """Test validation of invalid marker format"""
        invalid_lines = [
            ";;;invalid_marker;;; content",
            "Regular text line",
        ]

        with patch.object(
            self.validator.marker_validator, "validate_marker_line"
        ) as mock_validate:
            mock_validate.return_value = (False, ["Invalid marker format"])
            issues = self.validator.validate_marker_syntax(invalid_lines)

        # Should have error for invalid marker format
        format_errors = [issue for issue in issues if issue.code == "INVALID_MARKER"]
        assert len(format_errors) == 1
        assert format_errors[0].level == "error"
        assert format_errors[0].line_number == 1

    def test_validate_list_syntax_valid_lists(self):
        """Test validation of valid list syntax"""
        valid_lines = [
            "1. First item",
            "2. Second item",
            "   - Sub item",
            "3. Third item",
        ]

        with patch.object(
            self.validator.list_validator, "validate_list_structure"
        ) as mock_validate:
            mock_validate.return_value = []
            issues = self.validator.validate_list_syntax(valid_lines)

        assert len(issues) == 0

    def test_validate_list_syntax_invalid_lists(self):
        """Test validation of invalid list syntax"""
        invalid_lines = [
            "1. First item",
            "3. Wrong numbering",  # Should be 2
            "   - Sub item",
        ]

        with patch.object(
            self.validator.list_validator, "validate_list_structure"
        ) as mock_validate:
            mock_validate.return_value = ["Invalid list numbering"]
            issues = self.validator.validate_list_syntax(invalid_lines)

        assert len(issues) == 1
        assert issues[0].level == "warning"
        assert issues[0].category == "syntax"
        assert issues[0].code == "LIST_STRUCTURE"

    def test_validate_block_syntax_valid_blocks(self):
        """Test validation of valid block syntax"""
        valid_lines = [
            "# Header",
            "Content paragraph",
            "",
            "## Subheader",
            "More content",
        ]

        with patch.object(
            self.validator.block_validator, "validate_document_structure"
        ) as mock_validate:
            mock_validate.return_value = []
            issues = self.validator.validate_block_syntax(valid_lines)

        assert len(issues) == 0

    def test_validate_block_syntax_invalid_blocks(self):
        """Test validation of invalid block syntax"""
        invalid_lines = [
            "### Subheader without main header",
            "Content paragraph",
        ]

        with patch.object(
            self.validator.block_validator, "validate_document_structure"
        ) as mock_validate:
            mock_validate.return_value = ["Missing main header"]
            issues = self.validator.validate_block_syntax(invalid_lines)

        assert len(issues) == 1
        assert issues[0].level == "error"
        assert issues[0].category == "syntax"
        assert issues[0].code == "BLOCK_STRUCTURE"

    def test_complex_validation_scenario(self):
        """Test complex validation scenario with multiple issues"""
        complex_text = "Line 1\r\nLine 2\nInvalid ;;; marker\n\ufffd invalid char"
        complex_lines = complex_text.split("\n")

        # Test encoding validation
        encoding_issues = self.validator.validate_encoding(complex_text)
        assert (
            len(encoding_issues) >= 1
        )  # Should detect mixed line endings and invalid unicode

        # Test marker validation
        marker_issues = self.validator.validate_marker_syntax(complex_lines)
        marker_position_errors = [
            issue for issue in marker_issues if issue.code == "INVALID_MARKER_POSITION"
        ]
        assert len(marker_position_errors) >= 1

    def test_empty_input_handling(self):
        """Test handling of empty inputs"""
        # Empty text
        issues = self.validator.validate_encoding("")
        assert len(issues) == 0

        # Empty lines
        issues = self.validator.validate_marker_syntax([])
        assert len(issues) == 0

        issues = self.validator.validate_list_syntax([])
        assert len(issues) == 0

        issues = self.validator.validate_block_syntax([])
        assert len(issues) == 0

    def test_whitespace_only_lines(self):
        """Test validation of lines with only whitespace"""
        whitespace_lines = [
            "   ",
            "\t\t",
            "",
            "  \n  ",
        ]

        # These should not cause errors
        issues = self.validator.validate_marker_syntax(whitespace_lines)
        marker_errors = [
            issue
            for issue in issues
            if issue.code in ["INVALID_MARKER_POSITION", "INVALID_MARKER"]
        ]
        assert len(marker_errors) == 0

    def test_line_number_accuracy(self):
        """Test that line numbers in issues are accurate"""
        test_lines = [
            "Line 1",
            "Invalid ;;; marker position",  # Line 2
            "Line 3",
            "Another invalid ;;; marker",  # Line 4
        ]

        issues = self.validator.validate_marker_syntax(test_lines)
        position_errors = [
            issue for issue in issues if issue.code == "INVALID_MARKER_POSITION"
        ]

        # Should have errors on lines 2 and 4
        line_numbers = [issue.line_number for issue in position_errors]
        assert 2 in line_numbers
        assert 4 in line_numbers

    def test_unicode_handling(self):
        """Test handling of various Unicode characters"""
        unicode_text = "こんにちは世界\n한글\n العربية\n🌍🚀"
        issues = self.validator.validate_encoding(unicode_text)

        # Valid Unicode should not cause issues
        unicode_errors = [issue for issue in issues if issue.code == "INVALID_UNICODE"]
        assert len(unicode_errors) == 0

    def test_validation_issue_properties(self):
        """Test that validation issues have correct properties"""
        invalid_text = "Text with \ufffd and mixed\r\nline\nendings"
        issues = self.validator.validate_encoding(invalid_text)

        for issue in issues:
            assert isinstance(issue, ValidationIssue)
            assert issue.level in ["error", "warning", "info"]
            assert issue.category == "syntax"
            assert isinstance(issue.message, str)
            assert len(issue.message) > 0
            if issue.code:
                assert isinstance(issue.code, str)

    def test_marker_validator_integration(self):
        """Test integration with marker validator"""
        lines_with_markers = [
            ";;;valid;;; content ;;;",
            "normal text",
            ";;;invalid marker format",
        ]

        # Mock the marker validator to test different responses
        with patch.object(
            self.validator.marker_validator, "validate_marker_line"
        ) as mock_validate:
            # First call (valid marker) returns True
            # Second call (invalid marker) returns False with error
            mock_validate.side_effect = [
                (True, []),
                (False, ["Missing closing markers"]),
            ]

            issues = self.validator.validate_marker_syntax(lines_with_markers)

            # Should have one invalid marker error
            invalid_marker_errors = [
                issue for issue in issues if issue.code == "INVALID_MARKER"
            ]
            assert len(invalid_marker_errors) == 1
            assert "Missing closing markers" in invalid_marker_errors[0].message
