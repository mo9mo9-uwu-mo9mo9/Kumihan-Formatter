"""
変換コマンド - 互換性維持用レガシーファイル

Issue #319対応: 新しいconvertモジュールへの移行用
このファイルは既存コードとの互換性維持のために残されています。

新しいコードでは以下を使用してください:
from kumihan_formatter.commands.convert import ConvertCommand
"""

from typing import Optional

# click コマンド作成関数
import click

# 互換性のための再エクスポート
from kumihan_formatter.commands.convert.convert_command import ConvertCommand


@click.command()
@click.argument("input_file", required=False)
@click.option(
    "--output", "-o", default="./dist", help="出力ディレクトリ (デフォルト: ./dist)"
)
@click.option("--no-preview", is_flag=True, help="変換後のブラウザプレビューをスキップ")
@click.option("--watch", "-w", is_flag=True, help="ファイル変更を監視して自動変換")
@click.option("--config", "-c", help="設定ファイルのパス (廃止予定)")
@click.option("--show-test-cases", is_flag=True, help="テストケースを表示")
@click.option("--template", help="使用するテンプレート名")
@click.option("--include-source", is_flag=True, help="ソース表示機能を含める")
@click.option("--no-syntax-check", is_flag=True, help="変換前の構文チェックをスキップ")
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


def create_convert_command():
    """Click コマンドオブジェクトを返す"""
    return convert_command


# 廃止予定の警告
import warnings

warnings.warn(
    "commands/convert.py の直接使用は廃止予定です。"
    "新しいコードでは kumihan_formatter.commands.convert を使用してください。",
    DeprecationWarning,
    stacklevel=2,
)
