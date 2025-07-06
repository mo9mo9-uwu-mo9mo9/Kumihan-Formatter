"""
統一エラーハンドラー - Issue #401対応

全コンポーネントで一貫したエラーハンドリングを提供する統合システム。
既存のerror_handlingとcommon/error_frameworkを統合。
"""

import traceback
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from ..common.error_framework import ErrorContext
from ..utilities.logger import get_logger
from .error_factories import ErrorFactory
from .error_types import ErrorCategory, ErrorLevel, UserFriendlyError
from .smart_suggestions import SmartSuggestions


class UnifiedErrorHandler:
    """
    統一エラーハンドラー - プロジェクト全体で一貫したエラー処理を提供

    設計ドキュメント:
    - Issue #401: エラーハンドリングの強化と統合
    - 既存システムの統合と一貫性確保
    - ユーザーフレンドリーなエラーメッセージ

    機能:
    - Parser、Renderer、File系の統一エラー処理
    - 自動修正提案とユーザーガイダンス
    - エラーコンテキスト管理
    - 段階的回復戦略
    """

    def __init__(self, console_ui=None, enable_logging: bool = True):
        """統一エラーハンドラーを初期化

        Args:
            console_ui: UI表示用インスタンス
            enable_logging: ログ出力を有効にするか
        """
        self.console_ui = console_ui
        self.enable_logging = enable_logging
        self.logger = get_logger(__name__) if enable_logging else None

        # エラー統計とヒストリー
        self._error_history: List[UserFriendlyError] = []
        self._error_stats: Dict[str, int] = {}
        self._context_stack: List[ErrorContext] = []

        # 回復戦略設定
        self._max_recovery_attempts = 3
        self._recovery_callbacks: Dict[str, List[Callable]] = {}

        if self.logger:
            self.logger.info("UnifiedErrorHandler initialized")

    @contextmanager
    def error_context(
        self,
        operation: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        **context_data,
    ):
        """エラーコンテキストマネージャー

        Args:
            operation: 実行中の操作名
            file_path: 対象ファイルパス
            line_number: 行番号
            **context_data: 追加のコンテキスト情報
        """
        context = ErrorContext(
            file_path=file_path,
            line_number=line_number,
            operation=operation,
            system_info=context_data,
            timestamp=datetime.now(),
        )

        self._context_stack.append(context)

        try:
            if self.logger:
                self.logger.debug(f"Starting operation: {operation}")
            yield context

        except Exception as e:
            # エラーが発生した場合、自動的にハンドリング
            error = self.handle_exception(e, context.__dict__)

            # 回復を試行
            if not self._attempt_recovery(error, context):
                # 回復に失敗した場合は再発生
                raise

        finally:
            self._context_stack.pop()
            if self.logger:
                self.logger.debug(f"Completed operation: {operation}")

    def handle_exception(
        self, exception: Exception, context: Optional[Dict[str, Any]] = None
    ) -> UserFriendlyError:
        """例外を統一的にハンドリング

        Args:
            exception: 発生した例外
            context: エラーコンテキスト

        Returns:
            UserFriendlyError: 統一されたエラーオブジェクト
        """
        context = context or {}

        # 現在のコンテキストスタックから情報を取得
        if self._context_stack:
            current_context = self._context_stack[-1]
            context.update(
                {
                    "file_path": current_context.file_path,
                    "line_number": current_context.line_number,
                    "operation": current_context.operation,
                }
            )

        if self.logger:
            self.logger.error(
                f"Handling exception: {type(exception).__name__} - {str(exception)}"
            )
            self.logger.debug(f"Exception context: {context}")
            self.logger.debug(f"Traceback: {traceback.format_exc()}")

        # 例外タイプ別の処理
        error = self._create_error_from_exception(exception, context)

        # エラー統計を更新
        self._update_error_stats(error)

        # エラー履歴に追加
        self._error_history.append(error)

        return error

    def _create_error_from_exception(
        self, exception: Exception, context: Dict[str, Any]
    ) -> UserFriendlyError:
        """例外からUserFriendlyErrorを生成"""

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

        # 構文エラー（Parser関連）
        elif isinstance(exception, SyntaxError):
            return self._handle_syntax_error(exception, context)

        # 値エラー（Validation関連）
        elif isinstance(exception, ValueError):
            return self._handle_value_error(exception, context)

        # IOエラー（File系）
        elif isinstance(exception, (IOError, OSError)):
            return self._handle_io_error(exception, context)

        # その他の例外
        else:
            return ErrorFactory.create_unknown_error(
                original_error=str(exception), context=context
            )

    def _handle_syntax_error(
        self, exception: SyntaxError, context: Dict[str, Any]
    ) -> UserFriendlyError:
        """構文エラーの専用ハンドリング"""
        line_num = getattr(exception, "lineno", context.get("line_number", 0))
        text = getattr(exception, "text", str(exception))
        file_path = context.get("file_path")

        return ErrorFactory.create_syntax_error(
            line_num=line_num, invalid_content=text, file_path=file_path
        )

    def _handle_value_error(
        self, exception: ValueError, context: Dict[str, Any]
    ) -> UserFriendlyError:
        """値エラーの専用ハンドリング"""
        error_msg = str(exception)

        # Kumihan記法関連のエラーかチェック
        if any(
            keyword in error_msg.lower() for keyword in ["記法", "marker", "keyword"]
        ):
            # スマート提案を生成
            suggestions = SmartSuggestions.suggest_keyword(error_msg)

            return UserFriendlyError(
                error_code="E010",
                level=ErrorLevel.WARNING,
                category=ErrorCategory.SYNTAX,
                user_message=f"💭 記法の使用方法に問題があります: {error_msg}",
                solution=self._create_suggestion_solution(suggestions),
                context=context,
            )

        # 一般的な値エラー
        return UserFriendlyError(
            error_code="E011",
            level=ErrorLevel.ERROR,
            category=ErrorCategory.SYSTEM,
            user_message=f"🔧 入力値に問題があります: {error_msg}",
            solution=self._create_generic_solution("入力値を確認してください"),
            context=context,
        )

    def _handle_io_error(
        self, exception: Union[IOError, OSError], context: Dict[str, Any]
    ) -> UserFriendlyError:
        """I/Oエラーの専用ハンドリング"""
        _ = context.get("file_path", "不明なファイル")
        operation = context.get("operation", "ファイル操作")

        return UserFriendlyError(
            error_code="E012",
            level=ErrorLevel.ERROR,
            category=ErrorCategory.FILE_SYSTEM,
            user_message=f"📂 {operation}中にファイルエラーが発生しました",
            solution=self._create_file_operation_solution(str(exception)),
            technical_details=str(exception),
            context=context,
        )

    def _create_suggestion_solution(self, suggestions: List[str]):
        """スマート提案からSolutionを生成"""
        if suggestions:
            quick_fix = f"もしかして: {', '.join(suggestions[:3])}"
            detailed_steps = [
                f"「{suggestion}」を試してください" for suggestion in suggestions[:5]
            ]
        else:
            quick_fix = "Kumihan記法ガイドを確認してください"
            detailed_steps = [
                "記法の基本ルールを確認",
                "有効なキーワード一覧を参照",
                "記法の組み合わせ方を確認",
            ]

        from .error_types import ErrorSolution

        return ErrorSolution(
            quick_fix=quick_fix,
            detailed_steps=detailed_steps,
            external_links=["記法ガイド: SPEC.md を参照"],
        )

    def _create_generic_solution(self, quick_fix: str):
        """汎用的なSolutionを生成"""
        from .error_types import ErrorSolution

        return ErrorSolution(
            quick_fix=quick_fix,
            detailed_steps=[
                "エラーメッセージの詳細を確認",
                "入力ファイルの内容を確認",
                "必要に応じてGitHubでIssueを報告",
            ],
        )

    def _create_file_operation_solution(self, error_details: str):
        """ファイル操作エラー用のSolutionを生成"""
        from .error_types import ErrorSolution

        return ErrorSolution(
            quick_fix="ファイルの状態と権限を確認してください",
            detailed_steps=[
                "ファイルが他のアプリケーションで開かれていないか確認",
                "ファイルの読み取り/書き込み権限を確認",
                "ディスクの空き容量を確認",
                "ファイルパスに無効な文字がないか確認",
            ],
            alternative_approaches=[
                "ファイルを別の場所にコピーして再実行",
                "管理者権限で実行を試す",
            ],
        )

    def display_error(
        self,
        error: UserFriendlyError,
        verbose: bool = False,
        show_recovery_options: bool = True,
    ) -> None:
        """エラーを統一的に表示

        Args:
            error: 表示するエラー
            verbose: 詳細表示モード
            show_recovery_options: 回復オプションを表示するか
        """
        if self.logger:
            self.logger.info(
                f"Displaying error: {error.error_code} - {error.user_message}"
            )

        if not self.console_ui:
            # コンソールUI未使用時のフォールバック
            self._display_error_fallback(error, verbose)
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
        self.console_ui.console.print(
            f"[{style}][エラー] {error.user_message}[/{style}]"
        )

        # 解決方法
        self.console_ui.console.print(
            f"[green]💡 解決方法: {error.solution.quick_fix}[/green]"
        )

        # 詳細な手順（verboseモード）
        if verbose and error.solution.detailed_steps:
            self.console_ui.console.print("\n[cyan]詳細な解決手順:[/cyan]")
            for i, step in enumerate(error.solution.detailed_steps, 1):
                self.console_ui.console.print(f"[dim]   {i}. {step}[/dim]")

        # 代替手段
        if error.solution.alternative_approaches:
            self.console_ui.console.print("\n[yellow]代替手段:[/yellow]")
            for approach in error.solution.alternative_approaches:
                self.console_ui.console.print(f"[dim]   • {approach}[/dim]")

        # 回復オプション
        if show_recovery_options:
            recovery_options = self._get_recovery_options(error)
            if recovery_options:
                self.console_ui.console.print(
                    "\n[magenta]自動回復オプション:[/magenta]"
                )
                for option in recovery_options:
                    self.console_ui.console.print(f"[dim]   🔧 {option}[/dim]")

        # 技術的詳細（verboseモード）
        if verbose and error.technical_details:
            self.console_ui.console.print(
                f"\n[dim]技術的詳細: {error.technical_details}[/dim]"
            )

    def _display_error_fallback(self, error: UserFriendlyError, verbose: bool):
        """console_ui未使用時のフォールバック表示"""
        print(f"[{error.error_code}] {error.user_message}")
        print(f"解決方法: {error.solution.quick_fix}")

        if verbose and error.solution.detailed_steps:
            print("\n詳細な解決手順:")
            for i, step in enumerate(error.solution.detailed_steps, 1):
                print(f"   {i}. {step}")

    def _attempt_recovery(
        self, error: UserFriendlyError, context: ErrorContext
    ) -> bool:
        """エラーからの自動回復を試行

        Args:
            error: 回復対象のエラー
            context: エラーコンテキスト

        Returns:
            bool: 回復成功時True
        """
        error_type = error.category.value

        # 登録されている回復コールバックを実行
        if error_type in self._recovery_callbacks:
            for callback in self._recovery_callbacks[error_type]:
                try:
                    if callback(error, context):
                        if self.logger:
                            self.logger.info(
                                f"Recovery successful for {error.error_code}"
                            )
                        return True
                except Exception as recovery_error:
                    if self.logger:
                        self.logger.warning(
                            f"Recovery callback failed: {recovery_error}"
                        )

        return False

    def register_recovery_callback(
        self,
        error_category: str,
        callback: Callable[[UserFriendlyError, ErrorContext], bool],
    ) -> None:
        """回復コールバックを登録

        Args:
            error_category: エラーカテゴリ
            callback: 回復処理を行うコールバック関数
        """
        if error_category not in self._recovery_callbacks:
            self._recovery_callbacks[error_category] = []

        self._recovery_callbacks[error_category].append(callback)

        if self.logger:
            self.logger.debug(f"Recovery callback registered for {error_category}")

    def _get_recovery_options(self, error: UserFriendlyError) -> List[str]:
        """エラーに対する回復オプションを取得"""
        options = []

        # カテゴリ別の回復オプション
        if error.category == ErrorCategory.FILE_SYSTEM:
            options.extend(
                [
                    "ファイルの自動エンコーディング変換",
                    "一時ファイルでの処理継続",
                    "バックアップファイルからの復元",
                ]
            )
        elif error.category == ErrorCategory.SYNTAX:
            options.extend(
                ["記法の自動修正提案", "類似パターンからの推測", "部分的な変換継続"]
            )
        elif error.category == ErrorCategory.ENCODING:
            options.extend(["文字エンコーディングの自動検出", "UTF-8への自動変換"])

        return options

    def _update_error_stats(self, error: UserFriendlyError) -> None:
        """エラー統計を更新"""
        error_key = f"{error.category.value}_{error.level.value}"
        self._error_stats[error_key] = self._error_stats.get(error_key, 0) + 1

    def get_error_statistics(self) -> Dict[str, Any]:
        """エラー統計情報を取得"""
        total_errors = len(self._error_history)

        if total_errors == 0:
            return {"total_errors": 0}

        # カテゴリ別統計
        categories = {}
        levels = {}

        for error in self._error_history:
            categories[error.category.value] = (
                categories.get(error.category.value, 0) + 1
            )
            levels[error.level.value] = levels.get(error.level.value, 0) + 1

        # 最頻エラーを特定
        most_common_category = max(categories, key=categories.get)
        most_common_level = max(levels, key=levels.get)

        return {
            "total_errors": total_errors,
            "by_category": categories,
            "by_level": levels,
            "most_common_category": most_common_category,
            "most_common_level": most_common_level,
            "recent_errors": [
                {
                    "code": error.error_code,
                    "message": error.user_message,
                    "category": error.category.value,
                    "level": error.level.value,
                }
                for error in self._error_history[-5:]  # 最新5件
            ],
        }

    def clear_error_history(self) -> None:
        """エラー履歴をクリア"""
        self._error_history.clear()
        self._error_stats.clear()

        if self.logger:
            self.logger.info("Error history cleared")

    def export_error_log(self, file_path: Path) -> bool:
        """エラーログをファイルにエクスポート

        Args:
            file_path: エクスポート先ファイルパス

        Returns:
            bool: エクスポート成功時True
        """
        try:
            import json

            log_data = {
                "exported_at": datetime.now().isoformat(),
                "statistics": self.get_error_statistics(),
                "errors": [
                    {
                        "error_code": error.error_code,
                        "level": error.level.value,
                        "category": error.category.value,
                        "user_message": error.user_message,
                        "technical_details": error.technical_details,
                        "context": error.context,
                    }
                    for error in self._error_history
                ],
            }

            file_path.write_text(
                json.dumps(log_data, ensure_ascii=False, indent=2), encoding="utf-8"
            )

            if self.logger:
                self.logger.info(f"Error log exported to {file_path}")

            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to export error log: {e}")
            return False


# グローバルインスタンス（必要に応じて）
_global_handler: Optional[UnifiedErrorHandler] = None


def get_global_handler() -> UnifiedErrorHandler:
    """グローバル統一エラーハンドラーを取得（遅延初期化）"""
    global _global_handler
    if _global_handler is None:
        _global_handler = UnifiedErrorHandler()
    return _global_handler


def set_global_handler(handler: UnifiedErrorHandler) -> None:
    """グローバル統一エラーハンドラーを設定"""
    global _global_handler
    _global_handler = handler
