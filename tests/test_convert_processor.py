"""
ConvertProcessorのテスト

Test coverage targets:
- 変換ロジック: 85%
- プログレス表示: 70%
- ファイル処理: 80%
"""

import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from kumihan_formatter.commands.convert.convert_processor import ConvertProcessor
from kumihan_formatter.core.utilities.logger import get_logger


class TestConvertProcessor:
    """ConvertProcessorクラスのテスト"""

    def setup_method(self):
        """各テストメソッド実行前のセットアップ"""
        self.processor = ConvertProcessor()

    def test_init_creates_dependencies(self):
        """初期化時に必要な依存関係が作成されることを確認"""
        # Given & When
        processor = ConvertProcessor()

        # Then
        assert processor.logger is not None
        assert processor.file_ops is not None

    @patch("kumihan_formatter.commands.convert.convert_processor.parse")
    @patch("kumihan_formatter.commands.convert.convert_processor.render")
    def test_convert_file_basic_flow(self, mock_render, mock_parse):
        """基本的なファイル変換フローのテスト"""
        # Given
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test content")
            input_file = Path(f.name)

        output_dir = tempfile.mkdtemp()
        expected_output = Path(output_dir) / f"{input_file.stem}.html"

        # Mock the parse and render functions
        mock_ast = [{"type": "text", "content": "test"}]
        mock_parse.return_value = mock_ast
        mock_render.return_value = "<html>test</html>"

        with patch.object(self.processor.file_ops, "read_text_file") as mock_read:
            with patch.object(self.processor.file_ops, "write_text_file") as mock_write:
                mock_read.return_value = "test content"

                # When
                result = self.processor.convert_file(
                    input_path=input_file,
                    output_dir=output_dir,
                    config_obj=None,
                    show_test_cases=False,
                    template=None,
                    include_source=False,
                )

                # Then
                assert result == expected_output
                mock_read.assert_called_once_with(input_file)
                mock_parse.assert_called_once_with("test content", None)
                mock_render.assert_called_once_with(
                    mock_ast, None, template=None, title=input_file.stem
                )
                mock_write.assert_called_once_with(expected_output, "<html>test</html>")

        # Cleanup
        input_file.unlink()

    @patch("kumihan_formatter.commands.convert.convert_processor.parse")
    @patch("kumihan_formatter.commands.convert.convert_processor.render")
    def test_convert_file_with_source_display(self, mock_render, mock_parse):
        """ソース表示ありのファイル変換テスト"""
        # Given
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test content")
            input_file = Path(f.name)

        output_dir = tempfile.mkdtemp()

        mock_ast = [{"type": "text", "content": "test"}]
        mock_parse.return_value = mock_ast
        mock_render.return_value = "<html>test with source</html>"

        with patch.object(self.processor.file_ops, "read_text_file") as mock_read:
            with patch.object(self.processor.file_ops, "write_text_file") as mock_write:
                mock_read.return_value = "test content"

                # When
                result = self.processor.convert_file(
                    input_path=input_file,
                    output_dir=output_dir,
                    config_obj=None,
                    show_test_cases=False,
                    template="custom_template",
                    include_source=True,
                )

                # Then
                mock_render.assert_called_once_with(
                    mock_ast,
                    None,
                    template="custom_template",
                    title=input_file.stem,
                    source_text="test content",
                    source_filename=input_file.name,
                )

        # Cleanup
        input_file.unlink()

    @patch("kumihan_formatter.commands.convert.convert_processor.parse")
    @patch("kumihan_formatter.commands.convert.convert_processor.render")
    def test_convert_file_with_test_cases(self, mock_render, mock_parse):
        """テストケース表示ありのファイル変換テスト"""
        # Given
        test_content = """
        # [TEST-1] Basic test: This is a test
        Some content
        # [TEST-2] Advanced test: Another test
        More content
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(test_content)
            input_file = Path(f.name)

        output_dir = tempfile.mkdtemp()

        mock_ast = [{"type": "text", "content": "test"}]
        mock_parse.return_value = mock_ast
        mock_render.return_value = "<html>test</html>"

        with patch.object(self.processor.file_ops, "read_text_file") as mock_read:
            with patch.object(self.processor.file_ops, "write_text_file") as mock_write:
                with patch.object(
                    self.processor, "_show_test_cases"
                ) as mock_show_tests:
                    mock_read.return_value = test_content

                    # When
                    self.processor.convert_file(
                        input_path=input_file,
                        output_dir=output_dir,
                        config_obj=None,
                        show_test_cases=True,
                        template=None,
                        include_source=False,
                    )

                    # Then
                    mock_show_tests.assert_called_once_with(test_content)

        # Cleanup
        input_file.unlink()

    def test_determine_output_path_creates_directory(self):
        """出力ディレクトリが存在しない場合の作成テスト"""
        # Given
        input_file = Path("test.txt")
        output_dir = tempfile.mkdtemp() + "/new_subdir"

        # When
        result = self.processor._determine_output_path(input_file, output_dir)

        # Then
        assert result == Path(output_dir) / "test.html"
        assert Path(output_dir).exists()

        # Cleanup
        Path(output_dir).rmdir()

    def test_determine_output_path_existing_directory(self):
        """既存の出力ディレクトリでのテスト"""
        # Given
        input_file = Path("test_file.txt")
        output_dir = tempfile.mkdtemp()

        # When
        result = self.processor._determine_output_path(input_file, output_dir)

        # Then
        assert result == Path(output_dir) / "test_file.html"

    @patch("kumihan_formatter.commands.convert.convert_processor.parse")
    @patch("time.time")
    def test_parse_with_progress_small_file(self, mock_time, mock_parse):
        """小さなファイルのパース処理テスト"""
        # Given
        small_text = "small content"
        config = None
        input_path = Path("test.txt")

        mock_ast = [{"type": "text", "content": "test"}]
        mock_parse.return_value = mock_ast

        # 実行時間をシミュレート（time.time()が複数回呼ばれる可能性に対応）
        mock_time.side_effect = [
            0.0,
            0.1,
            0.1,
            0.1,
            0.1,
        ]  # start_time, elapsed計算用など

        # When
        result = self.processor._parse_with_progress(small_text, config, input_path)

        # Then
        assert result == mock_ast
        mock_parse.assert_called_once_with(small_text, config)

    @patch("kumihan_formatter.commands.convert.convert_processor.parse")
    @patch("time.sleep")
    def test_parse_with_progress_large_file(self, mock_sleep, mock_parse):
        """大きなファイルのパース処理テスト（50MB以上）"""
        # Given
        # 50MB以上のテキストをシミュレート
        large_text = "x" * (50 * 1024 * 1024 + 1)
        config = None
        input_path = Path("large_test.txt")

        mock_ast = [{"type": "text", "content": "test"}]
        mock_parse.return_value = mock_ast

        # When
        result = self.processor._parse_with_progress(large_text, config, input_path)

        # Then
        assert result == mock_ast
        mock_parse.assert_called_once_with(large_text, config)
        # 段階的表示のためのsleepが呼ばれることを確認
        assert mock_sleep.call_count >= 10

    @patch("kumihan_formatter.commands.convert.convert_processor.render")
    @patch("time.time")
    def test_render_with_progress_small_ast(self, mock_time, mock_render):
        """小さなASTのレンダリング処理テスト"""
        # Given
        small_ast = [{"type": "text", "content": "test"}] * 10
        config = None
        template = None
        title = "test"

        mock_render.return_value = "<html>test</html>"
        mock_time.side_effect = [
            0.0,
            0.1,
            0.1,
            0.1,
            0.1,
        ]  # start_time, elapsed計算用など

        # When
        result = self.processor._render_with_progress(
            small_ast, config, template, title
        )

        # Then
        assert result == "<html>test</html>"
        mock_render.assert_called_once_with(
            small_ast, config, template=template, title=title
        )

    @patch("kumihan_formatter.commands.convert.convert_processor.render")
    @patch("time.sleep")
    def test_render_with_progress_large_ast(self, mock_sleep, mock_render):
        """大きなASTのレンダリング処理テスト（5000ノード以上）"""
        # Given
        large_ast = [{"type": "text", "content": "test"}] * 6000
        config = None
        template = "custom"
        title = "test"

        mock_render.return_value = "<html>large content</html>"

        # When
        result = self.processor._render_with_progress(
            large_ast, config, template, title
        )

        # Then
        assert result == "<html>large content</html>"
        mock_render.assert_called_once_with(
            large_ast, config, template=template, title=title
        )
        # 段階的表示のためのsleepが呼ばれることを確認
        assert mock_sleep.call_count >= 10

    @patch("kumihan_formatter.commands.convert.convert_processor.render")
    def test_render_with_progress_with_source(self, mock_render):
        """ソース付きレンダリング処理テスト"""
        # Given
        ast = [{"type": "text", "content": "test"}]
        config = None
        template = None
        title = "test"
        source_text = "original source"
        source_filename = "test.txt"

        mock_render.return_value = "<html>test with source</html>"

        # When
        result = self.processor._render_with_progress(
            ast, config, template, title, source_text, source_filename
        )

        # Then
        assert result == "<html>test with source</html>"
        mock_render.assert_called_once_with(
            ast,
            config,
            template=template,
            title=title,
            source_text=source_text,
            source_filename=source_filename,
        )

    def test_show_test_cases_extraction(self):
        """テストケース抽出のテスト"""
        # Given
        text_with_tests = """
        # [TEST-1] Basic: This is a basic test
        Some content
        # [TEST-2] Advanced: This is an advanced test
        More content
        # [TEST-3] Complex: This is a complex test
        """

        with patch(
            "kumihan_formatter.commands.convert.convert_processor.get_console_ui"
        ) as mock_ui:
            mock_console = Mock()
            mock_ui.return_value = mock_console

            # When
            self.processor._show_test_cases(text_with_tests)

            # Then
            mock_console.test_cases_detected.assert_called_once()
            args = mock_console.test_cases_detected.call_args
            assert args[0][0] == 3  # 3つのテストケースが見つかる
            test_cases = args[0][1]
            assert len(test_cases) == 3
            assert test_cases[0] == ("1", "Basic", "This is a basic test")
            assert test_cases[1] == ("2", "Advanced", "This is an advanced test")
            assert test_cases[2] == ("3", "Complex", "This is a complex test")

    def test_show_test_cases_no_tests(self):
        """テストケースがない場合のテスト"""
        # Given
        text_without_tests = "Regular content without test cases"

        with patch(
            "kumihan_formatter.commands.convert.convert_processor.get_console_ui"
        ) as mock_ui:
            mock_console = Mock()
            mock_ui.return_value = mock_console

            # When
            self.processor._show_test_cases(text_without_tests)

            # Then
            mock_console.test_cases_detected.assert_not_called()

    @patch(
        "kumihan_formatter.core.file_path_utilities.FilePathUtilities.get_file_size_info"
    )
    def test_show_conversion_stats_no_errors(self, mock_size_info):
        """エラーなしの変換統計表示テスト"""
        # Given
        ast = [
            {"type": "text", "content": "test1"},
            {"type": "text", "content": "test2"},
        ]
        text = "test content"
        output_file = Path("output.html")
        input_path = Path("input.txt")

        mock_size_info.return_value = {"size_mb": 0.1}

        with patch(
            "kumihan_formatter.commands.convert.convert_processor.get_console_ui"
        ) as mock_ui:
            mock_console = Mock()
            mock_ui.return_value = mock_console

            # When
            self.processor._show_conversion_stats(ast, text, output_file, input_path)

            # Then
            mock_console.conversion_complete.assert_called_once_with(str(output_file))
            mock_console.validation_warning.assert_not_called()

    @patch(
        "kumihan_formatter.core.file_path_utilities.FilePathUtilities.get_file_size_info"
    )
    def test_show_conversion_stats_with_errors(self, mock_size_info):
        """エラーありの変換統計表示テスト"""
        # Given
        text_node = Mock()
        text_node.type = "text"
        error_node1 = Mock()
        error_node1.type = "error"
        error_node2 = Mock()
        error_node2.type = "error"

        ast = [text_node, error_node1, error_node2]
        text = "test content"
        output_file = Path("output.html")
        input_path = Path("regular_file.txt")

        mock_size_info.return_value = {"size_mb": 0.1}

        with patch(
            "kumihan_formatter.commands.convert.convert_processor.get_console_ui"
        ) as mock_ui:
            mock_console = Mock()
            mock_ui.return_value = mock_console

            # When
            self.processor._show_conversion_stats(ast, text, output_file, input_path)

            # Then
            mock_console.conversion_complete.assert_called_once_with(str(output_file))
            mock_console.validation_warning.assert_called_once_with(2, False)

    @patch(
        "kumihan_formatter.core.file_path_utilities.FilePathUtilities.get_file_size_info"
    )
    def test_show_conversion_stats_sample_file_errors(self, mock_size_info):
        """サンプルファイルでのエラー統計表示テスト"""
        # Given
        error_node = Mock()
        error_node.type = "error"
        ast = [error_node]
        text = "test content"
        output_file = Path("output.html")
        input_path = Path("02-basic.txt")  # サンプルファイル

        mock_size_info.return_value = {"size_mb": 0.1}

        with patch(
            "kumihan_formatter.commands.convert.convert_processor.get_console_ui"
        ) as mock_ui:
            mock_console = Mock()
            mock_ui.return_value = mock_console

            # When
            self.processor._show_conversion_stats(ast, text, output_file, input_path)

            # Then
            mock_console.validation_warning.assert_called_once_with(1, True)

    @patch(
        "kumihan_formatter.core.file_path_utilities.FilePathUtilities.get_file_size_info"
    )
    def test_show_conversion_stats_large_file_detailed_stats(self, mock_size_info):
        """大きなファイルの詳細統計表示テスト"""
        # Given
        ast = [{"type": "text", "content": "test"}] * 600  # 500ノード以上
        text = "test content"
        output_file = Path("output.html")
        input_path = Path("large_file.txt")

        # 1MB以上のファイルサイズをシミュレート
        mock_size_info.side_effect = [
            {"size_mb": 1.5},  # input file
            {"size_mb": 2.0},  # output file
        ]

        with patch(
            "kumihan_formatter.commands.convert.convert_processor.get_console_ui"
        ) as mock_ui:
            mock_console = Mock()
            mock_ui.return_value = mock_console

            # When
            self.processor._show_conversion_stats(ast, text, output_file, input_path)

            # Then
            mock_console.show_detailed_stats.assert_called_once()
            stats = mock_console.show_detailed_stats.call_args[0][0]
            assert stats["input_size_mb"] == 1.5
            assert stats["output_size_mb"] == 2.0
            assert stats["node_count"] == 600
            assert stats["error_count"] == 0

    def test_conversion_timing_logged(self):
        """変換時間がログに記録されることをテスト"""
        # Given
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test content")
            input_file = Path(f.name)

        output_dir = tempfile.mkdtemp()

        with patch(
            "kumihan_formatter.commands.convert.convert_processor.parse"
        ) as mock_parse:
            with patch(
                "kumihan_formatter.commands.convert.convert_processor.render"
            ) as mock_render:
                with patch.object(
                    self.processor.file_ops, "read_text_file"
                ) as mock_read:
                    with patch.object(
                        self.processor.file_ops, "write_text_file"
                    ) as mock_write:
                        with patch.object(self.processor.logger, "info") as mock_log:
                            mock_parse.return_value = []
                            mock_render.return_value = "<html></html>"
                            mock_read.return_value = "test"

                            # When
                            self.processor.convert_file(
                                input_path=input_file, output_dir=output_dir
                            )

                            # Then
                            # タイミングログが記録されることを確認
                            timing_logs = [
                                call
                                for call in mock_log.call_args_list
                                if "completed in" in str(call)
                            ]
                            assert len(timing_logs) > 0

        # Cleanup
        input_file.unlink()
