"""
エラーレポートビルダー機能

エラーレポートの段階的構築の責任を担当
Issue #540対応 - error_report.py から分離
"""

from pathlib import Path
from typing import TYPE_CHECKING

from .error_types import (
    DetailedError,
    ErrorCategory,
    ErrorLocation,
    ErrorSeverity,
    FixSuggestion,
)

if TYPE_CHECKING:
    from .error_report import ErrorReport


class ErrorReportBuilder:
    """エラーレポートビルダー - エラーレポートの段階的構築"""

    def __init__(self, source_file: Path | None = None):
        from .error_report import ErrorReport

        self.report = ErrorReport(source_file)

    def add_syntax_error(
        self, line: int, message: str, suggestion: str | None = None
    ) -> "ErrorReportBuilder":
        """構文エラー追加"""
        error = DetailedError(
            error_id=f"syntax_{line}",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.SYNTAX,
            title="構文エラー",
            message=message,
            location=ErrorLocation(line=line),
        )

        if suggestion:
            error.fix_suggestions.append(FixSuggestion(description=suggestion))

        self.report.add_error(error)
        return self

    def add_keyword_error(
        self, line: int, keyword: str, suggestion: str | None = None
    ) -> "ErrorReportBuilder":
        """キーワードエラー追加"""
        error = DetailedError(
            error_id=f"keyword_{line}_{keyword}",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.KEYWORD,
            title="無効なキーワード",
            message=f"無効なキーワードが見つかりました: {keyword}",
            location=ErrorLocation(line=line),
        )

        if suggestion:
            error.fix_suggestions.append(FixSuggestion(description=suggestion))

        self.report.add_error(error)
        return self

    def build(self) -> "ErrorReport":
        """エラーレポートを構築"""
        return self.report
