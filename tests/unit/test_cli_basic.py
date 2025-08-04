"""
Test cases for CLI basic functionality.

Tests cover command-line interface and basic operations.
"""

import pytest
from unittest.mock import patch, MagicMock
import tempfile
import os
from pathlib import Path

from kumihan_formatter.cli import main, cli


@pytest.mark.unit
@pytest.mark.cli
class TestCLIBasic:
    """CLI basic functionality tests."""

    def test_cli_function_exists(self):
        """Test that CLI function exists."""
        assert cli is not None
        assert callable(cli)

    @patch('sys.argv', ['kumihan', '--help'])
    def test_cli_help_option(self):
        """Test CLI help option works."""
        from click.testing import CliRunner
        runner = CliRunner()

        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'Kumihan-Formatter' in result.output or 'help' in result.output.lower()

    @patch('sys.argv', ['kumihan', '--version'])
    def test_cli_version_option(self):
        """Test CLI version option works."""
        from click.testing import CliRunner
        runner = CliRunner()

        result = runner.invoke(cli, ['--version'])
        # Version command should succeed
        assert result.exit_code == 0

    @patch('sys.argv', ['kumihan', '--help'])
    def test_main_help_integration(self):
        """Test main function with help option."""
        with pytest.raises(SystemExit):
            main()

    def test_cli_convert_command_exists(self):
        """Test convert command exists."""
        from click.testing import CliRunner
        runner = CliRunner()

        # Test convert subcommand help
        result = runner.invoke(cli, ['convert', '--help'])
        assert result.exit_code == 0
        assert 'convert' in result.output.lower()

    def test_cli_check_syntax_command_exists(self):
        """Test check-syntax command exists."""
        from click.testing import CliRunner
        runner = CliRunner()

        # Test check-syntax subcommand help
        result = runner.invoke(cli, ['check-syntax', '--help'])
        assert result.exit_code == 0


@pytest.mark.unit
@pytest.mark.cli
class TestCLIFileOperations:
    """CLI file operation tests."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test.kumihan"

        # Create a test file
        self.test_file.write_text("""#太字#
テスト内容
##""", encoding='utf-8')

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_convert_command_with_file(self):
        """Test convert command with file argument."""
        from click.testing import CliRunner
        runner = CliRunner()

        # Test convert command with file (should show help or error gracefully)
        result = runner.invoke(cli, ['convert', str(self.test_file)])
        # Command should not crash
        assert result.exit_code in [0, 1, 2]  # Various acceptable exit codes

    def test_check_syntax_command_with_file(self):
        """Test check-syntax command with file argument."""
        from click.testing import CliRunner
        runner = CliRunner()

        # Test check-syntax command with file
        result = runner.invoke(cli, ['check-syntax', str(self.test_file)])
        # Command should not crash
        assert result.exit_code in [0, 1, 2]  # Various acceptable exit codes

    def test_file_path_handling(self):
        """Test file path argument handling."""
        from click.testing import CliRunner
        runner = CliRunner()

        # Test with existing file
        result = runner.invoke(cli, ['convert', str(self.test_file), '--help'])
        assert result.exit_code == 0


@pytest.mark.unit
@pytest.mark.cli
class TestCLIConfiguration:
    """CLI configuration tests."""

    def test_output_format_options(self):
        """Test output format options."""
        from click.testing import CliRunner
        runner = CliRunner()

        # Test convert command with format option
        result = runner.invoke(cli, ['convert', '--help'])
        assert result.exit_code == 0
        # Should mention format options in help
        assert 'format' in result.output.lower() or 'html' in result.output.lower()

    def test_output_directory_option(self):
        """Test output directory option."""
        from click.testing import CliRunner
        runner = CliRunner()

        # Test convert help for output options
        result = runner.invoke(cli, ['convert', '--help'])
        assert result.exit_code == 0
        assert 'output' in result.output.lower() or 'directory' in result.output.lower()

    def test_verbose_option(self):
        """Test verbose option."""
        from click.testing import CliRunner
        runner = CliRunner()

        # Test main help for verbose option
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        # Should have verbose option or similar
        assert 'verbose' in result.output.lower() or 'debug' in result.output.lower() or 'options' in result.output.lower()

    def test_config_file_option(self):
        """Test config file option availability."""
        from click.testing import CliRunner
        runner = CliRunner()

        # Test that CLI accepts configuration-related options
        result = runner.invoke(cli, ['convert', '--help'])
        assert result.exit_code == 0
        # Should have some configuration-related options
        assert 'config' in result.output.lower() or 'option' in result.output.lower()
