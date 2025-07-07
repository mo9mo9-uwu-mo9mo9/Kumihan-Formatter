"""Refactored CLI entry point for Kumihan-Formatter

This is the new, modular CLI implementation that replaces the monolithic
cli.py file. Each command is now implemented in separate modules for
better maintainability and reduced complexity.
"""

import sys

import click

from .core.utilities.logger import get_logger


def setup_encoding() -> None:
    """Setup encoding for Windows and macOS compatibility"""
    logger = get_logger(__name__)
    import os
    import sys

    # Windows specific encoding setup
    if sys.platform == "win32":
        logger.debug("Windows platform detected, setting up UTF-8 encoding")
        # 環境変数ではなく、ストリームの設定で対応
        try:
            sys.stdout.reconfigure(encoding="utf-8")  # type: ignore
            sys.stderr.reconfigure(encoding="utf-8")  # type: ignore
            logger.info("UTF-8 encoding configured successfully")
        except AttributeError:
            # Python 3.7以前の場合のフォールバック
            # Note: Removed environment variable modification to avoid global side effects
            # Applications should handle encoding externally for older Python versions
            import warnings

            warnings.warn(
                "Python 3.7 or earlier detected. Please set PYTHONIOENCODING=utf-8 externally.",
                UserWarning,
            )
            logger.warning(
                "Python 3.7 or earlier detected, manual encoding setup may be required"
            )


@click.group()
def cli() -> None:
    """Kumihan-Formatter - 美しい組版を、誰でも簡単に。

    CLI tool for converting text files to beautifully formatted HTML.
    Optimized for doujin scenario writers and non-technical users.
    """
    pass


# Register commands using lazy loading
def register_commands() -> None:
    """Register all CLI commands with lazy loading"""
    logger = get_logger(__name__)
    # convert コマンドを最初に登録（最重要）
    logger.info("Registering CLI commands")
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
        ) -> None:
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
        logger.debug("Convert command registered successfully")
    except ImportError as e:
        # フォールバック: レガシー convert.py を使用
        logger.warning(f"Failed to import new convert command, using legacy: {e}")
        from .commands.convert import create_convert_command

        cli.add_command(create_convert_command(), name="convert")
        logger.debug("Legacy convert command registered")

    # 他のコマンドを個別に登録（失敗してもconvertは動作する）
    try:
        from .commands.check_syntax import create_check_syntax_command

        cli.add_command(create_check_syntax_command(), name="check-syntax")
        logger.debug("check-syntax command registered successfully")
    except ImportError as e:
        import warnings

        warnings.warn(f"check-syntax コマンドが読み込めませんでした: {e}")
        logger.error(f"Failed to load check-syntax command: {e}")

    try:
        from .commands.sample import create_sample_command, create_test_command

        cli.add_command(create_sample_command(), name="generate-sample")
        cli.add_command(create_test_command(), name="generate-test")
        logger.debug("Sample generation commands registered successfully")
    except ImportError as e:
        import warnings

        warnings.warn(f"sample コマンドが読み込めませんでした: {e}")
        logger.error(f"Failed to load sample commands: {e}")


def main() -> None:
    """Main entry point with enhanced error handling"""
    logger = get_logger(__name__)
    # エンコーディング設定を初期化
    logger.info("Kumihan-Formatter CLI starting")
    setup_encoding()

    # コマンドを登録
    register_commands()

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
                logger.debug(
                    f"Auto-routing file argument '{first_arg}' to convert command"
                )
                sys.argv.insert(1, "convert")

    # Execute CLI with minimal error handling to preserve Click's help behavior
    try:
        logger.debug(f"Executing command with args: {sys.argv}")
        cli()
    except KeyboardInterrupt:
        from .ui.console_ui import get_console_ui

        console_ui = get_console_ui()
        console_ui.info("操作が中断されました")
        console_ui.dim("Ctrl+C で中断されました")
        logger.info("Operation cancelled by user (KeyboardInterrupt)")
        sys.exit(130)
    except click.ClickException:
        # Let Click handle its own exceptions (including help)
        raise
    except Exception as e:
        # Handle other exceptions with friendly error handler
        logger.error(f"Unhandled exception in CLI: {e}", exc_info=True)
        from .core.error_handling import ErrorHandler as FriendlyErrorHandler
        from .ui.console_ui import get_console_ui

        friendly_error_handler = FriendlyErrorHandler(console_ui=get_console_ui())
        error = friendly_error_handler.handle_exception(
            e, context={"operation": "CLI実行", "args": sys.argv}
        )
        friendly_error_handler.display_error(error, verbose=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
