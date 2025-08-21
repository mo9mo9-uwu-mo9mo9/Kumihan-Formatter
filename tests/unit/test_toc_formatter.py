"""Test cases for TOC formatting functionality.

Tests for Issue #799: 目次完全自動生成機能実装 - フォーマッター部分
"""

import json
from unittest.mock import Mock

import pytest

from kumihan_formatter.core.toc_formatter import TOCFormatter
from kumihan_formatter.core.toc_generator import TOCEntry


class TestTOCFormatter:
    """Test cases for TOCFormatter class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.formatter = TOCFormatter()

    def create_mock_toc_entry(self, title: str, level: int, id_: str, children=None):
        """Helper method to create mock TOC entry"""
        entry = Mock(spec=TOCEntry)
        entry.title = title
        entry.level = level
        entry.heading_id = id_
        entry.children = children or []
        entry.get_text_content = Mock(return_value=title)
        return entry

    def test_format_html_empty_entries(self):
        """Test HTML formatting with empty entries list"""
        result = self.formatter.format_html([])

        assert result == ""

    def test_format_html_single_entry(self):
        """Test HTML formatting with single entry"""
        entries = [self.create_mock_toc_entry("Chapter 1", 1, "chapter-1")]

        result = self.formatter.format_html(entries)

        assert '<div class="toc">' in result
        assert '<ul class="toc-list">' in result
        assert 'class="toc-level-1"' in result
        assert 'href="#chapter-1"' in result
        assert "Chapter 1" in result
        assert "</div>" in result

    def test_format_html_nested_entries(self):
        """Test HTML formatting with nested entries"""
        child_entries = [
            self.create_mock_toc_entry("Section 1.1", 2, "section-1-1"),
            self.create_mock_toc_entry("Section 1.2", 2, "section-1-2"),
        ]

        entries = [
            self.create_mock_toc_entry("Chapter 1", 1, "chapter-1", child_entries)
        ]

        result = self.formatter.format_html(entries)

        # Check main structure
        assert '<div class="toc">' in result
        assert 'class="toc-level-1"' in result
        assert "Chapter 1" in result

        # Check nested structure
        assert 'class="toc-level-2"' in result
        assert "Section 1.1" in result
        assert "Section 1.2" in result
        assert 'href="#section-1-1"' in result
        assert 'href="#section-1-2"' in result

    def test_format_html_multiple_levels(self):
        """Test HTML formatting with multiple heading levels"""
        subsection = [
            self.create_mock_toc_entry("Subsection 1.1.1", 3, "subsection-1-1-1")
        ]

        section = [
            self.create_mock_toc_entry("Section 1.1", 2, "section-1-1", subsection)
        ]

        entries = [self.create_mock_toc_entry("Chapter 1", 1, "chapter-1", section)]

        result = self.formatter.format_html(entries)

        assert 'class="toc-level-1"' in result
        assert 'class="toc-level-2"' in result
        assert 'class="toc-level-3"' in result
        assert "Chapter 1" in result
        assert "Section 1.1" in result
        assert "Subsection 1.1.1" in result

    def test_format_html_special_characters(self):
        """Test HTML formatting with special characters in titles"""
        entries = [
            self.create_mock_toc_entry(
                "Chapter & Section: 日本語", 1, "chapter-section-japanese"
            )
        ]

        result = self.formatter.format_html(entries)

        # Special characters should be HTML escaped
        assert "Chapter &amp; Section: 日本語" in result
        assert 'href="#chapter-section-japanese"' in result

    def test_format_html_css_classes(self):
        """Test proper CSS class application"""
        entries = [
            self.create_mock_toc_entry("Title 1", 1, "title-1"),
            self.create_mock_toc_entry("Title 2", 2, "title-2"),
            self.create_mock_toc_entry("Title 3", 3, "title-3"),
        ]

        result = self.formatter.format_html(entries)

        # Check all expected CSS classes are present
        assert 'class="toc"' in result
        assert 'class="toc-list"' in result
        assert 'class="toc-level-1"' in result
        assert 'class="toc-level-2"' in result
        assert 'class="toc-level-3"' in result

    def test_format_json_empty_entries(self):
        """Test JSON formatting with empty entries list"""
        result = self.formatter.format_json([])

        json_data = json.loads(result)
        assert json_data == []

    def test_format_json_single_entry(self):
        """Test JSON formatting with single entry"""
        entries = [self.create_mock_toc_entry("Chapter 1", 1, "chapter-1")]

        result = self.formatter.format_json(entries)
        json_data = json.loads(result)

        assert len(json_data) == 1
        assert json_data[0]["title"] == "Chapter 1"
        assert json_data[0]["level"] == 1
        assert json_data[0]["id"] == "chapter-1"
        assert json_data[0]["children"] == []

    def test_format_json_nested_entries(self):
        """Test JSON formatting with nested entries"""
        child_entries = [self.create_mock_toc_entry("Section 1.1", 2, "section-1-1")]

        entries = [
            self.create_mock_toc_entry("Chapter 1", 1, "chapter-1", child_entries)
        ]

        result = self.formatter.format_json(entries)
        json_data = json.loads(result)

        assert len(json_data) == 1
        chapter = json_data[0]
        assert chapter["title"] == "Chapter 1"
        assert len(chapter["children"]) == 1
        assert chapter["children"][0]["title"] == "Section 1.1"

    def test_format_json_japanese_characters(self):
        """Test JSON formatting preserves Japanese characters"""
        entries = [self.create_mock_toc_entry("第1章：始まり", 1, "chapter-1")]

        result = self.formatter.format_json(entries)
        json_data = json.loads(result)

        assert json_data[0]["title"] == "第1章：始まり"
        # Verify JSON is properly formatted with Japanese characters
        assert "第1章：始まり" in result

    def test_format_plain_text_empty_entries(self):
        """Test plain text formatting with empty entries list"""
        result = self.formatter.format_plain_text([])

        assert result.strip() == ""

    def test_format_plain_text_single_entry(self):
        """Test plain text formatting with single entry"""
        entries = [self.create_mock_toc_entry("Chapter 1", 1, "chapter-1")]

        result = self.formatter.format_plain_text(entries)

        assert "Chapter 1" in result
        assert "1." in result  # Should include numbering

    def test_format_plain_text_nested_entries(self):
        """Test plain text formatting with nested structure"""
        child_entries = [
            self.create_mock_toc_entry("Section 1.1", 2, "section-1-1"),
            self.create_mock_toc_entry("Section 1.2", 2, "section-1-2"),
        ]

        entries = [
            self.create_mock_toc_entry("Chapter 1", 1, "chapter-1", child_entries)
        ]

        result = self.formatter.format_plain_text(entries)

        # Check indentation and structure
        lines = result.strip().split("\n")
        assert any("Chapter 1" in line for line in lines)
        assert any("Section 1.1" in line for line in lines)
        assert any("Section 1.2" in line for line in lines)

        # Check that subsections are indented
        chapter_line = next(line for line in lines if "Chapter 1" in line)
        section_lines = [line for line in lines if "Section" in line]

        # Sections should be more indented than chapter
        for section_line in section_lines:
            assert len(section_line) - len(section_line.lstrip()) > len(
                chapter_line
            ) - len(chapter_line.lstrip())

    def test_format_markdown_empty_entries(self):
        """Test Markdown formatting with empty entries list"""
        result = self.formatter.format_markdown([])

        assert result.strip() == ""

    def test_format_markdown_single_entry(self):
        """Test Markdown formatting with single entry"""
        entries = [self.create_mock_toc_entry("Chapter 1", 1, "chapter-1")]

        result = self.formatter.format_markdown(entries)

        assert "[Chapter 1](#chapter-1)" in result
        assert "- " in result  # Should use bullet points

    def test_format_markdown_nested_entries(self):
        """Test Markdown formatting with nested structure"""
        child_entries = [self.create_mock_toc_entry("Section 1.1", 2, "section-1-1")]

        entries = [
            self.create_mock_toc_entry("Chapter 1", 1, "chapter-1", child_entries)
        ]

        result = self.formatter.format_markdown(entries)

        assert "[Chapter 1](#chapter-1)" in result
        assert "[Section 1.1](#section-1-1)" in result

        # Check indentation (nested items should have more spaces)
        lines = result.strip().split("\n")
        chapter_line = next(line for line in lines if "Chapter 1" in line)
        section_line = next(line for line in lines if "Section 1.1" in line)

        chapter_indent = len(chapter_line) - len(chapter_line.lstrip())
        section_indent = len(section_line) - len(section_line.lstrip())

        assert section_indent > chapter_indent

    def test_html_escaping(self):
        """Test proper HTML escaping in HTML output"""
        entries = [
            self.create_mock_toc_entry(
                'Title with <tags> & "quotes"', 1, "title-with-tags"
            )
        ]

        result = self.formatter.format_html(entries)

        # HTML should be properly escaped
        assert "&lt;tags&gt;" in result
        assert "&amp;" in result
        assert "&quot;" in result
        assert "<tags>" not in result  # Should not contain unescaped HTML

    def test_format_with_custom_css_classes(self):
        """Test HTML formatting with custom CSS classes"""
        entries = [self.create_mock_toc_entry("Chapter 1", 1, "chapter-1")]

        # Test with custom CSS class configuration
        custom_formatter = TOCFormatter(
            css_classes={
                "container": "custom-toc",
                "list": "custom-list",
                "item": "custom-item",
            }
        )

        result = custom_formatter.format_html(entries)

        assert 'class="custom-toc"' in result
        assert 'class="custom-list"' in result
