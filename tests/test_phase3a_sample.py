"""Phase 3A Sample Command Tests - Issue #500

sample コマンドの統合テスト
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from kumihan_formatter.commands.sample import SampleCommand


class TestSampleCommand:
    """SampleCommandのテスト"""

    def setup_method(self):
        """各テストメソッドの前に実行"""
        # SampleCommandの初期化時にFileOperationsが必要なため、モック化
        with patch("kumihan_formatter.commands.sample.FileOperations"):
            with patch("kumihan_formatter.commands.sample.PathValidator"):
                with patch("kumihan_formatter.commands.sample.get_console_ui"):
                    self.command = SampleCommand()

    def test_sample_command_initialization(self):
        """SampleCommandの初期化テスト"""
        with patch("kumihan_formatter.commands.sample.FileOperations"):
            with patch("kumihan_formatter.commands.sample.PathValidator"):
                with patch("kumihan_formatter.commands.sample.get_console_ui"):
                    command = SampleCommand()
                    assert command is not None
                    assert hasattr(command, "file_ops")
                    assert hasattr(command, "path_validator")

    @patch("kumihan_formatter.commands.sample.get_console_ui")
    @patch("kumihan_formatter.commands.sample.render")
    @patch("kumihan_formatter.commands.sample.parse")
    @patch("shutil.rmtree")
    def test_execute_basic_sample_generation(
        self, mock_rmtree, mock_parse, mock_render, mock_console_ui
    ):
        """基本的なサンプル生成実行テスト"""
        # モックの設定
        mock_ui = MagicMock()
        mock_console_ui.return_value = mock_ui
        mock_parse.return_value = ["parsed_content"]
        mock_render.return_value = "<html>rendered content</html>"

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = str(Path(temp_dir) / "test_sample")

            # モックファイル操作の設定
            self.command.file_ops = MagicMock()
            self.command.path_validator = MagicMock()

            # 実行
            result = self.command.execute(
                output_dir=output_dir, use_source_toggle=False
            )

            # 結果の確認
            assert isinstance(result, Path)
            mock_ui.sample_generation.assert_called_once()

    @patch("kumihan_formatter.commands.sample.get_console_ui")
    @patch("kumihan_formatter.commands.sample.render")
    @patch("kumihan_formatter.commands.sample.parse")
    @patch("shutil.rmtree")
    def test_execute_with_source_toggle(
        self, mock_rmtree, mock_parse, mock_render, mock_console_ui
    ):
        """ソーストグル機能付きサンプル生成テスト"""
        # モックの設定
        mock_ui = MagicMock()
        mock_console_ui.return_value = mock_ui
        mock_parse.return_value = ["parsed_content"]
        mock_render.return_value = "<html>rendered content</html>"

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = str(Path(temp_dir) / "test_sample_with_toggle")

            # モックファイル操作の設定
            self.command.file_ops = MagicMock()
            self.command.path_validator = MagicMock()

            # ソーストグル機能ありで実行
            result = self.command.execute(output_dir=output_dir, use_source_toggle=True)

            # 結果の確認
            assert isinstance(result, Path)
            mock_ui.sample_generation.assert_called_once()

    @patch("kumihan_formatter.commands.sample.get_console_ui")
    @patch("shutil.rmtree")
    def test_execute_existing_directory_removal(self, mock_rmtree, mock_console_ui):
        """既存ディレクトリの削除テスト"""
        # モックの設定
        mock_ui = MagicMock()
        mock_console_ui.return_value = mock_ui

        with tempfile.TemporaryDirectory() as temp_dir:
            # 既存ディレクトリを作成
            existing_dir = Path(temp_dir) / "existing_sample"
            existing_dir.mkdir()
            assert existing_dir.exists()

            # モックファイル操作の設定
            self.command.file_ops = MagicMock()
            self.command.path_validator = MagicMock()

            # 実行（既存ディレクトリがある状態）
            with patch("pathlib.Path.exists", return_value=True):
                result = self.command.execute(output_dir=str(existing_dir))

                # rmtreeが呼び出されることを確認
                mock_rmtree.assert_called_once()

    @patch("kumihan_formatter.commands.sample.get_console_ui")
    def test_execute_default_output_dir(self, mock_console_ui):
        """デフォルト出力ディレクトリでのテスト"""
        # モックの設定
        mock_ui = MagicMock()
        mock_console_ui.return_value = mock_ui

        # モックファイル操作の設定
        self.command.file_ops = MagicMock()
        self.command.path_validator = MagicMock()

        # デフォルト出力ディレクトリで実行
        result = self.command.execute()  # デフォルト: "kumihan_sample"

        # デフォルトパスが返されることを確認
        assert isinstance(result, Path)
        assert result.name == "kumihan_sample"

    @patch("kumihan_formatter.commands.sample.get_console_ui")
    @patch("kumihan_formatter.commands.sample.SAMPLE_IMAGES")
    @patch("kumihan_formatter.commands.sample.SHOWCASE_SAMPLE")
    def test_execute_sample_content_usage(
        self, mock_showcase, mock_images, mock_console_ui
    ):
        """サンプルコンテンツの使用テスト"""
        # モックの設定
        mock_ui = MagicMock()
        mock_console_ui.return_value = mock_ui
        mock_showcase.return_value = "# サンプルコンテンツ"
        mock_images.return_value = {}

        # モックファイル操作の設定
        self.command.file_ops = MagicMock()
        self.command.path_validator = MagicMock()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = str(Path(temp_dir) / "content_test")

            # 実行
            result = self.command.execute(output_dir=output_dir)

            # サンプルコンテンツが使用されることを確認
            assert isinstance(result, Path)


class TestSampleCommandErrorHandling:
    """SampleCommandのエラーハンドリングテスト"""

    def setup_method(self):
        """各テストメソッドの前に実行"""
        with patch("kumihan_formatter.commands.sample.FileOperations"):
            with patch("kumihan_formatter.commands.sample.PathValidator"):
                with patch("kumihan_formatter.commands.sample.get_console_ui"):
                    self.command = SampleCommand()

    @patch("kumihan_formatter.commands.sample.get_console_ui")
    def test_execute_file_operations_error(self, mock_console_ui):
        """ファイル操作エラー時のテスト"""
        # モックの設定
        mock_ui = MagicMock()
        mock_console_ui.return_value = mock_ui

        # ファイル操作でエラーを発生させる
        self.command.file_ops = MagicMock()
        self.command.file_ops.write_file.side_effect = PermissionError(
            "Permission denied"
        )
        self.command.path_validator = MagicMock()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = str(Path(temp_dir) / "error_test")

            # エラーが適切に処理されることを確認
            with pytest.raises(Exception):
                self.command.execute(output_dir=output_dir)

    @patch("kumihan_formatter.commands.sample.get_console_ui")
    @patch("kumihan_formatter.commands.sample.parse")
    def test_execute_parse_error(self, mock_parse, mock_console_ui):
        """パース処理エラー時のテスト"""
        # モックの設定
        mock_ui = MagicMock()
        mock_console_ui.return_value = mock_ui
        mock_parse.side_effect = Exception("Parse error")

        # モックファイル操作の設定
        self.command.file_ops = MagicMock()
        self.command.path_validator = MagicMock()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = str(Path(temp_dir) / "parse_error_test")

            # パースエラーが適切に処理されることを確認
            with pytest.raises(Exception):
                self.command.execute(output_dir=output_dir)

    @patch("kumihan_formatter.commands.sample.get_console_ui")
    @patch("kumihan_formatter.commands.sample.render")
    def test_execute_render_error(self, mock_render, mock_console_ui):
        """レンダリング処理エラー時のテスト"""
        # モックの設定
        mock_ui = MagicMock()
        mock_console_ui.return_value = mock_ui
        mock_render.side_effect = Exception("Render error")

        # モックファイル操作の設定
        self.command.file_ops = MagicMock()
        self.command.path_validator = MagicMock()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = str(Path(temp_dir) / "render_error_test")

            # レンダリングエラーが適切に処理されることを確認
            with pytest.raises(Exception):
                self.command.execute(output_dir=output_dir)


class TestSampleCommandIntegration:
    """SampleCommandの統合テスト"""

    def setup_method(self):
        """各テストメソッドの前に実行"""
        with patch("kumihan_formatter.commands.sample.FileOperations"):
            with patch("kumihan_formatter.commands.sample.PathValidator"):
                with patch("kumihan_formatter.commands.sample.get_console_ui"):
                    self.command = SampleCommand()

    @patch("kumihan_formatter.commands.sample.get_console_ui")
    @patch("kumihan_formatter.commands.sample.render")
    @patch("kumihan_formatter.commands.sample.parse")
    def test_full_sample_generation_workflow(
        self, mock_parse, mock_render, mock_console_ui
    ):
        """完全なサンプル生成ワークフローテスト"""
        # モックの設定
        mock_ui = MagicMock()
        mock_console_ui.return_value = mock_ui
        mock_parse.return_value = ["parsed_ast"]
        mock_render.return_value = "<html>Complete sample</html>"

        # モックファイル操作の設定
        self.command.file_ops = MagicMock()
        self.command.path_validator = MagicMock()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = str(Path(temp_dir) / "full_workflow_test")

            # 完全なワークフローの実行
            result = self.command.execute(output_dir=output_dir, use_source_toggle=True)

            # 全体的な処理が完了することを確認
            assert isinstance(result, Path)
            mock_ui.sample_generation.assert_called_once()
            mock_parse.assert_called()
            mock_render.assert_called()

    @patch("kumihan_formatter.commands.sample.get_console_ui")
    def test_path_validation_integration(self, mock_console_ui):
        """パス検証統合テスト"""
        # モックの設定
        mock_ui = MagicMock()
        mock_console_ui.return_value = mock_ui

        # パス検証の設定
        self.command.file_ops = MagicMock()
        self.command.path_validator = MagicMock()
        self.command.path_validator.validate_output_path.return_value = True

        with tempfile.TemporaryDirectory() as temp_dir:
            # 複雑なパスでのテスト
            complex_path = str(Path(temp_dir) / "path with spaces" / "サブディレクトリ")

            result = self.command.execute(output_dir=complex_path)

            # パス検証が適切に動作することを確認
            assert isinstance(result, Path)


if __name__ == "__main__":
    pytest.main([__file__])
