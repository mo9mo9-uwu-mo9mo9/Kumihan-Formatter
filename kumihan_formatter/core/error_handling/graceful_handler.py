"""Graceful Error Handler

Issue #770対応: graceful error handlingの全面展開
エラーが発生してもユーザー体験を損なわない処理を提供
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from ..common.error_base import KumihanError
from ..common.error_types import ErrorCategory, ErrorSeverity
from ..utilities.logger import get_logger


@dataclass
class GracefulErrorRecord:
    """Graceful handling用エラー記録"""

    error: KumihanError
    timestamp: datetime
    context: Dict[str, Any]
    recovery_attempted: bool = False
    recovery_successful: bool = False
    user_notified: bool = False
    embedded_in_output: bool = False


@dataclass
class GracefulHandlingResult:
    """Graceful handling処理結果"""

    success: bool
    should_continue: bool
    recovered_data: Optional[Any] = None
    user_message: str = ""
    error_record: Optional[GracefulErrorRecord] = None


class GracefulErrorHandler:
    """Graceful Error Handler

    エラー発生時にシステムを停止せず、可能な限り処理を継続:
    - エラー情報の蓄積・記録
    - 自動復旧の試行
    - HTML出力へのエラー情報埋め込み
    - ユーザー向け適切な通知
    """

    def __init__(
        self,
        max_errors: int = 100,
        auto_recovery: bool = True,
        embed_errors_in_output: bool = True,
    ):
        """初期化

        Args:
            max_errors: 最大エラー記録数
            auto_recovery: 自動復旧試行有無
            embed_errors_in_output: 出力へのエラー埋め込み有無
        """
        self.max_errors = max_errors
        self.auto_recovery = auto_recovery
        self.embed_errors_in_output = embed_errors_in_output

        self.logger = get_logger(__name__)

        # エラー記録
        self.error_records: List[GracefulErrorRecord] = []
        self.error_counts: Dict[str, int] = {}

        # 復旧戦略レジストリ
        self.recovery_strategies: Dict[ErrorCategory, Callable] = {
            ErrorCategory.SYNTAX: self._recover_syntax_error,
            ErrorCategory.FILE_SYSTEM: self._recover_file_error,
            ErrorCategory.VALIDATION: self._recover_validation_error,
        }

    def handle_gracefully(
        self,
        error: KumihanError,
        context: Optional[Dict[str, Any]] = None,
        attempt_recovery: bool = True,
    ) -> GracefulHandlingResult:
        """Graceful error handling メイン処理

        Args:
            error: 処理するエラー
            context: 追加コンテキスト
            attempt_recovery: 復旧試行有無

        Returns:
            GracefulHandlingResult: 処理結果
        """
        # エラー記録作成
        error_record = GracefulErrorRecord(
            error=error, timestamp=datetime.now(), context=context or {}
        )

        # エラー統計更新
        error_type = f"{error.category.value}:{error.severity.value}"
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

        # ログ記録
        self.logger.warning(
            f"Graceful handling: {error.category.value} error - {error.message}"
        )

        # 復旧試行
        recovery_result = None
        if attempt_recovery and self.auto_recovery:
            recovery_result = self._attempt_recovery(error, error_record)

        # 継続可否判定
        should_continue = self._should_continue_processing(error, error_record)

        # エラー記録保存
        self._store_error_record(error_record)

        # 結果構築
        result = GracefulHandlingResult(
            success=True,
            should_continue=should_continue,
            recovered_data=recovery_result.get("data") if recovery_result else None,
            user_message=self._generate_user_message(error, error_record),
            error_record=error_record,
        )

        return result

    def _attempt_recovery(
        self, error: KumihanError, error_record: GracefulErrorRecord
    ) -> Optional[Dict[str, Any]]:
        """エラー復旧試行

        Args:
            error: エラー
            error_record: エラー記録

        Returns:
            Optional[Dict[str, Any]]: 復旧結果（None=復旧失敗）
        """
        error_record.recovery_attempted = True

        try:
            # カテゴリ別復旧戦略実行
            if error.category in self.recovery_strategies:
                strategy = self.recovery_strategies[error.category]
                recovery_result = strategy(error, error_record)

                if recovery_result:
                    error_record.recovery_successful = True
                    self.logger.info(f"Recovery successful for {error.category.value}")
                    return (
                        recovery_result
                        if isinstance(recovery_result, dict)
                        else {"success": True}
                    )

        except Exception as recovery_error:
            self.logger.error(f"Recovery failed: {recovery_error}")

        error_record.recovery_successful = False
        return None

    def _recover_syntax_error(
        self, error: KumihanError, error_record: GracefulErrorRecord
    ) -> Optional[Dict[str, Any]]:
        """構文エラー復旧戦略

        Args:
            error: 構文エラー
            error_record: エラー記録

        Returns:
            Optional[Dict[str, Any]]: 復旧結果
        """
        # 基本的な構文修正パターン
        recovery_patterns = {
            "incomplete_marker": self._fix_incomplete_marker,
            "unmatched_marker": self._fix_unmatched_marker,
            "invalid_nesting": self._fix_invalid_nesting,
        }

        error_message = error.message.lower()

        for pattern, fix_func in recovery_patterns.items():
            if pattern in error_message:
                try:
                    fixed_content = fix_func(error, error_record)
                    if fixed_content:
                        return {"data": fixed_content, "method": pattern}
                except Exception as e:
                    self.logger.warning(f"Recovery pattern failed for {pattern}: {e}")
                    continue

        return None

    def _fix_incomplete_marker(
        self, error: KumihanError, error_record: GracefulErrorRecord
    ) -> Optional[str]:
        """不完全マーカー修正

        Args:
            error: エラー
            error_record: エラー記録

        Returns:
            Optional[str]: 修正されたコンテンツ
        """
        # 簡単な修正パターン: 閉じマーカー追加
        if error.context and error.context.user_input:
            content = error.context.user_input
            if content.count("#") % 2 == 1:  # 奇数個の#
                return content + "#"

    def _fix_unmatched_marker(
        self, error: KumihanError, error_record: GracefulErrorRecord
    ) -> Optional[str]:
        """不一致マーカー修正

        Args:
            error: エラー
            error_record: エラー記録

        Returns:
            Optional[str]: 修正されたコンテンツ
        """
        # 基本的なバランス修正
        if error.context and error.context.user_input:
            content = error.context.user_input
            # 簡単なケース: 開きマーカーのみの場合
            if content.startswith("#") and not content.endswith("#"):
                return content + "#"

    def _fix_invalid_nesting(
        self, error: KumihanError, error_record: GracefulErrorRecord
    ) -> Optional[str]:
        """無効なネスト修正

        Args:
            error: エラー
            error_record: エラー記録

        Returns:
            Optional[str]: 修正されたコンテンツ
        """
        # ネスト問題の基本修正
        # より複雑なロジックが必要だが、現段階では基本対応
        return None

    def _recover_file_error(
        self, error: KumihanError, error_record: GracefulErrorRecord
    ) -> Optional[Dict[str, Any]]:
        """ファイルエラー復旧戦略

        Args:
            error: ファイルエラー
            error_record: エラー記録

        Returns:
            Optional[Dict[str, Any]]: 復旧結果
        """
        # ファイル関連エラーの復旧
        if "not found" in error.message.lower():
            # ファイルが見つからない場合の代替処理
            return {
                "data": "",
                "method": "empty_fallback",
                "message": "空のコンテンツで継続",
            }

        return None

    def _recover_validation_error(
        self, error: KumihanError, error_record: GracefulErrorRecord
    ) -> Optional[Dict[str, Any]]:
        """バリデーションエラー復旧戦略

        Args:
            error: バリデーションエラー
            error_record: エラー記録

        Returns:
            Optional[Dict[str, Any]]: 復旧結果
        """
        # バリデーションエラーの復旧
        # デフォルト値使用など
        return {
            "data": None,
            "method": "default_value",
            "message": "デフォルト値で継続",
        }

    def _should_continue_processing(
        self, error: KumihanError, error_record: GracefulErrorRecord
    ) -> bool:
        """処理継続可否判定

        Args:
            error: エラー
            error_record: エラー記録

        Returns:
            bool: 継続可否
        """
        # クリティカルエラーは停止
        if error.severity == ErrorSeverity.CRITICAL:
            return False

        # 復旧成功時は継続
        if error_record.recovery_successful:
            return True

        # 軽度エラーは継続
        return error.severity in [ErrorSeverity.LOW, ErrorSeverity.WARNING]

    def _store_error_record(self, error_record: GracefulErrorRecord) -> None:
        """エラー記録保存

        Args:
            error_record: エラー記録
        """
        # 最大記録数制限
        if len(self.error_records) >= self.max_errors:
            self.error_records.pop(0)  # 古い記録を削除

        self.error_records.append(error_record)

    def _generate_user_message(
        self, error: KumihanError, error_record: GracefulErrorRecord
    ) -> str:
        """ユーザー向けメッセージ生成

        Args:
            error: エラー
            error_record: エラー記録

        Returns:
            str: ユーザー向けメッセージ
        """
        if error_record.recovery_successful:
            return f"⚠️ 問題が発生しましたが、自動修正により処理を続行しました: {error.message}"
        else:
            return f"❌ エラーが発生しました: {error.message}"

    def get_error_summary(self) -> Dict[str, Any]:
        """エラーサマリー取得

        Returns:
            Dict[str, Any]: エラーサマリー
        """
        total_errors = len(self.error_records)
        recovered_errors = sum(1 for r in self.error_records if r.recovery_successful)

        return {
            "total_errors": total_errors,
            "recovered_errors": recovered_errors,
            "recovery_rate": recovered_errors / total_errors if total_errors > 0 else 0,
            "error_types": dict(self.error_counts),
            "recent_errors": [
                {
                    "message": r.error.message,
                    "category": r.error.category.value,
                    "timestamp": r.timestamp.isoformat(),
                    "recovered": r.recovery_successful,
                }
                for r in self.error_records[-5:]  # 最新5件
            ],
        }

    def generate_error_report_html(self) -> str:
        """HTML用エラーレポート生成

        Returns:
            str: HTML形式のエラーレポート
        """
        if not self.error_records:
            return ""

        html_parts = ['<div class="error-report">', "<h3>エラーレポート</h3>", "<ul>"]

        for record in self.error_records:
            error_info = {
                "message": record.error.message,
                "category": record.error.category.value,
                "recovered": record.recovery_successful,
            }

            icon = "✅" if error_info["recovered"] else "⚠️"
            html_parts.append(
                f'<li>{icon} {error_info["message"]} '
                f'<small>({error_info["category"]})</small></li>'
            )

        html_parts.append("</ul>")
        html_parts.append("</div>")

        return "\n".join(html_parts)

    def clear_records(self) -> None:
        """エラー記録クリア"""
        self.error_records.clear()
        self.error_counts.clear()


# グローバルインスタンス
_global_graceful_handler: Optional[GracefulErrorHandler] = None


def get_global_graceful_handler() -> GracefulErrorHandler:
    """グローバルGraceful Error Handler取得

    Returns:
        GracefulErrorHandler: グローバルハンドラー
    """
    global _global_graceful_handler
    if _global_graceful_handler is None:
        _global_graceful_handler = GracefulErrorHandler()
    return _global_graceful_handler


def handle_gracefully(
    error: KumihanError, context: Optional[Dict[str, Any]] = None
) -> GracefulHandlingResult:
    """便利関数: Graceful error handling

    Args:
        error: エラー
        context: コンテキスト

    Returns:
        GracefulHandlingResult: 処理結果
    """
    handler = get_global_graceful_handler()
    return handler.handle_gracefully(error, context)
