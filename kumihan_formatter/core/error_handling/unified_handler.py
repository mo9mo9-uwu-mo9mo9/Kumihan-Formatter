"""
統一エラーハンドラー - Issue #401対応

全コンポーネントで一貫したエラーハンドリングを提供する統合システム。
既存のerror_handlingとcommon/error_frameworkを統合。

Single Responsibility Principle適用: 567行から280行に削減
Issue #476 Phase5対応 - 機能別分割完了
"""

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Generator

from ..common.error_framework import ErrorContext
from ..utilities.logger import get_logger

# 分割済み機能のインポート
from .error_display import ErrorDisplay
from .error_factories import ErrorFactory
from .error_recovery import ErrorRecovery
from .error_statistics import ErrorStatistics
from .error_types import UserFriendlyError


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

    def __init__(self, console_ui: Any = None, enable_logging: bool = True) -> None:
        """統一エラーハンドラーを初期化

        Args:
            console_ui: UI表示用インスタンス
            enable_logging: ログ出力を有効にするか
        """
        self.console_ui = console_ui
        self.enable_logging = enable_logging
        self.logger = get_logger(__name__) if enable_logging else None

        # 分割された機能コンポーネント
        self.display = ErrorDisplay(console_ui, enable_logging)
        self.recovery = ErrorRecovery()
        self.statistics = ErrorStatistics(enable_logging)

        # 依存サービス
        self.error_factory = ErrorFactory()

    @contextmanager
    def error_context(
        self,
        operation: str,
        context: dict[str, Any] | None = None,
        auto_recover: bool = False,
    ) -> Generator[ErrorContext, None, None]:
        """エラーコンテキストマネージャー

        Args:
            operation: 実行中の操作名
            context: 操作コンテキスト
            auto_recover: 自動回復を試行するか

        Yields:
            ErrorContext: エラーコンテキスト
        """
        error_context = ErrorContext(operation=operation, system_info=context or {})

        try:
            yield error_context
        except Exception as e:
            # エラーをキャッチして統一処理
            user_error = self._create_error_from_exception(e, error_context)

            # 自動回復の試行
            if auto_recover:
                success = self.recovery.attempt_recovery(user_error)
                if success:
                    if self.logger:
                        self.logger.info("Auto-recovery successful")
                    return
                else:
                    if self.logger:
                        self.logger.warning("Auto-recovery failed")

            # エラー表示と処理
            self.handle_exception(e, error_context)
            raise

    def handle_exception(
        self,
        exception: Exception,
        context: ErrorContext | None = None,
        show_ui: bool = True,
        attempt_recovery: bool = True,
    ) -> UserFriendlyError:
        """例外を統一的に処理

        Args:
            exception: 処理する例外
            context: エラーコンテキスト
            show_ui: UI表示を行うか
            attempt_recovery: 回復を試行するか

        Returns:
            UserFriendlyError: 処理されたエラー
        """
        # UserFriendlyErrorを作成
        user_error = self._create_error_from_exception(exception, context)

        # 統計情報の更新
        self.statistics.update_error_stats(user_error)

        # UI表示
        if show_ui:
            self.display.display_error(user_error, show_suggestions=True)

        # 回復の試行
        if attempt_recovery:
            success = self.recovery.attempt_recovery(user_error)
            if success and self.logger:
                self.logger.info("Recovery successful")

        return user_error

    def _create_error_from_exception(
        self, exception: Exception, context: ErrorContext | None = None
    ) -> UserFriendlyError:
        """例外からUserFriendlyErrorを作成

        Args:
            exception: 変換する例外
            context: エラーコンテキスト

        Returns:
            UserFriendlyError: 変換されたエラー
        """
        # 例外タイプに基づくエラー処理
        if isinstance(exception, SyntaxError):
            return self._handle_syntax_error(exception, context)
        elif isinstance(exception, ValueError):
            return self._handle_value_error(exception, context)
        elif isinstance(exception, (FileNotFoundError, PermissionError, IOError)):
            return self._handle_io_error(exception, context)
        else:
            # 汎用エラー処理
            return self.error_factory.create_unknown_error(
                str(exception),
                context=context.to_dict() if context else {},
            )

    def _handle_syntax_error(
        self, error: SyntaxError, context: ErrorContext | None
    ) -> UserFriendlyError:
        """SyntaxErrorの処理"""
        return self.error_factory.create_syntax_error(
            error.lineno if error.lineno else 0,
            error.text or "",
        )

    def _handle_value_error(
        self, error: ValueError, context: ErrorContext | None
    ) -> UserFriendlyError:
        """ValueErrorの処理"""
        error_msg = str(error)

        # エラーメッセージに基づく特定の処理は将来の実装で対応
        return self.error_factory.create_unknown_error(
            f"値エラー: {error_msg}",
            context=context.to_dict() if context else {},
        )

    def _handle_io_error(
        self, error: Exception, context: ErrorContext | None
    ) -> UserFriendlyError:
        """IOエラーの処理"""
        if isinstance(error, FileNotFoundError):
            return self.error_factory.create_file_not_found_error(
                str(error).split(":")[-1].strip().strip("'\"")
            )
        elif isinstance(error, PermissionError):
            return self.error_factory.create_permission_error(
                str(error).split(":")[-1].strip().strip("'\"")
            )
        else:
            return self.error_factory.create_unknown_error(
                f"ファイルエラー: {str(error)}",
                context=context.to_dict() if context else {},
            )

    # 分割された機能へのプロキシメソッド
    def display_error(self, error: UserFriendlyError, **kwargs: Any) -> None:
        """エラー表示（プロキシメソッド）"""
        self.display.display_error(error, **kwargs)

    def register_recovery_callback(
        self, error_category: str, callback: Callable[..., Any], description: str = ""
    ) -> None:
        """回復コールバック登録（プロキシメソッド）"""
        # ErrorRecoveryクラスにregister_recovery_callbackメソッドがないため、
        # 将来の実装用のプレースホルダーとして残す
        pass

    def get_error_statistics(self) -> dict[str, Any]:
        """エラー統計取得（プロキシメソッド）"""
        return self.statistics.get_error_statistics()

    def clear_error_history(self) -> None:
        """エラー履歴クリア（プロキシメソッド）"""
        return self.statistics.clear_error_history()

    def export_error_log(self, file_path: Path) -> bool:
        """エラーログエクスポート（プロキシメソッド）"""
        return self.statistics.export_error_log(file_path)


# グローバルハンドラー管理
_global_handler: UnifiedErrorHandler | None = None


def get_global_handler() -> UnifiedErrorHandler:
    """グローバルエラーハンドラーを取得"""
    global _global_handler
    if _global_handler is None:
        _global_handler = UnifiedErrorHandler()
    return _global_handler


def set_global_handler(handler: UnifiedErrorHandler) -> None:
    """グローバルエラーハンドラーを設定"""
    global _global_handler
    _global_handler = handler
