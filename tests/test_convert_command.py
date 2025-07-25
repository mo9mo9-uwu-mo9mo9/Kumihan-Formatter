"""
ConvertCommandのテスト

Test coverage targets:
- CLI引数バリデーション: 80%
- エラーハンドリング: 90%
- コマンド実行フロー: 70%
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, call, patch

import pytest

from kumihan_formatter.commands.convert.convert_command import ConvertCommand
from kumihan_formatter.core.utilities.logger import get_logger


class TestConvertCommand:
    """ConvertCommandクラスのテスト"""

    def setup_method(self):
        """各テストメソッド実行前のセットアップ"""
        self.command = ConvertCommand()

    def test_init_creates_dependencies(self):
        """初期化時に必要な依存関係が作成されることを確認"""
        # Given & When
        command = ConvertCommand()

        # Then
        assert command.validator is not None
        assert command.processor is not None
        assert command.watcher is not None
        assert command.friendly_error_handler is not None
        assert command.logger is not None

    @patch("sys.exit")
    @patch("webbrowser.open")
    def test_execute_basic_conversion_flow(self, mock_browser, mock_exit):
        """基本的な変換フローの正常実行をテスト"""
        # Given
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test content")
            input_file = f.name

        output_dir = tempfile.mkdtemp()

        # Mock the dependencies
        with patch.object(
            self.command.validator, "validate_input_file"
        ) as mock_validate:
            with patch.object(self.command.validator, "check_file_size") as mock_size:
                with patch.object(
                    self.command.processor, "convert_file"
                ) as mock_convert:
                    mock_validate.return_value = Path(input_file)
                    mock_size.return_value = True
                    mock_convert.return_value = Path(output_dir) / "output.html"

                    # When
                    self.command.execute(
                        input_file=input_file,
                        output=output_dir,
                        no_preview=True,
                        watch=False,
                        config=None,
                        show_test_cases=False,
                        template_name=None,
                        include_source=False,
                        syntax_check=False,
                    )

                    # Then
                    mock_validate.assert_called_once_with(input_file)
                    mock_size.assert_called_once()
                    mock_convert.assert_called_once()
                    mock_exit.assert_called_once_with(0)

        # Cleanup
        Path(input_file).unlink()

    @patch("sys.exit")
    def test_execute_with_syntax_check_errors(self, mock_exit):
        """構文チェックでエラーが発見された場合のテスト"""
        # Given
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test content")
            input_file = f.name

        output_dir = tempfile.mkdtemp()

        # Mock error report with errors
        mock_error_report = Mock()
        mock_error_report.has_errors.return_value = True
        mock_error_report.error_count = 3
        mock_error_report.to_console_output.return_value = "Error details"

        with patch.object(
            self.command.validator, "validate_input_file"
        ) as mock_validate:
            with patch.object(self.command.validator, "check_file_size") as mock_size:
                with patch.object(
                    self.command.validator, "perform_syntax_check"
                ) as mock_syntax:
                    with patch.object(
                        self.command.validator, "save_error_report"
                    ) as mock_save:
                        mock_validate.return_value = Path(input_file)
                        mock_size.return_value = True
                        mock_syntax.return_value = mock_error_report

                        # When
                        self.command.execute(
                            input_file=input_file,
                            output=output_dir,
                            no_preview=True,
                            watch=False,
                            config=None,
                            show_test_cases=False,
                            template_name=None,
                            include_source=False,
                            syntax_check=True,
                        )

                        # Then
                        mock_syntax.assert_called_once()
                        mock_save.assert_called_once()
                        # sys.exitが最後に1で呼ばれることを確認
                        exit_calls = mock_exit.call_args_list
                        assert len(exit_calls) >= 1
                        assert exit_calls[-1] == call(1)

        # Cleanup
        Path(input_file).unlink()

    @patch("sys.exit")
    def test_execute_with_syntax_check_warnings_only(self, mock_exit):
        """構文チェックで警告のみの場合のテスト"""
        # Given
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test content")
            input_file = f.name

        output_dir = tempfile.mkdtemp()

        # Mock error report with warnings only
        mock_error_report = Mock()
        mock_error_report.has_errors.return_value = False
        mock_error_report.has_warnings.return_value = True
        mock_error_report.warning_count = 2
        mock_error_report.to_console_output.return_value = "Warning details"

        with patch.object(
            self.command.validator, "validate_input_file"
        ) as mock_validate:
            with patch.object(self.command.validator, "check_file_size") as mock_size:
                with patch.object(
                    self.command.validator, "perform_syntax_check"
                ) as mock_syntax:
                    with patch.object(
                        self.command.processor, "convert_file"
                    ) as mock_convert:
                        mock_validate.return_value = Path(input_file)
                        mock_size.return_value = True
                        mock_syntax.return_value = mock_error_report
                        mock_convert.return_value = Path(output_dir) / "output.html"

                        # When
                        self.command.execute(
                            input_file=input_file,
                            output=output_dir,
                            no_preview=True,
                            watch=False,
                            config=None,
                            show_test_cases=False,
                            template_name=None,
                            include_source=False,
                            syntax_check=True,
                        )

                        # Then
                        mock_syntax.assert_called_once()
                        mock_convert.assert_called_once()
                        mock_exit.assert_called_once_with(0)

        # Cleanup
        Path(input_file).unlink()

    def test_execute_with_large_file_user_cancellation(self):
        """大きなファイルでユーザーがキャンセルした場合のテスト"""
        # Given
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test content")
            input_file = f.name

        output_dir = tempfile.mkdtemp()

        with patch.object(
            self.command.validator, "validate_input_file"
        ) as mock_validate:
            with patch.object(self.command.validator, "check_file_size") as mock_size:
                with patch("sys.exit") as mock_exit:
                    mock_validate.return_value = Path(input_file)
                    mock_size.return_value = False  # User cancels

                    # When
                    self.command.execute(
                        input_file=input_file,
                        output=output_dir,
                        no_preview=True,
                        watch=False,
                        config=None,
                        show_test_cases=False,
                        template_name=None,
                        include_source=False,
                        syntax_check=False,
                    )

                    # Then
                    mock_size.assert_called_once()
                    # sys.exitが呼ばれることを確認
                    mock_exit.assert_called()

        # Cleanup
        Path(input_file).unlink()

    @patch("sys.exit")
    @patch("webbrowser.open")
    def test_execute_with_browser_preview(self, mock_browser, mock_exit):
        """ブラウザプレビューありの実行テスト"""
        # Given
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test content")
            input_file = f.name

        output_dir = tempfile.mkdtemp()
        output_file = Path(output_dir) / "output.html"

        with patch.object(
            self.command.validator, "validate_input_file"
        ) as mock_validate:
            with patch.object(self.command.validator, "check_file_size") as mock_size:
                with patch.object(
                    self.command.processor, "convert_file"
                ) as mock_convert:
                    mock_validate.return_value = Path(input_file)
                    mock_size.return_value = True
                    mock_convert.return_value = output_file

                    # When
                    self.command.execute(
                        input_file=input_file,
                        output=output_dir,
                        no_preview=False,  # ブラウザプレビューあり
                        watch=False,
                        config=None,
                        show_test_cases=False,
                        template_name=None,
                        include_source=False,
                        syntax_check=False,
                    )

                    # Then
                    mock_browser.assert_called_once_with(output_file.resolve().as_uri())
                    mock_exit.assert_called_once_with(0)

        # Cleanup
        Path(input_file).unlink()

    @patch("sys.exit")
    def test_execute_with_watch_mode(self, mock_exit):
        """ファイル監視モードのテスト"""
        # Given
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test content")
            input_file = f.name

        output_dir = tempfile.mkdtemp()

        with patch.object(
            self.command.validator, "validate_input_file"
        ) as mock_validate:
            with patch.object(self.command.validator, "check_file_size") as mock_size:
                with patch.object(
                    self.command.processor, "convert_file"
                ) as mock_convert:
                    with patch.object(
                        self.command.watcher, "start_watch_mode"
                    ) as mock_watch:
                        mock_validate.return_value = Path(input_file)
                        mock_size.return_value = True
                        mock_convert.return_value = Path(output_dir) / "output.html"

                        # When
                        self.command.execute(
                            input_file=input_file,
                            output=output_dir,
                            no_preview=True,
                            watch=True,  # 監視モードあり
                            config=None,
                            show_test_cases=False,
                            template_name=None,
                            include_source=False,
                            syntax_check=False,
                        )

                        # Then
                        mock_watch.assert_called_once_with(
                            input_file,
                            output_dir,
                            None,  # config_obj
                            False,  # show_test_cases
                            None,  # template_name
                            False,  # include_source
                            False,  # syntax_check
                        )

        # Cleanup
        Path(input_file).unlink()

    @patch("sys.exit")
    def test_execute_handles_file_not_found_error(self, mock_exit):
        """ファイル未発見エラーの処理テスト"""
        # Given
        non_existent_file = "non_existent_file.txt"
        output_dir = tempfile.mkdtemp()

        with patch.object(
            self.command.validator, "validate_input_file"
        ) as mock_validate:
            mock_validate.side_effect = FileNotFoundError("File not found")

            # When
            self.command.execute(
                input_file=non_existent_file,
                output=output_dir,
                no_preview=True,
                watch=False,
                config=None,
                show_test_cases=False,
                template_name=None,
                include_source=False,
                syntax_check=False,
            )

            # Then
            mock_exit.assert_called_once_with(1)

    @patch("sys.exit")
    def test_execute_handles_unicode_decode_error(self, mock_exit):
        """文字エンコーディングエラーの処理テスト"""
        # Given
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test content")
            input_file = f.name

        output_dir = tempfile.mkdtemp()

        with patch.object(
            self.command.validator, "validate_input_file"
        ) as mock_validate:
            mock_validate.side_effect = UnicodeDecodeError(
                "utf-8", b"", 0, 1, "invalid"
            )

            # When
            self.command.execute(
                input_file=input_file,
                output=output_dir,
                no_preview=True,
                watch=False,
                config=None,
                show_test_cases=False,
                template_name=None,
                include_source=False,
                syntax_check=False,
            )

            # Then
            mock_exit.assert_called_once_with(1)

        # Cleanup
        Path(input_file).unlink()

    @patch("sys.exit")
    def test_execute_handles_permission_error(self, mock_exit):
        """ファイル権限エラーの処理テスト"""
        # Given
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test content")
            input_file = f.name

        output_dir = tempfile.mkdtemp()

        with patch.object(
            self.command.validator, "validate_input_file"
        ) as mock_validate:
            mock_validate.side_effect = PermissionError("Permission denied")

            # When
            self.command.execute(
                input_file=input_file,
                output=output_dir,
                no_preview=True,
                watch=False,
                config=None,
                show_test_cases=False,
                template_name=None,
                include_source=False,
                syntax_check=False,
            )

            # Then
            mock_exit.assert_called_once_with(1)

        # Cleanup
        Path(input_file).unlink()

    @patch("sys.exit")
    def test_execute_handles_generic_error(self, mock_exit):
        """一般的なエラーの処理テスト"""
        # Given
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test content")
            input_file = f.name

        output_dir = tempfile.mkdtemp()

        with patch.object(
            self.command.validator, "validate_input_file"
        ) as mock_validate:
            mock_validate.side_effect = RuntimeError("Unexpected error")

            # When
            self.command.execute(
                input_file=input_file,
                output=output_dir,
                no_preview=True,
                watch=False,
                config=None,
                show_test_cases=False,
                template_name=None,
                include_source=False,
                syntax_check=False,
            )

            # Then
            mock_exit.assert_called_once_with(1)

        # Cleanup
        Path(input_file).unlink()

    def test_private_error_handlers_call_friendly_error_handler(self):
        """プライベートエラーハンドラーがFriendlyErrorHandlerを呼び出すことをテスト"""
        # Given
        test_error = FileNotFoundError("test")
        input_file = "test.txt"

        with patch.object(
            self.command.friendly_error_handler, "handle_exception"
        ) as mock_handle:
            with patch.object(
                self.command.friendly_error_handler, "display_error"
            ) as mock_display:
                with patch("sys.exit") as mock_exit:
                    mock_handle.return_value = Mock()

                    # When
                    self.command._handle_file_error(test_error, input_file)

                    # Then
                    mock_handle.assert_called_once_with(
                        test_error, context={"file_path": input_file}
                    )
                    mock_display.assert_called_once()
                    mock_exit.assert_called_once_with(1)

    def test_all_options_parameter_passing(self):
        """全オプションが適切にプロセッサーに渡されることをテスト"""
        # Given
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test content")
            input_file = f.name

        output_dir = tempfile.mkdtemp()

        with patch.object(
            self.command.validator, "validate_input_file"
        ) as mock_validate:
            with patch.object(self.command.validator, "check_file_size") as mock_size:
                with patch.object(
                    self.command.processor, "convert_file"
                ) as mock_convert:
                    with patch("sys.exit"):
                        mock_validate.return_value = Path(input_file)
                        mock_size.return_value = True
                        mock_convert.return_value = Path(output_dir) / "output.html"

                        # When
                        self.command.execute(
                            input_file=input_file,
                            output=output_dir,
                            no_preview=True,
                            watch=False,
                            config=None,
                            show_test_cases=True,
                            template_name="custom_template",
                            include_source=True,
                            syntax_check=False,
                        )

                        # Then
                        mock_convert.assert_called_once_with(
                            Path(input_file),
                            output_dir,
                            None,  # config_obj
                            show_test_cases=True,
                            template="custom_template",
                            include_source=True,
                        )

        # Cleanup
        Path(input_file).unlink()
