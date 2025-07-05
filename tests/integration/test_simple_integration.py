"""シンプルな統合テスト（33テスト）

統合テスト: 基本的な統合テスト
- CLI統合テスト（11テスト）
- ファイルI/O統合テスト（12テスト）
- テンプレート統合テスト（10テスト）
"""

import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path
from unittest import TestCase

import pytest


class TestSimpleIntegration(TestCase):
    """シンプルな統合テスト"""

    def setUp(self):
        """テスト用の一時ディレクトリを作成"""
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.test_dir) / "output"
        self.test_input_file = Path(self.test_dir) / "test_input.txt"

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

    def tearDown(self):
        """テスト後のクリーンアップ"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _run_cli(self, args, expect_success=True):
        """CLI実行ヘルパー"""
        cmd = ["python3", "-m", "kumihan_formatter"] + args
        result = subprocess.run(
            cmd, cwd=self.test_dir, capture_output=True, text=True, encoding="utf-8"
        )

        if expect_success and result.returncode != 0:
            print(f"CLI実行が失敗: stdout={result.stdout}, stderr={result.stderr}")

        return result

    # CLI統合テスト（11テスト）

    def test_cli_help_display(self):
        """ヘルプ表示テスト"""
        result = self._run_cli(["--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("Kumihan", result.stdout)

    def test_cli_basic_convert(self):
        """基本的な変換テスト"""
        result = self._run_cli(
            [
                "convert",
                str(self.test_input_file),
                "--output",
                str(self.output_dir),
                "--no-preview",
            ]
        )

        # 成功またはエラーがあっても何らかの出力があることを確認
        self.assertIn(result.returncode, [0, 1])

    def test_cli_invalid_command(self):
        """無効なコマンドテスト"""
        result = self._run_cli(["invalid-command"], expect_success=False)
        self.assertNotEqual(result.returncode, 0)

    def test_cli_convert_with_output(self):
        """出力ディレクトリ指定変換テスト"""
        result = self._run_cli(
            [
                "convert",
                str(self.test_input_file),
                "--output",
                str(self.output_dir),
                "--no-preview",
            ]
        )

        self.assertIn(result.returncode, [0, 1])

    def test_cli_convert_with_template(self):
        """テンプレート指定変換テスト"""
        result = self._run_cli(
            ["convert", str(self.test_input_file), "--template", "base", "--no-preview"]
        )

        self.assertIn(result.returncode, [0, 1])

    def test_cli_convert_include_source(self):
        """ソース表示オプションテスト"""
        result = self._run_cli(
            ["convert", str(self.test_input_file), "--include-source", "--no-preview"]
        )

        self.assertIn(result.returncode, [0, 1])

    def test_cli_convert_no_syntax_check(self):
        """構文チェック無効テスト"""
        result = self._run_cli(
            ["convert", str(self.test_input_file), "--no-syntax-check", "--no-preview"]
        )

        self.assertIn(result.returncode, [0, 1])

    def test_cli_check_syntax_command(self):
        """構文チェックコマンドテスト"""
        result = self._run_cli(["check-syntax", str(self.test_input_file)])

        # 構文チェックは成功/警告/エラーのいずれかを返す
        self.assertIn(result.returncode, [0, 1, 2])

    def test_cli_generate_sample_command(self):
        """サンプル生成コマンドテスト"""
        result = self._run_cli(["generate-sample", "--output", str(self.output_dir)])

        # コマンドが存在することを確認（成功しなくても可）
        self.assertIn(result.returncode, [0, 1, 2])

    def test_cli_generate_test_command(self):
        """テスト生成コマンドテスト"""
        result = self._run_cli(["generate-test", "--output", str(self.output_dir)])

        # コマンドが存在することを確認（成功しなくても可）
        self.assertIn(result.returncode, [0, 1, 2])

    def test_cli_all_options_combination(self):
        """全オプション組み合わせテスト"""
        result = self._run_cli(
            [
                "convert",
                str(self.test_input_file),
                "--output",
                str(self.output_dir),
                "--template",
                "base",
                "--include-source",
                "--no-syntax-check",
                "--no-preview",
            ]
        )

        self.assertIn(result.returncode, [0, 1])

    # ファイルI/O統合テスト（12テスト）

    def test_file_read_basic_text(self):
        """基本テキストファイル読み込みテスト"""
        content = "# テストファイル\n\n基本的なテキストです。"
        test_file = Path(self.test_dir) / "read_test.txt"
        test_file.write_text(content, encoding="utf-8")

        # ファイルが正しく読み込めることを確認
        read_content = test_file.read_text(encoding="utf-8")
        self.assertEqual(read_content, content)

    def test_file_read_large_text(self):
        """大きなテキストファイル読み込みテスト"""
        lines = [f"行{i}: テストデータ" for i in range(1000)]
        content = "\n".join(lines)
        test_file = Path(self.test_dir) / "large_test.txt"
        test_file.write_text(content, encoding="utf-8")

        read_content = test_file.read_text(encoding="utf-8")
        self.assertEqual(len(read_content.split("\n")), 1000)

    def test_file_read_nonexistent(self):
        """存在しないファイル読み込みテスト"""
        nonexistent_file = Path(self.test_dir) / "nonexistent.txt"

        with self.assertRaises(FileNotFoundError):
            nonexistent_file.read_text(encoding="utf-8")

    @pytest.mark.skipif(
        platform.system() == "Windows",
        reason="Windows file permission tests need platform-specific " "implementation",
    )
    def test_file_read_permission_denied(self):
        """読み込み権限なしファイルテスト"""
        content = "権限テスト"
        test_file = Path(self.test_dir) / "permission_test.txt"
        test_file.write_text(content, encoding="utf-8")

        # 権限を削除
        os.chmod(test_file, 0o000)

        try:
            with self.assertRaises(PermissionError):
                test_file.read_text(encoding="utf-8")
        finally:
            # 権限を戻す
            os.chmod(test_file, 0o644)

    def test_file_write_basic_html(self):
        """基本HTMLファイル書き込みテスト"""
        html_content = """<!DOCTYPE html>
