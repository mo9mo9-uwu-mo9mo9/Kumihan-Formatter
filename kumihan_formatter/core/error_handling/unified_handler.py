"""統一エラーハンドラー

Issue #770対応: 分散したエラー処理を統一し、
一貫性のあるエラーハンドリングとログ出力を提供
"""

from dataclasses import dataclass
from logging import Logger
from typing import Any, Dict, Optional

from ..common.error_base import KumihanError
from ..common.error_types import ErrorCategory, ErrorContext, ErrorSeverity
from ..error_analysis.error_config import ErrorConfigManager
from ..utilities.logger import get_logger


@dataclass
class ErrorHandleResult:
    """エラー処理結果"""

    should_continue: bool
    user_message: str
    logged: bool
    graceful_handled: bool
    original_error: Exception
    kumihan_error: KumihanError


class UnifiedErrorHandler:
    """統一エラーハンドリングシステム

    全モジュールで一貫したエラー処理を提供:
    - エラー分類・変換
    - 設定ベース処理戦略
    - 統一ログフォーマット
    - graceful handling
    """

    def __init__(
        self,
        config_manager: Optional[ErrorConfigManager] = None,
        logger: Optional[Logger] = None,
        component_name: str = "unknown",
    ):
        """初期化

        Args:
            config_manager: エラー設定管理（None時は新規作成）
            logger: ロガー（None時は新規作成）
            component_name: コンポーネント名（ログ識別用）
        """
        self.config = config_manager or ErrorConfigManager()
        self.logger = logger or get_logger(__name__)
        self.component_name = component_name

        # エラー統計
        self.error_counts: Dict[str, int] = {}

    def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        operation: str = "unknown_operation",
    ) -> ErrorHandleResult:
        """統一エラー処理メイン処理

        Args:
            error: 発生した例外
            context: エラーコンテキスト（ファイル名・行番号等）
            operation: 実行中の操作名

        Returns:
            ErrorHandleResult: 処理結果
        """
        # 1. エラー分類・変換
        kumihan_error = self._convert_to_kumihan_error(error, context, operation)

        # 2. エラー統計更新
        error_type = kumihan_error.category.value
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

        # 3. 処理戦略決定
        should_continue = self._should_continue_processing(
            kumihan_error, self.error_counts[error_type]
        )

        # 4. ログ出力（統一フォーマット）
        self._log_error(kumihan_error, operation)

        # 5. graceful handling（設定に応じ）
        graceful_handled = False
        if self.config.config.graceful_errors:
            graceful_handled = self._apply_graceful_handling(kumihan_error)

        # 6. ユーザー向けメッセージ生成
        user_message = self._generate_user_message(kumihan_error)

        return ErrorHandleResult(
            should_continue=should_continue,
            user_message=user_message,
            logged=True,
            graceful_handled=graceful_handled,
            original_error=error,
            kumihan_error=kumihan_error,
        )

    def _convert_to_kumihan_error(
        self, error: Exception, context: Optional[Dict[str, Any]], operation: str
    ) -> KumihanError:
        """例外をKumihanErrorに変換

        Args:
            error: 元の例外
            context: コンテキスト情報
            operation: 操作名

        Returns:
            KumihanError: 変換されたエラー
        """
        # 既にKumihanErrorの場合は そのまま返す
        if isinstance(error, KumihanError):
            return error

        # エラータイプに基づく分類
        severity, category = self._classify_error(error)

        # コンテキスト作成
        error_context = ErrorContext(
            file_path=context.get("file_path") if context else None,
            line_number=context.get("line_number") if context else None,
            column_number=context.get("column_number") if context else None,
            operation=operation,
            user_input=context.get("user_input") if context else None,
            system_info=context.get("system_info") if context else None,
        )

        # 提案生成
        suggestions = self._generate_suggestions(error, category)

        return KumihanError(
            message=str(error),
            severity=severity,
            category=category,
            context=error_context,
            suggestions=suggestions,
            original_error=error,
        )

    def _classify_error(self, error: Exception) -> tuple[ErrorSeverity, ErrorCategory]:
        """エラーを分類してseverityとcategoryを決定

        Args:
            error: 例外オブジェクト

        Returns:
            tuple: (severity, category)
        """
        error_message = str(error).lower()

        # ファイルシステムエラー
        if isinstance(error, (FileNotFoundError, PermissionError, OSError)):
            return ErrorSeverity.ERROR, ErrorCategory.FILE_SYSTEM

        # 構文エラー
        if isinstance(error, SyntaxError) or "syntax" in error_message:
            return ErrorSeverity.WARNING, ErrorCategory.SYNTAX

        # 値エラー・型エラー
        if isinstance(error, (ValueError, TypeError)):
            return ErrorSeverity.WARNING, ErrorCategory.VALIDATION

        # メモリエラー
        if isinstance(error, MemoryError):
            return ErrorSeverity.CRITICAL, ErrorCategory.SYSTEM

        # ネットワーク関連
        if "connection" in error_message or "network" in error_message:
            return ErrorSeverity.ERROR, ErrorCategory.NETWORK

        # その他
        return ErrorSeverity.ERROR, ErrorCategory.UNKNOWN

    def _generate_suggestions(
        self, error: Exception, category: ErrorCategory
    ) -> list[str]:
        """エラーカテゴリに基づく提案生成

        Args:
            error: 例外オブジェクト
            category: エラーカテゴリ

        Returns:
            list[str]: 提案リスト
        """
        suggestions = []
        error_message = str(error).lower()

        if category == ErrorCategory.FILE_SYSTEM:
            if "not found" in error_message:
                suggestions.extend(
                    [
                        "ファイルパスが正しいことを確認してください",
                        "ファイルが存在し、読み取り可能であることを確認してください",
                        "相対パスではなく絶対パスを試してみてください",
                    ]
                )
            elif "permission" in error_message:
                suggestions.extend(
                    [
                        "ファイルの読み取り権限を確認してください",
                        "管理者権限で実行してみてください",
                        "ファイルが他のプロセスで使用されていないか確認してください",
                    ]
                )
            else:
                # 一般的なファイルシステムエラー
                suggestions.extend(
                    [
                        "ディスク容量を確認してください",
                        "ファイルパスに無効な文字が含まれていないか確認してください",
                    ]
                )

        elif category == ErrorCategory.SYNTAX:
            suggestions.extend(
                [
                    "記法の構文を確認してください",
                    "マーカーが正しく閉じられているか確認してください",
                    "特殊文字が正しくエスケープされているか確認してください",
                ]
            )

        elif category == ErrorCategory.VALIDATION:
            suggestions.extend(
                [
                    "入力値の形式を確認してください",
                    "設定ファイルの内容を確認してください",
                ]
            )

        elif category == ErrorCategory.SYSTEM:
            suggestions.extend(
                [
                    "システムリソースを確認してください",
                    "大きなファイルの場合、分割処理を検討してください",
                ]
            )

        # 一般的な提案を追加
        if not suggestions:
            suggestions.extend(
                [
                    "エラーの詳細については、ログファイルを確認してください",
                    "問題が解決しない場合は、開発者にお問い合わせください",
                ]
            )

        return suggestions

    def _should_continue_processing(
        self, error: KumihanError, occurrence_count: int
    ) -> bool:
        """処理を継続すべきかを判定

        Args:
            error: KumihanError
            occurrence_count: このタイプのエラーの発生回数

        Returns:
            bool: 継続可否
        """
        # クリティカルエラーは即座停止
        if error.severity == ErrorSeverity.CRITICAL:
            return False

        # 設定管理による判定
        return self.config.should_continue_on_error(
            error.category.value, occurrence_count
        )

    def _log_error(self, error: KumihanError, operation: str) -> None:
        """統一フォーマットでエラーログ出力

        Args:
            error: KumihanError
            operation: 操作名
        """
        # ログレベル決定
        if error.severity == ErrorSeverity.CRITICAL:
            log_func = self.logger.critical
        elif error.severity == ErrorSeverity.ERROR:
            log_func = self.logger.error
        elif error.severity == ErrorSeverity.WARNING:
            log_func = self.logger.warning
        else:
            log_func = self.logger.info

        # 統一フォーマットメッセージ構築
        message_parts = [f"[{self.component_name.upper()}] {error.message}"]

        if error.context and str(error.context) != "No context":
            message_parts.append(f"Context: {error.context}")

        if operation != "unknown_operation":
            message_parts.append(f"Operation: {operation}")

        if error.suggestions:
            suggestions_str = "; ".join(error.suggestions[:2])  # 最初の2つのみ
            message_parts.append(f"Suggestions: {suggestions_str}")

        log_message = " | ".join(message_parts)

        # ログ出力
        log_func(log_message)

        # 詳細トレースバック（DEBUG レベル）
        if error.original_error and error.traceback_info:
            self.logger.debug(f"Detailed traceback: {error.traceback_info}")

    def _apply_graceful_handling(self, error: KumihanError) -> bool:
        """graceful error handling適用

        Args:
            error: KumihanError

        Returns:
            bool: graceful handling適用成功
        """
        try:
            # graceful handlingロジック
            # エラー情報を収集し、後でHTML等に埋め込み可能な形で保存

            # 現状は基本的な情報ログのみ
            self.logger.info(
                f"Graceful handling applied for {error.category.value}: {error.message}"
            )
            return True

        except Exception as e:
            self.logger.warning(f"Failed to apply graceful handling: {e}")
            return False

    def _generate_user_message(self, error: KumihanError) -> str:
        """ユーザー向けメッセージ生成

        Args:
            error: KumihanError

        Returns:
            str: ユーザー向けメッセージ
        """
        if self.config.config.show_suggestions and error.suggestions:
            return error.get_user_message()
        else:
            return error.message

    def get_error_statistics(self) -> Dict[str, int]:
        """エラー統計取得

        Returns:
            Dict[str, int]: エラータイプ別発生回数
        """
        return self.error_counts.copy()

    def reset_statistics(self) -> None:
        """エラー統計リセット"""
        self.error_counts.clear()


# 便利関数: グローバルハンドラー取得
_global_handler: Optional[UnifiedErrorHandler] = None


def get_global_error_handler() -> UnifiedErrorHandler:
    """グローバル統一エラーハンドラー取得

    Returns:
        UnifiedErrorHandler: グローバルハンドラー
    """
    global _global_handler
    if _global_handler is None:
        _global_handler = UnifiedErrorHandler(component_name="global")
    return _global_handler


def handle_error_unified(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    operation: str = "unknown_operation",
    component_name: str = "unknown",
) -> ErrorHandleResult:
    """便利関数: 統一エラー処理

    Args:
        error: 例外
        context: コンテキスト
        operation: 操作名
        component_name: コンポーネント名

    Returns:
        ErrorHandleResult: 処理結果
    """
    handler = UnifiedErrorHandler(component_name=component_name)
    return handler.handle_error(error, context, operation)
