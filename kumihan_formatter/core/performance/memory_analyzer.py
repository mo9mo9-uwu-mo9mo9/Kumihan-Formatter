"""
メモリ分析器 - 高度な分析とレポート機能

メモリ使用量の分析、トレンド解析、レポート生成を行う専用モジュール
Issue #402対応 - パフォーマンス最適化
"""

import time
from typing import Any, Callable, Optional, Sequence, Union

from ..utilities.logger import get_logger
from .memory_alert_manager import MemoryAlertManager
from .memory_gc_manager import MemoryGCManager
from .memory_report_generator import MemoryReportGenerator
from .memory_types import (
    MemoryLeak,
    MemorySnapshot,
)


class MemoryAnalyzer:
    """メモリ分析とレポート生成機能

    機能:
    - メモリトレンド分析
    - 包括的レポート生成
    - ガベージコレクション最適化
    - メモリアラート管理
    """

    def __init__(self) -> None:
        """メモリ分析器を初期化"""
        self.logger = get_logger(__name__)

        # 専門コンポーネント
        self.report_generator = MemoryReportGenerator()
        self.alert_manager = MemoryAlertManager()
        self.gc_manager = MemoryGCManager()

        self.logger.info("メモリ分析器初期化完了")

    def register_alert_callback(
        self, callback: Callable[[str, dict[str, Any]], None]
    ) -> None:
        """アラートコールバックを登録

        Args:
            callback: アラート発生時に呼び出される関数
        """
        self.alert_manager.register_alert_callback(callback)

    def get_memory_trend(
        self, snapshots: list[MemorySnapshot], window_minutes: int = 30
    ) -> dict[str, Any]:
        """メモリ使用量のトレンドを分析

        Args:
            snapshots: 分析対象のスナップショットリスト
            window_minutes: 分析ウィンドウ（分）

        Returns:
            dict: トレンド分析結果
        """
        if not snapshots:
            return {"error": "No snapshots available"}

        current_time = time.time()
        window_seconds = window_minutes * 60
        cutoff_time = current_time - window_seconds

        # ウィンドウ内のスナップショットを抽出
        window_snapshots = [s for s in snapshots if s.timestamp >= cutoff_time]

        if len(window_snapshots) < 2:
            return {"error": "Insufficient data for trend analysis"}

        # トレンド計算
        memory_values = [s.memory_mb for s in window_snapshots]
        gc_object_values = [s.gc_objects for s in window_snapshots]

        start_memory = memory_values[0]
        end_memory = memory_values[-1]
        memory_change = end_memory - start_memory
        memory_change_percent = (
            (memory_change / start_memory * 100) if start_memory > 0 else 0
        )

        start_gc = gc_object_values[0]
        end_gc = gc_object_values[-1]
        gc_change = end_gc - start_gc

        # 統計
        avg_memory = sum(memory_values) / len(memory_values)
        max_memory = max(memory_values)
        min_memory = min(memory_values)

        # 変化率の計算
        memory_slope = self._calculate_slope(
            [s.timestamp for s in window_snapshots], memory_values
        )
        gc_slope = self._calculate_slope(
            [s.timestamp for s in window_snapshots],
            [float(x) for x in gc_object_values],
        )

        return {
            "window_minutes": window_minutes,
            "data_points": len(window_snapshots),
            "memory_trend": {
                "start_mb": start_memory,
                "end_mb": end_memory,
                "change_mb": memory_change,
                "change_percent": memory_change_percent,
                "slope_mb_per_hour": memory_slope * 3600,
                "average_mb": avg_memory,
                "max_mb": max_memory,
                "min_mb": min_memory,
            },
            "gc_objects_trend": {
                "start_count": start_gc,
                "end_count": end_gc,
                "change": gc_change,
                "slope_per_hour": gc_slope * 3600,
            },
            "is_increasing": memory_slope > 0,
            "growth_rate": (
                "rapid"
                if abs(memory_change_percent) > 10
                else "moderate" if abs(memory_change_percent) > 2 else "stable"
            ),
        }

    def _calculate_slope(
        self, x_values: Sequence[float], y_values: Sequence[float]
    ) -> float:
        """最小二乗法で傾きを計算

        Args:
            x_values: X軸の値（通常は時間）
            y_values: Y軸の値（メモリ使用量など）

        Returns:
            float: 傾き
        """
        if len(x_values) != len(y_values) or len(x_values) < 2:
            return 0.0

        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)

        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return 0.0

        slope = (n * sum_xy - sum_x * sum_y) / denominator
        return slope

    def generate_memory_report(
        self,
        snapshots: list[MemorySnapshot],
        leaks: Optional[list[MemoryLeak]] = None,
        include_trend: bool = True,
        trend_window_minutes: int = 30,
    ) -> dict[str, Any]:
        """包括的なメモリレポートを生成

        Args:
            snapshots: メモリスナップショットリスト
            leaks: 検出されたメモリリーク（オプション）
            include_trend: トレンド分析を含めるか
            trend_window_minutes: トレンド分析のウィンドウ（分）

        Returns:
            dict: メモリレポート
        """
        # トレンド分析を事前計算（必要時のみ）
        trend_analysis = None
        if include_trend and len(snapshots) > 1:
            trend_analysis = self.get_memory_trend(snapshots, trend_window_minutes)

        # レポート生成器に委譲
        return self.report_generator.generate_memory_report(
            snapshots=snapshots,
            leaks=leaks,
            include_trend=include_trend,
            trend_window_minutes=trend_window_minutes,
            trend_analysis=trend_analysis,
        )

    def force_garbage_collection(self) -> dict[str, Any]:
        """ガベージコレクションを強制実行

        Returns:
            dict: GC実行結果
        """
        return self.gc_manager.force_garbage_collection()

    def optimize_memory_settings(self) -> dict[str, Any]:
        """メモリ設定を最適化

        Returns:
            dict: 最適化結果
        """
        return self.gc_manager.optimize_memory_settings()

    def check_memory_alerts(self, snapshot: MemorySnapshot) -> None:
        """メモリアラートをチェック

        Args:
            snapshot: チェック対象のスナップショット
        """
        self.alert_manager.check_memory_alerts(snapshot)

    def check_memory_alerts_batch(self, snapshots: list[MemorySnapshot]) -> None:
        """複数のスナップショットに対してアラートをチェック

        Args:
            snapshots: チェック対象のスナップショットリスト
        """
        self.alert_manager.check_memory_alerts_batch(snapshots)

    def get_stats(self) -> dict[str, Any]:
        """統計情報を取得

        Returns:
            dict: 統計情報
        """
        combined_stats = {}

        # 各コンポーネントの統計を統合
        report_stats = self.report_generator.get_stats()
        alert_stats = self.alert_manager.get_stats()
        gc_stats = self.gc_manager.get_stats()

        combined_stats.update(report_stats)
        combined_stats.update(alert_stats)
        combined_stats.update(gc_stats)

        return combined_stats

    def reset_stats(self) -> None:
        """統計情報をリセット"""
        # 各コンポーネントの統計をリセット
        self.report_generator.reset_stats()
        self.alert_manager.reset_stats()
        self.gc_manager.reset_stats()

        self.logger.info("全コンポーネントの統計情報をリセット")