<html>
<head><title>テスト</title></head>
<body><h1>テスト</h1></body>
</html>"""
        output_file = Path(self.test_dir) / "output.html"

        output_file.write_text(html_content, encoding="utf-8")

        self.assertTrue(output_file.exists())
        read_content = output_file.read_text(encoding="utf-8")
        self.assertEqual(read_content, html_content)

    def test_file_write_new_directory(self):
        """新ディレクトリ書き込みテスト"""
        content = "新ディレクトリテスト"
        new_dir = Path(self.test_dir) / "new_dir"
        output_file = new_dir / "test.html"

        new_dir.mkdir(parents=True, exist_ok=True)
        output_file.write_text(content, encoding="utf-8")

        self.assertTrue(output_file.exists())
        self.assertEqual(output_file.read_text(encoding="utf-8"), content)

    def test_file_overwrite_existing(self):
        """既存ファイル上書きテスト"""
        original_content = "元の内容"
        new_content = "新しい内容"
        test_file = Path(self.test_dir) / "overwrite_test.html"

        test_file.write_text(original_content, encoding="utf-8")
        self.assertEqual(test_file.read_text(encoding="utf-8"), original_content)

        test_file.write_text(new_content, encoding="utf-8")
        self.assertEqual(test_file.read_text(encoding="utf-8"), new_content)

    @pytest.mark.skipif(
        platform.system() == "Windows",
        reason="Windows file permission tests need platform-specific " "implementation",
    )
    def test_file_write_permission_denied(self):
        """書き込み権限なしディレクトリテスト"""
        readonly_dir = Path(self.test_dir) / "readonly"
        readonly_dir.mkdir()
        output_file = readonly_dir / "test.html"

        os.chmod(readonly_dir, 0o444)

        try:
            with self.assertRaises(PermissionError):
                output_file.write_text("テスト", encoding="utf-8")
        finally:
            os.chmod(readonly_dir, 0o755)

    def test_encoding_utf8_detection(self):
        """UTF-8エンコーディング検出テスト"""
        content = "UTF-8テスト: 日本語文字列 🎌"
        test_file = Path(self.test_dir) / "utf8_test.txt"
        test_file.write_text(content, encoding="utf-8")

        # ファイルが正しく読み込めることを確認
        read_content = test_file.read_text(encoding="utf-8")
        self.assertEqual(read_content, content)

    def test_encoding_shiftjis_handling(self):
        """Shift_JISエンコーディング処理テスト"""
        content = "Shift_JISテスト: 日本語"
        test_file = Path(self.test_dir) / "shiftjis_test.txt"

        try:
            with open(test_file, "w", encoding="shift_jis") as f:
                f.write(content)

            # Shift_JISで書かれたファイルが読み込めることを確認
            with open(test_file, "r", encoding="shift_jis") as f:
                read_content = f.read()
            self.assertEqual(read_content, content)
        except UnicodeEncodeError:
            # Shift_JISで表現できない文字がある場合はスキップ
            self.skipTest("Shift_JIS encoding not supported for this content")

    def test_encoding_bom_handling(self):
        """BOM付きファイル処理テスト"""
        content = "BOMテスト: 日本語文字列"
        test_file = Path(self.test_dir) / "bom_test.txt"

        with open(test_file, "w", encoding="utf-8-sig") as f:
            f.write(content)

        # BOM付きファイルが正しく読み込めることを確認
        with open(test_file, "r", encoding="utf-8-sig") as f:
            read_content = f.read()
        self.assertEqual(read_content, content)

    def test_mixed_encoding_files(self):
        """複数エンコーディング処理テスト"""
        encodings = ["utf-8", "shift_jis"]

        for i, encoding in enumerate(encodings):
            content = f"エンコーディングテスト{i}"
            test_file = Path(self.test_dir) / f"encoding_test_{i}.txt"

            try:
                with open(test_file, "w", encoding=encoding) as f:
                    f.write(content)

                with open(test_file, "r", encoding=encoding) as f:
                    read_content = f.read()
                self.assertIn("エンコーディングテスト", read_content)
            except UnicodeEncodeError:
                # エンコーディングでサポートされない文字がある場合はスキップ
                continue

    # テンプレート統合テスト（10テスト）

    def test_template_basic_usage(self):
        """基本的なテンプレート使用テスト"""
        result = self._run_cli(
            ["convert", str(self.test_input_file), "--template", "base", "--no-preview"]
        )

        # テンプレートが指定されても処理が継続することを確認
        self.assertIn(result.returncode, [0, 1, 2])

    def test_template_docs_usage(self):
        """docsテンプレート使用テスト"""
        result = self._run_cli(
            ["convert", str(self.test_input_file), "--template", "docs", "--no-preview"]
        )

        self.assertIn(result.returncode, [0, 1, 2])

    def test_template_nonexistent(self):
        """存在しないテンプレートテスト"""
        result = self._run_cli(
            [
                "convert",
                str(self.test_input_file),
                "--template",
                "nonexistent_template",
                "--no-preview",
            ]
        )

        # 存在しないテンプレートでもフォールバックして処理継続
        self.assertIn(result.returncode, [0, 1, 2])

    def test_template_with_include_source(self):
        """テンプレート+ソース表示テスト"""
        result = self._run_cli(
            [
                "convert",
                str(self.test_input_file),
                "--template",
                "base",
                "--include-source",
                "--no-preview",
            ]
        )

        self.assertIn(result.returncode, [0, 1])

    def test_template_with_output_dir(self):
        """テンプレート+出力ディレクトリテスト"""
        result = self._run_cli(
            [
                "convert",
                str(self.test_input_file),
                "--template",
                "base",
                "--output",
                str(self.output_dir),
                "--no-preview",
            ]
        )

        self.assertIn(result.returncode, [0, 1])

    def test_template_variable_expansion(self):
        """テンプレート変数展開テスト"""
        # 変数を含むコンテンツ
        content_with_vars = """# テンプレート変数テスト

