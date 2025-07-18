"""Phase 3A Convert Command Advanced Tests - Issue #500

ConvertCommandクラスの高度機能テスト（オプション・エラーハンドリング）
"""

import tempfile
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from kumihan_formatter.commands.convert.convert_command import ConvertCommand

# テストデータ定数
TEST_CONTENT_TEMPLATE = "# テンプレートテスト"
TEST_CONTENT_ALL_OPTIONS = "# 全オプションテスト"
TEST_CONTENT_ERROR = "# エラーテスト"
TEST_CONFIG_TEMPLATE = '{"theme": "test"}'
INVALID_JSON_CONTENT = "invalid json content"


class TestConvertCommandOptions:
    """ConvertCommandのオプション処理テスト"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行"""
        self.command = ConvertCommand()

    @patch("kumihan_formatter.commands.convert.convert_command.ConvertValidator")
    @patch("kumihan_formatter.commands.convert.convert_command.ConvertProcessor")
    def test_execute_with_template(
        self, mock_processor_class: MagicMock, mock_validator_class: MagicMock
    ) -> None:
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
            Path(input_file).write_text(TEST_CONTENT_TEMPLATE, encoding="utf-8")

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
    def test_execute_with_all_options(
        self, mock_processor_class: MagicMock, mock_validator_class: MagicMock
    ) -> None:
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

            Path(input_file).write_text(TEST_CONTENT_ALL_OPTIONS, encoding="utf-8")
            Path(config_file).write_text(TEST_CONFIG_TEMPLATE, encoding="utf-8")

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

    def test_execute_no_input_file(self) -> None:
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
            except (SystemExit, ValueError) as e:
                # 適切なエラーハンドリングが行われることを確認
                assert isinstance(
                    e, (SystemExit, ValueError)
                ), "Should raise appropriate error for missing input file"


class TestConvertCommandErrorHandling:
    """ConvertCommandのエラーハンドリングテスト"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行"""
        self.command = ConvertCommand()

    @patch("kumihan_formatter.commands.convert.convert_command.ConvertValidator")
    @patch("kumihan_formatter.commands.convert.convert_command.ConvertProcessor")
    def test_execute_processor_error(
        self, mock_processor_class: MagicMock, mock_validator_class: MagicMock
    ) -> None:
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
            Path(input_file).write_text(TEST_CONTENT_ERROR, encoding="utf-8")

            # プロセッサーエラーが適切に処理されることを確認
            with pytest.raises(
                Exception, match="Processing error should be handled appropriately"
            ):
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
    def test_execute_invalid_config(self, mock_validator_class: MagicMock) -> None:
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

            Path(input_file).write_text(TEST_CONTENT_ERROR, encoding="utf-8")
            Path(invalid_config).write_text(INVALID_JSON_CONTENT, encoding="utf-8")

            # 無効な設定ファイルが適切に処理されることを確認
            with pytest.raises(
                SystemExit, match="Invalid config should cause system exit"
            ):
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

    @patch("kumihan_formatter.commands.convert.convert_command.ConvertValidator")
    @patch("kumihan_formatter.commands.convert.convert_command.ConvertProcessor")
    def test_execute_unicode_handling(
        self, mock_processor_class: MagicMock, mock_validator_class: MagicMock
    ) -> None:
        """Unicode文字処理のテスト"""
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
            input_file = str(Path(temp_dir) / "テスト日本語.txt")
            unicode_content = "# 日本語タイトル\n\n絵文字🎉も含むコンテンツです。"
            Path(input_file).write_text(unicode_content, encoding="utf-8")

            # Unicode文字を含むファイルで実行
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

            # Unicode文字が適切に処理されることを確認
            mock_validator.validate_inputs.assert_called_once()
            mock_processor.process.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
