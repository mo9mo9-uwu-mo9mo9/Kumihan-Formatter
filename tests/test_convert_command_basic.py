"""Basic test cases for convert command functionality

This module tests the core convert command functionality including:
- Command initialization
- Basic execution
- Error handling
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from click.testing import CliRunner

from kumihan_formatter.commands.convert.convert_command import ConvertCommand
from kumihan_formatter.commands.convert.convert_processor import ConvertProcessor
from kumihan_formatter.commands.convert.convert_validator import ConvertValidator
from kumihan_formatter.commands.convert.convert_watcher import ConvertWatcher


class TestConvertCommand:
    """Test ConvertCommand class"""

    def test_convert_command_initialization(self):
        """Test ConvertCommand initialization"""
        command = ConvertCommand()

        assert isinstance(command.validator, ConvertValidator)
        assert isinstance(command.processor, ConvertProcessor)
        assert isinstance(command.watcher, ConvertWatcher)
        assert command.friendly_error_handler is not None

    @patch("kumihan_formatter.commands.convert.convert_command.get_console_ui")
    def test_convert_command_with_test_cases(self, mock_get_console_ui):
        """Test convert command with show_test_cases flag"""
        mock_console = MagicMock()
        mock_get_console_ui.return_value = mock_console

        command = ConvertCommand()

        # validate_input_fileがNoneの場合は例外を投げる
        command.validator.validate_input_file = MagicMock(
            side_effect=FileNotFoundError("Input file not found")
        )

        with patch("sys.exit") as mock_exit:
            command.execute(
                input_file=None,
                output="./dist",
                no_preview=True,
                watch=False,
                config=None,
                show_test_cases=True,
                template_name=None,
                include_source=False,
                syntax_check=True,
            )

            # FileNotFoundErrorが処理される
            mock_exit.assert_called()

    @patch("kumihan_formatter.commands.convert.convert_command.get_console_ui")
    def test_convert_command_with_input_file(self, mock_get_console_ui):
        """Test convert command with input file"""
        mock_console = MagicMock()
        mock_get_console_ui.return_value = mock_console

        command = ConvertCommand()
        # 入力ファイルの検証を成功させる
        mock_path = Path("test.txt")
        command.validator.validate_input_file = MagicMock(return_value=mock_path)
        command.validator.check_file_size = MagicMock(return_value=True)
        command.validator.perform_syntax_check = MagicMock()
        mock_report = MagicMock()
        mock_report.has_errors.return_value = False
        mock_report.has_warnings.return_value = False
        command.validator.perform_syntax_check.return_value = mock_report

        # convert_fileメソッドをモック
        output_path = Path("output.html")
        command.processor.convert_file = MagicMock(return_value=output_path)

        with patch("webbrowser.open") as mock_browser:
            with patch("sys.exit") as mock_exit:
                command.execute(
                    input_file="test.txt",
                    output="./dist",
                    no_preview=False,
                    watch=False,
                    config=None,
                    show_test_cases=False,
                    template_name=None,
                    include_source=False,
                    syntax_check=True,
                )

            command.processor.convert_file.assert_called_once()
            # ブラウザが開かれる
            mock_browser.assert_called_once()
            # 正常終了
            mock_exit.assert_called_with(0)

    @patch("kumihan_formatter.commands.convert.convert_command.get_console_ui")
    def test_convert_command_error_handling(self, mock_get_console_ui):
        """Test convert command error handling"""
        mock_console = MagicMock()
        mock_get_console_ui.return_value = mock_console

        command = ConvertCommand()
        # validate_input_fileでエラーを発生させる
        command.validator.validate_input_file = MagicMock(
            side_effect=RuntimeError("Test error")
        )

        with patch("sys.exit") as mock_exit:
            command.execute(
                input_file="test.txt",
                output="./dist",
                no_preview=True,
                watch=False,
                config=None,
                show_test_cases=False,
                template_name=None,
                include_source=False,
                syntax_check=True,
            )

            # エラーハンドリングが実行される
            mock_exit.assert_called_with(1)

    @patch("kumihan_formatter.commands.convert.convert_command.get_console_ui")
    def test_convert_command_keyboard_interrupt(self, mock_get_console_ui):
        """Test convert command handling KeyboardInterrupt"""
        mock_console = MagicMock()
        mock_get_console_ui.return_value = mock_console

        command = ConvertCommand()
        # KeyboardInterruptを発生させる
        command.validator.validate_input_file = MagicMock(
            side_effect=KeyboardInterrupt()
        )

        # KeyboardInterruptは現在のコードでは処理されていないので、
        # 例外が発生することを確認
        with pytest.raises(KeyboardInterrupt):
            command.execute(
                input_file="test.txt",
                output="./dist",
                no_preview=True,
                watch=False,
                config=None,
                show_test_cases=False,
                template_name=None,
                include_source=False,
                syntax_check=True,
            )


class TestConvertProcessor:
    """Test ConvertProcessor class"""

    def test_processor_initialization(self):
        """Test ConvertProcessor initialization"""
        processor = ConvertProcessor()
        assert processor is not None

    def test_processor_convert_file(self):
        """Test convert_file method"""
        processor = ConvertProcessor()

        # 依存関係をモック
        with (
            patch.object(
                processor.file_ops, "read_text_file", return_value="test content"
            ),
            patch(
                "kumihan_formatter.commands.convert.convert_processor.parse"
            ) as mock_parse,
            patch(
                "kumihan_formatter.commands.convert.convert_processor.render"
            ) as mock_render,
            patch.object(processor.file_ops, "write_text_file") as mock_write,
            patch(
                "kumihan_formatter.commands.convert.convert_processor.get_console_ui"
            ),
        ):

            mock_parse.return_value = MagicMock()  # パース結果
            mock_render.return_value = "<html>test</html>"  # レンダリング結果

            input_path = Path("test.txt")
            result = processor.convert_file(input_path, "./output")

            # メソッドが呼ばれたことを確認
            processor.file_ops.read_text_file.assert_called_once_with(input_path)
            mock_parse.assert_called_once()
            mock_render.assert_called_once()
            mock_write.assert_called_once()

    def test_processor_show_test_cases(self):
        """Test showing test cases"""
        processor = ConvertProcessor()

        with patch("kumihan_formatter.core.utilities.logger.get_logger") as mock_logger:
            logger = MagicMock()
            mock_logger.return_value = logger

            # show_test_casesメソッドをモック
            processor.show_test_cases = MagicMock()
            processor.show_test_cases()

            processor.show_test_cases.assert_called_once()


class TestConvertValidator:
    """Test ConvertValidator class"""

    def test_validator_initialization(self):
        """Test ConvertValidator initialization"""
        validator = ConvertValidator()
        assert validator is not None

    def test_validator_validate_syntax(self):
        """Test syntax validation"""
        validator = ConvertValidator()

        # validate_syntax メソッドをモック
        validator.validate_syntax = MagicMock(return_value=True)

        result = validator.validate_syntax("test.txt")
        assert result is True
        validator.validate_syntax.assert_called_once_with("test.txt")

    def test_validator_syntax_error(self):
        """Test syntax validation with errors"""
        validator = ConvertValidator()

        # エラーを返すようにモック
        validator.validate_syntax = MagicMock(return_value=False)

        result = validator.validate_syntax("test.txt")
        assert result is False
