"""
メモリアラート管理器 - メモリアラート機能の独立クラス

MemoryAnalyzerから抽出されたアラート管理機能を専門的に扱う
Issue #476対応 - 300行制限による技術的負債削減
"""

import time
from typing import Any, Callable

from ..utilities.logger import get_logger
from .memory_types import MEMORY_ALERT_THRESHOLDS, MemorySnapshot


class MemoryAlertManager:
    """メモリアラート管理専用クラス

    機能:
    - メモリアラート監視
    - コールバック管理
    - クールダウン制御
    - アラート発火
    """

    def __init__(self) -> None:
        """メモリアラート管理器を初期化"""
        self.logger = get_logger(__name__)

        # アラート管理
        self.alert_callbacks: list[Callable[[str, dict[str, Any]], None]] = []
        self.last_alert_time: dict[str, float] = {}
        self.alert_cooldown = 300.0  # 5分間のクールダウン

        # 統計
        self.stats = {
            "total_alerts_triggered": 0,
        }

        self.logger.info("メモリアラート管理器初期化完了")

    def register_alert_callback(
        self, callback: Callable[[str, dict[str, Any]], None]
    ) -> None:
        """アラートコールバックを登録

        Args:
            callback: アラート発生時に呼び出される関数
        """
        self.alert_callbacks.append(callback)
        self.logger.debug("アラートコールバック登録完了")

    def check_memory_alerts(self, snapshot: MemorySnapshot) -> None:
        """メモリアラートをチェック

        Args:
            snapshot: チェック対象のスナップショット
        """
        current_time = time.time()

        # 警告レベルチェック
        if snapshot.is_memory_warning:
            alert_type = "memory_warning"
            if self._can_trigger_alert(alert_type, current_time):
                self._trigger_alert(
                    alert_type,
                    {
                        "memory_usage_ratio": snapshot.memory_usage_ratio,
                        "memory_mb": snapshot.memory_mb,
                        "available_mb": snapshot.available_mb,
                        "threshold": MEMORY_ALERT_THRESHOLDS["warning"],
                    },
                )

        # クリティカルレベルチェック
        if snapshot.is_memory_critical:
            alert_type = "memory_critical"
            if self._can_trigger_alert(alert_type, current_time):
                self._trigger_alert(
                    alert_type,
                    {
                        "memory_usage_ratio": snapshot.memory_usage_ratio,
                        "memory_mb": snapshot.memory_mb,
                        "available_mb": snapshot.available_mb,
                        "threshold": MEMORY_ALERT_THRESHOLDS["critical"],
                    },
                )

    def check_memory_alerts_batch(self, snapshots: list[MemorySnapshot]) -> None:
        """複数のスナップショットに対してアラートをチェック

        Args:
            snapshots: チェック対象のスナップショットリスト
        """
        for snapshot in snapshots:
            self.check_memory_alerts(snapshot)

    def _can_trigger_alert(self, alert_type: str, current_time: float) -> bool:
        """アラートを発火できるかチェック（クールダウン考慮）

        Args:
            alert_type: アラートタイプ
            current_time: 現在時刻

        Returns:
            bool: アラート発火可能かどうか
        """
        last_time = self.last_alert_time.get(alert_type, 0)
        return current_time - last_time >= self.alert_cooldown

    def _trigger_alert(self, alert_type: str, context: dict[str, Any]) -> None:
        """アラートを発火

        Args:
            alert_type: アラートタイプ
            context: アラートコンテキスト
        """
        current_time = time.time()
        self.last_alert_time[alert_type] = current_time

        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        self.logger.warning(f"メモリアラート発火: {alert_type} {context_str}")

        # 登録されたコールバックを実行
        for callback in self.alert_callbacks:
            try:
                callback(alert_type, context)
            except Exception as e:
                self.logger.error(f"アラートコールバック実行エラー: {e}")

        self.stats["total_alerts_triggered"] += 1

    def get_stats(self) -> dict[str, Any]:
        """統計情報を取得

        Returns:
            dict: 統計情報
        """
        return self.stats.copy()

    def reset_stats(self) -> None:
        """統計情報をリセット"""
        old_stats = self.stats.copy()
        self.stats = {
            "total_alerts_triggered": 0,
        }

        self.logger.info(f"アラート管理器統計情報をリセット old_stats={old_stats}")

    def trigger_alert(self, alert_type: str, context: dict[str, Any]) -> None:
        """アラート発火（publicメソッド）"""
        self._trigger_alert(alert_type, context)
