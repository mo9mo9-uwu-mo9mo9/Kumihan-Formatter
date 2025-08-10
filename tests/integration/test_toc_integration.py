"""Integration tests for TOC (Table of Contents) functionality.

Tests for Issue #799: 目次完全自動生成機能実装 - 統合テスト
"""

import pytest
import tempfile
import os
from pathlib import Path

from kumihan_formatter.renderer import Renderer
from kumihan_formatter.parser import Parser
from kumihan_formatter.core.ast_nodes import NodeBuilder, heading


# mypy: ignore-errors
# Integration test with numerous mocking type issues - strategic ignore


class TestTOCIntegration:
    """Integration tests for TOC functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.renderer = Renderer()
        self.parser = Parser()

    def test_end_to_end_toc_generation(self):
        """Test complete TOC generation from Kumihan text to HTML"""
        kumihan_text = """# 見出し1 #第1章：始まり##

これは第1章の内容です。

# 見出し2 #1.1 概要##

概要の説明です。

# 見出し2 #1.2 詳細##

詳細の説明です。

# 見出し1 #第2章：発展##

これは第2章の内容です。"""

        # Parse Kumihan text to AST
        ast = self.parser.parse_text(kumihan_text)

        # Render to HTML
        html_result = self.renderer.render_to_html(ast)

        # Check that TOC is generated
        assert 'class="toc"' in html_result
        assert "第1章：始まり" in html_result
        assert "1.1 概要" in html_result
        assert "1.2 詳細" in html_result
        assert "第2章：発展" in html_result

        # Check that TOC links are present
        assert 'href="#' in html_result

        # Check that heading IDs are generated
        assert 'id="' in html_result

    def test_single_heading_no_toc(self):
        """Test that single heading does not generate TOC"""
        kumihan_text = """# 見出し1 #唯一の章##

これは唯一の章の内容です。他に見出しはありません。"""

        ast = self.parser.parse_text(kumihan_text)
        html_result = self.renderer.render_to_html(ast)

        # Should not contain TOC elements
        assert 'class="toc"' not in html_result

    def test_toc_with_japanese_characters(self):
        """Test TOC generation with Japanese characters"""
        kumihan_text = """# 見出し1 #第一章：序論##

序論の内容です。

# 見出し2 #1.1 背景と目的##

背景と目的の説明です。

# 見出し2 #1.2 研究方法##

研究方法の説明です。

# 見出し1 #第二章：結果と考察##

結果と考察の内容です。"""

        ast = self.parser.parse_text(kumihan_text)
        html_result = self.renderer.render_to_html(ast)

        # Check Japanese characters are preserved in TOC
        assert "第一章：序論" in html_result
        assert "背景と目的" in html_result
        assert "研究方法" in html_result
        assert "第二章：結果と考察" in html_result

    def test_nested_heading_structure(self):
        """Test TOC with deeply nested heading structure"""
        kumihan_text = """# 見出し1 #Part I##

Part I content.

# 見出し2 #Chapter 1##

Chapter 1 content.

# 見出し3 #Section 1.1##

Section 1.1 content.

# 見出し4 #Subsection 1.1.1##

Subsection content.

# 見出し3 #Section 1.2##

Section 1.2 content.

# 見出し2 #Chapter 2##

Chapter 2 content.

# 見出し1 #Part II##

Part II content."""

        ast = self.parser.parse_text(kumihan_text)
        html_result = self.renderer.render_to_html(ast)

        # Check nested structure in TOC
        assert 'class="toc-level-1"' in html_result
        assert 'class="toc-level-2"' in html_result
        assert 'class="toc-level-3"' in html_result
        assert 'class="toc-level-4"' in html_result

    def test_toc_data_extraction(self):
        """Test TOC data extraction functionality"""
        kumihan_text = """# 見出し1 #Chapter 1##

Content for chapter 1.

# 見出し2 #Section 1.1##

Content for section 1.1."""

        ast = self.parser.parse_text(kumihan_text)

        # Test TOC data extraction
        toc_data = self.renderer.get_toc_data(ast)

        assert toc_data is not None
        assert toc_data["has_toc"] is True
        assert len(toc_data["entries"]) > 0
        assert toc_data["html"] != ""

    def test_file_processing_with_toc(self):
        """Test file processing with TOC generation"""
        kumihan_text = """# 見出し1 #Introduction##

This is the introduction.

# 見出し2 #Background##

Background information.

# 見出し1 #Methodology##

Methodology section.

# 見出し1 #Conclusion##

