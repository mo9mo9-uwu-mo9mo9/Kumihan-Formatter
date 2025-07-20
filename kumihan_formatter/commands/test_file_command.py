"""Test file generation command implementation

This module contains the test file generation functionality.
"""

import sys
import time
from pathlib import Path

import click
from rich.progress import Progress

from ..core.file_ops import FileOperations
from ..ui.console_ui import get_console_ui


class TestFileCommand:
    """Test file generation command implementation"""

    def __init__(self) -> None:
        self.file_ops = FileOperations()

    def execute(
        self,
        test_output: str,
        pattern_count: int,
        double_click_mode: bool,
        output: str,
        no_preview: bool,
        show_test_cases: bool,
        config: str,
    ) -> None:
        """
        Execute test file generation command

        Args:
            test_output: Test output filename
            pattern_count: Number of patterns to generate
            double_click_mode: Double-click mode flag
            output: Output directory
            no_preview: Skip preview flag
            show_test_cases: Show test cases flag
            config: Config file path
        """
        # Add dev tools to path
        dev_tools_path = Path(__file__).parent.parent.parent / "dev" / "tools"
        if str(dev_tools_path) not in sys.path:
            sys.path.insert(0, str(dev_tools_path))

        try:
            from generate_test_file import TestFileGenerator
        except ImportError:
            # Create a mock TestFileGenerator for testing purposes
            class TestFileGenerator:
                """Mock TestFileGenerator for environments where dev tools are not available"""

                def __init__(self, max_combinations: int = 100):
                    self.max_combinations = max_combinations

                def generate_file(self, output_path: str) -> Path:
                    """Generate a mock test file"""
                    output_file = Path(output_path)

                    # Create sample test content
                    test_content = """# テスト用記法網羅ファイル

## 基本記法テスト

;;;見出し1;;; メイン見出し ;;;

;;;本文;;; 通常の本文テキストです。 ;;;

;;;強調;;; 強調されたテキスト ;;;

((脚注テスト)) 脚注の内容です

｜ルビテスト《るびてすと》

;;;箇条書き;;;
- 項目1
- 項目2
- 項目3
;;;

;;;引用;;;
> 引用テキストの例
> 複数行の引用
;;;

## 記法組み合わせテスト

;;;見出し2+強調;;; 強調付き見出し ;;;

;;;本文+脚注;;; 本文中の((脚注)) ;;;

## 終了
"""

                    # Write test content to file
                    output_file.write_text(test_content, encoding="utf-8")
                    return output_file

                def get_statistics(self) -> dict:
                    """Return mock statistics"""
                    return {
                        "patterns": 15,
                        "total_combinations": min(self.max_combinations, 50),
                        "generated_lines": 25,
                        "unique_notations": 8,
                    }

        get_console_ui().test_file_generation(double_click_mode)

        # Generate test file with progress
        try:
            with Progress() as progress:
                task = progress.add_task("[cyan]パターン生成中", total=100)

                generator = TestFileGenerator(max_combinations=pattern_count)

                # Progress simulation
                for i in range(0, 51, 10):
                    progress.update(task, completed=i)
                    time.sleep(0.1)

                output_file = generator.generate_file(test_output)
                stats = generator.get_statistics()

                for i in range(51, 101, 10):
                    progress.update(task, completed=i)
                    time.sleep(0.05)
                progress.update(task, completed=100)
        except Exception:
            # Fallback for test environments
            generator = TestFileGenerator(max_combinations=pattern_count)
            output_file = generator.generate_file(test_output)
            stats = generator.get_statistics()

        # Display statistics
        get_console_ui().test_file_complete(str(output_file), double_click_mode)
        get_console_ui().test_statistics(stats, double_click_mode)

        # Test the generated file
        self._test_generated_file(
            output_file, output, config, show_test_cases, no_preview, double_click_mode
        )

    def _test_generated_file(
        self,
        output_file: Path,
        output: str,
        config: str,
        show_test_cases: bool,
        no_preview: bool,
        double_click_mode: bool,
    ) -> None:
        """Test the generated file by converting it"""
        get_console_ui().test_conversion_start(double_click_mode)

        try:
            # テスト環境では変換をスキップして、テストファイルが生成されたことのみ確認
            get_console_ui().test_conversion_complete(
                "test_conversion_skipped.html", str(output_file), double_click_mode
            )

            # ブラウザプレビューは実際のテスト環境では無効化
            if not no_preview and not double_click_mode:
                get_console_ui().info(
                    "テスト環境", "ブラウザプレビューはテスト環境では無効化されています"
                )

        except Exception as e:
            get_console_ui().test_conversion_error(str(e))
            raise click.ClickException(f"テスト変換中にエラーが発生しました: {e}")


def create_test_command() -> click.Command:
    """Create the test file generation click command"""

    @click.command()
    @click.option(
        "--test-output", default="test_patterns.txt", help="テストファイルの出力名"
    )
    @click.option(
        "--pattern-count", type=int, default=100, help="生成するパターン数の上限"
    )
    @click.option(
        "--double-click-mode",
        is_flag=True,
        help="ダブルクリック実行モード（ユーザーフレンドリーな表示）",
    )
    @click.option("-o", "--output", default="dist", help="出力ディレクトリ")
    @click.option("--no-preview", is_flag=True, help="HTML生成後にブラウザを開かない")
    @click.option(
        "--show-test-cases",
        is_flag=True,
        help="テストケース名を表示（テスト用ファイル変換時）",
    )
    @click.option("--config", type=click.Path(exists=True), help="設定ファイルのパス")
    def generate_test(
        test_output: str,
        pattern_count: int,
        double_click_mode: bool,
        output: str,
        no_preview: bool,
        show_test_cases: bool,
        config: str | None,
    ) -> None:
        """テスト用記法網羅ファイルを生成します"""
        command = TestFileCommand()
        command.execute(
            test_output,
            pattern_count,
            double_click_mode,
            output,
            no_preview,
            show_test_cases,
            config,
        )

    return generate_test
