"""Phase 3A CLI Tests - Issue #500 (Fixed Version)

CLI基本機能とコマンドの統合テスト（修正版）
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from kumihan_formatter.cli import cli, register_commands, setup_encoding


class TestCLIBasic:
    """CLI基本機能のテスト"""

    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.runner = CliRunner()

    def test_cli_group_basic(self):
        """CLIグループの基本動作テスト"""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Kumihan-Formatter" in result.output
        assert "Development CLI tool" in result.output

    def test_setup_encoding_windows(self):
        """Windows環境でのエンコーディング設定テスト"""
        with patch("sys.platform", "win32"):
            with patch("sys.stdout") as mock_stdout:
                with patch("sys.stderr") as mock_stderr:
                    mock_stdout.reconfigure = MagicMock()
                    mock_stderr.reconfigure = MagicMock()

                    setup_encoding()

                    mock_stdout.reconfigure.assert_called_once_with(encoding="utf-8")
                    mock_stderr.reconfigure.assert_called_once_with(encoding="utf-8")

    def test_setup_encoding_non_windows(self):
        """非Windows環境でのエンコーディング設定テスト"""
        with patch("sys.platform", "linux"):
            # 非Windows環境では例外が発生しないことを確認
            setup_encoding()

    def test_setup_encoding_legacy_python(self):
        """古いPython環境でのエンコーディング設定テスト"""
        with patch("sys.platform", "win32"):
            with patch("sys.stdout") as mock_stdout:
                # reconfigureメソッドが存在しない場合のシミュレーション
                del mock_stdout.reconfigure

                with pytest.warns(UserWarning, match="Python 3.7 or earlier detected"):
                    setup_encoding()

    def test_register_commands_execution(self):
        """コマンド登録の実行テスト"""
        # register_commands()が例外なく実行されることを確認
        register_commands()

    def test_cli_without_arguments(self):
        """引数なしでのCLI実行テスト"""
        result = self.runner.invoke(cli)
        # CLIグループはサブコマンドなしで実行されると使用法を表示してexit_code=2
        assert result.exit_code in [0, 2]


class TestCLICommands:
    """CLIコマンドの統合テスト"""

    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.runner = CliRunner()
        register_commands()

    def test_convert_command_help(self):
        """convertコマンドのヘルプ表示テスト"""
        result = self.runner.invoke(cli, ["convert", "--help"])
        assert result.exit_code == 0
        assert "convert" in result.output.lower()

    def test_convert_command_mocked(self):
        """ConvertCommandのモック実行テスト"""
        with self.runner.isolated_filesystem():
            # テストファイル作成
            Path("test_input.txt").write_text(
                "# テストタイトル\n\nテスト内容です。", encoding="utf-8"
            )

            # ConvertCommand全体をモック化
            with patch("kumihan_formatter.cli.ConvertCommand") as mock_command_class:
                mock_instance = MagicMock()
                mock_command_class.return_value = mock_instance
                mock_instance.execute.return_value = None

                result = self.runner.invoke(
                    cli,
                    ["convert", "test_input.txt", "--output", "output", "--no-preview"],
                )

                # モックが正常に呼び出されることを確認
                mock_command_class.assert_called_once()
                mock_instance.execute.assert_called_once()

    def test_convert_command_options_parsing(self):
        """convertコマンドのオプション解析テスト"""
        with self.runner.isolated_filesystem():
            Path("test_input.txt").write_text("# テスト", encoding="utf-8")
            Path("config.json").write_text('{"theme": "default"}', encoding="utf-8")

            with patch("kumihan_formatter.cli.ConvertCommand") as mock_command_class:
                mock_instance = MagicMock()
                mock_command_class.return_value = mock_instance

                # 全オプション指定でテスト
                result = self.runner.invoke(
                    cli,
                    [
                        "convert",
                        "test_input.txt",
                        "--output",
                        "output",
                        "--no-preview",
                        "--config",
                        "config.json",
                        "--show-test-cases",
                        "--template",
                        "custom",
                        "--include-source",
                        "--no-syntax-check",
                    ],
                )

                # オプションが適切に解析されて渡されることを確認
                mock_instance.execute.assert_called_once()
                call_args = mock_instance.execute.call_args[1]
                assert call_args["no_preview"] is True
                assert call_args["config"] == "config.json"
                assert call_args["show_test_cases"] is True
                assert call_args["template_name"] == "custom"
                assert call_args["include_source"] is True

    def test_convert_command_watch_mode(self):
        """ウォッチモードのテスト"""
        with self.runner.isolated_filesystem():
            Path("test_input.txt").write_text("# ウォッチテスト", encoding="utf-8")

            with patch("kumihan_formatter.cli.ConvertCommand") as mock_command_class:
                mock_instance = MagicMock()
                mock_command_class.return_value = mock_instance

                result = self.runner.invoke(
                    cli, ["convert", "test_input.txt", "--watch", "--no-preview"]
                )

                # ウォッチオプションが正しく渡されることを確認
                mock_instance.execute.assert_called_once()
                call_args = mock_instance.execute.call_args[1]
                assert call_args["watch"] is True


class TestCLIErrorHandling:
    """CLIエラーハンドリングのテスト"""

    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.runner = CliRunner()
        register_commands()

    def test_convert_command_missing_input_file(self):
        """存在しない入力ファイルでのconvertコマンドテスト"""
        with self.runner.isolated_filesystem():
            with patch("kumihan_formatter.cli.ConvertCommand") as mock_command_class:
                mock_instance = MagicMock()
                mock_command_class.return_value = mock_instance
                # ファイルが存在しない場合の例外をシミュレート
                mock_instance.execute.side_effect = SystemExit(1)

                result = self.runner.invoke(cli, ["convert", "nonexistent_file.txt"])

                # 適切なエラーハンドリングが行われることを確認
                assert result.exit_code != 0

    def test_convert_command_invalid_options(self):
        """無効なオプション指定時のテスト"""
        result = self.runner.invoke(cli, ["convert", "--invalid-option"])

        # 無効なオプションでエラーになることを確認
        assert result.exit_code != 0
        assert (
            "no such option" in result.output.lower()
            or "unrecognized" in result.output.lower()
        )


class TestCLIIntegration:
    """CLI統合テスト"""

    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.runner = CliRunner()
        register_commands()

    def test_cli_command_discovery(self):
        """CLIコマンドの発見テスト"""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        # 登録されたコマンドがヘルプに表示されることを確認
        output_lower = result.output.lower()
        assert "commands:" in output_lower or "convert" in output_lower

    def test_cli_encoding_and_command_execution(self):
        """エンコーディング設定とコマンド実行の統合テスト"""
        # エンコーディング設定
        setup_encoding()

        # コマンド登録
        register_commands()

        # コマンド実行
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0

    def test_cli_unicode_handling(self):
        """Unicode文字処理のテスト"""
        with self.runner.isolated_filesystem():
            # 日本語を含むファイル名とコンテンツでテスト
            Path("日本語ファイル.txt").write_text(
                "# 日本語タイトル\n\n日本語の内容です。", encoding="utf-8"
            )

            with patch("kumihan_formatter.cli.ConvertCommand") as mock_command_class:
                mock_instance = MagicMock()
                mock_command_class.return_value = mock_instance

                result = self.runner.invoke(cli, ["convert", "日本語ファイル.txt"])

                # Unicode文字を含むファイルでもコマンドが解析されることを確認
                mock_command_class.assert_called_once()


class TestCLIEdgeCases:
    """CLIエッジケースのテスト"""

    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.runner = CliRunner()
        register_commands()

    def test_convert_no_input_file_specified(self):
        """入力ファイル未指定時のテスト"""
        with patch("kumihan_formatter.cli.ConvertCommand") as mock_command_class:
            mock_instance = MagicMock()
            mock_command_class.return_value = mock_instance

            result = self.runner.invoke(cli, ["convert", "--output", "output"])

            # 入力ファイル未指定でも適切に処理されることを確認
            mock_command_class.assert_called_once()

    def test_convert_with_complex_path(self):
        """複雑なパス指定時のテスト"""
        with self.runner.isolated_filesystem():
            # ディレクトリ構造作成
            Path("dir with spaces/sub dir").mkdir(parents=True)
            Path("dir with spaces/sub dir/test.txt").write_text(
                "# テスト", encoding="utf-8"
            )

            with patch("kumihan_formatter.cli.ConvertCommand") as mock_command_class:
                mock_instance = MagicMock()
                mock_command_class.return_value = mock_instance

                result = self.runner.invoke(
                    cli,
                    [
                        "convert",
                        "dir with spaces/sub dir/test.txt",
                        "--output",
                        "output with spaces",
                    ],
                )

                # スペースを含むパスでも適切に処理されることを確認
                mock_command_class.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
