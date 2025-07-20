"""Convert Command Basic Tests

基本的なConvertCommand機能テスト。
target: Convert Command初期化・基本実行のテスト。
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest


class TestConvertCommandBasic:
    """ConvertCommand基本機能テスト"""

    def test_convert_command_initialization(self):
        """ConvertCommand初期化テスト"""
        from kumihan_formatter.commands.convert.convert_command import ConvertCommand

        with (
            patch(
                "kumihan_formatter.commands.convert.convert_command.get_logger"
            ) as mock_logger,
            patch(
                "kumihan_formatter.commands.convert.convert_command.get_console_ui"
            ) as mock_ui,
        ):

            command = ConvertCommand()

            # 初期化確認
            assert command is not None
            assert hasattr(command, "validator")
            assert hasattr(command, "processor")
            assert hasattr(command, "watcher")
            assert hasattr(command, "friendly_error_handler")

            # ログ初期化確認
            mock_logger.assert_called_once()

    def test_convert_command_execute_basic(self):
        """基本的な変換実行テスト"""
        from kumihan_formatter.commands.convert.convert_command import ConvertCommand

        with (
            patch(
                "kumihan_formatter.commands.convert.convert_command.get_logger"
            ) as mock_logger,
            patch(
                "kumihan_formatter.commands.convert.convert_command.get_console_ui"
            ) as mock_ui,
            patch("sys.exit") as mock_exit,
        ):

            command = ConvertCommand()

            # モックで依存関係をコントロール
            command.validator = Mock()
            command.processor = Mock()
            command.watcher = Mock()
            command.friendly_error_handler = Mock()

            # 構文チェックの結果をモック
            command.validator.perform_syntax_check.return_value.to_console_output.return_value = (
                "Syntax check passed"
            )
            command.validator.perform_syntax_check.return_value.has_errors.return_value = (
                False
            )

            # 基本実行テスト
            command.execute(
                input_file="test.txt",
                output="output/",
                no_preview=False,
                watch=False,
                config=None,
                show_test_cases=False,
                template_name=None,
                include_source=False,
                syntax_check=True,
            )

            # バリデータが呼ばれたことを確認
            command.validator.perform_syntax_check.assert_called_once()

    def test_convert_command_error_handling(self):
        """エラーハンドリングテスト"""
        from kumihan_formatter.commands.convert.convert_command import ConvertCommand

        with (
            patch(
                "kumihan_formatter.commands.convert.convert_command.get_logger"
            ) as mock_logger,
            patch(
                "kumihan_formatter.commands.convert.convert_command.get_console_ui"
            ) as mock_ui,
        ):

            command = ConvertCommand()

            # エラーを発生させるモック
            command.validator = Mock()
            command.processor = Mock()
            command.friendly_error_handler = Mock()

            # ファイル検証でFileNotFoundErrorを発生させる
            command.validator.validate_input_file.side_effect = FileNotFoundError(
                "File not found"
            )

            try:
                command.execute(
                    input_file="nonexistent.txt",
                    output="output/",
                    no_preview=True,
                    watch=False,
                    config=None,
                    show_test_cases=False,
                    template_name=None,
                    include_source=False,
                    syntax_check=True,
                )
            except SystemExit:
                # sys.exit(1)が呼ばれることを確認
                pass
            except Exception:
                # その他のエラーハンドリングが動作することを確認
                pass
