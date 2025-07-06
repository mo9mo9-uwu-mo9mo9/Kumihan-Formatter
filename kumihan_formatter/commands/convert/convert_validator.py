"""
変換コマンド - 検証機能

ファイル検証・サイズチェック・構文チェックの責任を担当
Issue #319対応 - convert.py から分離
"""

import sys
from pathlib import Path

from ...core.file_ops import FileOperations, PathValidator
from ...core.reporting import ErrorReport
from ...core.syntax import check_files
from ...ui.console_ui import get_console_ui


class ConvertValidator:
    """変換コマンド用バリデーター

    責任: 入力ファイルの検証・構文チェック
    """

    def __init__(self):
        self.file_ops = FileOperations(ui=get_console_ui())
        self.path_validator = PathValidator()

    def validate_input_file(self, input_file: str) -> Path:
        """入力ファイルを検証"""
        if not input_file:
            get_console_ui().error("入力ファイルが指定されていません")
            get_console_ui().dim(
                "テストファイル生成には --generate-test オプションを使用してください"
            )
            sys.exit(1)

        return self.path_validator.validate_input_file(input_file)

    def check_file_size(self, input_path: Path) -> bool:
        """ファイルサイズをチェックし、必要に応じて警告を表示"""
        size_info = self.file_ops.get_file_size_info(input_path)

        if size_info["is_large"]:
            # 大きなファイルの警告を表示
            if not self.file_ops.check_large_file_warning(input_path):
                get_console_ui().info("処理を中断しました")
                return False

            # 推定処理時間を表示
            estimated_time = self.file_ops.estimate_processing_time(
                size_info["size_mb"]
            )
            get_console_ui().hint(f"推定処理時間: {estimated_time}")

        return True

    def perform_syntax_check(self, input_path: Path) -> ErrorReport:
        """詳細な構文チェックを実行"""
        get_console_ui().info("記法チェック", f"{input_path.name} の記法を検証中...")

        try:
            # 構文チェック実行
            results = check_files([input_path], verbose=False)

            # ErrorReport形式に変換
            error_report = ErrorReport(source_file=input_path)

            if results:
                for file_path, errors in results.items():
                    for error in errors:
                        # 旧形式から新形式に変換
                        detailed_error = self._convert_to_detailed_error(
                            error, file_path
                        )
                        error_report.add_error(detailed_error)

            return error_report

        except Exception as e:
            get_console_ui().error("記法チェック中にエラーが発生しました", str(e))
            # 空のレポートを返す
            return ErrorReport(source_file=input_path)

    def _convert_to_detailed_error(self, error, file_path: Path):
        """旧エラー形式から新DetailedError形式に変換"""
        from ...core.reporting import (
            DetailedError,
            ErrorCategory,
            ErrorLocation,
            ErrorSeverity,
        )

        return DetailedError(
            error_id=f"syntax_{error.line}_{hash(error.message)}",
            severity=(
                ErrorSeverity.ERROR
                if error.severity == ErrorSeverity.ERROR
                else ErrorSeverity.WARNING
            ),
            category=ErrorCategory.SYNTAX,
            title="記法エラー",
            message=error.message,
            file_path=file_path,
            location=ErrorLocation(line=error.line) if hasattr(error, "line") else None,
        )

    def save_error_report(
        self, error_report: ErrorReport, input_path: Path, output_dir: str
    ) -> None:
        """エラーレポートをファイルに保存"""
        try:
            output_path = Path(output_dir) / f"{input_path.stem}_errors.txt"
            error_report.to_file_report(output_path)
            get_console_ui().info(
                "エラーレポート", f"詳細レポートを保存しました: {output_path}"
            )
        except Exception as e:
            get_console_ui().warning("エラーレポートの保存に失敗しました", str(e))
