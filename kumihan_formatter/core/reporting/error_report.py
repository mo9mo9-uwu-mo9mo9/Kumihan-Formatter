"""
エラーレポート機能

エラーの収集・集約の責任を担当（基本機能のみ）
Issue #540対応 - error_report.py から機能分離
"""

from datetime import datetime
from pathlib import Path

from .error_report_formatter import ErrorReportFormatter
from .error_report_output import ErrorReportOutput
from .error_types import (
    DetailedError,
    ErrorSeverity,
)


class ErrorReport:
    """エラーレポート統合クラス - エラー収集・分類・サマリー生成"""

    def __init__(self, source_file: Path | None = None):
        self.source_file = source_file
        self.errors: list[DetailedError] = []
        self.warnings: list[DetailedError] = []
        self.info: list[DetailedError] = []
        self.generation_time = datetime.now()

        # 機能クラスのインスタンス
        self._formatter = ErrorReportFormatter()
        self._output = ErrorReportOutput()

    def add_error(self, error: DetailedError) -> None:
        """エラーを追加"""
        if error.severity in [ErrorSeverity.ERROR, ErrorSeverity.CRITICAL]:
            self.errors.append(error)
        elif error.severity == ErrorSeverity.WARNING:
            self.warnings.append(error)
        else:
            self.info.append(error)

    def has_errors(self) -> bool:
        """エラーが存在するかチェック"""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """警告が存在するかチェック"""
        return len(self.warnings) > 0

    @property
    def error_count(self) -> int:
        """エラー数を取得"""
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        """警告数を取得"""
        return len(self.warnings)

    def get_total_count(self) -> int:
        """総問題数を取得"""
        return len(self.errors) + len(self.warnings) + len(self.info)

    def get_summary(self) -> str:
        """サマリー情報を取得"""
        error_count = len(self.errors)
        warning_count = len(self.warnings)
        info_count = len(self.info)

        parts = []
        if error_count > 0:
            parts.append(f"{error_count}個のエラー")
        if warning_count > 0:
            parts.append(f"{warning_count}個の警告")
        if info_count > 0:
            parts.append(f"{info_count}個の情報")

        if not parts:
            return "問題は見つかりませんでした"

        return "、".join(parts) + "が見つかりました"

    def to_console_output(self, show_info: bool = False) -> str:
        """コンソール表示用の文字列を生成"""
        return self._formatter.to_console_output(
            self.errors,
            self.warnings,
            self.info,
            self.source_file,
            self.generation_time,
            show_info,
        )

    def to_file_report(self, output_path: Path) -> None:
        """詳細レポートをテキストファイルに出力"""
        self._output.to_file_report(
            self.errors,
            self.warnings,
            self.info,
            self.source_file,
            self.generation_time,
            output_path,
        )
