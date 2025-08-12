"""Error reporting and formatting for syntax validation

This module handles formatting error reports, outputting results in different
formats (text, JSON), and managing error presentation.
"""

import json
import sys
from pathlib import Path

from .syntax_errors import ErrorSeverity, SyntaxError
from .syntax_validator import KumihanSyntaxValidator


class SyntaxReporter:
    """Handles formatting and reporting of syntax validation results"""

    @staticmethod
    def check_files(
        file_paths: list[Path], verbose: bool = False
    ) -> dict[str, list[SyntaxError]]:
        """Check multiple files for syntax errors"""
        validator = KumihanSyntaxValidator()
        results = {}

        for file_path in file_paths:
            if verbose:
                print(f"Checking {file_path}...")

            errors = validator.validate_file(file_path)
            if errors:
                results[str(file_path)] = errors

        return results

    @staticmethod
    def format_error_report(
        results: dict[str, list[SyntaxError]], show_suggestions: bool = True
    ) -> str:
        """Format error report as string"""
        if not results:
            return "✅ 記法エラーは見つかりませんでした。"

        # Group errors by severity
        by_severity: dict[ErrorSeverity, list[SyntaxError]] = {}
        for file_errors in results.values():
            for error in file_errors:
                if error.severity not in by_severity:
                    by_severity[error.severity] = []
                by_severity[error.severity].append(error)

        # Format output
        output_lines = []
        for severity in [
            ErrorSeverity.ERROR,
            ErrorSeverity.WARNING,
            ErrorSeverity.INFO,
        ]:
            if severity in by_severity:
                for error in by_severity[severity]:
                    icon = {"ERROR": "❌", "WARNING": "⚠️", "INFO": "ℹ️"}[severity.value]
                    output_lines.append(
                        f"  {icon} Line {error.line_number}: {error.message}"
                    )
                    if error.context:
                        output_lines.append(f"     Context: {error.context}")

        return "\n".join(output_lines)

    @staticmethod
    def format_json_report(results: dict[str, list[SyntaxError]]) -> str:
        """Format error report as JSON"""
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
        return json.dumps(json_results, ensure_ascii=False, indent=2)

    @staticmethod
    def get_error_counts(results: dict[str, list[SyntaxError]]) -> dict[str, int]:
        """Get counts of errors by severity"""
        counts = {"ERROR": 0, "WARNING": 0, "INFO": 0, "TOTAL": 0}

        for errors in results.values():
            for error in errors:
                counts[error.severity.value] += 1
                counts["TOTAL"] += 1

        return counts

    @staticmethod
    def should_exit_with_error(results: dict[str, list[SyntaxError]]) -> bool:
        """Determine if process should exit with error code"""
        error_count = sum(
            1
            for errors in results.values()
            for error in errors
            if error.severity == ErrorSeverity.ERROR
        )
        return error_count > 0

    @staticmethod
    def print_summary(results: dict[str, list[SyntaxError]]) -> None:
        """Print summary of validation results"""
        if not results:
            print("✅ 記法エラーは見つかりませんでした。")
        else:
            counts = SyntaxReporter.get_error_counts(results)
            print(f"🔍 {len(results)} ファイルで {counts['TOTAL']} 個の問題を発見")
            print(
                f"   エラー: {counts['ERROR']}, 警告: {counts['WARNING']}, 情報: {counts['INFO']}"
            )


def main() -> None:
    """CLI entry point for syntax checker"""
    import argparse

    parser = argparse.ArgumentParser(description="Kumihan記法 構文チェッカー")
    parser.add_argument("files", nargs="+", type=Path, help="チェックするファイルパス")
    parser.add_argument("-v", "--verbose", action="store_true", help="詳細な出力")
    parser.add_argument(
        "--no-suggestions", action="store_true", help="修正提案を表示しない"
    )
    parser.add_argument(
        "--format", choices=["text", "json"], default="text", help="出力形式"
    )

    args = parser.parse_args()

    # Check files
    results = SyntaxReporter.check_files(args.files, args.verbose)

    if args.format == "json":
        print(SyntaxReporter.format_json_report(results))
    else:
        print(SyntaxReporter.format_error_report(results, not args.no_suggestions))

    # Exit with appropriate code
    if SyntaxReporter.should_exit_with_error(results):
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
