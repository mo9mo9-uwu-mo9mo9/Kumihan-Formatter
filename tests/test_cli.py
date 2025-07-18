"""Test cases for CLI basic functionality

This module tests the core CLI functionality including:
- Command registration and initialization
- Encoding setup for different platforms
- Command routing and execution
- Error handling and user feedback
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import click
import pytest
from click.testing import CliRunner

from kumihan_formatter.cli import cli, main, register_commands, setup_encoding


class TestCLIBasics:
    """Test basic CLI functionality"""

    def test_cli_group_exists(self):
        """Test that CLI group is properly defined"""
        assert isinstance(cli, click.Group)
        assert cli.name is not None

    def test_cli_help_text(self):
        """Test CLI help text displays correctly"""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Kumihan-Formatter" in result.output
        assert "開発用CLIツール" in result.output

    def test_cli_without_args_shows_help(self):
        """Test that CLI without arguments shows help"""
        runner = CliRunner()
        result = runner.invoke(cli, [])
        # Click 8.0+ returns exit code 2 for help
        assert result.exit_code in (0, 2)
        assert "Usage:" in result.output


class TestEncodingSetup:
    """Test encoding setup for different platforms"""

    @patch("sys.platform", "win32")
    @patch("sys.stdout")
    @patch("sys.stderr")
    def test_setup_encoding_windows(self, mock_stderr, mock_stdout):
        """Test encoding setup on Windows"""
        mock_stdout.reconfigure = MagicMock()
        mock_stderr.reconfigure = MagicMock()

        setup_encoding()

        mock_stdout.reconfigure.assert_called_once_with(encoding="utf-8")
        mock_stderr.reconfigure.assert_called_once_with(encoding="utf-8")

    @patch("sys.platform", "darwin")
    def test_setup_encoding_macos(self):
        """Test encoding setup on macOS (should not modify)"""
        with patch("sys.stdout") as mock_stdout:
            setup_encoding()
            # macOSでは何も設定しない
            mock_stdout.reconfigure.assert_not_called()

    @patch("sys.platform", "win32")
    @patch("sys.stdout")
    def test_setup_encoding_old_python(self, mock_stdout):
        """Test encoding setup with old Python version"""
        # reconfigure メソッドがない古いPythonをシミュレート
        del mock_stdout.reconfigure

        with patch("warnings.warn") as mock_warn:
            setup_encoding()
            mock_warn.assert_called_once()
            assert "Python 3.7" in str(mock_warn.call_args[0][0])


class TestCommandRegistration:
    """Test command registration functionality"""

    def test_register_commands_adds_convert(self):
        """Test that convert command is registered"""
        # 新しいCLIグループを作成してテスト
        test_cli = click.Group()

        with patch("kumihan_formatter.cli.cli", test_cli):
            register_commands()

        assert "convert" in test_cli.commands

    def test_register_commands_fallback_convert(self):
        """Test fallback to legacy convert when new module fails"""
        test_cli = click.Group()

        # 新しいconvertモジュールのインポートを失敗させる
        # 注: 現在のコードではcreate_convert_commandが存在しないため、
        # ImportErrorの処理のみをテスト
        with (
            patch("kumihan_formatter.cli.cli", test_cli),
            patch.dict(
                "sys.modules",
                {"kumihan_formatter.commands.convert.convert_command": None},
            ),
            patch("warnings.warn") as mock_warn,
        ):
            with pytest.raises(ImportError):
                register_commands()

    def test_register_commands_optional_commands(self):
        """Test that optional commands don't break registration"""
        test_cli = click.Group()

        # check-syntaxのインポートを失敗させる
        with (
            patch("kumihan_formatter.cli.cli", test_cli),
            patch(
                "kumihan_formatter.commands.check_syntax.create_check_syntax_command",
                side_effect=ImportError("Test import error"),
            ),
            patch("warnings.warn") as mock_warn,
        ):
            register_commands()

        # convertは登録されているが、check-syntaxは登録されていない
        assert "convert" in test_cli.commands
        assert "check-syntax" not in test_cli.commands
        # 警告が表示される
        mock_warn.assert_called()


