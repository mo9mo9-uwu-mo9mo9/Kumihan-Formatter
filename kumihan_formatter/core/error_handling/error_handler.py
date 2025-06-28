"""
エラーハンドラー - 例外処理とエラー表示
"""

from pathlib import Path
from typing import Any, Dict, List

from .error_factories import ErrorFactory
from .error_types import ErrorLevel, UserFriendlyError


class ErrorHandler:
    """
    エラーハンドラー（例外をユーザーフレンドリーエラーに変換）

    設計ドキュメント:
    - 記法仕様: /SPEC.md#エラーハンドリング・検証
    - アーキテクチャ: /CONTRIBUTING.md#アーキテクチャ概要
    - 依存関係: /docs/CLASS_DEPENDENCY_MAP.md

    関連クラス:
    - ErrorFactory: エラーオブジェクト生成
    - UserFriendlyError: エラー情報の表現
    - ErrorLevel: エラーレベル分類
    - console_ui: エラー表示UI

    責務:
    - 例外の捕捉とユーザーフレンドリーな変換
    - エラー履歴の管理と分析
    - コンソールUIでのエラー表示制御
    - 初心者向けの分かりやすいエラーメッセージ生成
    """

    def __init__(self, console_ui=None):
        """エラーハンドラを初期化"""
        self.console_ui = console_ui
        self._error_history: List[UserFriendlyError] = []

    def handle_exception(self, exception: Exception, context: Dict[str, Any] = None) -> UserFriendlyError:
        """例外をユーザーフレンドリーエラーに変換"""
        context = context or {}

        # ファイル関連エラー
        if isinstance(exception, FileNotFoundError):
            file_path = context.get("file_path", str(exception))
            return ErrorFactory.create_file_not_found_error(file_path)

        # エンコーディングエラー
        elif isinstance(exception, UnicodeDecodeError):
            file_path = context.get("file_path", "不明なファイル")
            return ErrorFactory.create_encoding_error(file_path)

        # 権限エラー
        elif isinstance(exception, PermissionError):
            file_path = context.get("file_path", str(exception))
            operation = context.get("operation", "アクセス")
            return ErrorFactory.create_permission_error(file_path, operation)

        # その他の例外
        else:
            return ErrorFactory.create_unknown_error(original_error=str(exception), context=context)

    def display_error(self, error: UserFriendlyError, verbose: bool = False) -> None:
        """エラーを画面に表示"""
        if not self.console_ui:
            print(f"[{error.error_code}] {error.user_message}")
            print(f"解決方法: {error.solution.quick_fix}")
            return

        # エラーレベル別の表示スタイル
        level_styles = {
            ErrorLevel.INFO: "blue",
            ErrorLevel.WARNING: "yellow",
            ErrorLevel.ERROR: "red",
            ErrorLevel.CRITICAL: "red on yellow",
        }

        style = level_styles.get(error.level, "red")

        # メインメッセージ
        self.console_ui.console.print(f"[{style}][エラー] {error.user_message}[/{style}]")

        # 解決方法
        self.console_ui.console.print(f"[green]💡 解決方法: {error.solution.quick_fix}[/green]")

        # 詳細な手順（verboseモード）
        if verbose and error.solution.detailed_steps:
            self.console_ui.console.print("\n[cyan]詳細な解決手順:[/cyan]")
            for step in error.solution.detailed_steps:
                self.console_ui.console.print(f"[dim]   {step}[/dim]")

        # 代替手段
        if error.solution.alternative_approaches:
            self.console_ui.console.print("\n[yellow]代替手段:[/yellow]")
            for approach in error.solution.alternative_approaches:
                self.console_ui.console.print(f"[dim]   • {approach}[/dim]")

        # 技術的詳細（verboseモード）
        if verbose and error.technical_details:
            self.console_ui.console.print(f"\n[dim]技術的詳細: {error.technical_details}[/dim]")

        # エラー履歴に追加
        self._error_history.append(error)

    def show_error_context(self, file_path: Path, line_number: int, error_line: str) -> None:
        """エラー箇所の前後コンテキストを表示"""
        if not self.console_ui:
            return

        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()

            self.console_ui.console.print("\n[red]📍 エラー発生箇所:[/red]")

            # 前後2行を表示
            start_line = max(0, line_number - 3)
            end_line = min(len(lines), line_number + 2)

            for i in range(start_line, end_line):
                line_content = lines[i] if i < len(lines) else ""
                line_num_display = i + 1

                if i == line_number - 1:  # エラー行
                    self.console_ui.console.print(f"[red]→ {line_num_display:3d}: {line_content}[/red]")
                else:
                    self.console_ui.console.print(f"[dim]  {line_num_display:3d}: {line_content}[/dim]")

        except Exception:
            # ファイル読み込みでエラーが発生した場合はスキップ
            pass

    def get_error_statistics(self) -> Dict[str, Any]:
        """エラー統計を取得"""
        if not self._error_history:
            return {}

        categories = {}
        levels = {}

        for error in self._error_history:
            categories[error.category.value] = categories.get(error.category.value, 0) + 1
            levels[error.level.value] = levels.get(error.level.value, 0) + 1

        return {
            "total_errors": len(self._error_history),
            "by_category": categories,
            "by_level": levels,
            "most_recent": self._error_history[-1].error_code if self._error_history else None,
        }
