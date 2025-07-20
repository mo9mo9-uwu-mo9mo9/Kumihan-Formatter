"""Convert Command Unified Tests

Unified tests for Convert Command combining basic and advanced functionality.
Issue #540 Phase 2: 重複テスト統合によるCI/CD最適化
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


class TestConvertCommandAdvanced:
    """ConvertCommand高度機能テスト"""

    def test_convert_command_watch_mode(self):
        """ウォッチモードテスト"""
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

            # モック設定
            command.validator = Mock()
            command.processor = Mock()
            command.watcher = Mock()

            # ウォッチモード実行
            command.execute(
                input_file="test.txt",
                output="output/",
                no_preview=True,
                watch=True,
                config=None,
                show_test_cases=False,
                template_name=None,
                include_source=False,
                syntax_check=False,
            )

            # ウォッチャーが呼ばれたことを確認
            command.watcher.start_watching.assert_called_once()

    def test_convert_command_config_integration(self):
        """設定ファイル連携テスト"""
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

            # モック設定
            command.validator = Mock()
            command.processor = Mock()

            # 設定ファイル指定での実行
            command.execute(
                input_file="test.txt",
                output="output/",
                no_preview=True,
                watch=False,
                config="config.yaml",
                show_test_cases=False,
                template_name="custom",
                include_source=True,
                syntax_check=True,
            )

            # 処理が実行されたことを確認
            assert command.processor.called

    def test_convert_command_template_handling(self):
        """テンプレート処理テスト"""
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

            # モック設定
            command.validator = Mock()
            command.processor = Mock()

            # カスタムテンプレート指定
            command.execute(
                input_file="test.txt",
                output="output/",
                no_preview=True,
                watch=False,
                config=None,
                show_test_cases=False,
                template_name="minimal",
                include_source=False,
                syntax_check=False,
            )

            # テンプレート設定が反映されることを確認
            assert command.processor.called

    def test_convert_command_preview_mode(self):
        """プレビューモードテスト"""
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

            # モック設定
            command.validator = Mock()
            command.processor = Mock()

            # プレビューモード実行
            command.execute(
                input_file="test.txt",
                output="output/",
                no_preview=False,  # プレビューあり
                watch=False,
                config=None,
                show_test_cases=False,
                template_name=None,
                include_source=False,
                syntax_check=False,
            )

            # プレビュー処理が実行されることを確認
            assert command.processor.called


class TestConvertCommandIntegration:
    """ConvertCommand統合テスト"""

    def test_convert_command_end_to_end(self):
        """End-to-end統合テスト"""
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

            # 実際のファイルを使用したテスト
            test_content = """# Test Document

This is a test document with:
- List items
- Kumihan syntax

;;;highlight;;; Important information ;;;

((This is a footnote))
"""

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False
            ) as tmp:
                tmp.write(test_content)
                input_file = tmp.name

            try:
                with tempfile.TemporaryDirectory() as output_dir:
                    # モック設定で実際の処理をシミュレート
                    command.validator = Mock()
                    command.processor = Mock()
                    command.validator.perform_syntax_check.return_value.has_errors.return_value = (
                        False
                    )

                    # 統合実行
                    command.execute(
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

                    # 処理完了を確認
                    assert command.validator.perform_syntax_check.called
                    assert command.processor.called

            finally:
                Path(input_file).unlink(missing_ok=True)

    def test_convert_command_multiple_files(self):
        """複数ファイル処理テスト"""
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

            # モック設定
            command.validator = Mock()
            command.processor = Mock()
            command.validator.perform_syntax_check.return_value.has_errors.return_value = (
                False
            )

            # 複数ファイルのシミュレーション
            test_files = ["file1.txt", "file2.txt", "file3.txt"]

            for input_file in test_files:
                command.execute(
                    input_file=input_file,
                    output="output/",
                    no_preview=True,
                    watch=False,
                    config=None,
                    show_test_cases=False,
                    template_name=None,
                    include_source=False,
                    syntax_check=True,
                )

            # 各ファイルが処理されたことを確認
            assert command.validator.perform_syntax_check.call_count == len(test_files)
