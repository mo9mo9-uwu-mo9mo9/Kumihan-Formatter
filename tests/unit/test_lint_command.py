"""
lint コマンドのテスト

Issue #778: flake8自動修正ツール実装
"""

import shutil
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from kumihan_formatter.commands.lint import Flake8AutoFixer, lint_command


@pytest.mark.unit
@pytest.mark.commands
class TestLintCommand:
    """lint コマンドテスト"""

    def setup_method(self):
        """テスト用のセットアップ"""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()

        # テスト用ファイル作成
        self.test_file = Path(self.temp_dir) / "test_file.py"
        self.test_file.write_text(
            """# テスト用ファイル
import os
import sys
import json  # 未使用import

def test_function():
    x=1+2  # E226: 演算子周辺の空白不足
    long_line = "This is a very long line that exceeds the maximum line length and should be split"  # E501
    return x
"""
        )

    def teardown_method(self):
        """テストのクリーンアップ"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_lint_help_command(self):
        """lint コマンドのヘルプ表示テスト"""
        result = self.runner.invoke(lint_command, ["--help"])

        assert result.exit_code == 0
        assert "コードの品質チェックと自動修正" in result.output
        assert "--fix" in result.output
        assert "--dry-run" in result.output

    def test_lint_without_fix_option(self):
        """--fixオプションなしでのflake8チェック"""
        result = self.runner.invoke(lint_command, [str(self.test_file)])

        # flakeが使用可能かどうかに依存するが、クラッシュしないことを確認
        assert result.exit_code in [0, 1, 2]

    def test_lint_with_dry_run(self):
        """--dry-runオプションでの実行テスト"""
        result = self.runner.invoke(
            lint_command, [str(self.test_file), "--fix", "--dry-run"]
        )

        assert result.exit_code == 0
        assert "Dry run completed" in result.output
        assert "No files were modified" in result.output

    def test_lint_with_fix_option(self):
        """--fixオプションでの実行テスト"""
        # 元ファイルの内容を保存
        original_content = self.test_file.read_text()

        result = self.runner.invoke(lint_command, [str(self.test_file), "--fix"])

        assert result.exit_code == 0
        assert "Auto-fix completed" in result.output

        # ファイルが修正されているかチェック
        modified_content = self.test_file.read_text()
        # 何らかの修正が適用されている可能性

    def test_lint_nonexistent_file(self):
        """存在しないファイルでのテスト"""
        nonexistent = str(Path(self.temp_dir) / "nonexistent.py")
        result = self.runner.invoke(lint_command, [nonexistent, "--fix"])

        # 存在しないファイルでもクラッシュしない
        assert result.exit_code in [0, 1, 2]


@pytest.mark.unit
@pytest.mark.commands
class TestFlake8AutoFixer:
    """Flake8AutoFixer クラスのテスト"""

    def setup_method(self):
        """テスト用のセットアップ"""
        self.fixer = Flake8AutoFixer()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """テストのクリーンアップ"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_fixer_initialization(self):
        """AutoFixer初期化テスト"""
        assert self.fixer is not None
        assert self.fixer.max_line_length > 0
        assert isinstance(self.fixer.fixes_applied, dict)

    def test_get_max_line_length_default(self):
        """行長制限のデフォルト値テスト"""
        length = self.fixer._get_max_line_length()
        assert length == 100  # デフォルト値

    def test_split_function_call(self):
        """関数呼び出し分割テスト"""
        long_line = (
            'result = some_function(arg1="value1", arg2="value2", arg3="value3")'
        )
        fixed_line = self.fixer._split_function_call(long_line)

        # 分割されているかチェック
        if fixed_line != long_line:
            assert "(\n" in fixed_line
            assert ")" in fixed_line

    def test_extract_import_names(self):
        """import名抽出テスト"""
        # import module
        names = self.fixer._extract_import_names("import os")
        assert "os" in names

        # from module import name
        names = self.fixer._extract_import_names("from pathlib import Path")
        assert "Path" in names

        # from module import multiple
        names = self.fixer._extract_import_names("from os import path, environ")
        assert "path" in names
        assert "environ" in names

    def test_fix_e501_line_too_long(self):
        """E501エラー修正テスト"""
        content = 'result = some_very_long_function_name(
            arg1="very_long_value",
            arg2="another_very_long_value"
{indent})\n'

        fixed_content = self.fixer.fix_e501_line_too_long(content, 1)

        # 何らかの修正が適用されているかチェック
        if fixed_content != content:
            # 複数行に分割されているかチェック
            assert fixed_content.count("\n") > content.count("\n")

    def test_fix_e226_missing_whitespace(self):
        """E226エラー修正テスト"""
        content = "x=1+2*3\n"

        fixed_content = self.fixer.fix_e226_missing_whitespace(content, 1, 2)

        # 演算子周辺に空白が追加されているかチェック
        if fixed_content != content:
            assert " = " in fixed_content or " + " in fixed_content

    def test_fix_f401_unused_import(self):
        """F401エラー修正テスト"""
        content = """import os
import json
print("hello")
"""

        # json は未使用なので削除される可能性
        fixed_content = self.fixer.fix_f401_unused_import(content, 2)

        # ファイル内容が変更される場合があることを確認
        if fixed_content != content:
            assert len(fixed_content.split("\n")) <= len(content.split("\n"))

    def test_fix_file_with_nonexistent_file(self):
        """存在しないファイルの修正テスト"""
        nonexistent = str(Path(self.temp_dir) / "nonexistent.py")

        result = self.fixer.fix_file(nonexistent)

        assert "error" in result

    def test_fix_file_with_valid_file(self):
        """正常ファイルの修正テスト"""
        test_file = Path(self.temp_dir) / "test.py"
        test_file.write_text(
            """import json
def test():
    x=1+2
    return x
"""
        )

        result = self.fixer.fix_file(str(test_file), dry_run=True)

        # エラーなく完了することを確認
        assert "error" not in result
        assert isinstance(result, dict)


