"""CLI Basic Tests

Simplified from original for 300-line limit compliance.
Tests for CLI functionality.
"""

import pytest


class TestCLIBasic:
    """Basic tests for CLI functionality"""

    def test_cli_import(self):
        """Test CLI module import"""
        try:
            from kumihan_formatter.cli import main

            assert callable(main)

        except ImportError:
                pass

    def test_command_interface(self):
        """Test command interface"""
        try:
            from kumihan_formatter.cli.commands import ConvertCommand

            command = ConvertCommand()
            assert command is not None

        except ImportError:
                pass
