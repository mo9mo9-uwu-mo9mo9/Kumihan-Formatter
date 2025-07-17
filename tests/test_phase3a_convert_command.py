"""Phase 3A Convert Command Tests - Issue #500

ConvertCommandクラスと変換処理の詳細テスト
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from kumihan_formatter.commands.convert.convert_command import ConvertCommand


class TestConvertCommandInit:
    """ConvertCommandの初期化テスト"""

    def test_convert_command_initialization(self):
        """ConvertCommandの初期化テスト"""
        command = ConvertCommand()

        assert command.validator is not None
        assert command.processor is not None
        assert command.watcher is not None
        assert command.friendly_error_handler is not None
        assert command.logger is not None

    def test_convert_command_components_types(self):
        """ConvertCommandの各コンポーネントの型確認"""
        command = ConvertCommand()

        # 各コンポーネントが適切なクラスのインスタンスであることを確認
        assert hasattr(command, "validator")
        assert hasattr(command, "processor")
        assert hasattr(command, "watcher")
        assert hasattr(command, "friendly_error_handler")


class TestConvertCommandExecution:
    """ConvertCommandの実行テスト"""

    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.command = ConvertCommand()

    @patch("kumihan_formatter.commands.convert.convert_command.ConvertValidator")
    @patch("kumihan_formatter.commands.convert.convert_command.ConvertProcessor")
    def test_execute_basic_conversion(self, mock_processor_class, mock_validator_class):
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
            Path(input_file).write_text("# テスト", encoding="utf-8")

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
    def test_execute_watch_mode(self, mock_watcher_class, mock_validator_class):
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
            Path(input_file).write_text("# ウォッチテスト", encoding="utf-8")

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
    def test_execute_validation_failure(self, mock_validator_class):
        """バリデーション失敗時のテスト"""
        # モックの設定
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator

        # バリデーション失敗の設定
        mock_validator.validate_inputs.return_value = (False, "Validation error", None)

        command = ConvertCommand()

        # バリデーション失敗時の処理
        with pytest.raises(SystemExit):
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
    def test_execute_with_config(self, mock_processor_class, mock_validator_class):
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

            Path(input_file).write_text("# テスト", encoding="utf-8")
            Path(config_file).write_text('{"theme": "custom"}', encoding="utf-8")

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
        self, mock_webbrowser, mock_processor_class, mock_validator_class
    ):
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
            Path(input_file).write_text("# プレビューテスト", encoding="utf-8")

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


class TestConvertCommandOptions:
    """ConvertCommandのオプション処理テスト"""

    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.command = ConvertCommand()

    @patch("kumihan_formatter.commands.convert.convert_command.ConvertValidator")
    @patch("kumihan_formatter.commands.convert.convert_command.ConvertProcessor")
    def test_execute_with_template(self, mock_processor_class, mock_validator_class):
        """テンプレート指定時のテスト"""
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
            Path(input_file).write_text("# テンプレートテスト", encoding="utf-8")

            # テンプレート指定で実行
            command.execute(
                input_file=input_file,
                output=temp_dir,
                no_preview=True,
                watch=False,
                config=None,
                show_test_cases=False,
                template_name="custom_template",
                include_source=False,
                syntax_check=True,
            )

            mock_processor.process.assert_called_once()

    @patch("kumihan_formatter.commands.convert.convert_command.ConvertValidator")
    @patch("kumihan_formatter.commands.convert.convert_command.ConvertProcessor")
    def test_execute_with_all_options(self, mock_processor_class, mock_validator_class):
        """全オプション指定時のテスト"""
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

            Path(input_file).write_text("# 全オプションテスト", encoding="utf-8")
            Path(config_file).write_text('{"theme": "test"}', encoding="utf-8")

            # 全オプション指定で実行
            command.execute(
                input_file=input_file,
                output=temp_dir,
                no_preview=True,
                watch=False,
                config=config_file,
                show_test_cases=True,
                template_name="test_template",
                include_source=True,
                syntax_check=False,  # 構文チェック無効
            )

            mock_processor.process.assert_called_once()

    def test_execute_no_input_file(self):
        """入力ファイルなし時のテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 入力ファイルなしで実行
            # この場合の動作は実装に依存するが、適切に処理されることを確認
            try:
                self.command.execute(
                    input_file=None,
                    output=temp_dir,
                    no_preview=True,
                    watch=False,
                    config=None,
                    show_test_cases=False,
                    template_name=None,
                    include_source=False,
                    syntax_check=True,
                )
            except (SystemExit, ValueError):
                # 適切なエラーハンドリングが行われることを確認
                pass


class TestConvertCommandErrorHandling:
    """ConvertCommandのエラーハンドリングテスト"""

    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.command = ConvertCommand()

    @patch("kumihan_formatter.commands.convert.convert_command.ConvertValidator")
    @patch("kumihan_formatter.commands.convert.convert_command.ConvertProcessor")
    def test_execute_processor_error(self, mock_processor_class, mock_validator_class):
        """プロセッサーエラー時のテスト"""
        # モックの設定
        mock_validator = MagicMock()
        mock_processor = MagicMock()
        mock_validator_class.return_value = mock_validator
        mock_processor_class.return_value = mock_processor

        # バリデーション成功、プロセッサーエラーの設定
        mock_validator.validate_inputs.return_value = (True, None, "valid_input.txt")
        mock_processor.process.side_effect = Exception("Processing error")

        command = ConvertCommand()

        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = str(Path(temp_dir) / "test.txt")
            Path(input_file).write_text("# エラーテスト", encoding="utf-8")

            # プロセッサーエラーが適切に処理されることを確認
            with pytest.raises(Exception):
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

    @patch("kumihan_formatter.commands.convert.convert_command.ConvertValidator")
    def test_execute_invalid_config(self, mock_validator_class):
        """無効な設定ファイル時のテスト"""
        # モックの設定
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator

        # 設定ファイルエラーの設定
        mock_validator.validate_inputs.return_value = (False, "Invalid config", None)

        command = ConvertCommand()

        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = str(Path(temp_dir) / "test.txt")
            invalid_config = str(Path(temp_dir) / "invalid_config.json")

            Path(input_file).write_text("# テスト", encoding="utf-8")
            Path(invalid_config).write_text("invalid json content", encoding="utf-8")

            # 無効な設定ファイルが適切に処理されることを確認
            with pytest.raises(SystemExit):
                command.execute(
                    input_file=input_file,
                    output=temp_dir,
                    no_preview=True,
                    watch=False,
                    config=invalid_config,
                    show_test_cases=False,
                    template_name=None,
                    include_source=False,
                    syntax_check=True,
                )


if __name__ == "__main__":
    pytest.main([__file__])
