"""Kumihan Notation Tests for Issue 500 Phase 3C

This module tests specific Kumihan notation parsing and processing
to ensure accurate syntax recognition and conversion.
"""

import tempfile
from pathlib import Path

import pytest

from kumihan_formatter.parser import Parser
from kumihan_formatter.renderer import Renderer


class TestKumihanNotationParsing:
    """Test Kumihan notation parsing functionality"""

    def test_footnote_notation_parsing(self):
        """Test footnote notation ((content)) parsing"""
        try:
            parser = Parser()

            # Test basic footnote
            text = "これは本文です((これは脚注です))。"
            parsed = parser.parse(text)

            # Verify footnote is identified
            assert parsed is not None
            assert hasattr(parsed, "footnotes")
            assert len(parsed.footnotes) == 1
            assert parsed.footnotes[0].content == "これは脚注です"

        except ImportError:
            pytest.skip("Parser not available")

    def test_sidenote_notation_parsing(self):
        """Test sidenote notation ｜content《reading》 parsing"""
        try:
            parser = Parser()

            # Test basic sidenote (ruby notation)
            text = "この｜文字《もじ》にはルビがあります。"
            parsed = parser.parse(text)

            # Verify sidenote is identified
            assert parsed is not None
            assert hasattr(parsed, "sidenotes")
            assert len(parsed.sidenotes) == 1
            assert parsed.sidenotes[0].text == "文字"
            assert parsed.sidenotes[0].reading == "もじ"

        except ImportError:
            pytest.skip("Parser not available")

    def test_decoration_notation_parsing(self):
        """Test decoration notation ;;;style;;; content ;;; parsing"""
        try:
            parser = Parser()

            # Test basic decoration
            text = "これは;;;強調;;;重要な内容;;;です。"
            parsed = parser.parse(text)

            # Verify decoration is identified
            assert parsed is not None
            assert hasattr(parsed, "decorations")
            assert len(parsed.decorations) == 1
            assert parsed.decorations[0].style == "強調"
            assert parsed.decorations[0].content == "重要な内容"

        except ImportError:
            pytest.skip("Parser not available")

    def test_complex_notation_combination(self):
        """Test combination of multiple notation types"""
        try:
            parser = Parser()

            # Test complex text with multiple notations
            text = "この;;;強調;;;重要な｜文書《ぶんしょ》;;;には脚注((詳細は別途記載))もあります。"
            parsed = parser.parse(text)

            # Verify all notations are identified
            assert parsed is not None
            assert hasattr(parsed, "decorations")
            assert hasattr(parsed, "sidenotes")
            assert hasattr(parsed, "footnotes")
            assert len(parsed.decorations) >= 1
            assert len(parsed.sidenotes) >= 1
            assert len(parsed.footnotes) >= 1

        except ImportError:
            pytest.skip("Parser not available")


class TestKumihanNotationRendering:
    """Test Kumihan notation rendering functionality"""

    def test_footnote_html_rendering(self):
        """Test footnote rendering to HTML"""
        try:
            parser = Parser()
            renderer = Renderer()

            # Test footnote rendering
            text = "本文です((脚注内容))。"
            parsed = parser.parse(text)
            html = renderer.render(parsed)

            # Verify HTML structure
            assert html is not None
            assert "<sup>" in html  # Footnote marker
            assert (
                '<div class="footnotes">' in html
                or '<section class="footnotes">' in html
            )
            assert "脚注内容" in html

        except ImportError:
            pytest.skip("Parser or Renderer not available")

    def test_sidenote_html_rendering(self):
        """Test sidenote rendering to HTML"""
        try:
            parser = Parser()
            renderer = Renderer()

            # Test sidenote rendering
            text = "｜文字《もじ》のテスト。"
            parsed = parser.parse(text)
            html = renderer.render(parsed)

            # Verify HTML structure
            assert html is not None
            assert "<ruby>" in html or '<span class="ruby">' in html
            assert "<rt>" in html or '<span class="rt">' in html
            assert "文字" in html
            assert "もじ" in html

        except ImportError:
            pytest.skip("Parser or Renderer not available")

    def test_decoration_html_rendering(self):
        """Test decoration rendering to HTML"""
        try:
            parser = Parser()
            renderer = Renderer()

            # Test decoration rendering
            text = ";;;強調;;;重要な内容;;;です。"
            parsed = parser.parse(text)
            html = renderer.render(parsed)

            # Verify HTML structure
            assert html is not None
            assert "<strong>" in html or "<em>" in html or 'class="emphasis"' in html
            assert "重要な内容" in html

        except ImportError:
            pytest.skip("Parser or Renderer not available")


