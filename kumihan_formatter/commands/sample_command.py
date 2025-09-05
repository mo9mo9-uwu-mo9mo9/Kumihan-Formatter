"""Sample generation command implementation

This module contains the sample generation functionality.
"""

from pathlib import Path
import os
from typing import Any

import click
from rich.progress import Progress

# Issue #1207: Migrated from deprecated file_ops to new io system
from ..parser import parse
from ..sample_content import SAMPLE_IMAGES, SHOWCASE_SAMPLE

from ..ui.console_ui import get_console_ui

from ..core.rendering import render


def get_console_ui() -> Any:  # type: ignore[no-redef]
    # 旧ダミー関数との互換のため再定義し、新実装を委譲
    from ..ui.console_ui import get_console_ui as _get

    return _get()


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
        self,
        output_dir: str = "kumihan_sample",
        use_source_toggle: bool = False,
        *,
        dry_run: bool = False,
        force: bool = False,
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

        # Remove existing output directory if it exists（安全ガード）
        if output_path.exists():
            if force or str(os.getenv("KUMIHAN_FORCE", "")).lower() in {"1", "true"}:
                import shutil

                if not dry_run:
                    shutil.rmtree(output_path)
                else:
                    get_console_ui().dim(
                        f"[dry-run] 既存ディレクトリ削除をスキップ: {output_path}"
                    )
            else:
                get_console_ui().warning(
                    f"出力先が既に存在します。--force か KUMIHAN_FORCE=1 を指定してください: {output_path}"
                )
                return output_path

        # Create output directory using new FileManager
        if not dry_run:
            self.core_manager.ensure_directory(output_path)

        # Create sample text file using new FileManager
        sample_txt = output_path / "showcase.txt"
        if not dry_run:
            self.core_manager.write_file(sample_txt, SHOWCASE_SAMPLE)

        # Create images directory and sample images using new FileManager
        images_dir = output_path / "images"
        if not dry_run:
            self.core_manager.ensure_directory(images_dir)
        # Sample images creation - simplified implementation
        for filename, base64_data in SAMPLE_IMAGES.items():
            image_path = images_dir / filename
            # Create placeholder image content for sample
            placeholder_content = f"<!-- Sample Image: {filename} -->"
            if not dry_run:
                self.core_manager.write_file(
                    image_path.with_suffix(".txt"), placeholder_content
                )

        # Convert to HTML
        html = self._generate_html(use_source_toggle)

        # Save HTML file using new FileManager
        html_path = output_path / "showcase.html"
        if not dry_run:
            self.core_manager.write_file(html_path, html)

        # Show completion message
        if not dry_run:
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
                    html = render([ast], context)
                else:
                    context = {"template": "base.html.j2", "title": "showcase"}
                    html = render([ast], context)
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
                html = render([ast], context)
            else:
                context = {"template": "base.html.j2", "title": "showcase"}
                html = render([ast], context)

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
    @click.option("--dry-run", is_flag=True, help="ファイル出力や削除を実行しない")
    @click.option("--force", is_flag=True, help="既存出力の削除を強制実行")
    def generate_sample(
        output: Any, with_source_toggle: Any, quiet: Any, dry_run: Any, force: Any
    ) -> None:
        """機能ショーケースサンプルを生成します"""

        # Determine source toggle usage
        use_source_toggle = with_source_toggle

        command = SampleCommand()
        command.execute(output, use_source_toggle, dry_run=dry_run, force=force)

    return generate_sample


# Re-export for backward compatibility (統合: sample.py → sample_command.py)
__all__ = ["create_sample_command", "SampleCommand"]
