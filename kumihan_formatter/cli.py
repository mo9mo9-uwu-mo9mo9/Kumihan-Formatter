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
    try:
        from .commands.check_syntax import create_check_syntax_command
        from .commands.sample import create_sample_command, create_test_command
        from .commands.zip_dist import create_zip_dist_command
        
        # convert コマンドは特殊なパスにある
        try:
            from .commands.convert import create_convert_command
            cli.add_command(create_convert_command(), name="convert")
        except ImportError:
            # ファイルから直接インポート
            from kumihan_formatter.commands.convert import convert_command
            cli.add_command(convert_command, name="convert")
        
        cli.add_command(create_zip_dist_command(), name="zip-dist")
        cli.add_command(create_sample_command(), name="generate-sample")
        cli.add_command(create_test_command(), name="generate-test")
        cli.add_command(create_check_syntax_command(), name="check-syntax")
    except ImportError as e:
        # テスト環境では一部のコマンドが利用できない可能性がある
        import warnings
        warnings.warn(f"一部のコマンドが読み込めませんでした: {e}")
        pass


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
            if not first_arg.startswith("-") and not first_arg in [
                "convert",
                "zip-dist",
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
