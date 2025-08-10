"""
変換コマンド - 検証機能

ファイル検証・サイズチェック・構文チェックの責任を担当
Issue #319対応 - convert.py から分離
"""

import sys
from pathlib import Path
from typing import Any

from ...core.file_ops import FileOperations, PathValidator

# Reporting module removed during cleanup - using simplified error reporting
# Error types module removed during cleanup - using simplified error handling
from ...core.syntax import check_files
from ...ui.console_ui import get_console_ui


class ConvertValidator:
    """変換コマンド用バリデーター

    責任: 入力ファイルの検証・構文チェック
    """

    def __init__(self) -> None:
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
        from ...core.file_path_utilities import FilePathUtilities

        size_info = FilePathUtilities.get_file_size_info(input_path)

        if size_info["is_large"]:
            # 大きなファイルの警告を表示
            if not self.file_ops.check_large_file_warning(input_path):
                get_console_ui().info("処理を中断しました")
                return False

            # 推定処理時間を表示
            estimated_time = FilePathUtilities.estimate_processing_time(size_info["size_mb"])
            get_console_ui().hint(f"推定処理時間: {estimated_time}")

        return True

    def perform_syntax_check(self, input_path: Path) -> dict[str, Any]:
        """詳細な構文チェックを実行"""
        get_console_ui().info("記法チェック", f"{input_path.name} の記法を検証中...")

        try:
            # 構文チェック実行
            results = check_files([input_path], verbose=False)

            # 辞書形式のエラーレポートに変換
            error_report: dict[str, Any] = {
                "source_file": str(input_path),
                "errors": [],
                "has_errors": False,
            }

            if results:
                for file_path, errors in results.items():
                    for error in errors:
                        # 辞書形式のエラー情報に変換
                        error_info = self._convert_to_error_info(error, file_path)
                        error_report["errors"].append(error_info)
                        error_report["has_errors"] = True

            return error_report

        except Exception as e:
            get_console_ui().error("記法チェック中にエラーが発生しました", str(e))
            # 空のレポートを返す
            return {"source_file": str(input_path), "errors": [], "has_errors": False}

    def _convert_to_error_info(self, error: Any, file_path: Path) -> dict[str, Any]:
        """エラーオブジェクトを辞書形式の情報に変換"""
        # エラーオブジェクトから行番号を安全に取得
        line_number = None
        if hasattr(error, "line"):
            line_number = error.line
        elif hasattr(error, "lineno"):
            line_number = error.lineno

        # メッセージの安全な取得
        message = error.message if hasattr(error, "message") else str(error)

        # 重要度の判定
        severity = "error"
        if hasattr(error, "severity"):
            severity = "error" if str(error.severity).lower() == "error" else "warning"

        return {
            "error_id": f"syntax_{line_number or 0}_{hash(message)}",
            "severity": severity,
            "category": "syntax",
            "title": "記法エラー",
            "message": message,
            "file_path": str(file_path),
            "line_number": line_number,
        }

    def save_error_report(
        self, error_report: dict[str, Any], input_path: Path, output_dir: str
    ) -> None:
        """エラーレポートをファイルに保存"""
        try:
            output_path = Path(output_dir) / f"{input_path.stem}_errors.txt"
            self._save_error_report_to_file(error_report, output_path)
            get_console_ui().info("エラーレポート", f"詳細レポートを保存しました: {output_path}")
        except Exception as e:
            get_console_ui().warning("エラーレポートの保存に失敗しました", str(e))

    def _save_error_report_to_file(self, error_report: dict[str, Any], output_path: Path) -> None:
        """エラーレポートを実際にファイルに書き出し"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"エラーレポート: {error_report['source_file']}\n")
            f.write("=" * 50 + "\n\n")

            if not error_report["has_errors"]:
                f.write("エラーは検出されませんでした。\n")
            else:
                f.write(f"検出されたエラー数: {len(error_report['errors'])}\n\n")

                for i, error in enumerate(error_report["errors"], 1):
                    f.write(f"エラー {i}:\n")
                    f.write(f"  重要度: {error['severity']}\n")
                    f.write(f"  カテゴリ: {error['category']}\n")
                    f.write(f"  タイトル: {error['title']}\n")
                    f.write(f"  メッセージ: {error['message']}\n")
                    f.write(f"  ファイル: {error['file_path']}\n")
                    if error["line_number"]:
                        f.write(f"  行番号: {error['line_number']}\n")
                    f.write("\n")
