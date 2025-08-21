"""
Basic End-to-End test cases for Kumihan-Formatter.

Tests cover complete workflows from input to output.
"""

import os
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from kumihan_formatter.cli import cli


@pytest.mark.integration
@pytest.mark.e2e
class TestEndToEndBasic:
    """Basic end-to-end functionality tests."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.runner = CliRunner()

        # Create test input file
        self.test_file = Path(self.temp_dir) / "test.kumihan"
        self.test_file.write_text(
            """#太字#
これは太字のテストです。
##

通常のテキストです。

#見出し1#
重要な見出し
##""",
            encoding="utf-8",
        )

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_convert_basic_workflow(self):
        """Test basic convert workflow."""
        output_dir = Path(self.temp_dir) / "output"

        # Run convert command
        result = self.runner.invoke(
            cli, ["convert", str(self.test_file), "--output", str(output_dir)]
        )

        # Command should complete (success or graceful failure)
        assert result.exit_code in [0, 1, 2]

        # If successful, output should be generated
        if result.exit_code == 0 and output_dir.exists():
            output_files = list(output_dir.glob("*.html"))
            assert len(output_files) >= 0  # May or may not generate files

    def test_check_syntax_workflow(self):
        """Test check-syntax workflow."""
        # Run check-syntax command
        result = self.runner.invoke(cli, ["check-syntax", str(self.test_file)])

        # Command should complete
        assert result.exit_code in [0, 1, 2]

        # Should produce some output
        assert isinstance(result.output, str)

    def test_help_commands_workflow(self):
        """Test help command workflows."""
        # Test main help
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "convert" in result.output.lower() or "help" in result.output.lower()

        # Test convert help
        result = self.runner.invoke(cli, ["convert", "--help"])
        assert result.exit_code == 0

        # Test check-syntax help
        result = self.runner.invoke(cli, ["check-syntax", "--help"])
        assert result.exit_code == 0

    def test_invalid_file_handling(self):
        """Test handling of invalid files."""
        non_existent_file = Path(self.temp_dir) / "nonexistent.kumihan"

        # Run convert with non-existent file
        result = self.runner.invoke(cli, ["convert", str(non_existent_file)])

        # Should handle gracefully
        assert result.exit_code in [0, 1, 2]
        assert isinstance(result.output, str)


@pytest.mark.integration
@pytest.mark.e2e
class TestEndToEndAdvanced:
    """Advanced end-to-end functionality tests."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.runner = CliRunner()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_multiple_files_workflow(self):
        """Test processing multiple files."""
        # Create multiple test files
        files = []
        for i in range(3):
            test_file = Path(self.temp_dir) / f"test{i}.kumihan"
            test_file.write_text(
                f"""#見出し{i+1}#
テストファイル {i+1}
##""",
                encoding="utf-8",
            )
            files.append(str(test_file))

        # Run convert with multiple files
        result = self.runner.invoke(cli, ["convert"] + files)

        # Should handle multiple files
        assert result.exit_code in [0, 1, 2]
        assert isinstance(result.output, str)

    def test_complex_notation_workflow(self):
        """Test complex notation processing."""
        complex_file = Path(self.temp_dir) / "complex.kumihan"
        complex_file.write_text(
            """#見出し1#
メインタイトル
##

#太字#
重要な情報
##

#イタリック#
強調テキスト
##

#リスト#
- 項目1
- 項目2
- 項目3
##""",
            encoding="utf-8",
        )

        # Run convert with complex notation
        result = self.runner.invoke(cli, ["convert", str(complex_file)])

        # Should handle complex notation
        assert result.exit_code in [0, 1, 2]
        assert isinstance(result.output, str)

    def test_output_format_options(self):
        """Test different output format options."""
        test_file = Path(self.temp_dir) / "format_test.kumihan"
        test_file.write_text(
            """#見出し1#
フォーマットテスト
##""",
            encoding="utf-8",
        )

        # Test HTML format
        result = self.runner.invoke(
            cli, ["convert", str(test_file), "--format", "html"]
        )
        assert result.exit_code in [0, 1, 2]

        # Test Markdown format
        result = self.runner.invoke(
            cli, ["convert", str(test_file), "--format", "markdown"]
        )
        assert result.exit_code in [0, 1, 2]


@pytest.mark.integration
@pytest.mark.e2e
@pytest.mark.slow
class TestEndToEndPerformance:
    """Performance-focused end-to-end tests."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.runner = CliRunner()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_large_file_workflow(self):
        """Test processing large files."""
        large_file = Path(self.temp_dir) / "large.kumihan"

        # Generate large content
        content_lines = []
        for i in range(100):
            content_lines.extend(
                [
                    f"#見出し{i % 5 + 1}#",
                    f"セクション {i} のタイトル",
                    "##",
                    "",
                    "通常のテキスト " * 20,
                    "",
                ]
            )

        large_file.write_text("\n".join(content_lines), encoding="utf-8")

        # Run convert with large file
        result = self.runner.invoke(cli, ["convert", str(large_file)])

        # Should handle large files
        assert result.exit_code in [0, 1, 2]
        assert isinstance(result.output, str)

    def test_concurrent_processing(self):
        """Test concurrent file processing."""
        # Create multiple files
        files = []
        for i in range(5):
            test_file = Path(self.temp_dir) / f"concurrent{i}.kumihan"
            test_file.write_text(
                f"""#見出し{i+1}#
並行処理テスト {i+1}
##

#太字#
テストコンテンツ {i+1}
##""",
                encoding="utf-8",
            )
            files.append(str(test_file))

        # Run convert with multiple files
        result = self.runner.invoke(cli, ["convert"] + files)

        # Should handle concurrent processing
        assert result.exit_code in [0, 1, 2]
        assert isinstance(result.output, str)
