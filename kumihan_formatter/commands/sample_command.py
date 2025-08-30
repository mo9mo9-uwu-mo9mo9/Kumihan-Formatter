"""Sample generation command implementation

This module contains the sample generation functionality.
"""

from pathlib import Path
from typing import Any

import click
from rich.progress import Progress

# Issue #1207: Migrated from deprecated file_ops to new io system
from ..parser import parse
from ..core.rendering.main_renderer import MainRenderer
from ..sample_content import SAMPLE_IMAGES, SHOWCASE_SAMPLE

# from ..ui.console_ui import get_console_ui  # TODO: console_ui module not found

from ..core.rendering import render


def get_console_ui() -> Any:
    """Dummy console UI for compatibility"""

    class DummyConsoleUI:
        def print_success(self, msg: str) -> None:
            print(f"✅ {msg}")

        def print_error(self, msg: str) -> None:
            print(f"❌ {msg}")

        def print_warning(self, msg: str) -> None:
            print(f"⚠️ {msg}")

        def print_info(self, msg: str) -> None:
            print(f"ℹ️ {msg}")

        def sample_generation(self, output_path: str) -> None:
            print(f"📁 サンプル生成開始: {output_path}")

        def sample_complete(
            self, output_path: str, txt_name: str, html_name: str, image_count: int
        ) -> None:
            print(f"✅ サンプル生成完了: {output_path}")
            print(f"📄 テキスト: {txt_name}")
            print(f"🌐 HTML: {html_name}")
            print(f"🖼️ 画像: {image_count}個")

    return DummyConsoleUI()


from ..managers.core_manager import CoreManager
from ..core.io.validators import PathValidator


class SampleCommand:
    """Sample generation command implementation"""

    def __init__(self) -> None:
        # 新しい統合ファイルマネージャーを使用（廃止予定のfile_opsから移行）
        self.core_manager = CoreManager({})
        from ..core.io.validators import PathValidator

        self.path_validator = PathValidator()

    def execute(
        self, output_dir: str = "kumihan_sample", use_source_toggle: bool = False
    ) -> Path:
        """
        Execute sample generation command

        Args:
            output_dir: Output directory name
            use_source_toggle: Include source toggle feature

        Returns:
            Path to output directory
        """
        output_path = Path(output_dir)

        get_console_ui().sample_generation(str(output_path))

        # Remove existing output directory if it exists
        if output_path.exists():
            import shutil

            shutil.rmtree(output_path)

        # Create output directory using new FileManager
        self.core_manager.ensure_directory(output_path)

        # Create sample text file using new FileManager
        sample_txt = output_path / "showcase.txt"
        self.core_manager.write_file(sample_txt, SHOWCASE_SAMPLE)

        # Create images directory and sample images using new FileManager
        images_dir = output_path / "images"
        self.core_manager.ensure_directory(images_dir)
        # Sample images creation - simplified implementation
        for filename, base64_data in SAMPLE_IMAGES.items():
            image_path = images_dir / filename
            # Create placeholder image content for sample
            placeholder_content = f"<!-- Sample Image: {filename} -->"
            self.core_manager.write_file(
                image_path.with_suffix(".txt"), placeholder_content
            )

        # Convert to HTML
        html = self._generate_html(use_source_toggle)

        # Save HTML file using new FileManager
        html_path = output_path / "showcase.html"
        self.core_manager.write_file(html_path, html)

        # Show completion message
        get_console_ui().sample_complete(
            str(output_path.absolute()),
            sample_txt.name,
            html_path.name,
            len(SAMPLE_IMAGES),
        )

        return output_path

    def _generate_html(self, use_source_toggle: bool) -> str:
        """Generate HTML from sample content"""
        try:
            with Progress() as progress:
                # Parse
                task = progress.add_task("[cyan]テキストを解析中", total=100)
                ast = parse(SHOWCASE_SAMPLE)
                progress.update(task, completed=100)

                # Render (template selection)
                task = progress.add_task("[cyan]HTMLを生成中", total=100)
                if use_source_toggle:
                    context = {
                        "template": "base-with-source-toggle.html.j2",
                        "title": "showcase",
                        "source_text": SHOWCASE_SAMPLE,
                        "source_filename": "showcase.txt",
                    }
                    html = render(ast, context)
                else:
                    context = {"template": "base.html.j2", "title": "showcase"}
                    html = render(ast, context)
                progress.update(task, completed=100)
        except Exception:
            # Fallback for test environments
            ast = parse(SHOWCASE_SAMPLE)
            if use_source_toggle:
                context = {
                    "template": "base-with-source-toggle.html.j2",
                    "title": "showcase",
                    "source_text": SHOWCASE_SAMPLE,
                    "source_filename": "showcase.txt",
                }
                html = render(ast, context)
            else:
                context = {"template": "base.html.j2", "title": "showcase"}
                html = render(ast, context)

        return html


def create_sample_command() -> Any:
    """Create the sample generation click command"""

    @click.command()
    @click.option(
        "-o", "--output", default="kumihan_sample", help="サンプル出力ディレクトリ"
    )
    @click.option(
        "--with-source-toggle",
        is_flag=True,
        help="記法と結果を切り替えるトグル機能付きで出力",
    )
    @click.option(
        "--quiet", is_flag=True, help="対話的プロンプトを無効化（バッチ実行用）"
    )
    def generate_sample(output: Any, with_source_toggle: Any, quiet: Any) -> None:
        """機能ショーケースサンプルを生成します"""

        # Determine source toggle usage
        use_source_toggle = with_source_toggle

        command = SampleCommand()
        command.execute(output, use_source_toggle)

    return generate_sample


# Re-export for backward compatibility (統合: sample.py → sample_command.py)
__all__ = ["create_sample_command", "SampleCommand"]
