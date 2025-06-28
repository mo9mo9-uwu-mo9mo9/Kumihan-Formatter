"""Check syntax command implementation

This module provides syntax checking functionality for Kumihan markup files.
"""

import sys
from pathlib import Path
from typing import List

import click

from ..core.syntax import ErrorSeverity, check_files, format_error_report
from ..ui.console_ui import ui


class CheckSyntaxCommand:
    """Check syntax command implementation"""

    def execute(
        self, files: List[str], recursive: bool = False, show_suggestions: bool = True, format_output: str = "text"
    ) -> None:
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
                ui.error("チェックするファイルが見つかりません")
                sys.exit(1)

            ui.info("構文チェック", f"{len(file_paths)} ファイルをチェック中...")

            # Run syntax check
            results = check_files(file_paths, verbose=False)

            # Output results
            if format_output == "json":
                self._output_json(results)
            else:
                self._output_text(results, show_suggestions)

            # Exit with appropriate code
            if results:
                error_count = sum(
                    1 for errors in results.values() for error in errors if error.severity == ErrorSeverity.ERROR
                )
                if error_count > 0:
                    sys.exit(1)
                else:
                    sys.exit(0)  # Only warnings
            else:
                sys.exit(0)  # No errors

        except Exception as e:
            ui.error(f"構文チェック中にエラーが発生しました: {e}")
            sys.exit(1)

    def _collect_files(self, file_patterns: List[str], recursive: bool) -> List[Path]:
        """Collect files to check from patterns"""
        file_paths = []

        for pattern in file_patterns:
            path = Path(pattern)

            if path.is_file():
                if path.suffix == ".txt":
                    file_paths.append(path)
                else:
                    ui.warning(f"スキップ: {pattern} (txtファイルではありません)")
            elif path.is_dir():
                if recursive:
                    # Find all .txt files recursively
                    txt_files = list(path.rglob("*.txt"))
                    file_paths.extend(txt_files)
                    ui.info("検索", f"{path} から {len(txt_files)} ファイルを発見")
                else:
                    # Find .txt files in directory (non-recursive)
                    txt_files = list(path.glob("*.txt"))
                    file_paths.extend(txt_files)
                    ui.info("検索", f"{path} から {len(txt_files)} ファイルを発見")
            else:
                ui.warning(f"ファイルが見つかりません: {pattern}")

        return file_paths

    def _output_text(self, results, show_suggestions: bool) -> None:
        """Output results in text format"""
        report = format_error_report(results, show_suggestions)

        if not results:
            ui.success("構文チェック完了", "記法エラーは見つかりませんでした")
        else:
            total_errors = sum(len(errors) for errors in results.values())
            error_count = sum(
                1 for errors in results.values() for error in errors if error.severity == ErrorSeverity.ERROR
            )
            warning_count = sum(
                1 for errors in results.values() for error in errors if error.severity == ErrorSeverity.WARNING
            )

            ui.warning(f"構文チェック完了", f"{len(results)} ファイルで {total_errors} 個の問題を発見")
            ui.dim(f"エラー: {error_count}, 警告: {warning_count}")
            print()
            print(report)

    def _output_json(self, results) -> None:
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


def create_check_syntax_command():
    """Create the check-syntax click command"""

    @click.command()
    @click.argument("files", nargs=-1, required=True)
    @click.option("-r", "--recursive", is_flag=True, help="ディレクトリを再帰的に検索")
    @click.option("--no-suggestions", is_flag=True, help="修正提案を表示しない")
    @click.option("--format", "output_format", type=click.Choice(["text", "json"]), default="text", help="出力形式")
    def check_syntax(files, recursive, no_suggestions, output_format):
        """Kumihan記法の構文をチェックします"""

        command = CheckSyntaxCommand()
        command.execute(
            list(files), recursive=recursive, show_suggestions=not no_suggestions, format_output=output_format
        )

    return check_syntax
