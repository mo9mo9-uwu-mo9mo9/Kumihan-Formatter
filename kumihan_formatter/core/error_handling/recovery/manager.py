"""
エラー回復管理システム - Issue #401対応

複数の回復戦略を統合管理し、エラーからの自動回復を提供。
"""

from typing import Any, List, Tuple

from ...utilities.logger import get_logger
from ..error_types import UserFriendlyError
from .base import RecoveryStrategy
from .content_strategies import MemoryErrorRecoveryStrategy, SyntaxErrorRecoveryStrategy
from .file_strategies import (
    FileEncodingRecoveryStrategy,
    FileNotFoundRecoveryStrategy,
    FilePermissionRecoveryStrategy,
)


class RecoveryManager:
    """
    エラー回復管理システム

    設計ドキュメント:
    - Issue #401: エラーハンドリングの強化と統合
    - 複数の回復戦略を統合管理
    - 優先度ベースの回復試行

    機能:
    - 回復戦略の登録・管理
    - エラータイプ別の自動回復
    - 回復履歴の記録
    - 回復成功率の分析
    """

    def __init__(self, enable_logging: bool = True):
        """回復管理システムを初期化

        Args:
            enable_logging: ログ出力を有効にするか
        """
        self.enable_logging = enable_logging
        self.logger = get_logger(__name__) if enable_logging else None

        # 回復戦略のリスト
        self.strategies: list[RecoveryStrategy] = []

        # 回復履歴
        self.recovery_history: List[dict[str, Any]] = []

        # デフォルト戦略を登録
        self._register_default_strategies()

        if self.logger:
            self.logger.info("RecoveryManager initialized")

    def _register_default_strategies(self) -> None:
        """デフォルトの回復戦略を登録"""
        self.register_strategy(MemoryErrorRecoveryStrategy())
        self.register_strategy(FileEncodingRecoveryStrategy())
        self.register_strategy(FilePermissionRecoveryStrategy())
        self.register_strategy(FileNotFoundRecoveryStrategy())
        self.register_strategy(SyntaxErrorRecoveryStrategy())

    def register_strategy(self, strategy: RecoveryStrategy) -> None:
        """回復戦略を登録

        Args:
            strategy: 登録する回復戦略
        """
        self.strategies.append(strategy)
        # 優先度でソート（小さいほど高優先度）
        self.strategies.sort(key=lambda s: s.priority)

        if self.logger:
            self.logger.debug(f"Registered recovery strategy: {strategy.name}")

    def attempt_recovery(
        self, error: UserFriendlyError, context: dict[str, Any]
    ) -> Tuple[bool, list[str]]:
        """エラーからの回復を試行

        Args:
            error: 回復対象のエラー
            context: エラーコンテキスト

        Returns:
            Tuple[bool, list[str]]: (回復成功フラグ, 実行された回復操作のメッセージリスト)
        """
        recovery_messages = []

        if self.logger:
            self.logger.info(f"Attempting recovery for error: {error.error_code}")

        for strategy in self.strategies:
            if strategy.can_handle(error, context):
                try:
                    success, message = strategy.attempt_recovery(error, context)

                    # 回復履歴に記録
                    self.recovery_history.append(
                        {
                            "strategy": strategy.name,
                            "error_code": error.error_code,
                            "success": success,
                            "message": message,
                            "timestamp": str(context.get("timestamp", "unknown")),
                        }
                    )

                    if success:
                        if message:
                            recovery_messages.append(f"[{strategy.name}] {message}")

                        if self.logger:
                            self.logger.info(
                                f"Recovery successful with strategy: {strategy.name}"
                            )

                        return True, recovery_messages

                    elif message:
                        recovery_messages.append(f"[{strategy.name}] 失敗: {message}")

                except Exception as e:
                    error_msg = f"戦略実行エラー: {str(e)}"
                    recovery_messages.append(f"[{strategy.name}] {error_msg}")

                    if self.logger:
                        self.logger.error(
                            f"Recovery strategy {strategy.name} failed: {e}"
                        )

        if self.logger:
            self.logger.warning(
                f"All recovery strategies failed for error: {error.error_code}"
            )

        return False, recovery_messages

    def get_recovery_statistics(self) -> dict[str, Any]:
        """回復統計情報を取得

        Returns:
            dict[str, Any]: 回復統計情報
        """
        if not self.recovery_history:
            return {"total_attempts": 0}

        total_attempts = len(self.recovery_history)
        successful_attempts = sum(
            1 for entry in self.recovery_history if entry["success"]
        )

        # 戦略別統計
        strategy_stats = {}
        for entry in self.recovery_history:
            strategy = entry["strategy"]
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {"attempts": 0, "successes": 0}

            strategy_stats[strategy]["attempts"] += 1
            if entry["success"]:
                strategy_stats[strategy]["successes"] += 1

        # 成功率を計算
        for strategy, stats in strategy_stats.items():
            stats["success_rate"] = (
                stats["successes"] / stats["attempts"] if stats["attempts"] > 0 else 0  # type: ignore
            )

        return {
            "total_attempts": total_attempts,
            "successful_attempts": successful_attempts,
            "overall_success_rate": successful_attempts / total_attempts,
            "strategy_statistics": strategy_stats,
            "recent_recoveries": self.recovery_history[-10:],  # 最新10件
        }

    def clear_history(self) -> None:
        """回復履歴をクリア"""
        self.recovery_history.clear()

        if self.logger:
            self.logger.info("Recovery history cleared")


# グローバルインスタンス
_global_recovery_manager: RecoveryManager | None = None


def get_global_recovery_manager() -> RecoveryManager:
    """グローバル回復管理システムを取得（遅延初期化）"""
    global _global_recovery_manager
    if _global_recovery_manager is None:
        _global_recovery_manager = RecoveryManager()
    return _global_recovery_manager


def set_global_recovery_manager(manager: RecoveryManager) -> None:
    """グローバル回復管理システムを設定"""
    global _global_recovery_manager
    _global_recovery_manager = manager
