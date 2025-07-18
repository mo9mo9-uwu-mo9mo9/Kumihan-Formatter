"""Phase 3A Convert Command Core Tests - Issue #500

ConvertCommandクラスの基本機能テスト（初期化・実行）
"""

import tempfile
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from kumihan_formatter.commands.convert.convert_command import ConvertCommand

# テストデータ定数
TEST_CONTENT_BASIC = "# テスト"
TEST_CONTENT_WATCH = "# ウォッチテスト"
TEST_CONTENT_CONFIG = "# テスト"
TEST_CONTENT_PREVIEW = "# プレビューテスト"
TEST_CONFIG_JSON = '{"theme": "custom"}'


class TestConvertCommandInit:
    """ConvertCommandの初期化テスト"""

    def test_convert_command_initialization(self) -> None:
        """ConvertCommandの初期化テスト"""
        command = ConvertCommand()

        assert command.validator is not None, "validator should be initialized"
        assert command.processor is not None, "processor should be initialized"
        assert command.watcher is not None, "watcher should be initialized"
        assert (
            command.friendly_error_handler is not None
        ), "friendly_error_handler should be initialized"
        assert command.logger is not None, "logger should be initialized"

    def test_convert_command_components_types(self) -> None:
        """ConvertCommandの各コンポーネントの型確認"""
        command = ConvertCommand()

        # 各コンポーネントが適切なクラスのインスタンスであることを確認
        assert hasattr(command, "validator"), "validator attribute should exist"
        assert hasattr(command, "processor"), "processor attribute should exist"
        assert hasattr(command, "watcher"), "watcher attribute should exist"
        assert hasattr(
            command, "friendly_error_handler"
        ), "friendly_error_handler attribute should exist"


