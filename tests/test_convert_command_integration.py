"""Convert Command Integration Tests

Integration tests for Convert Command end-to-end functionality.
Issue #540 Phase 2: 300行制限遵守のための分割
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


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
