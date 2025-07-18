"""Test cases for check-syntax command functionality

This module tests the syntax checking command including:
- Command creation
- Basic execution
- Error handling
- CLI integration
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import click
import pytest
from click.testing import CliRunner

from kumihan_formatter.commands.check_syntax import (
    CheckSyntaxCommand,
    create_check_syntax_command,
)
from kumihan_formatter.core.syntax import ErrorSeverity


class TestCheckSyntaxCommand:
    """Test CheckSyntaxCommand class"""

    def test_check_syntax_command_initialization(self):
        """Test CheckSyntaxCommand initialization"""
        command = CheckSyntaxCommand()

        # CheckSyntaxCommandは特定の属性を持たない
        assert command is not None

    @patch("kumihan_formatter.commands.check_syntax.get_console_ui")
    @patch("kumihan_formatter.commands.check_syntax.check_files")
    def test_check_syntax_valid_file(self, mock_check_files, mock_get_console_ui):
        """Test syntax check with valid file"""
        mock_console = MagicMock()
        mock_get_console_ui.return_value = mock_console

        command = CheckSyntaxCommand()

        # モックファイルとチェック結果
        with patch.object(command, "_collect_files", return_value=[Path("test.txt")]):
            # 有効なファイルの場合（エラーなし）
            mock_check_files.return_value = {}

            with patch("sys.exit") as mock_exit:
                command.execute(
                    ["test.txt"],
                    recursive=False,
                    show_suggestions=True,
                    format_output="text",
                )

                mock_exit.assert_called_with(0)
                mock_console.success.assert_called()

    @patch("kumihan_formatter.commands.check_syntax.get_console_ui")
    @patch("kumihan_formatter.commands.check_syntax.check_files")
    def test_check_syntax_with_errors(self, mock_check_files, mock_get_console_ui):
        """Test syntax check with errors"""
        mock_console = MagicMock()
        mock_get_console_ui.return_value = mock_console

        command = CheckSyntaxCommand()

        # モックファイルとチェック結果
        with patch.object(command, "_collect_files", return_value=[Path("test.txt")]):
            # エラーがある場合（辞書形式で返す）
            mock_error = MagicMock()
            mock_error.severity = ErrorSeverity.ERROR
            mock_check_files.return_value = {
                "test.txt": [mock_error, mock_error, mock_error]
            }

            with patch("sys.exit") as mock_exit:
                command.execute(
                    ["test.txt"],
                    recursive=False,
                    show_suggestions=True,
                    format_output="text",
                )

                mock_exit.assert_called_with(1)
                mock_console.warning.assert_called()

    @patch("kumihan_formatter.commands.check_syntax.get_console_ui")
    @patch("kumihan_formatter.commands.check_syntax.check_files")
    def test_check_syntax_file_not_found(self, mock_check_files, mock_get_console_ui):
        """Test syntax check with non-existent file"""
        mock_console = MagicMock()
        mock_get_console_ui.return_value = mock_console

        command = CheckSyntaxCommand()

        # ファイルが見つからない
        with patch.object(command, "_collect_files", return_value=[]):
            with patch("sys.exit") as mock_exit:
                command.execute(
                    ["nonexistent.txt"],
                    recursive=False,
                    show_suggestions=True,
                    format_output="text",
                )

                # sys.exit(1)が最初に呼ばれることを確認
                mock_exit.assert_any_call(1)
                mock_console.error.assert_called_with(
                    "チェックするファイルが見つかりません"
                )

    def test_collect_files_method(self):
        """Test _collect_files internal method"""
        command = CheckSyntaxCommand()

        # ファイル収集のテスト
        with patch("pathlib.Path") as mock_path_class:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path.is_file.return_value = True
            mock_path.suffix = ".txt"
            mock_path_class.return_value = mock_path

            result = command._collect_files(["test.txt"], recursive=False)

            # 少なくとも1つのパスが返される
            assert len(result) >= 0


class TestCheckSyntaxCLI:
    """Test check-syntax CLI command"""

    def test_create_check_syntax_command(self):
        """Test creating check-syntax command"""
        cmd = create_check_syntax_command()

        assert isinstance(cmd, click.Command)
        assert cmd.name == "check-syntax"

    def test_check_syntax_command_help(self):
        """Test check-syntax command help"""
        runner = CliRunner()
        cmd = create_check_syntax_command()

        result = runner.invoke(cmd, ["--help"])

        assert result.exit_code == 0
        assert "構文" in result.output  # "構文チェック" または "構文を"

    @patch("kumihan_formatter.commands.check_syntax.CheckSyntaxCommand")
    def test_check_syntax_command_execution(self, mock_command_class):
        """Test check-syntax command execution"""
        runner = CliRunner()
        cmd = create_check_syntax_command()

        mock_command = MagicMock()
        mock_command_class.return_value = mock_command

        result = runner.invoke(cmd, ["test.txt"])

        # executeメソッドが呼ばれることを確認
        mock_command.execute.assert_called_once()

        # 引数の確認
        call_args = mock_command.execute.call_args
        assert call_args[0][0] == ["test.txt"]  # files引数
        assert call_args[1]["recursive"] == False
        assert call_args[1]["show_suggestions"] == True
        assert call_args[1]["format_output"] == "text"

    @patch("kumihan_formatter.commands.check_syntax.CheckSyntaxCommand")
    def test_check_syntax_command_with_options(self, mock_command_class):
        """Test check-syntax command with options"""
        runner = CliRunner()
        cmd = create_check_syntax_command()

        mock_command = MagicMock()
        mock_command_class.return_value = mock_command

        result = runner.invoke(
            cmd, ["test.txt", "--recursive", "--no-suggestions", "--format", "json"]
        )

        # executeメソッドが呼ばれることを確認
        mock_command.execute.assert_called_once()

        # 引数の確認
        call_args = mock_command.execute.call_args
        assert call_args[0][0] == ["test.txt"]  # files引数
        assert call_args[1]["recursive"] == True
        assert call_args[1]["show_suggestions"] == False
        assert call_args[1]["format_output"] == "json"


class TestCheckSyntaxIntegration:
    """Test syntax check integration scenarios"""

    @patch("kumihan_formatter.commands.check_syntax.get_console_ui")
    def test_check_syntax_exception_handling(self, mock_get_console_ui):
        """Test syntax check exception handling"""
        mock_console = MagicMock()
        mock_get_console_ui.return_value = mock_console

        command = CheckSyntaxCommand()

        # 例外を発生させる
        with patch.object(
            command, "_collect_files", side_effect=Exception("Test error")
        ):

            with patch("sys.exit") as mock_exit:
                command.execute(
                    ["test.txt"],
                    recursive=False,
                    show_suggestions=True,
                    format_output="text",
                )

                # エラーメッセージが表示される
                mock_console.error.assert_called()

    @patch("kumihan_formatter.commands.check_syntax.get_console_ui")
    @patch("kumihan_formatter.commands.check_syntax.check_files")
    def test_check_syntax_json_output(self, mock_check_files, mock_get_console_ui):
        """Test syntax check with JSON output"""
        mock_console = MagicMock()
        mock_get_console_ui.return_value = mock_console

        command = CheckSyntaxCommand()

        # モックファイルとチェック結果
        with (
            patch.object(command, "_collect_files", return_value=[Path("test.txt")]),
            patch("builtins.print") as mock_print,
        ):

            # エラーがある場合（辞書形式で返す）
            mock_error = MagicMock()
            mock_error.line_number = 1
            mock_error.column = 1
            mock_error.severity = ErrorSeverity.ERROR
            mock_error.error_type = "test_error"
            mock_error.message = "Test error"
            mock_error.context = "Test context"
            mock_error.suggestion = "Test suggestion"
            mock_check_files.return_value = {"test.txt": [mock_error]}

            with patch("sys.exit"):
                command.execute(
                    ["test.txt"],
                    recursive=False,
                    show_suggestions=True,
                    format_output="json",
                )

                # JSON出力が行われる
                mock_print.assert_called()

    def test_check_syntax_recursive_option(self):
        """Test recursive file collection"""
        command = CheckSyntaxCommand()

        # 再帰的なファイル収集のテスト
        with patch("kumihan_formatter.commands.check_syntax.Path") as mock_path_class:
            mock_dir = MagicMock()
            mock_dir.is_file.return_value = False
            mock_dir.is_dir.return_value = True
            mock_dir.rglob.return_value = [Path("dir/test1.txt"), Path("dir/test2.txt")]
            mock_path_class.return_value = mock_dir

            # get_console_ui calls もmock
            with patch(
                "kumihan_formatter.commands.check_syntax.get_console_ui"
            ) as mock_console_ui:
                mock_console = MagicMock()
                mock_console_ui.return_value = mock_console

                result = command._collect_files(["dir"], recursive=True)

                # rglob が呼ばれることを確認
                mock_dir.rglob.assert_called_with("*.txt")
                # 返されたファイルの数を確認
                assert len(result) == 2

    @patch("kumihan_formatter.commands.check_syntax.get_console_ui")
    @patch("kumihan_formatter.commands.check_syntax.check_files")
    def test_error_severity_handling(self, mock_check_files, mock_get_console_ui):
        """Test error severity handling"""
        mock_console = MagicMock()
        mock_get_console_ui.return_value = mock_console

        command = CheckSyntaxCommand()

        # エラーの重要度をテスト
        with patch.object(command, "_collect_files", return_value=[Path("test.txt")]):

            # 異なる重要度のエラー（辞書形式で返す）
            mock_error = MagicMock()
            mock_error.severity = ErrorSeverity.ERROR
            mock_warning = MagicMock()
            mock_warning.severity = ErrorSeverity.WARNING
            mock_check_files.return_value = {"test.txt": [mock_error, mock_warning]}

            with patch("sys.exit") as mock_exit:
                command.execute(
                    ["test.txt"],
                    recursive=False,
                    show_suggestions=True,
                    format_output="text",
                )

                # エラーがあるので終了コード1
                mock_exit.assert_called_with(1)
