"""
変換コマンドモジュール

Convert command の責任分離実装
Issue #319対応 - 単一責任原則に基づくリファクタリング

元ファイル: commands/convert.py (375行) → 4つのモジュールに分割
"""

from .convert_command import ConvertCommand
from .convert_processor import ConvertProcessor
from .convert_validator import ConvertValidator
from .convert_watcher import ConvertWatcher

# Define create_convert_command function here to avoid circular imports
import click
from typing import Optional


def create_convert_command():
    """Create and return the convert command"""

    @click.command()
    @click.argument("input_file", required=False)
    @click.option(
        "--output", "-o", default="./dist", help="出力ディレクトリ (デフォルト: ./dist)"
    )
    @click.option(
        "--no-preview", is_flag=True, help="変換後のブラウザプレビューをスキップ"
    )
    @click.option("--watch", "-w", is_flag=True, help="ファイル変更を監視して自動変換")
    @click.option("--config", "-c", help="設定ファイルのパス (廃止予定)")
    @click.option("--show-test-cases", is_flag=True, help="テストケースを表示")
    @click.option("--template", help="使用するテンプレート名")
    @click.option("--include-source", is_flag=True, help="ソース表示機能を含める")
    @click.option(
        "--no-syntax-check", is_flag=True, help="変換前の構文チェックをスキップ"
    )
    def convert_command(
        input_file: Optional[str],
        output: str,
        no_preview: bool,
        watch: bool,
        config: Optional[str],
        show_test_cases: bool,
        template: Optional[str],
        include_source: bool,
        no_syntax_check: bool,
    ):
        """
        テキストファイルをHTMLに変換する

        INPUT_FILE: 変換するテキストファイルのパス
        """
        command = ConvertCommand()
        command.execute(
            input_file=input_file,
            output=output,
            no_preview=no_preview,
            watch=watch,
            config=config,
            show_test_cases=show_test_cases,
            template_name=template,
            include_source=include_source,
            syntax_check=not no_syntax_check,
        )

    return convert_command


__all__ = [
    "ConvertCommand",
    "ConvertValidator",
    "ConvertProcessor",
    "ConvertWatcher",
    "create_convert_command",
]
