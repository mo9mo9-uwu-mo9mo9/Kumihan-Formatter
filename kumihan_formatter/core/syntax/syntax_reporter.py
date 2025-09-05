"""Error reporting and formatting for syntax validation

This module handles formatting error reports, outputting results in different
formats (text, JSON), and managing error presentation.
"""

import json
import sys
from pathlib import Path
import io

from .syntax_errors import ErrorSeverity, SyntaxError, ErrorTypes

# NOTE: 実装が必要なモジュール - Issue #1217対応
# from .syntax_validator import KumihanSyntaxValidator


class SyntaxReporter:
    """Handles formatting and reporting of syntax validation results"""

    @staticmethod
    def check_files(
        file_paths: list[Path], verbose: bool = False
    ) -> dict[str, list[SyntaxError]]:
        """指定ファイル群の最小構文検証を実行し、エラー一覧を返す。

        ルール（最小実装）:
        - ブロック記法: 開始行（例: "#見出し1#" など）と終了行（"##"）の対応を検証。
          未対応の終了（UNMATCHED_BLOCK_END）/未クローズ（UNCLOSED_BLOCK）を検出。
        - 行内バッククォート: 逆数個（奇数）の場合はWARNING（INVALID_SYNTAX）。
        - 空のキーワード: "# #" のように中身が空の場合はWARNING（EMPTY_KEYWORD）。
        - タブ文字: INFO として通知（改善提案）。
        """
        results: dict[str, list[SyntaxError]] = {}

        for file_path in file_paths:
            if verbose:
                print(f"Checking {file_path}...")

            try:
                text = Path(file_path).read_text(encoding="utf-8")
            except UnicodeDecodeError:
                results[str(file_path)] = [
                    SyntaxError(
                        line_number=1,
                        column=1,
                        severity=ErrorSeverity.ERROR,
                        error_type=ErrorTypes.ENCODING,
                        message="UTF-8として読み込めませんでした",
                        context="encoding",
                        suggestion="ファイルのエンコーディングをUTF-8に変換してください",
                    )
                ]
                continue
            except Exception as e:
                results[str(file_path)] = [
                    SyntaxError(
                        line_number=1,
                        column=1,
                        severity=ErrorSeverity.ERROR,
                        error_type=ErrorTypes.FILE_NOT_FOUND,
                        message=f"ファイルを読み込めません: {e}",
                        context=str(file_path),
                    )
                ]
                continue

            errors = SyntaxReporter._validate_text(text)
            if errors:
                results[str(file_path)] = errors

        return results

    @staticmethod
    def _validate_text(text: str) -> list[SyntaxError]:
        errors: list[SyntaxError] = []
        open_stack: list[tuple[int, str]] = []  # (line_no, line_text)

        lines = text.splitlines()
        for idx, raw in enumerate(lines, start=1):
            line = raw.rstrip("\n")

            # タブ文字（情報）
            if "\t" in line:
                errors.append(
                    SyntaxError(
                        line_number=idx,
                        column=line.find("\t") + 1,
                        severity=ErrorSeverity.INFO,
                        error_type=ErrorTypes.SYNTAX_ERROR,
                        message="タブ文字が含まれています",
                        context=line.strip(),
                        suggestion="スペースに置き換えることを推奨します",
                    )
                )

            s = line.strip()

            # 空のキーワード（例: "# #"）
            if s.startswith("#") and s.endswith("#") and len(s) >= 2:
                inner = s.strip("#").strip()
                if inner == "":
                    errors.append(
                        SyntaxError(
                            line_number=idx,
                            column=1,
                            severity=ErrorSeverity.WARNING,
                            error_type=ErrorTypes.EMPTY_KEYWORD,
                            message="空のキーワード行です",
                            context=s,
                            suggestion="キーワード名を指定するか、この行を削除してください",
                        )
                    )

            # ブロック開始（例: "#見出し1#" など、閉じ行は"##"）
            if (
                s.startswith("#")
                and not s.startswith("##")
                and s.endswith("#")
                and s != "#"
            ):
                open_stack.append((idx, s))
                continue

            # ブロック終了
            if s == "##":
                if not open_stack:
                    errors.append(
                        SyntaxError(
                            line_number=idx,
                            column=1,
                            severity=ErrorSeverity.ERROR,
                            error_type=ErrorTypes.UNMATCHED_BLOCK_END,
                            message="対応する開始行のない終了マーカーです",
                            context=s,
                            suggestion="直前の開始行（#...#）を確認してください",
                        )
                    )
                else:
                    open_stack.pop()

            # 行内バッククォートの未対応（奇数個）
            if line.count("`") % 2 == 1:
                errors.append(
                    SyntaxError(
                        line_number=idx,
                        column=line.find("`") + 1 if "`" in line else 1,
                        severity=ErrorSeverity.WARNING,
                        error_type=ErrorTypes.INVALID_SYNTAX,
                        message="バッククォートの対応が取れていません",
                        context=line.strip(),
                        suggestion="` をもう一つ追加するか削除してください",
                    )
                )

        # 未クローズのブロックを報告
        for ln, opener in open_stack:
            errors.append(
                SyntaxError(
                    line_number=ln,
                    column=1,
                    severity=ErrorSeverity.ERROR,
                    error_type=ErrorTypes.UNCLOSED_BLOCK,
                    message="ブロックが閉じられていません（対応する '##' が必要）",
                    context=opener,
                    suggestion="対応する終了行 '##' を追加してください",
                )
            )

        return errors

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

        # Format output（severityの大文字小文字差を吸収）
        output_lines: list[str] = []
        icons = {
            ErrorSeverity.ERROR: "❌",
            ErrorSeverity.WARNING: "⚠️",
            ErrorSeverity.INFO: "ℹ️",
        }
        for severity in [ErrorSeverity.ERROR, ErrorSeverity.WARNING, ErrorSeverity.INFO]:
            if severity in by_severity:
                for error in by_severity[severity]:
                    icon = icons.get(severity, "•")
                    output_lines.append(f"  {icon} Line {error.line_number}: {error.message}")
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
                sev = error.severity
                # Enum → 上位互換の大文字キー
                key = (
                    "ERROR"
                    if sev == ErrorSeverity.ERROR
                    else "WARNING"
                    if sev == ErrorSeverity.WARNING
                    else "INFO"
                )
                counts[key] += 1
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
                f"   エラー: {counts['ERROR']}, 警告: {counts['WARNING']}, "
                f"情報: {counts['INFO']}"
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
