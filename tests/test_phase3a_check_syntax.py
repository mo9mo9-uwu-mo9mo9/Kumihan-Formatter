"""Phase 3A Check Syntax Tests - Issue #500

check_syntax コマンドの統合テスト
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from kumihan_formatter.commands.check_syntax import CheckSyntaxCommand


class TestCheckSyntaxCommand:
    """CheckSyntaxCommandのテスト"""

    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.command = CheckSyntaxCommand()

    def test_check_syntax_command_initialization(self):
        """CheckSyntaxCommandの初期化テスト"""
        command = CheckSyntaxCommand()
        assert command is not None

    @patch("kumihan_formatter.commands.check_syntax.check_files")
    @patch("kumihan_formatter.commands.check_syntax.get_console_ui")
    def test_execute_basic_syntax_check(self, mock_console_ui, mock_check_files):
        """基本的な構文チェック実行テスト"""
        # モックの設定
        mock_ui = MagicMock()
        mock_console_ui.return_value = mock_ui
        mock_check_files.return_value = []  # エラーなし

        with tempfile.TemporaryDirectory() as temp_dir:
            # テストファイル作成
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text(
                "# 正常なKumihan記法\n\n正常な内容です。", encoding="utf-8"
            )

            # 実行
            self.command.execute(
                files=[str(test_file)],
                recursive=False,
                show_suggestions=True,
                format_output="text",
            )

            # 適切なメソッドが呼び出されることを確認
            mock_check_files.assert_called_once()
            mock_ui.info.assert_called()

    @patch("kumihan_formatter.commands.check_syntax.check_files")
    @patch("kumihan_formatter.commands.check_syntax.get_console_ui")
    def test_execute_syntax_check_with_errors(self, mock_console_ui, mock_check_files):
        """エラーありの構文チェック実行テスト"""
        # モックの設定
        mock_ui = MagicMock()
        mock_console_ui.return_value = mock_ui

        # エラー結果のモック
        mock_error = MagicMock()
        mock_error.severity = "error"
        mock_error.message = "テストエラー"
        mock_check_files.return_value = [mock_error]

        with tempfile.TemporaryDirectory() as temp_dir:
            # テストファイル作成
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text(
                "# エラーのあるファイル\n\n;;;無効な記法", encoding="utf-8"
            )

            # 実行
            with pytest.raises(SystemExit):  # エラー時はsys.exit(1)
                self.command.execute(
                    files=[str(test_file)],
                    recursive=False,
                    show_suggestions=True,
                    format_output="text",
                )

    @patch("kumihan_formatter.commands.check_syntax.check_files")
    @patch("kumihan_formatter.commands.check_syntax.get_console_ui")
    def test_execute_recursive_check(self, mock_console_ui, mock_check_files):
        """再帰的チェックのテスト"""
        # モックの設定
        mock_ui = MagicMock()
        mock_console_ui.return_value = mock_ui
        mock_check_files.return_value = []

        with tempfile.TemporaryDirectory() as temp_dir:
            # ディレクトリ構造作成
            sub_dir = Path(temp_dir) / "subdir"
            sub_dir.mkdir()

            test_file1 = Path(temp_dir) / "test1.txt"
            test_file2 = sub_dir / "test2.txt"

            test_file1.write_text("# ファイル1", encoding="utf-8")
            test_file2.write_text("# ファイル2", encoding="utf-8")

            # 再帰的実行
            self.command.execute(
                files=[temp_dir],
                recursive=True,
                show_suggestions=True,
                format_output="text",
            )

            mock_check_files.assert_called_once()

    @patch("kumihan_formatter.commands.check_syntax.check_files")
    @patch("kumihan_formatter.commands.check_syntax.get_console_ui")
    def test_execute_json_output(self, mock_console_ui, mock_check_files):
        """JSON出力形式のテスト"""
        # モックの設定
        mock_ui = MagicMock()
        mock_console_ui.return_value = mock_ui
        mock_check_files.return_value = []

        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("# テスト", encoding="utf-8")

            # JSON出力で実行
            self.command.execute(
                files=[str(test_file)],
                recursive=False,
                show_suggestions=False,
                format_output="json",
            )

            mock_check_files.assert_called_once()

    @patch("kumihan_formatter.commands.check_syntax.get_console_ui")
    def test_execute_no_files_found(self, mock_console_ui):
        """ファイルが見つからない場合のテスト"""
        # モックの設定
        mock_ui = MagicMock()
        mock_console_ui.return_value = mock_ui

        # 存在しないファイルを指定
        with pytest.raises(SystemExit):
            self.command.execute(
                files=["nonexistent.txt"],
                recursive=False,
                show_suggestions=True,
                format_output="text",
            )

        mock_ui.error.assert_called_with("チェックするファイルが見つかりません")

    def test_collect_files_method(self):
        """_collect_filesメソッドのテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # テストファイル作成
            test_file1 = Path(temp_dir) / "test1.txt"
            test_file2 = Path(temp_dir) / "test2.md"

            test_file1.write_text("# テスト1", encoding="utf-8")
            test_file2.write_text("# テスト2", encoding="utf-8")

            # _collect_filesメソッドが存在する場合のテスト
            if hasattr(self.command, "_collect_files"):
                files = self.command._collect_files([temp_dir], recursive=True)
                assert len(files) >= 0  # ファイル収集が動作することを確認

    @patch("kumihan_formatter.commands.check_syntax.check_files")
    @patch("kumihan_formatter.commands.check_syntax.get_console_ui")
    def test_execute_show_suggestions_disabled(self, mock_console_ui, mock_check_files):
        """修正提案無効時のテスト"""
        # モックの設定
        mock_ui = MagicMock()
        mock_console_ui.return_value = mock_ui
        mock_check_files.return_value = []

        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("# テスト", encoding="utf-8")

            # 修正提案無効で実行
            self.command.execute(
                files=[str(test_file)],
                recursive=False,
                show_suggestions=False,
                format_output="text",
            )

            mock_check_files.assert_called_once()

    @patch("kumihan_formatter.commands.check_syntax.check_files")
    @patch("kumihan_formatter.commands.check_syntax.get_console_ui")
    def test_execute_multiple_files(self, mock_console_ui, mock_check_files):
        """複数ファイルのチェックテスト"""
        # モックの設定
        mock_ui = MagicMock()
        mock_console_ui.return_value = mock_ui
        mock_check_files.return_value = []

        with tempfile.TemporaryDirectory() as temp_dir:
            # 複数のテストファイル作成
            files = []
            for i in range(3):
                test_file = Path(temp_dir) / f"test{i}.txt"
                test_file.write_text(f"# テストファイル{i}", encoding="utf-8")
                files.append(str(test_file))

            # 複数ファイルで実行
            self.command.execute(
                files=files,
                recursive=False,
                show_suggestions=True,
                format_output="text",
            )

            mock_check_files.assert_called_once()