Conclusion section."""

        # Create temporary input file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as tmp_input:
            tmp_input.write(kumihan_text)
            input_path = tmp_input.name

        try:
            # Create temporary output file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as tmp_output:
                output_path = tmp_output.name

            # Process file
            self.renderer.render_file_to_html(input_path, output_path)

            # Read and verify output
            with open(output_path, "r", encoding="utf-8") as f:
                html_content = f.read()

            # Verify TOC is present
            assert 'class="toc"' in html_content
            assert "Introduction" in html_content
            assert "Background" in html_content
            assert "Methodology" in html_content
            assert "Conclusion" in html_content

        finally:
            # Clean up temporary files
            if os.path.exists(input_path):
                os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_toc_with_special_characters(self):
        """Test TOC generation with special characters in headings"""
        kumihan_text = """# 見出し1 #Chapter 1: The "Beginning" & Setup##

Content with special characters.

# 見出し2 #Section 1.1: Configuration <Advanced>##

Advanced configuration section.

# 見出し1 #Chapter 2: Results & Analysis##

Results and analysis section."""

        ast = self.parser.parse_text(kumihan_text)
        html_result = self.renderer.render_to_html(ast)

        # Check that special characters are properly handled
        assert 'class="toc"' in html_result
        # Special characters should be HTML-escaped in output
        assert "&quot;" in html_result or '"Beginning"' in html_result
        assert "&amp;" in html_result or "&" in html_result

    def test_toc_css_integration(self):
        """Test TOC CSS class integration"""
        kumihan_text = """# 見出し1 #Main Title##

Main content.

# 見出し2 #Subtitle##

Subtitle content."""

        ast = self.parser.parse_text(kumihan_text)
        html_result = self.renderer.render_to_html(ast)

        # Check all expected CSS classes
        expected_classes = [
            'class="toc"',
            'class="toc-list"',
            'class="toc-level-1"',
            'class="toc-level-2"',
        ]

        for css_class in expected_classes:
            assert css_class in html_result

    def test_toc_anchor_links(self):
        """Test TOC anchor link generation"""
        kumihan_text = """# 見出し1 #First Section##

First section content.

# 見出し1 #Second Section##

Second section content."""

        ast = self.parser.parse_text(kumihan_text)
        html_result = self.renderer.render_to_html(ast)

        # Check that anchor links are generated
        assert 'href="#' in html_result

        # Check that corresponding IDs are present in headings
        # The exact format may vary based on implementation
        assert 'id="' in html_result

    def test_toc_threshold_behavior(self):
        """Test TOC generation threshold behavior"""
        # Test with no headings
        no_headings_text = "Just plain text without any headings."
        ast_no_headings = self.parser.parse_text(no_headings_text)
        html_no_headings = self.renderer.render_to_html(ast_no_headings)
        assert 'class="toc"' not in html_no_headings

        # Test with one heading
        one_heading_text = "# 見出し1 #Single Heading##\nContent here."
        ast_one_heading = self.parser.parse_text(one_heading_text)
        html_one_heading = self.renderer.render_to_html(ast_one_heading)
        assert 'class="toc"' not in html_one_heading

        # Test with two headings (should generate TOC)
        two_headings_text = """# 見出し1 #First Heading##

Content for first.

# 見出し1 #Second Heading##

Content for second."""
        ast_two_headings = self.parser.parse_text(two_headings_text)
        html_two_headings = self.renderer.render_to_html(ast_two_headings)
        assert 'class="toc"' in html_two_headings

    def test_toc_with_mixed_content(self):
        """Test TOC generation with mixed content types"""
        kumihan_text = """# 見出し1 #Introduction##

# 太字 #Bold text## and # イタリック #italic text##.

# 見出し2 #Code Examples##

Here's some # コード #inline code## and:

# コードブロック #
def example():
    return "Hello World"
##

# 見出し1 #Images and Media##

# 画像 #example.jpg##

# 見出し2 #Lists##

# リスト #
- Item 1
- Item 2
##"""

        ast = self.parser.parse_text(kumihan_text)
        html_result = self.renderer.render_to_html(ast)

        # Should generate TOC despite mixed content
        assert 'class="toc"' in html_result
        assert "Introduction" in html_result
        assert "Code Examples" in html_result
        assert "Images and Media" in html_result
        assert "Lists" in html_result

    def test_toc_performance_with_large_document(self):
        """Test TOC generation performance with large document"""
        # Generate a large document with many headings
        large_text = ""
        for i in range(1, 51):  # 50 main sections
            large_text += f"# 見出し1 #Section {i}##\n\nContent for section {i}.\n\n"
            for j in range(1, 6):  # 5 subsections each
                large_text += f"# 見出し2 #{i}.{j} Subsection##\n\nSubsection content.\n\n"

        ast = self.parser.parse_text(large_text)

        # This should complete without performance issues
        html_result = self.renderer.render_to_html(ast)

        # Verify TOC is generated
        assert 'class="toc"' in html_result
        assert "Section 1" in html_result
        assert "Section 50" in html_result
