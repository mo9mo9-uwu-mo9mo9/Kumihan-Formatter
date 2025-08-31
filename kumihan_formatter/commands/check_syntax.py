"""Check syntax command implementation

This module provides syntax checking functionality for Kumihan markup files.
"""

import sys
from pathlib import Path
from typing import Any

import click

from ..core.common.error_base import ErrorSeverity
from ..core.syntax import check_files, format_error_report

# from ..ui.console_ui import get_console_ui  # TODO: console_ui module not found


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

        def error(self, msg: str) -> None:
            print(f"❌ {msg}")

        def info(self, msg: str, details: str = "") -> None:
            if details:
                print(f"ℹ️ {msg}: {details}")
            else:
                print(f"ℹ️ {msg}")

        def warning(self, msg: str) -> None:
            print(f"⚠️ {msg}")

        def success(self, title: str, msg: str = "") -> None:
            if msg:
                print(f"✅ {title}: {msg}")
            else:
                print(f"✅ {title}")

        def dim(self, msg: str) -> None:
            print(f"💭 {msg}")

    return DummyConsoleUI()


class CheckSyntaxCommand:
    """Check syntax command implementation"""

    def check(self, files: list[str], **kwargs: Any) -> dict[str, Any]:
        """Alias for execute method for backward compatibility"""
        return self.execute(files, **kwargs)

    def execute(
        self,
        files: list[str],
        recursive: bool = False,
        show_suggestions: bool = True,
        format_output: str = "text",
    ) -> dict[str, Any]:
        """
        Execute syntax check command

        Args:
            files: List of file paths to check
            recursive: Check directories recursively
            show_suggestions: Show fix suggestions
            format_output: Output format (text/json)
        """
        try:
            # Collect files to check
            file_paths = self._collect_files(files, recursive)

            if not file_paths:
                get_console_ui().error("チェックするファイルが見つかりません")
                sys.exit(1)

            get_console_ui().info(
                "構文チェック", f"{len(file_paths)} ファイルをチェック中..."
            )

            # Run syntax check
            results = check_files(file_paths, verbose=False)

            # Output results
            if format_output == "json":
                self._output_json(results)
            else:
                self._output_text(results, show_suggestions)

            # Return results
            if results:
                if isinstance(results, dict):
                    error_count = sum(
                        1
                        for errors in results.values()
                        for error in errors
                        if error.severity == ErrorSeverity.ERROR
                    )

                return {
                    "success": error_count == 0,
                    "error_count": error_count,
                    "results": results,
                }
            else:
                return {"success": True, "error_count": 0, "results": {}}
        except Exception as e:
            get_console_ui().error(f"構文チェック中にエラーが発生しました: {e}")
            return {"success": False, "error_count": -1, "results": {}}

    def _collect_files(self, file_patterns: list[str], recursive: bool) -> list[Path]:
        """Collect files to check from patterns"""
        file_paths = []

        for pattern in file_patterns:
            path = Path(pattern)

            if path.is_file():
                if path.suffix == ".txt":
                    file_paths.append(path)
                else:
                    get_console_ui().warning(
                        f"スキップ: {pattern} (txtファイルではありません)"
                    )
            elif path.is_dir():
                if recursive:
                    # Find all .txt files recursively
                    txt_files = list(path.rglob("*.txt"))
                    file_paths.extend(txt_files)
                    get_console_ui().info(
                        "検索", f"{path} から {len(txt_files)} ファイルを発見"
                    )
                else:
                    # Find .txt files in directory (non-recursive)
                    txt_files = list(path.glob("*.txt"))
                    file_paths.extend(txt_files)
                    get_console_ui().info(
                        "検索", f"{path} から {len(txt_files)} ファイルを発見"
                    )
            else:
                get_console_ui().warning(f"ファイルが見つかりません: {pattern}")

        return file_paths

    def _output_text(self, results: Any, show_suggestions: bool) -> None:
        """Output results in text format"""
        report = format_error_report(results, show_suggestions)

        if not results:
            get_console_ui().success(
                "構文チェック完了", "記法エラーは見つかりませんでした"
            )
        else:
            total_errors = sum(len(errors) for errors in results.values())
            error_count = sum(
                1
                for errors in results.values()
                for error in errors
                if error.severity == ErrorSeverity.ERROR
            )
            warning_count = sum(
                1
                for errors in results.values()
                for error in errors
                if error.severity == ErrorSeverity.WARNING
            )

            get_console_ui().warning(
                "構文チェック完了",
                f"{len(results)} ファイルで {total_errors} 個の問題を発見",
            )
            get_console_ui().dim(f"エラー: {error_count}, 警告: {warning_count}")
            print()
            print(report)

    def _output_json(self, results: Any) -> None:
        """Output results in JSON format"""
        import json

        json_results = {}
        for file_path, errors in results.items():
            json_results[file_path] = [
                {
                    "line": error.line_number,
                    "column": error.column,
                    "severity": error.severity.value,
                    "type": error.error_type,
                    "message": error.message,
                    "context": error.context,
                    "suggestion": error.suggestion,
                }
                for error in errors
            ]

        print(json.dumps(json_results, ensure_ascii=False, indent=2))


def create_check_syntax_command() -> click.Command:
    """Create the check-syntax click command"""

    @click.command()
    @click.argument("files", nargs=-1, required=True)
    @click.option("-r", "--recursive", is_flag=True, help="ディレクトリを再帰的に検索")
    @click.option("--no-suggestions", is_flag=True, help="修正提案を表示しない")
    @click.option(
        "--format",
        "output_format",
        type=click.Choice(["text", "json"]),
        default="text",
        help="出力形式",
    )
    def check_syntax(
        files: Any, recursive: Any, no_suggestions: Any, output_format: Any
    ) -> None:
        """Kumihan記法の構文をチェックします"""

        command = CheckSyntaxCommand()
        command.execute(
            list(files),
            recursive=recursive,
            show_suggestions=not no_suggestions,
            format_output=output_format,
        )

    return check_syntax
