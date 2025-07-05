"""Refactored CLI entry point for Kumihan-Formatter

This is the new, modular CLI implementation that replaces the monolithic
cli.py file. Each command is now implemented in separate modules for
better maintainability and reduced complexity.
"""

import sys

import click


def setup_encoding():
    """Setup encoding for Windows and macOS compatibility"""
    # This is now handled by the ConsoleUI class
    pass


@click.group()
def cli():
    """Kumihan-Formatter - 美しい組版を、誰でも簡単に。

    CLI tool for converting text files to beautifully formatted HTML.
    Optimized for doujin scenario writers and non-technical users.
    """
    pass


# Register commands using lazy loading
def register_commands():
    """Register all CLI commands with lazy loading"""
    # convert コマンドを最初に登録（最重要）
    try:
        # 新しい convert モジュール構造を使用
        from typing import Optional

        import click

        from .commands.convert.convert_command import ConvertCommand

        @click.command()
        @click.argument("input_file", required=False)
        @click.option(
            "--output",
            "-o",
            default="./dist",
            help="出力ディレクトリ (デフォルト: ./dist)",
        )
        @click.option(
            "--no-preview", is_flag=True, help="変換後のブラウザプレビューをスキップ"
        )
        @click.option(
            "--watch", "-w", is_flag=True, help="ファイル変更を監視して自動変換"
        )
        @click.option("--config", "-c", help="設定ファイルのパス")
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
            """テキストファイルをHTMLに変換する"""
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

        cli.add_command(convert_command, name="convert")
    except ImportError:
        # フォールバック: レガシー convert.py を使用
        from .commands.convert import create_convert_command

        cli.add_command(create_convert_command(), name="convert")

    # 他のコマンドを個別に登録（失敗してもconvertは動作する）
    try:
        from .commands.check_syntax import create_check_syntax_command

        cli.add_command(create_check_syntax_command(), name="check-syntax")
    except ImportError as e:
        import warnings

        warnings.warn(f"check-syntax コマンドが読み込めませんでした: {e}")

    try:
        from .commands.sample import create_sample_command, create_test_command

        cli.add_command(create_sample_command(), name="generate-sample")
        cli.add_command(create_test_command(), name="generate-test")
    except ImportError as e:
        import warnings

        warnings.warn(f"sample コマンドが読み込めませんでした: {e}")


def main():
    """Main entry point with enhanced error handling"""
    # コマンドを登録
    register_commands()

    from .core.error_handling import ErrorHandler as FriendlyErrorHandler
    from .ui.console_ui import ui

    friendly_error_handler = FriendlyErrorHandler(console_ui=ui)

    try:
        # Handle legacy command routing
        if len(sys.argv) > 1:
            # Legacy support: if first argument is a file, route to convert
            first_arg = sys.argv[1]
            if not first_arg.startswith("-") and first_arg not in [
                "convert",
                "generate-sample",
                "generate-test",
                "check-syntax",
            ]:
                # Check if it's a file path
                from pathlib import Path

                if Path(first_arg).exists() or first_arg.endswith(".txt"):
                    # Insert 'convert' command
                    sys.argv.insert(1, "convert")

        # Execute CLI
        cli()

    except KeyboardInterrupt:
        ui.info("操作が中断されました")
        ui.dim("Ctrl+C で中断されました")
        sys.exit(130)
    except click.ClickException as e:
        # Click自体のエラーは元の処理を維持
        e.show()
        sys.exit(e.exit_code)
    except (FileNotFoundError, UnicodeDecodeError, PermissionError) as e:
        # 一般的なエラーは新システムで処理
        error = friendly_error_handler.handle_exception(e)
        friendly_error_handler.display_error(error, verbose=True)
        sys.exit(1)
    except Exception as e:
        # その他の予期しないエラー
        error = friendly_error_handler.handle_exception(
            e, context={"operation": "CLI実行", "args": sys.argv}
        )
        friendly_error_handler.display_error(error, verbose=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
