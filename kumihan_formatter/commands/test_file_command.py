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
            from generate_test_file import TestFileGenerator  # type: ignore
        except ImportError:
            get_console_ui().error("テストファイル生成ツールが見つかりません")
            get_console_ui().dim("dev/tools/generate_test_file.py を確認してください")
            sys.exit(1)

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
            from ..config import load_config
            from .convert import ConvertCommand

            config_obj = load_config(config)
            if config:
                config_obj.validate_config()  # type: ignore

            # Ensure the output directory is clean
            output_dir = Path(output or "dist")
            test_html_file = output_dir / f"{output_file.stem}.html"
            if test_html_file.exists():
                test_html_file.unlink()

            convert_command = ConvertCommand()
            test_output_file = convert_command._convert_file(  # type: ignore
                output_file,
                output or "dist",
                config_obj,
                show_stats=False,
                show_test_cases=show_test_cases,
            )

            get_console_ui().test_conversion_complete(
                str(test_output_file), str(output_file), double_click_mode
            )

            if not no_preview:
                import webbrowser

                if double_click_mode:
                    get_console_ui().info("ブラウザ", "ブラウザで結果を表示中...")
                else:
                    get_console_ui().browser_opening()
                webbrowser.open(test_output_file.resolve().as_uri())

        except Exception as e:
            get_console_ui().test_conversion_error(str(e))
            raise click.ClickException(f"テスト変換中にエラーが発生しました: {e}")


def create_test_command():  # type: ignore
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
    def generate_test(  # type: ignore
        test_output,
        pattern_count,
        double_click_mode,
        output,
        no_preview,
        show_test_cases,
        config,
    ):
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