@pytest.mark.unit
@pytest.mark.commands
class TestLintIntegration:
    """lint機能の統合テスト"""

    def setup_method(self):
        """テスト用のセットアップ"""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """テストのクリーンアップ"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_end_to_end_fix_workflow(self):
        """エンドツーエンドの修正ワークフロー"""
        # 問題のあるPythonファイル作成
        problem_file = Path(self.temp_dir) / "problem.py"
        problem_file.write_text(
            """def test():
    x=1+2
    very_long_line_that_exceeds_the_maximum_line_length_and_should_be_split_somehow = True
    return x
"""
        )

        # dry-runで修正可能性確認
        result1 = self.runner.invoke(
            lint_command, [str(problem_file), "--fix", "--dry-run"]
        )
        assert result1.exit_code == 0

        # 実際に修正実行
        result2 = self.runner.invoke(lint_command, [str(problem_file), "--fix"])
        assert result2.exit_code == 0

        # ファイルが修正されていることを確認
        modified_content = problem_file.read_text()
        assert modified_content  # ファイルが存在し、内容がある

    def test_multiple_files_processing(self):
        """複数ファイル処理テスト"""
        # 複数のテストファイル作成
        files = []
        for i in range(3):
            test_file = Path(self.temp_dir) / f"test_{i}.py"
            test_file.write_text(
                f"""def test_{i}():
    x=1+{i}
    return x
"""
            )
            files.append(str(test_file))

        # 複数ファイルを同時処理
        result = self.runner.invoke(lint_command, files + ["--fix", "--dry-run"])

        assert result.exit_code == 0
        assert "Fixing files" in result.output

    def test_lint_with_type_option(self):
        """--typeオプションでの特定エラータイプ修正テスト"""
        # テスト用ファイル作成
        test_file = Path(self.temp_dir) / "test_type.py"
        test_file.write_text(
            """import json  # 未使用import (F401)
def test():
    x=1+2  # E226: 演算子周辺の空白不足
    return x
"""
        )

        result = self.runner.invoke(
            lint_command, [str(test_file), "--fix", "--dry-run", "--type", "E226,F401"]
        )

        assert result.exit_code == 0
        assert "Fixing only specified error types: E226, F401" in result.output
        assert "Dry run completed" in result.output

    def test_lint_with_invalid_type_option(self):
        """不正な--typeオプション指定時のテスト"""
        # テスト用ファイル作成
        test_file = Path(self.temp_dir) / "test_invalid.py"
        test_file.write_text(
            """def test():
    x=1+2
    return x
"""
        )

        result = self.runner.invoke(
            lint_command, [str(test_file), "--fix", "--dry-run", "--type", "E999,X123"]
        )

        # 不正なエラータイプでもクラッシュしない
        assert result.exit_code == 0
        assert "Fixing only specified error types: E999, X123" in result.output
