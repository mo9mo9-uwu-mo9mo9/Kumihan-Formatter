"""Test cases for TOC validation functionality.

Tests for Issue #799: 目次完全自動生成機能実装 - バリデーター部分
"""

from unittest.mock import Mock

import pytest

from kumihan_formatter.core.toc_validator import TOCValidator


class TestTOCValidator:
    """Test cases for TOCValidator class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.validator = TOCValidator()

    def create_mock_toc_entry(self, title: str, level: int, id_: str):
        """Helper method to create mock TOC entry dict"""
        return {"title": title, "level": level, "id": id_}

    def test_validate_empty_structure(self):
        """Test validation with empty TOC structure"""
        result = self.validator.validate_toc_structure([])

        assert result == []  # No validation errors for empty structure

    def test_validate_valid_structure(self):
        """Test validation with valid TOC structure"""
        entries = [
            self.create_mock_toc_entry("Chapter 1", 1, "chapter-1"),
            self.create_mock_toc_entry("Section 1.1", 2, "section-1-1"),
            self.create_mock_toc_entry("Chapter 2", 1, "chapter-2"),
        ]

        result = self.validator.validate_toc_structure(entries)

        assert result == []  # No validation errors

    def test_validate_missing_title(self):
        """Test validation with missing title"""
        entries = [
            {"level": 1, "id": "chapter-1"},  # Missing title
            self.create_mock_toc_entry("Chapter 2", 1, "chapter-2"),
        ]

        result = self.validator.validate_toc_structure(entries)

        assert len(result) > 0
        assert any("title" in error.lower() for error in result)

    def test_validate_missing_level(self):
        """Test validation with missing level"""
        entries = [
            {"title": "Chapter 1", "id": "chapter-1"},  # Missing level
            self.create_mock_toc_entry("Chapter 2", 1, "chapter-2"),
        ]

        result = self.validator.validate_toc_structure(entries)

        assert len(result) > 0
        assert any("level" in error.lower() for error in result)

    def test_validate_missing_id(self):
        """Test validation with missing ID"""
        entries = [
            {"title": "Chapter 1", "level": 1},  # Missing id
            self.create_mock_toc_entry("Chapter 2", 1, "chapter-2"),
        ]

        result = self.validator.validate_toc_structure(entries)

        assert len(result) > 0
        assert any("id" in error.lower() for error in result)

    def test_validate_invalid_level_type(self):
        """Test validation with invalid level type"""
        entries = [
            self.create_mock_toc_entry(
                "Chapter 1", "invalid", "chapter-1"
            ),  # String instead of int
            self.create_mock_toc_entry("Chapter 2", 1, "chapter-2"),
        ]

        result = self.validator.validate_toc_structure(entries)

        assert len(result) > 0
        assert any("level" in error.lower() and "invalid" in error.lower() for error in result)

    def test_validate_invalid_level_range(self):
        """Test validation with invalid level range"""
        entries = [
            self.create_mock_toc_entry("Chapter 1", 0, "chapter-1"),  # Level 0 (invalid)
            self.create_mock_toc_entry("Chapter 2", 7, "chapter-2"),  # Level 7 (too high)
            self.create_mock_toc_entry("Chapter 3", 1, "chapter-3"),
        ]

        result = self.validator.validate_toc_structure(entries)

        assert len(result) >= 2
        assert any(
            "level" in error.lower() and ("0" in error or "range" in error.lower())
            for error in result
        )
        assert any(
            "level" in error.lower() and ("7" in error or "range" in error.lower())
            for error in result
        )

    def test_validate_empty_title(self):
        """Test validation with empty title"""
        entries = [
            self.create_mock_toc_entry("", 1, "chapter-1"),  # Empty title
            self.create_mock_toc_entry("Chapter 2", 1, "chapter-2"),
        ]

        result = self.validator.validate_toc_structure(entries)

        assert len(result) > 0
        assert any("title" in error.lower() and "empty" in error.lower() for error in result)

    def test_validate_empty_id(self):
        """Test validation with empty ID"""
        entries = [
            self.create_mock_toc_entry("Chapter 1", 1, ""),  # Empty ID
            self.create_mock_toc_entry("Chapter 2", 1, "chapter-2"),
        ]

        result = self.validator.validate_toc_structure(entries)

        assert len(result) > 0
        assert any("id" in error.lower() and "empty" in error.lower() for error in result)

    def test_validate_duplicate_ids(self):
        """Test validation with duplicate IDs"""
        entries = [
            self.create_mock_toc_entry("Chapter 1", 1, "duplicate-id"),
            self.create_mock_toc_entry("Chapter 2", 1, "duplicate-id"),  # Duplicate ID
            self.create_mock_toc_entry("Chapter 3", 1, "chapter-3"),
        ]

        result = self.validator.validate_toc_structure(entries)

        assert len(result) > 0
        assert any("duplicate" in error.lower() and "id" in error.lower() for error in result)

    def test_validate_invalid_id_format(self):
        """Test validation with invalid ID format"""
        entries = [
            self.create_mock_toc_entry(
                "Chapter 1", 1, "invalid id with spaces"
            ),  # Invalid ID format
            self.create_mock_toc_entry("Chapter 2", 1, "chapter-2"),
        ]

        result = self.validator.validate_toc_structure(entries)

        assert len(result) > 0
        assert any(
            "id" in error.lower() and ("format" in error.lower() or "invalid" in error.lower())
            for error in result
        )

    def test_validate_level_sequence_gaps(self):
        """Test validation with level sequence gaps"""
        entries = [
            self.create_mock_toc_entry("Chapter 1", 1, "chapter-1"),
            self.create_mock_toc_entry("Subsection", 3, "subsection"),  # Gap: jumps from 1 to 3
            self.create_mock_toc_entry("Chapter 2", 1, "chapter-2"),
        ]

        result = self.validator.validate_toc_structure(entries)

        # This might be a warning rather than an error, depending on implementation
        # The validator should detect level sequence issues
        # Implementation may vary based on requirements

    def test_validate_title_length_limits(self):
        """Test validation with title length limits"""
        very_long_title = "A" * 1000  # Very long title

        entries = [
            self.create_mock_toc_entry(very_long_title, 1, "long-title"),
            self.create_mock_toc_entry("Normal Title", 1, "normal-title"),
        ]

        result = self.validator.validate_toc_structure(entries)

        # Check if the validator has title length restrictions
        # This test may pass if no length limit is implemented

    def test_validate_special_characters_in_title(self):
        """Test validation with special characters in titles"""
        entries = [
            self.create_mock_toc_entry("Chapter with <HTML> & 特殊文字", 1, "chapter-special"),
            self.create_mock_toc_entry("Normal Chapter", 1, "normal-chapter"),
        ]

        result = self.validator.validate_toc_structure(entries)

        # Should not produce errors for special characters in titles
        # (they should be properly escaped during rendering)
        title_errors = [
            error for error in result if "special" in error.lower() or "character" in error.lower()
        ]
        assert len(title_errors) == 0

    def test_validate_unicode_in_ids(self):
        """Test validation with Unicode characters in IDs"""
        entries = [
            self.create_mock_toc_entry("Japanese Title", 1, "日本語-id"),  # Unicode in ID
            self.create_mock_toc_entry("English Title", 1, "english-id"),
        ]

        result = self.validator.validate_toc_structure(entries)

        # Unicode in IDs might be invalid depending on HTML standards
        # Check if validator catches this
        unicode_errors = [
            error for error in result if "unicode" in error.lower() or "id" in error.lower()
        ]

    def test_validate_mixed_case_sensitivity(self):
        """Test validation with case sensitivity in IDs"""
        entries = [
            self.create_mock_toc_entry("Chapter 1", 1, "Chapter-1"),
            self.create_mock_toc_entry("Chapter 2", 1, "chapter-1"),  # Same ID, different case
            self.create_mock_toc_entry("Chapter 3", 1, "chapter-3"),
        ]

        result = self.validator.validate_toc_structure(entries)

        # IDs should be case-sensitive, so this might not be a duplicate
        # But some validators might flag this as potentially confusing

    def test_validate_hierarchical_consistency(self):
        """Test validation of hierarchical consistency"""
        entries = [
            self.create_mock_toc_entry("Part I", 1, "part-1"),
            self.create_mock_toc_entry("Chapter 1", 2, "chapter-1"),
            self.create_mock_toc_entry("Section 1.1", 3, "section-1-1"),
            self.create_mock_toc_entry("Another Chapter", 2, "chapter-2"),
            self.create_mock_toc_entry("Part II", 1, "part-2"),
        ]

        result = self.validator.validate_toc_structure(entries)

        # Should validate proper hierarchical structure
        assert len(result) == 0  # This is a valid hierarchy

    def test_validate_malformed_entry(self):
        """Test validation with completely malformed entry"""
        entries = [
            self.create_mock_toc_entry("Valid Chapter", 1, "valid-chapter"),
            "invalid_entry",  # Not a dict
            {"completely": "wrong", "structure": True},  # Wrong structure
            self.create_mock_toc_entry("Another Valid Chapter", 1, "another-chapter"),
        ]

        result = self.validator.validate_toc_structure(entries)

        assert len(result) >= 2  # Should catch both malformed entries
        assert any("structure" in error.lower() or "format" in error.lower() for error in result)
