"""
エラー回復戦略の基底クラス - Issue #401対応

回復戦略の共通インターフェースと抽象基底クラスを定義。
"""

from abc import ABC, abstractmethod
from typing import Any

from ...utilities.logger import get_logger
from ..error_types import UserFriendlyError


class RecoveryStrategy(ABC):
    """回復戦略の基底クラス"""

    def __init__(self, name: str, priority: int = 5):
        """回復戦略を初期化

        Args:
            name: 戦略名
            priority: 優先度（1-10、小さいほど高優先度）
        """
        self.name = name
        self.priority = priority
        self.logger = get_logger(__name__)

    @abstractmethod
    def can_handle(self, error: UserFriendlyError, context: dict[str, Any]) -> bool:
        """このエラーを処理できるかチェック

        Args:
            error: 対象のエラー
            context: エラーコンテキスト

        Returns:
            bool: 処理可能な場合True
        """
        pass

    @abstractmethod
    def attempt_recovery(
        self, error: UserFriendlyError, context: dict[str, Any]
    ) -> tuple[bool, str | None]:
        """回復を試行

        Args:
            error: 対象のエラー
            context: エラーコンテキスト

        Returns:
            tuple[bool, str | None]: (成功フラグ, メッセージ)
        """
        pass
