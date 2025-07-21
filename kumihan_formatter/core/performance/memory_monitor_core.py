"""
メモリ監視コア機能 - 基本監視とスナップショット
メモリ監視の基本機能とスナップショット取得
Issue #402対応 - パフォーマンス最適化

分割後の統合インターフェース:
- memory_monitor_basic.py: 基本監視制御
- memory_monitor_stats.py: 統計収集・スナップショット
- memory_monitor_data.py: データ管理・オブジェクト追跡
"""

from typing import Any

from .memory_monitor_basic import MemoryMonitorBasic
from .memory_monitor_data import MemoryDataManager
from .memory_monitor_stats import MemoryStatsCollector
from .memory_types import MemorySnapshot


class MemoryMonitor:
    """メモリ監視システムのコア機能（統合インターフェース）
    基本機能:
    - リアルタイムメモリ追跡
    - スナップショット取得
    - カスタムオブジェクト追跡
    - 基本統計収集
    """

    def __init__(
        self,
        sampling_interval: float = 1.0,
        max_snapshots: int = 1000,
        leak_detection_threshold: int = 10,
        enable_object_tracking: bool = True,
    ):
        """メモリモニターを初期化

        Args:
            sampling_interval: サンプリング間隔（秒）
            max_snapshots: 保持する最大スナップショット数
            leak_detection_threshold: リーク検出の閾値
            enable_object_tracking: オブジェクト追跡を有効にするか
        """
        # 分割されたコンポーネントを初期化
        self.basic_monitor = MemoryMonitorBasic(
            sampling_interval,
            max_snapshots,
            leak_detection_threshold,
            enable_object_tracking,
        )
        self.stats_collector = MemoryStatsCollector(
            max_snapshots, enable_object_tracking
        )
        self.data_manager = MemoryDataManager(enable_object_tracking)

        # 統計収集のコールバックを設定
        self.basic_monitor.set_snapshot_callback(self._take_snapshot_callback)

    def _take_snapshot_callback(self) -> None:
        """スナップショット取得のコールバック"""
        snapshot = self.stats_collector.take_snapshot()
        # 統計を更新
        snapshots_count = self.data_manager.get_stats().get("total_snapshots", 0)
        if isinstance(snapshots_count, int):
            self.data_manager.update_stats("total_snapshots", snapshots_count + 1)

    def start_monitoring(self) -> None:
        """メモリ監視を開始"""
        self.basic_monitor.start_monitoring()

    def stop_monitoring(self) -> None:
        """メモリ監視を停止"""
        self.basic_monitor.stop_monitoring()

    def take_snapshot(self) -> MemorySnapshot:
        """現在のメモリ状況のスナップショットを取得"""
        return self.stats_collector.take_snapshot()

    def register_object(self, obj: Any, obj_type: str) -> None:
        """カスタムオブジェクトを追跡に登録"""
        self.data_manager.register_object(obj, obj_type)

    def get_memory_usage(self) -> dict[str, Any]:
        """現在のメモリ使用量情報を取得"""
        return self.stats_collector.get_memory_usage()

    def clear_data(self) -> None:
        """蓄積されたデータをクリア"""
        self.data_manager.clear_data()

    def cleanup_weak_refs(self) -> None:
        """死んでいるweak referenceをクリーンアップ"""
        self.data_manager.cleanup_weak_refs()

    # 後方互換性のためのプロパティ
    @property
    def snapshots(self) -> list[Any]:
        """スナップショットリストへのアクセス"""
        return self.stats_collector.get_snapshots()

    @property
    def stats(self) -> dict[str, Any]:
        """統計情報へのアクセス"""
        return self.data_manager.get_stats()