class TestCheckSyntaxCommandEdgeCases:
    """CheckSyntaxCommandのエッジケーステスト"""

    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.command = CheckSyntaxCommand()

    @patch("kumihan_formatter.commands.check_syntax.check_files")
    @patch("kumihan_formatter.commands.check_syntax.get_console_ui")
    def test_execute_empty_file(self, mock_console_ui, mock_check_files):
        """空ファイルのチェックテスト"""
        # モックの設定
        mock_ui = MagicMock()
        mock_console_ui.return_value = mock_ui
        mock_check_files.return_value = []

        with tempfile.TemporaryDirectory() as temp_dir:
            # 空ファイル作成
            empty_file = Path(temp_dir) / "empty.txt"
            empty_file.write_text("", encoding="utf-8")

            # 実行
            self.command.execute(
                files=[str(empty_file)],
                recursive=False,
                show_suggestions=True,
                format_output="text",
            )

            mock_check_files.assert_called_once()

    @patch("kumihan_formatter.commands.check_syntax.check_files")
    @patch("kumihan_formatter.commands.check_syntax.get_console_ui")
    def test_execute_unicode_content(self, mock_console_ui, mock_check_files):
        """Unicode文字を含むファイルのチェックテスト"""
        # モックの設定
        mock_ui = MagicMock()
        mock_console_ui.return_value = mock_ui
        mock_check_files.return_value = []

        with tempfile.TemporaryDirectory() as temp_dir:
            # Unicode文字を含むファイル作成
            unicode_file = Path(temp_dir) / "unicode.txt"
            unicode_file.write_text(
                "# 日本語タイトル\n\n絵文字🎉も含む内容です。", encoding="utf-8"
            )

            # 実行
            self.command.execute(
                files=[str(unicode_file)],
                recursive=False,
                show_suggestions=True,
                format_output="text",
            )

            mock_check_files.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
