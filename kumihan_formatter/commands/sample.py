"""Sample generation command implementation

This module contains the sample generation functionality that was
previously part of the large cli.py file.
"""

import sys
import time
from pathlib import Path
from typing import Optional

import click
from rich.progress import Progress

from ..core.file_ops import FileOperations, PathValidator
from ..parser import parse
from ..renderer import render
from ..sample_content import SAMPLE_IMAGES, SHOWCASE_SAMPLE
from ..ui.console_ui import ui


class SampleCommand:
    """Sample generation command implementation"""

    def __init__(self):
        self.file_ops = FileOperations(ui=ui)
        self.path_validator = PathValidator()

    def execute(self, output_dir: str = "kumihan_sample", use_source_toggle: bool = False) -> Path:
        """
        Execute sample generation command

        Args:
            output_dir: Output directory name
            use_source_toggle: Include source toggle feature

        Returns:
            Path to output directory
        """
        output_path = Path(output_dir)

        ui.sample_generation(str(output_path))

        # Create output directory
        self.file_ops.ensure_directory(output_path)

        # Create sample text file
        sample_txt = output_path / "showcase.txt"
        self.file_ops.write_text_file(sample_txt, SHOWCASE_SAMPLE)

        # Create images directory and sample images
        images_dir = output_path / "images"
        self.file_ops.create_sample_images(images_dir, SAMPLE_IMAGES)

        # Convert to HTML
        html = self._generate_html(use_source_toggle)

        # Save HTML file
        html_path = output_path / "showcase.html"
        self.file_ops.write_text_file(html_path, html)

        # Show completion message
        ui.sample_complete(str(output_path.absolute()), sample_txt.name, html_path.name, len(SAMPLE_IMAGES))

        return output_path

    def _generate_html(self, use_source_toggle: bool) -> str:
        """Generate HTML from sample content"""
        with Progress() as progress:
            # Parse
            task = progress.add_task("[cyan]テキストを解析中", total=100)
            ast = parse(SHOWCASE_SAMPLE)
            progress.update(task, completed=100)

            # Render (template selection)
            task = progress.add_task("[cyan]HTMLを生成中", total=100)
            if use_source_toggle:
                html = render(
                    ast,
                    template="base-with-source-toggle.html.j2",
                    title="showcase",
                    source_text=SHOWCASE_SAMPLE,
                    source_filename="showcase.txt",
                )
            else:
                html = render(ast, template="base.html.j2", title="showcase")
            progress.update(task, completed=100)

        return html


class TestFileCommand:
    """Test file generation command implementation"""

    def __init__(self):
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
            ui.error("テストファイル生成ツールが見つかりません")
            ui.dim("dev/tools/generate_test_file.py を確認してください")
            sys.exit(1)

        ui.test_file_generation(double_click_mode)

        # Generate test file with progress
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

        # Display statistics
        ui.test_file_complete(str(output_file), double_click_mode)
        ui.test_statistics(stats, double_click_mode)

        # Test the generated file
        self._test_generated_file(output_file, output, config, show_test_cases, no_preview, double_click_mode)

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
        ui.test_conversion_start(double_click_mode)

        try:
            from ..config import load_config
            from .convert import ConvertCommand

            config_obj = load_config(config)
            if config:
                config_obj.validate_config()

            convert_command = ConvertCommand()
            test_output_file = convert_command._convert_file(
                output_file, output or "dist", config_obj, show_stats=False, show_test_cases=show_test_cases
            )

            ui.test_conversion_complete(str(test_output_file), str(output_file), double_click_mode)

            if not no_preview:
                import webbrowser

                if double_click_mode:
                    ui.info("ブラウザ", "ブラウザで結果を表示中...")
                else:
                    ui.browser_opening()
                webbrowser.open(test_output_file.resolve().as_uri())

        except Exception as e:
            ui.test_conversion_error(str(e))
            raise click.ClickException(f"テスト変換中にエラーが発生しました: {e}")


def create_sample_command():
    """Create the sample generation click command"""

    @click.command()
    @click.option("-o", "--output", default="kumihan_sample", help="サンプル出力ディレクトリ")
    @click.option("--with-source-toggle", is_flag=True, help="記法と結果を切り替えるトグル機能付きで出力")
    @click.option("--quiet", is_flag=True, help="対話的プロンプトを無効化（バッチ実行用）")
    def generate_sample(output, with_source_toggle, quiet):
        """機能ショーケースサンプルを生成します"""

        # Determine source toggle usage
        use_source_toggle = with_source_toggle

        command = SampleCommand()
        command.execute(output, use_source_toggle)

    return generate_sample


def create_test_command():
    """Create the test file generation click command"""

    @click.command()
    @click.option("--test-output", default="test_patterns.txt", help="テストファイルの出力名")
    @click.option("--pattern-count", type=int, default=100, help="生成するパターン数の上限")
    @click.option("--double-click-mode", is_flag=True, help="ダブルクリック実行モード（ユーザーフレンドリーな表示）")
    @click.option("-o", "--output", default="dist", help="出力ディレクトリ")
    @click.option("--no-preview", is_flag=True, help="HTML生成後にブラウザを開かない")
    @click.option("--show-test-cases", is_flag=True, help="テストケース名を表示（テスト用ファイル変換時）")
    @click.option("--config", type=click.Path(exists=True), help="設定ファイルのパス")
    def generate_test(test_output, pattern_count, double_click_mode, output, no_preview, show_test_cases, config):
        """テスト用記法網羅ファイルを生成します"""
        command = TestFileCommand()
        command.execute(test_output, pattern_count, double_click_mode, output, no_preview, show_test_cases, config)

    return generate_test
