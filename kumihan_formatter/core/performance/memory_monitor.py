"""
統合メモリ監視システム - 分割されたコンポーネントの統合

分割されたメモリ監視コンポーネントを統合し、
元のMemoryMonitorクラスと同等の機能を提供する
Issue #402対応 - パフォーマンス最適化
"""

from typing import Any, Callable, Optional

from ..utilities.logger import get_logger
from .memory_analyzer import MemoryAnalyzer
from .memory_leak_detector import MemoryLeakDetector
from .memory_monitor_core import MemoryMonitor as CoreMemoryMonitor
from .memory_types import MemoryLeak, MemorySnapshot


class MemoryMonitor:
    """統合メモリ監視システム

    分割されたコンポーネントを統合し、元のMemoryMonitorクラスの
    すべての機能を提供します:
    - リアルタイムメモリ追跡（Core）
    - メモリリーク検出（LeakDetector）
    - 分析・レポート生成（Analyzer）
    """

    def __init__(
        self,
        sampling_interval: float = 1.0,
        max_snapshots: int = 1000,
        leak_detection_threshold: int = 10,
        enable_object_tracking: bool = True,
    ):
        """統合メモリモニターを初期化

        Args:
            sampling_interval: サンプリング間隔（秒）
            max_snapshots: 保持する最大スナップショット数
            leak_detection_threshold: リーク検出の閾値
            enable_object_tracking: オブジェクト追跡を有効にするか
        """
        self.logger = get_logger(__name__)

        # コンポーネント初期化
        self.core = CoreMemoryMonitor(
            sampling_interval=sampling_interval,
            max_snapshots=max_snapshots,
            leak_detection_threshold=leak_detection_threshold,
            enable_object_tracking=enable_object_tracking,
        )

        self.leak_detector = MemoryLeakDetector(
            leak_detection_threshold=leak_detection_threshold,
            min_data_points=10,
            analysis_window_hours=24.0,
        )

        self.analyzer = MemoryAnalyzer()

        self.logger.info("統合メモリ監視システム初期化完了")

    # Core機能の委譲
    def start_monitoring(self) -> None:
        """メモリ監視を開始"""
        self.core.start_monitoring()

    def stop_monitoring(self) -> None:
        """メモリ監視を停止"""
        self.core.stop_monitoring()

    def take_snapshot(self) -> MemorySnapshot:
        """メモリスナップショットを取得"""
        snapshot = self.core.take_snapshot()

        # リーク検出器に分析を委譲
        self.leak_detector.analyze_snapshot(snapshot)

        # アラートチェック
        self.analyzer.check_memory_alerts(snapshot)

        return snapshot

    def register_object(self, obj: Any, obj_type: str) -> None:
        """カスタムオブジェクトを追跡に登録"""
        self.core.register_object(obj, obj_type)

    def get_memory_usage(self) -> dict[str, Any]:
        """現在のメモリ使用量情報を取得"""
        return self.core.get_memory_usage()

    def clear_data(self) -> None:
        """蓄積されたデータをクリア"""
        self.core.clear_data()
        self.leak_detector.clear_leak_data()

    # リーク検出機能の委譲
    def get_memory_leaks(
        self, severity_filter: Optional[str] = None
    ) -> list[MemoryLeak]:
        """検出されたメモリリークを取得"""
        return self.leak_detector.get_memory_leaks(severity_filter)

    # 分析機能の委譲
    def get_memory_trend(self, window_minutes: int = 30) -> dict[str, Any]:
        """メモリ使用量のトレンドを分析"""
        return self.analyzer.get_memory_trend(self.core.snapshots, window_minutes)

    def generate_memory_report(
        self, include_trend: bool = True, trend_window_minutes: int = 30
    ) -> dict[str, Any]:
        """包括的なメモリレポートを生成"""
        leaks = self.leak_detector.get_memory_leaks()
        return self.analyzer.generate_memory_report(
            self.core.snapshots, leaks, include_trend, trend_window_minutes
        )

    def force_garbage_collection(self) -> dict[str, Any]:
        """ガベージコレクションを強制実行"""
        return self.analyzer.force_garbage_collection()

    def optimize_memory_settings(self) -> dict[str, Any]:
        """メモリ設定を最適化"""
        return self.analyzer.optimize_memory_settings()

    def register_alert_callback(
        self, callback: Callable[[str, dict[str, Any]], None]
    ) -> None:
        """アラートコールバックを登録"""
        self.analyzer.register_alert_callback(callback)

    # プロパティアクセス（後方互換性のため）
    @property
    def snapshots(self) -> list[MemorySnapshot]:
        """スナップショットリストへのアクセス"""
        return self.core.snapshots

    @property
    def stats(self) -> dict[str, Any]:
        """統計情報への統合アクセス"""
        core_stats = self.core.stats
        analyzer_stats = self.analyzer.get_stats()
        leak_stats = self.leak_detector.get_leak_summary()

        return {
            "core": core_stats,
            "analyzer": analyzer_stats,
            "leak_detector": leak_stats,
        }

    # 内部メソッド（後方互換性）

    def _check_memory_alerts(self, snapshot: MemorySnapshot) -> None:
        """メモリアラートチェック（後方互換性）"""
        self.analyzer.check_memory_alerts(snapshot)

    def _trigger_alert(self, alert_type: str, context: dict[str, Any]) -> None:
        """アラート発火（後方互換性）"""
        self.analyzer.alert_manager.trigger_alert(alert_type, context)

    def _cleanup_weak_refs(self) -> None:
        """WeakReferenceクリーンアップ（後方互換性）"""
        self.core._cleanup_weak_refs()