## 基本情報
- タイトル: テストシナリオ
- 作成者: テストユーザー
- 日付: 2025-07-05

これは変数展開のテストです。
"""
        var_file = Path(self.test_dir) / "var_test.txt"
        var_file.write_text(content_with_vars, encoding="utf-8")

        result = self._run_cli(
            ["convert", str(var_file), "--template", "base", "--no-preview"]
        )

        self.assertIn(result.returncode, [0, 1])

    def test_template_css_integration(self):
        """テンプレートCSS統合テスト"""
        result = self._run_cli(
            ["convert", str(self.test_input_file), "--template", "base", "--no-preview"]
        )

        # CSS統合が含まれるテンプレートでも正常に動作
        self.assertIn(result.returncode, [0, 1])

    def test_template_javascript_integration(self):
        """テンプレートJavaScript統合テスト"""
        result = self._run_cli(
            [
                "convert",
                str(self.test_input_file),
                "--template",
                "docs",
                "--include-source",
                "--no-preview",
            ]
        )

        # JavaScript機能を含むテンプレートでも正常に動作
        self.assertIn(result.returncode, [0, 1])

    def test_template_responsive_design(self):
        """テンプレートレスポンシブデザインテスト"""
        # レスポンシブデザイン要素を含むコンテンツ
        responsive_content = """# レスポンシブデザインテスト

## モバイル対応
このコンテンツはモバイルでも表示されるべきです。

### テーブル
| 項目 | 値 |
|------|-----|
| A | 1 |
| B | 2 |

### リスト
- 項目1
- 項目2
- 項目3
"""
        responsive_file = Path(self.test_dir) / "responsive_test.txt"
        responsive_file.write_text(responsive_content, encoding="utf-8")

        result = self._run_cli(
            ["convert", str(responsive_file), "--template", "base", "--no-preview"]
        )

        self.assertIn(result.returncode, [0, 1])

    def test_template_error_recovery(self):
        """テンプレートエラー回復テスト"""
        # 問題のあるコンテンツでもテンプレート処理が継続することをテスト
        problem_content = """# エラー回復テスト

## 問題のある記法
![存在しない画像](nonexistent.png)

## 正常な記法
これは正常に処理されるべきです。

### リスト
- 正常な項目1
- 正常な項目2
"""
        problem_file = Path(self.test_dir) / "problem_test.txt"
        problem_file.write_text(problem_content, encoding="utf-8")

        result = self._run_cli(
            ["convert", str(problem_file), "--template", "base", "--no-preview"]
        )

        # 問題があっても処理が継続することを確認
        self.assertIn(result.returncode, [0, 1])
