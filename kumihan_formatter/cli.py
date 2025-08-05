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
            # Note: Removed environment variable modification to avoid global
            # side effects
            # Applications should handle encoding externally for older Python versions
            import warnings

            warnings.warn(
                "Python 3.7 or earlier detected. Please set "
                "PYTHONIOENCODING=utf-8 externally.",
                UserWarning,
            )
            logger.warning(
                "Python 3.7 or earlier detected, manual encoding setup may be required"
            )


@click.group()
@click.version_option(version="3.0.0-dev", prog_name="kumihan-formatter")
def cli() -> None:
    """Kumihan-Formatter - 開発用CLIツール

    Development CLI tool for Kumihan-Formatter.
    For end users, please use the GUI version.
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
        @click.option(
            "--progress-level",
            "-p",  # 短縮オプション追加
            type=click.Choice(
                ["silent", "minimal", "detailed", "verbose"], case_sensitive=False
            ),
            default="detailed",
            envvar="KUMIHAN_PROGRESS_LEVEL",  # 環境変数サポート
            help="プログレス表示の詳細レベル (silent/minimal/detailed/verbose)",
        )
        @click.option(
            "--no-progress-tooltip",
            is_flag=True,
            envvar="KUMIHAN_NO_PROGRESS_TOOLTIP",  # 環境変数サポート
            help="プログレス表示でツールチップ情報を無効化",
        )
        @click.option(
            "--disable-cancellation",
            is_flag=True,
            envvar="KUMIHAN_DISABLE_CANCELLATION",  # 環境変数サポート
            help="処理のキャンセル機能を無効化",
        )
        @click.option(
            "--progress-style",
            type=click.Choice(["bar", "spinner", "percentage"], case_sensitive=False),
            default="bar",
            envvar="KUMIHAN_PROGRESS_STYLE",
            help="プログレス表示スタイル (bar/spinner/percentage)",
        )
        @click.option(
            "--progress-log",
            type=click.Path(dir_okay=False, writable=True),
            envvar="KUMIHAN_PROGRESS_LOG",
            help="プログレスログの出力先ファイル（JSONフォーマット）",
        )
        @click.option(
            "--continue-on-error",
            is_flag=True,
            envvar="KUMIHAN_CONTINUE_ON_ERROR",
            help="Issue #700: 記法エラーが発生してもHTML生成を継続する",
        )
        @click.option(
            "--graceful-errors",
            is_flag=True,
            envvar="KUMIHAN_GRACEFUL_ERRORS",
            help="Issue #700: エラー情報をHTMLに埋め込んで表示する",
        )
        @click.option(
            "--error-level",
            type=click.Choice(
                ["strict", "normal", "lenient", "ignore"], case_sensitive=False
            ),
            default="normal",
            envvar="KUMIHAN_ERROR_LEVEL",
            help="Phase3: エラー処理レベル設定（strict/normal/lenient/ignore）",
        )
        @click.option(
            "--no-suggestions",
            is_flag=True,
            help="Phase3: エラー修正提案を非表示",
        )
        @click.option(
            "--no-statistics",
            is_flag=True,
            help="Phase3: エラー統計を非表示",
        )
        def convert_command(
            input_file: str | None,
            output: str,
            no_preview: bool,
            watch: bool,
            config: str | None,
            show_test_cases: bool,
            template: str | None,
            include_source: bool,
            no_syntax_check: bool,
            progress_level: str,
            no_progress_tooltip: bool,
            disable_cancellation: bool,
            progress_style: str,
            progress_log: str | None,
            continue_on_error: bool,
            graceful_errors: bool,
            error_level: str,
            no_suggestions: bool,
            no_statistics: bool,
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
                progress_level=progress_level,
                show_progress_tooltip=not no_progress_tooltip,
                enable_cancellation=not disable_cancellation,
                progress_style=progress_style,
                progress_log=progress_log,
                continue_on_error=continue_on_error,
                graceful_errors=graceful_errors,
                error_level=error_level,
                no_suggestions=no_suggestions,
                no_statistics=no_statistics,
            )

        cli.add_command(convert_command, name="convert")
        logger.debug("Convert command registered successfully")
    except ImportError as e:
        # フォールバック: レガシー convert.py を使用
        logger.warning(f"Failed to import new convert command, using legacy: {e}")
        from .commands.convert import create_convert_command  # type: ignore

        cli.add_command(create_convert_command(), name="convert")
        logger.debug("Legacy convert command registered")

    # lint コマンドを登録（Issue #778対応）
    try:
        from .commands.lint import lint_command

        cli.add_command(lint_command, name="lint")
        logger.debug("lint command registered successfully")
    except ImportError as e:
        import warnings

        warnings.warn(f"lint コマンドが読み込めませんでした: {e}")
        logger.error(f"Failed to load lint command: {e}")

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
        from .commands.sample import create_sample_command

        cli.add_command(create_sample_command(), name="generate-sample")  # type: ignore
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
        # Issue #770: 統一エラーハンドリング適用
        logger.error(f"Unhandled exception in CLI: {e}", exc_info=True)
        from .core.error_handling import handle_error_unified
        from .core.error_handling.log_formatter import ErrorMessageBuilder
        from .ui.console_ui import get_console_ui

        # 統一エラーハンドリングで処理
        result = handle_error_unified(
            e,
            context={"operation": "CLI実行", "args": sys.argv},
            operation="main_cli",
            component_name="CLI",
        )

        # ユーザー向けメッセージ表示
        console_ui = get_console_ui()
        console_message = ErrorMessageBuilder.build_console_message(
            result.kumihan_error, colored=True
        )
        console_ui.error(console_message)
        sys.exit(1)


def interactive_repl():
    """対話型変換REPL - ダブルクリック実行用"""
    import os
    import sys
    from pathlib import Path

    # プロジェクトルートをPythonパスに追加
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

    try:
        from kumihan_formatter.core.parser.kumihan_parser import KumihanParser
        from kumihan_formatter.core.renderer.html_renderer import HTMLRenderer
        from kumihan_formatter.core.utilities.logger import get_logger
    except ImportError as e:
        print(f"❌ インポートエラー: {e}")
        input("Enterキーを押して終了...")
        return

    logger = get_logger(__name__)

    # エンコーディング設定
    setup_encoding()

    print("🚀 Kumihan-Formatter 対話型変換ツール")
    print("=" * 50)
    print("📝 テキストを入力してHTML変換をテストできます")
    print("💡 'exit' または 'quit' で終了")
    print("💡 'help' でヘルプ表示")
    print("💡 'clear' で画面クリア")
    print("-" * 50)

    parser = KumihanParser()
    renderer = HTMLRenderer()

    history = []

    while True:
        try:
            # プロンプト表示
            user_input = input("\n📝 Kumihan記法: ").strip()

            if not user_input:
                continue

            # 特殊コマンド処理
            if user_input.lower() in ["exit", "quit"]:
                print("👋 終了します")
                break
            elif user_input.lower() == "help":
                print("\n📖 ヘルプ:")
                print("  - Kumihan記法を入力するとHTML変換されます")
                print("  - 例: # 太字 #テスト## → <strong>テスト</strong>")
                print("  - 'history' で履歴表示")
                print("  - 'clear' で画面クリア")
                print("  - 'exit' で終了")
                continue
            elif user_input.lower() == "clear":
                os.system("clear" if os.name == "posix" else "cls")
                continue
            elif user_input.lower() == "history":
                print("\n📚 変換履歴:")
                for i, (input_text, output_html) in enumerate(history[-10:], 1):
                    print(f"  {i}. 入力: {input_text[:50]}...")
                    print(f"     出力: {output_html[:100]}...")
                continue

            # Kumihan記法の変換実行
            try:
                # パース処理
                result = parser.parse_text(user_input)

                # HTML生成
                html_content = renderer.render(result)

                # 結果表示
                print("\n✅ 変換成功:")
                print(f"📄 HTML: {html_content}")

                # 履歴に追加
                history.append((user_input, html_content))

            except Exception as parse_error:
                print(f"\n❌ 変換エラー: {parse_error}")
                logger.error(f"Parse error: {parse_error}")

        except KeyboardInterrupt:
            print("\n\n👋 Ctrl+C で終了します")
            break
        except Exception as e:
            print(f"\n❌ 予期しないエラー: {e}")
            logger.error(f"Unexpected error: {e}")

    input("\nEnterキーを押して終了...")


if __name__ == "__main__":
    # ダブルクリック実行時は対話REPLを起動
    if len(sys.argv) == 1:
        interactive_repl()
    else:
        # コマンドライン引数がある場合は通常のCLI
        main()


if __name__ == "__main__":
    main()