class TestMainFunction:
    """Test main entry point functionality"""

    def test_main_keyboard_interrupt_handling(self):
        """Test handling of Ctrl+C interruption"""
        with (
            patch("kumihan_formatter.cli.cli", side_effect=KeyboardInterrupt()),
            patch("sys.exit") as mock_exit,
            patch("kumihan_formatter.ui.console_ui.get_console_ui") as mock_ui,
        ):

            console_ui = MagicMock()
            mock_ui.return_value = console_ui

            main()

            console_ui.info.assert_called_with("操作が中断されました")
            console_ui.dim.assert_called_with("Ctrl+C で中断されました")
            mock_exit.assert_called_with(130)

    def test_main_legacy_file_routing(self):
        """Test automatic routing of file arguments to convert command"""
        # ファイルが存在する場合のテスト
        with (
            patch("sys.argv", ["kumihan", "test.txt"]),
            patch("pathlib.Path.exists", return_value=True),
            patch("kumihan_formatter.cli.cli") as mock_cli,
        ):

            main()

            # sys.argvにconvertが挿入されているか確認
            assert sys.argv[1] == "convert"
            assert sys.argv[2] == "test.txt"

    def test_main_legacy_file_routing_txt_extension(self):
        """Test routing for .txt files even if they don't exist"""
        with (
            patch("sys.argv", ["kumihan", "nonexistent.txt"]),
            patch("pathlib.Path.exists", return_value=False),
            patch("kumihan_formatter.cli.cli") as mock_cli,
        ):

            main()

            # .txtファイルはconvertにルーティングされる
            assert sys.argv[1] == "convert"
            assert sys.argv[2] == "nonexistent.txt"

    def test_main_no_routing_for_commands(self):
        """Test that existing commands are not routed"""
        original_argv = ["kumihan", "check-syntax", "file.txt"]
        with (
            patch("sys.argv", original_argv.copy()),
            patch("kumihan_formatter.cli.cli") as mock_cli,
        ):

            main()

            # コマンドが既に指定されている場合はルーティングしない
            assert sys.argv == original_argv

    def test_main_exception_handling(self):
        """Test general exception handling"""
        test_error = RuntimeError("Test error")

        with (
            patch("kumihan_formatter.cli.cli", side_effect=test_error),
            patch("sys.exit") as mock_exit,
            patch(
                "kumihan_formatter.core.error_handling.ErrorHandler"
            ) as mock_handler_class,
        ):

            mock_handler = MagicMock()
            mock_handler_class.return_value = mock_handler
            mock_handler.handle_exception.return_value = MagicMock()

            main()

            mock_handler.handle_exception.assert_called_once()
            mock_handler.display_error.assert_called_once()
            mock_exit.assert_called_with(1)

    def test_main_click_exception_passthrough(self):
        """Test that Click exceptions are passed through"""
        click_error = click.ClickException("Click error")

        with (
            patch("kumihan_formatter.cli.cli", side_effect=click_error),
            pytest.raises(click.ClickException),
        ):
            main()


class TestCLIIntegration:
    """Test CLI integration scenarios"""

    def test_convert_command_available(self):
        """Test that convert command is available in CLI"""
        runner = CliRunner()
        # コマンドを登録
        register_commands()

        result = runner.invoke(cli, ["convert", "--help"])
        assert result.exit_code == 0
        assert "テキストファイルをHTMLに変換する" in result.output

    def test_multiple_command_help(self):
        """Test help for multiple commands"""
        runner = CliRunner()
        register_commands()

        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        # 少なくともconvertコマンドは表示される
        assert "convert" in result.output

    @patch("kumihan_formatter.commands.convert.convert_command.ConvertCommand")
    def test_convert_command_execution(self, mock_convert_class):
        """Test convert command execution with options"""
        runner = CliRunner()
        mock_convert = MagicMock()
        mock_convert_class.return_value = mock_convert

        # コマンドを登録
        register_commands()

        result = runner.invoke(
            cli,
            [
                "convert",
                "input.txt",
                "--output",
                "output_dir",
                "--no-preview",
                "--config",
                "config.toml",
            ],
        )

        mock_convert.execute.assert_called_once()
        call_args = mock_convert.execute.call_args[1]
        assert call_args["input_file"] == "input.txt"
        assert call_args["output"] == "output_dir"
        assert call_args["no_preview"] is True
        assert call_args["config"] == "config.toml"