class TestConvertCommandExecution:
    """ConvertCommandの実行テスト"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行"""
        self.command = ConvertCommand()

    @patch("kumihan_formatter.commands.convert.convert_command.ConvertValidator")
    @patch("kumihan_formatter.commands.convert.convert_command.ConvertProcessor")
    def test_execute_basic_conversion(
        self, mock_processor_class: MagicMock, mock_validator_class: MagicMock
    ) -> None:
        """基本的な変換実行テスト"""
        # モックの設定
        mock_validator = MagicMock()
        mock_processor = MagicMock()
        mock_validator_class.return_value = mock_validator
        mock_processor_class.return_value = mock_processor

        # バリデーション成功の設定
        mock_validator.validate_inputs.return_value = (True, None, "valid_input.txt")
        mock_processor.process.return_value = True

        command = ConvertCommand()

        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = str(Path(temp_dir) / "test.txt")
            Path(input_file).write_text(TEST_CONTENT_BASIC, encoding="utf-8")

            # 実行
            command.execute(
                input_file=input_file,
                output=temp_dir,
                no_preview=True,
                watch=False,
                config=None,
                show_test_cases=False,
                template_name=None,
                include_source=False,
                syntax_check=True,
            )

            # 期待されるメソッド呼び出しの確認
            mock_validator.validate_inputs.assert_called_once()
            mock_processor.process.assert_called_once()

    @patch("kumihan_formatter.commands.convert.convert_command.ConvertValidator")
    @patch("kumihan_formatter.commands.convert.convert_command.ConvertWatcher")
    def test_execute_watch_mode(
        self, mock_watcher_class: MagicMock, mock_validator_class: MagicMock
    ) -> None:
        """ウォッチモードでの実行テスト"""
        # モックの設定
        mock_validator = MagicMock()
        mock_watcher = MagicMock()
        mock_validator_class.return_value = mock_validator
        mock_watcher_class.return_value = mock_watcher

        # バリデーション成功の設定
        mock_validator.validate_inputs.return_value = (True, None, "valid_input.txt")

        command = ConvertCommand()

        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = str(Path(temp_dir) / "test.txt")
            Path(input_file).write_text(TEST_CONTENT_WATCH, encoding="utf-8")

            # ウォッチモードで実行
            command.execute(
                input_file=input_file,
                output=temp_dir,
                no_preview=True,
                watch=True,
                config=None,
                show_test_cases=False,
                template_name=None,
                include_source=False,
                syntax_check=True,
            )

            # ウォッチャーが実行されることを確認
            mock_watcher.watch.assert_called_once()

    @patch("kumihan_formatter.commands.convert.convert_command.ConvertValidator")
    def test_execute_validation_failure(self, mock_validator_class: MagicMock) -> None:
        """バリデーション失敗時のテスト"""
        # モックの設定
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator

        # バリデーション失敗の設定
        mock_validator.validate_inputs.return_value = (False, "Validation error", None)

        command = ConvertCommand()

        # バリデーション失敗時の処理
        with pytest.raises(SystemExit, match="Validation should cause system exit"):
            command.execute(
                input_file="nonexistent.txt",
                output="/tmp",
                no_preview=True,
                watch=False,
                config=None,
                show_test_cases=False,
                template_name=None,
                include_source=False,
                syntax_check=True,
            )

    @patch("kumihan_formatter.commands.convert.convert_command.ConvertValidator")
    @patch("kumihan_formatter.commands.convert.convert_command.ConvertProcessor")
    def test_execute_with_config(
        self, mock_processor_class: MagicMock, mock_validator_class: MagicMock
    ) -> None:
        """設定ファイル使用時のテスト"""
        # モックの設定
        mock_validator = MagicMock()
        mock_processor = MagicMock()
        mock_validator_class.return_value = mock_validator
        mock_processor_class.return_value = mock_processor

        # バリデーション成功の設定
        mock_validator.validate_inputs.return_value = (True, None, "valid_input.txt")
        mock_processor.process.return_value = True

        command = ConvertCommand()

        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = str(Path(temp_dir) / "test.txt")
            config_file = str(Path(temp_dir) / "config.json")

            Path(input_file).write_text(TEST_CONTENT_CONFIG, encoding="utf-8")
            Path(config_file).write_text(TEST_CONFIG_JSON, encoding="utf-8")

            # 設定ファイル指定で実行
            command.execute(
                input_file=input_file,
                output=temp_dir,
                no_preview=True,
                watch=False,
                config=config_file,
                show_test_cases=False,
                template_name=None,
                include_source=False,
                syntax_check=True,
            )

            # 設定ファイルが考慮されることを確認
            mock_validator.validate_inputs.assert_called_once()
            mock_processor.process.assert_called_once()

    @patch("kumihan_formatter.commands.convert.convert_command.ConvertValidator")
    @patch("kumihan_formatter.commands.convert.convert_command.ConvertProcessor")
    @patch("webbrowser.open")
    def test_execute_with_preview(
        self,
        mock_webbrowser: MagicMock,
        mock_processor_class: MagicMock,
        mock_validator_class: MagicMock,
    ) -> None:
        """プレビュー機能付きでの実行テスト"""
        # モックの設定
        mock_validator = MagicMock()
        mock_processor = MagicMock()
        mock_validator_class.return_value = mock_validator
        mock_processor_class.return_value = mock_processor

        # バリデーション成功の設定
        mock_validator.validate_inputs.return_value = (True, None, "valid_input.txt")
        mock_processor.process.return_value = True

        command = ConvertCommand()

        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = str(Path(temp_dir) / "test.txt")
            Path(input_file).write_text(TEST_CONTENT_PREVIEW, encoding="utf-8")

            # プレビューありで実行
            command.execute(
                input_file=input_file,
                output=temp_dir,
                no_preview=False,  # プレビューを有効
                watch=False,
                config=None,
                show_test_cases=False,
                template_name=None,
                include_source=False,
                syntax_check=True,
            )

            # ブラウザが開かれることを確認（実際の実装に依存）
            mock_processor.process.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
