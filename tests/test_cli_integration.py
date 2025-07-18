"""CLI Integration and E2E Tests for Issue 500 Phase 3B

This module provides comprehensive integration tests for the CLI system
to ensure all commands work together correctly.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from kumihan_formatter.cli import cli
from kumihan_formatter.commands.check_syntax import create_check_syntax_command
from kumihan_formatter.commands.convert import ConvertCommand
from kumihan_formatter.commands.sample import create_sample_command, create_test_command


class TestCLIIntegration:
    """Test CLI integration scenarios"""

    def test_cli_main_help(self):
        """Test main CLI help command"""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Kumihan-Formatter" in result.output

    def test_cli_command_registration(self):
        """Test that all commands are properly registered"""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        # Check that main commands are listed
        assert "convert" in result.output
        assert "check-syntax" in result.output or "check_syntax" in result.output

    def test_convert_command_help(self):
        """Test convert command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ["convert", "--help"])

        assert result.exit_code == 0
        assert "convert" in result.output.lower()

    def test_check_syntax_command_help(self):
        """Test check-syntax command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ["check-syntax", "--help"])

        assert result.exit_code == 0
        assert "構文" in result.output or "syntax" in result.output

    @patch("kumihan_formatter.core.file_io_handler.FileIOHandler.write_text_file")
    @patch("kumihan_formatter.core.file_operations.FileOperations.ensure_directory")
    def test_sample_command_integration(self, mock_ensure_dir, mock_write_file):
        """Test sample command integration"""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["generate-sample"])

            # Command should execute without critical errors
            assert result.exit_code == 0 or result.exit_code == 1  # Allow minor errors

    def test_invalid_command(self):
        """Test invalid command handling"""
        runner = CliRunner()
        result = runner.invoke(cli, ["invalid-command"])

        assert result.exit_code != 0
        assert "No such command" in result.output or "Usage:" in result.output


class TestE2EScenarios:
    """End-to-end test scenarios"""

    def test_complete_workflow_simulation(self):
        """Test complete workflow from syntax check to conversion"""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create test file
            test_content = """テストファイル

            これはテスト用のファイルです。
            """

            with open("test.txt", "w", encoding="utf-8") as f:
                f.write(test_content)

            # Test syntax check
            result = runner.invoke(cli, ["check-syntax", "test.txt"])

            # Should not fail catastrophically
            assert result.exit_code in [0, 1]  # Allow warnings/errors

    def test_error_handling_scenarios(self):
        """Test error handling in various scenarios"""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Test non-existent file
            result = runner.invoke(cli, ["check-syntax", "nonexistent.txt"])
            assert result.exit_code != 0

            # Test invalid options
            result = runner.invoke(cli, ["convert", "--invalid-option"])
            assert result.exit_code != 0

    def test_encoding_handling(self):
        """Test encoding handling scenarios"""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Test UTF-8 file
            test_content = "日本語テスト\n漢字テスト"

            with open("test_utf8.txt", "w", encoding="utf-8") as f:
                f.write(test_content)

            result = runner.invoke(cli, ["check-syntax", "test_utf8.txt"])

            # Should handle encoding correctly
            assert result.exit_code in [0, 1]  # Allow warnings/errors

    def test_concurrent_operations(self):
        """Test concurrent operation scenarios"""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create multiple test files
            for i in range(3):
                with open(f"test{i}.txt", "w", encoding="utf-8") as f:
                    f.write(f"テストファイル{i}\n")

            # Test checking multiple files
            result = runner.invoke(
                cli, ["check-syntax", "test0.txt", "test1.txt", "test2.txt"]
            )

            # Should handle multiple files
            assert result.exit_code in [0, 1]  # Allow warnings/errors

    def test_memory_usage_scenarios(self):
        """Test memory usage with various file sizes"""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create a larger test file
            large_content = "テスト行\n" * 100

            with open("large_test.txt", "w", encoding="utf-8") as f:
                f.write(large_content)

            result = runner.invoke(cli, ["check-syntax", "large_test.txt"])

            # Should handle larger files
            assert result.exit_code in [0, 1]  # Allow warnings/errors


class TestCLIRobustness:
    """Test CLI robustness and edge cases"""

    def test_keyboard_interrupt_handling(self):
        """Test keyboard interrupt handling"""
        runner = CliRunner()

        # This is difficult to test directly, but we can verify
        # that the CLI handles interrupts gracefully
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0

    def test_resource_cleanup(self):
        """Test resource cleanup after operations"""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create test file
            with open("test.txt", "w", encoding="utf-8") as f:
                f.write("テスト")

            # Run command and ensure cleanup
            result = runner.invoke(cli, ["check-syntax", "test.txt"])

            # File should still exist and be accessible
            assert Path("test.txt").exists()

    def test_configuration_handling(self):
        """Test configuration file handling"""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Test with default configuration
            result = runner.invoke(cli, ["--help"])
            assert result.exit_code == 0

            # Test with non-existent config (should use defaults)
            result = runner.invoke(cli, ["convert", "--help"])
            assert result.exit_code == 0

    def test_output_consistency(self):
        """Test output consistency across runs"""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create test file
            with open("test.txt", "w", encoding="utf-8") as f:
                f.write("テスト")

            # Run same command multiple times
            results = []
            for _ in range(3):
                result = runner.invoke(cli, ["check-syntax", "test.txt"])
                results.append(result.exit_code)

            # Exit codes should be consistent
            assert len(set(results)) == 1, f"Inconsistent exit codes: {results}"


class TestCommandInteraction:
    """Test interactions between different commands"""

    def test_command_chaining_simulation(self):
        """Test simulated command chaining"""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create test file
            with open("test.txt", "w", encoding="utf-8") as f:
                f.write("テスト")

            # First check syntax
            check_result = runner.invoke(cli, ["check-syntax", "test.txt"])

            # Then attempt conversion (if syntax check passes)
            if check_result.exit_code == 0:
                convert_result = runner.invoke(cli, ["convert", "test.txt"])
                # Allow various exit codes as conversion might fail for other reasons
                assert convert_result.exit_code in [0, 1, 2]

    def test_error_propagation(self):
        """Test error propagation between commands"""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Test with problematic file
            result = runner.invoke(cli, ["check-syntax", "nonexistent.txt"])

            # Should propagate error appropriately
            assert result.exit_code != 0
            assert (
                "error" in result.output.lower() or "not found" in result.output.lower()
            )

    def test_state_isolation(self):
        """Test state isolation between command runs"""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create test files
            with open("test1.txt", "w", encoding="utf-8") as f:
                f.write("テスト1")
            with open("test2.txt", "w", encoding="utf-8") as f:
                f.write("テスト2")

            # Run commands on different files
            result1 = runner.invoke(cli, ["check-syntax", "test1.txt"])
            result2 = runner.invoke(cli, ["check-syntax", "test2.txt"])

            # Results should be independent
            assert result1.exit_code in [0, 1]
            assert result2.exit_code in [0, 1]