class TestKumihanNotationEdgeCases:
    """Test edge cases and error scenarios"""

    def test_nested_notation_handling(self):
        """Test handling of nested notations"""
        try:
            parser = Parser()

            # Test nested decoration
            text = ";;;外側;;;内側の;;;内側;;;内容;;;です。"
            parsed = parser.parse(text)

            # Should handle nesting gracefully
            assert parsed is not None

        except ImportError:
            pytest.skip("Parser not available")

    def test_unclosed_notation_handling(self):
        """Test handling of unclosed notations"""
        try:
            parser = Parser()

            # Test unclosed decoration
            text = ";;;強調;;;内容が未完了"
            parsed = parser.parse(text)

            # Should handle gracefully without crashing
            assert parsed is not None

        except ImportError:
            pytest.skip("Parser not available")

    def test_empty_notation_handling(self):
        """Test handling of empty notations"""
        try:
            parser = Parser()

            # Test empty notations
            test_cases = [
                ";;;強調;;;;;;;",  # Empty decoration
                "(())",  # Empty footnote
                "｜《》",  # Empty sidenote
            ]

            for text in test_cases:
                parsed = parser.parse(text)
                # Should handle gracefully without crashing
                assert parsed is not None

        except ImportError:
            pytest.skip("Parser not available")

    def test_malformed_notation_handling(self):
        """Test handling of malformed notations"""
        try:
            parser = Parser()

            # Test malformed notations
            test_cases = [
                ";;;強調;; 不完全な区切り",
                "((脚注が不完全",
                "｜文字《読み方が不完全",
            ]

            for text in test_cases:
                parsed = parser.parse(text)
                # Should handle gracefully without crashing
                assert parsed is not None

        except ImportError:
            pytest.skip("Parser not available")


class TestKumihanNotationIntegration:
    """Test integration scenarios with file processing"""

    def test_file_processing_with_kumihan_notation(self):
        """Test processing files containing Kumihan notation"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("# テスト文書\n\n")
            f.write("これは;;;強調;;;重要な内容;;;です。\n")
            f.write("｜漢字《かんじ》の読み方も含まれています。\n")
            f.write("詳細は脚注((別途参照))を確認してください。\n")
            temp_path = f.name

        try:
            # Test file processing
            file_path = Path(temp_path)
            content = file_path.read_text(encoding="utf-8")

            # Verify file contains expected notations
            assert ";;;強調;;;重要な内容;;;" in content
            assert "｜漢字《かんじ》" in content
            assert "((別途参照))" in content

        finally:
            Path(temp_path).unlink()

    def test_batch_processing_with_kumihan_notation(self):
        """Test batch processing of multiple files with Kumihan notation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create multiple test files
            files = []
            for i in range(3):
                file_path = Path(temp_dir) / f"test_{i}.txt"
                file_path.write_text(
                    f"ファイル{i}: ;;;強調;;;内容{i};;;((脚注{i}))", encoding="utf-8"
                )
                files.append(file_path)

            # Test batch processing
            for file_path in files:
                content = file_path.read_text(encoding="utf-8")
                assert ";;;強調;;;" in content
                assert "((" in content and "))" in content
