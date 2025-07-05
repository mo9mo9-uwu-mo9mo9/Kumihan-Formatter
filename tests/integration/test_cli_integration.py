"""CLI全体の動作確認テスト（11テスト）

統合テスト: CLI全体の動作確認
- CLI基本動作テスト（3テスト）
- convert コマンド統合テスト（5テスト）
- 補助コマンド統合テスト（3テスト）
"""

import shutil
import subprocess
import tempfile
from pathlib import Path
from unittest import TestCase


class TestCLIIntegration(TestCase):
    """CLI全体の動作確認統合テスト"""

    def setUp(self):
        """テスト用の一時ディレクトリを作成"""
        self.test_dir = tempfile.mkdtemp()
        self.test_input_file = Path(self.test_dir) / "test_input.txt"
        self.test_output_dir = Path(self.test_dir) / "output"
        self.test_config_file = Path(self.test_dir) / "config.yaml"

        # テスト用の入力ファイルを作成
        self.test_input_file.write_text(
            """# テストシナリオ

## 基本的な変換テスト

これは統合テストのためのサンプルテキストです。

### 項目リスト
- 項目1
- 項目2
- 項目3

**太字テキスト**と*イタリックテキスト*のテストです。
""",
            encoding="utf-8",
        )

        # テスト用の設定ファイルを作成
        self.test_config_file.write_text(
            """
title: "統合テスト用設定"
output_dir: "./output"
template: "base"
""",
            encoding="utf-8",
        )

    def tearDown(self):
        """テスト後のクリーンアップ"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _run_cli(self, args, expect_success=True):
        """CLI実行ヘルパー"""
        cmd = ["python", "-m", "kumihan_formatter"] + args
        result = subprocess.run(
            cmd, cwd=self.test_dir, capture_output=True, text=True, encoding="utf-8"
        )

        if expect_success:
            self.assertEqual(result.returncode, 0, f"CLI実行が失敗: {result.stderr}")

        return result

    # CLI基本動作テスト（3テスト）

    def test_cli_help_display(self):
        """ヘルプ表示テスト"""
        result = self._run_cli(["--help"])
        self.assertIn("Kumihan-Formatter", result.stdout)
        self.assertIn("convert", result.stdout)

    def test_cli_version_info(self):
        """バージョン情報テスト"""
        result = self._run_cli(["--version"])
        # バージョン情報が出力されることを確認
        self.assertTrue(result.stdout.strip() or result.stderr.strip())

    def test_cli_invalid_command(self):
        """無効なコマンドテスト"""
        result = self._run_cli(["invalid-command"], expect_success=False)
        self.assertNotEqual(result.returncode, 0)

    # convert コマンド統合テスト（5テスト）

    def test_convert_basic_conversion(self):
        """基本的な変換処理テスト"""
        self._run_cli(
            [
                "convert",
                str(self.test_input_file),
                "--output",
                str(self.test_output_dir),
                "--no-preview",
            ]
        )

        # 出力ディレクトリが作成されることを確認
        self.assertTrue(self.test_output_dir.exists())

        # HTMLファイルが生成されることを確認
        html_files = list(self.test_output_dir.glob("*.html"))
        self.assertGreater(len(html_files), 0)

    def test_convert_with_options(self):
        """オプション付き変換テスト"""
        result = self._run_cli(
            [
                "convert",
                str(self.test_input_file),
                "--output",
                str(self.test_output_dir),
                "--no-preview",
                "--include-source",
                "--no-syntax-check",
            ]
        )

        # 変換が成功することを確認
        self.assertEqual(result.returncode, 0)

    def test_convert_with_config_file(self):
        """設定ファイル使用テスト"""
        result = self._run_cli(
            [
                "convert",
                str(self.test_input_file),
                "--config",
                str(self.test_config_file),
                "--no-preview",
            ]
        )

        # 設定ファイルが読み込まれて変換が成功することを確認
        self.assertEqual(result.returncode, 0)

    def test_convert_with_template(self):
        """テンプレート指定テスト"""
        result = self._run_cli(
            [
                "convert",
                str(self.test_input_file),
                "--output",
                str(self.test_output_dir),
                "--template",
                "base",
                "--no-preview",
            ]
        )

        # テンプレートが指定されて変換が成功することを確認
        self.assertEqual(result.returncode, 0)

    def test_convert_syntax_check_modes(self):
        """構文チェック有効/無効テスト"""
        # 構文チェック有効（デフォルト）
        result1 = self._run_cli(
            [
                "convert",
                str(self.test_input_file),
                "--output",
                str(self.test_output_dir),
                "--no-preview",
            ]
        )
        self.assertEqual(result1.returncode, 0)

        # 構文チェック無効
        result2 = self._run_cli(
            [
                "convert",
                str(self.test_input_file),
                "--output",
                str(self.test_output_dir),
                "--no-syntax-check",
                "--no-preview",
            ]
        )
        self.assertEqual(result2.returncode, 0)

    # 補助コマンド統合テスト（3テスト）

    def test_check_syntax_command(self):
        """check-syntax コマンドテスト"""
        result = self._run_cli(["check-syntax", str(self.test_input_file)])

        # 構文チェックが実行されることを確認
        # エラーがなければ成功、エラーがあれば報告される
        self.assertTrue(result.returncode in [0, 1])  # 0=成功, 1=構文エラー検出

    def test_generate_sample_command(self):
        """generate-sample コマンドテスト"""
        result = self._run_cli(
            ["generate-sample", "--output", str(self.test_output_dir)]
        )

        # サンプルファイルが生成されることを確認
        if result.returncode == 0:
            sample_files = list(Path(self.test_output_dir).glob("*.txt"))
            self.assertGreater(len(sample_files), 0)

    def test_generate_test_command(self):
        """generate-test コマンドテスト"""
        result = self._run_cli(["generate-test", "--output", str(self.test_output_dir)])

        # テストファイルが生成されることを確認
        if result.returncode == 0:
            test_files = list(Path(self.test_output_dir).glob("*test*.txt"))
            self.assertGreater(len(test_files), 0)
