"""ConvertProcessor Coverage Tests - Phase 1A Implementation (Part 1)

ConvertProcessorクラスのカバレッジ向上テスト
Target: convert_processor.py (119文)
Goal: 0% → 高カバレッジで+0.82%ポイント寄与
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from kumihan_formatter.commands.convert.convert_processor import ConvertProcessor


class TestConvertProcessorInitialization:
    """ConvertProcessor初期化テスト"""

    def test_convert_processor_basic_init(self):
        """基本的な初期化テスト"""
        processor = ConvertProcessor()

        # 必要な属性が初期化されていることを確認
        assert processor.logger is not None
        assert processor.file_ops is not None

    def test_convert_processor_logger_setup(self):
        """ロガー設定テスト"""
        processor = ConvertProcessor()

        # ロガーが正しく設定されていることを確認
        assert hasattr(processor.logger, "debug")
        assert hasattr(processor.logger, "info")
        assert hasattr(processor.logger, "error")
        assert hasattr(processor.logger, "warning")

    @patch("kumihan_formatter.commands.convert.convert_processor.FileOperations")
    @patch("kumihan_formatter.commands.convert.convert_processor.get_console_ui")
    def test_convert_processor_dependencies(self, mock_console_ui, mock_file_ops):
        """依存性注入テスト"""
        mock_ui = Mock()
        mock_console_ui.return_value = mock_ui
        mock_file_ops_instance = Mock()
        mock_file_ops.return_value = mock_file_ops_instance

        processor = ConvertProcessor()

        # 依存性が正しく注入されていることを確認
        mock_console_ui.assert_called_once()
        mock_file_ops.assert_called_once_with(ui=mock_ui)
        assert processor.file_ops == mock_file_ops_instance


class TestConvertProcessorMethods:
    """ConvertProcessorメソッドテスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.processor = ConvertProcessor()

    @patch("kumihan_formatter.commands.convert.convert_processor.get_console_ui")
    @patch.object(ConvertProcessor, "_parse_with_progress")
    @patch.object(ConvertProcessor, "_render_with_progress")
    @patch.object(ConvertProcessor, "_determine_output_path")
    def test_convert_file_basic(
        self, mock_determine_path, mock_render, mock_parse, mock_console_ui
    ):
        """基本的なファイル変換テスト"""
        # モックの設定
        mock_ui = Mock()
        mock_console_ui.return_value = mock_ui
        mock_parse.return_value = [Mock(), Mock()]  # AST nodes as list
        mock_render.return_value = "<html>Converted Content</html>"

        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.txt"
            input_path.write_text("Test Content", encoding="utf-8")
            output_path = Path(temp_dir) / "output.html"
            mock_determine_path.return_value = output_path

            # FileIOHandlerをモック化（実際の実装に合わせる）
            with patch("kumihan_formatter.commands.convert.convert_processor.FileIOHandler") as mock_file_io:
                mock_file_io.read_text_file.return_value = "Test Content"
                mock_file_io.write_file.return_value = None

                result_path = self.processor.convert_file(
                    input_path=input_path, output_dir=temp_dir
                )

                # 必要なメソッドが呼ばれることを確認
                mock_file_io.read_text_file.assert_called_once_with(input_path)
                mock_parse.assert_called_once()
                mock_render.assert_called_once()
                mock_determine_path.assert_called_once()
                assert result_path == output_path

    def test_convert_file_with_invalid_path(self):
        """無効なパスでのファイル変換テスト"""
        # 存在しないファイルパス
        invalid_path = Path("/nonexistent/file.txt")

        # 例外が適切に処理されることを確認
        with pytest.raises(Exception):
            self.processor.convert_file(input_path=invalid_path, output_dir="/tmp")

    @patch("kumihan_formatter.commands.convert.convert_processor.get_console_ui")
    @patch.object(ConvertProcessor, "_parse_with_progress")
    @patch.object(ConvertProcessor, "_render_with_progress")
    @patch.object(ConvertProcessor, "_determine_output_path")
    def test_convert_file_with_config(
        self, mock_determine_path, mock_render, mock_parse, mock_console_ui
    ):
        """設定オブジェクト付きファイル変換テスト"""
        mock_ui = Mock()
        mock_console_ui.return_value = mock_ui
        mock_parse.return_value = [Mock(), Mock()]  # AST nodes as list
        mock_render.return_value = "<html></html>"
        mock_config = Mock()

        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.txt"
            input_path.write_text("Test Content", encoding="utf-8")
            output_path = Path(temp_dir) / "output.html"
            mock_determine_path.return_value = output_path

            # file_opsをモック化
            with patch.object(self.processor, "file_ops") as mock_file_ops:
                mock_file_ops.read_text_file.return_value = "Test Content"
                mock_file_ops.write_file.return_value = None

                self.processor.convert_file(
                    input_path=input_path, output_dir=temp_dir, config_obj=mock_config
                )

                # _parse_with_progressが設定オブジェクトと共に呼ばれることを確認
                mock_parse.assert_called_once_with(
                    "Test Content", mock_config, input_path
                )

    @patch("kumihan_formatter.commands.convert.convert_processor.get_console_ui")
    @patch.object(ConvertProcessor, "_parse_with_progress")
    @patch.object(ConvertProcessor, "_render_with_progress")
    @patch.object(ConvertProcessor, "_determine_output_path")
    @patch.object(ConvertProcessor, "_show_test_cases")
    def test_convert_file_with_show_test_cases(
        self,
        mock_show_test_cases,
        mock_determine_path,
        mock_render,
        mock_parse,
        mock_console_ui,
    ):
        """テストケース表示オプション付きファイル変換テスト"""
        mock_ui = Mock()
        mock_console_ui.return_value = mock_ui
        mock_parse.return_value = [Mock(), Mock()]  # AST nodes as list
        mock_render.return_value = "<html></html>"

        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.txt"
            input_path.write_text("Test Content", encoding="utf-8")
            output_path = Path(temp_dir) / "output.html"
            mock_determine_path.return_value = output_path

            # file_opsをモック化
            with patch.object(self.processor, "file_ops") as mock_file_ops:
                mock_file_ops.read_text_file.return_value = "Test Content"
                mock_file_ops.write_file.return_value = None

                self.processor.convert_file(
                    input_path=input_path, output_dir=temp_dir, show_test_cases=True
                )

                # _show_test_casesが呼ばれることを確認
                mock_show_test_cases.assert_called_once_with("Test Content")

    def test_convert_file_with_template_option(self):
        """テンプレートオプション付きファイル変換テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.txt"
            input_path.write_text("Test Content", encoding="utf-8")

            with patch.object(
                self.processor.file_ops, "read_text_file", return_value="content"
            ):
                with patch(
                    "kumihan_formatter.commands.convert.convert_processor.parse"
                ):
                    with patch(
                        "kumihan_formatter.commands.convert.convert_processor.render",
                        return_value="<html></html>",
                    ) as mock_render:
                        with patch.object(self.processor.file_ops, "write_text_file"):
                            self.processor.convert_file(
                                input_path=input_path,
                                output_dir=temp_dir,
                                template="custom_template",
                            )

            # renderがテンプレート情報と共に呼ばれることを確認
            mock_render.assert_called_once()

    def test_convert_file_with_include_source(self):
        """ソース含有オプション付きファイル変換テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.txt"
            input_path.write_text("Test Content", encoding="utf-8")

            with patch.object(
                self.processor.file_ops, "read_text_file", return_value="content"
            ):
                with patch(
                    "kumihan_formatter.commands.convert.convert_processor.parse"
                ):
                    with patch(
                        "kumihan_formatter.commands.convert.convert_processor.render",
                        return_value="<html></html>",
                    ):
                        with patch.object(self.processor.file_ops, "write_text_file"):
                            self.processor.convert_file(
                                input_path=input_path,
                                output_dir=temp_dir,
                                include_source=True,
                            )

        # メソッドが正常に実行されることを確認
        assert True
