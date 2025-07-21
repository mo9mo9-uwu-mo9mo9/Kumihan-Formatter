"""メモリ監視システム - 統合インターフェース

Single Responsibility Principle適用: メモリ監視の責任分離
Issue #476 Phase4対応 - memory.py分割による技術的負債削減
"""

import threading
import time
from typing import Any, Dict, List, Optional

# ...utilities.logger.get_logger removed as unused
from ..core.base import PerformanceComponent, PerformanceMetric
from ..core.metrics import MemorySnapshot
from .leak_detector import LeakDetector
from .memory_sampler import MemorySampler
from .object_monitor import ObjectMonitor


class MemoryMonitor(PerformanceComponent):
    """高度なメモリ監視システム - 統合インターフェース

    機能:
    - リアルタイムメモリ追跡（MemorySamplerに委譲）
    - メモリリーク検出（LeakDetectorに委譲）
    - カスタムオブジェクト追跡（ObjectMonitorに委譲）
    - メモリ使用量アラート
    """

    def __init__(
        self,
        config: Dict[str, Any] | None = None,
        sampling_interval: float = 1.0,
        max_snapshots: int = 1000,
        leak_detection_threshold: int = 10,
        enable_object_tracking: bool = True,
    ):
        """メモリモニターを初期化

        Args:
            config: 設定辞書
            sampling_interval: サンプリング間隔（秒）
            max_snapshots: 保持する最大スナップショット数
            leak_detection_threshold: リーク検出の閾値
            enable_object_tracking: オブジェクト追跡を有効にするか
        """
        super().__init__(config)
        self.sampling_interval = sampling_interval

        # 責任分離されたコンポーネント
        self.memory_sampler = MemorySampler(max_snapshots=max_snapshots)
        self.leak_detector = LeakDetector(
            leak_detection_threshold=leak_detection_threshold
        )
        self.object_monitor = ObjectMonitor(enable_tracking=enable_object_tracking)

        # 監視制御
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

        self.logger.info(
            f"MemoryMonitor initialized: sampling_interval={sampling_interval}, "
            f"max_snapshots={max_snapshots}, leak_threshold={leak_detection_threshold}"
        )

    def initialize(self) -> None:
        """メモリモニターを初期化"""
        # ガベージコレクションの設定
        import gc

        gc.set_debug(gc.DEBUG_STATS)
        self.is_initialized = True
        self.logger.info("MemoryMonitor initialized successfully")

    def start_monitoring(self) -> None:
        """リアルタイムメモリ監視を開始"""
        if self.monitoring_active:
            self.logger.warning("Memory monitoring is already active")
            return

        self.monitoring_active = True
        self.stop_event.clear()
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True
        )
        self.monitoring_thread.start()
        self.logger.info("Memory monitoring started")

    def stop_monitoring(self) -> None:
        """リアルタイムメモリ監視を停止"""
        if not self.monitoring_active:
            self.logger.warning("Memory monitoring is not active")
            return

        self.monitoring_active = False
        self.stop_event.set()
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5.0)
        self.logger.info("Memory monitoring stopped")

    def _monitoring_loop(self) -> None:
        """監視ループ"""
        while not self.stop_event.wait(self.sampling_interval):
            try:
                snapshot = self._capture_snapshot()
                self.memory_sampler.add_snapshot(snapshot)
                self._detect_leaks()
                self._check_alerts()
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")

    def _capture_snapshot(self) -> MemorySnapshot:
        """現在のメモリ状態のスナップショットを取得

        Returns:
            メモリスナップショット
        """
        snapshot = self.memory_sampler.capture_snapshot()

        # カスタムオブジェクト情報を追加
        snapshot.custom_objects = self.object_monitor.get_object_counts()

        return snapshot

    def _detect_leaks(self) -> None:
        """メモリリークを検出"""
        snapshots = self.memory_sampler.snapshots
        if len(snapshots) < 2:
            return

        current_snapshot = snapshots[-1]
        previous_snapshot = snapshots[-2]

        self.leak_detector.detect_leaks(current_snapshot, previous_snapshot)

    def _check_alerts(self) -> None:
        """アラートをチェック"""
        snapshots = self.memory_sampler.snapshots
        if not snapshots:
            return

        latest_snapshot = snapshots[-1]
        self.leak_detector.check_alerts(latest_snapshot)

    def track_object(self, obj: Any, object_type: str) -> None:
        """オブジェクトを追跡対象に追加

        Args:
            obj: 追跡するオブジェクト
            object_type: オブジェクトの種類
        """
        self.object_monitor.track_object(obj, object_type)

    def get_memory_usage(self) -> Dict[str, float]:
        """現在のメモリ使用量を取得

        Returns:
            メモリ使用量情報
        """
        memory_usage = self.memory_sampler.get_memory_usage()
        if memory_usage:
            memory_usage["tracked_objects"] = float(
                self.object_monitor.get_total_tracked_objects()
            )
        return memory_usage

    def get_leak_summary(self) -> Dict[str, Any]:
        """リーク検出のサマリーを取得

        Returns:
            リークサマリー
        """
        return self.leak_detector.get_leak_summary()

    def collect_metrics(self) -> List[PerformanceMetric]:
        """メトリクスを収集

        Returns:
            収集されたメトリクス
        """
        metrics = []
        current_time = time.time()

        memory_usage = self.get_memory_usage()
        for name, value in memory_usage.items():
            metrics.append(
                PerformanceMetric(
                    name=name,
                    value=value,
                    unit="MB" if "_mb" in name else "count",
                    timestamp=current_time,
                    category="memory",
                    metadata={"component": "MemoryMonitor"},
                )
            )

        leak_summary = self.leak_detector.get_leak_summary()
        metrics.append(
            PerformanceMetric(
                name="memory_leaks_detected",
                value=float(leak_summary["total_leaks"]),
                unit="count",
                timestamp=current_time,
                category="memory",
                metadata={
                    "severity_breakdown": leak_summary.get("severity_breakdown", {})
                },
            )
        )

        return metrics

    def generate_report(self) -> Dict[str, Any]:
        """メモリ監視レポートを生成

        Returns:
            レポートデータ
        """
        current_time = time.time()

        # 基本統計
        memory_stats = self.get_memory_usage()
        leak_summary = self.leak_detector.get_leak_summary()

        # トレンド分析
        trend_analysis = self.memory_sampler.analyze_memory_trend()

        # 詳細情報
        detailed_leaks = self.leak_detector.get_detailed_leaks()

        return {
            "timestamp": current_time,
            "monitoring_duration": self.memory_sampler.get_monitoring_duration(),
            "total_snapshots": self.memory_sampler.get_snapshot_count(),
            "memory_stats": memory_stats,
            "leak_summary": leak_summary,
            "trend_analysis": trend_analysis,
            "detailed_leaks": detailed_leaks,
            "recommendations": self._generate_recommendations(),
        }

    def _generate_recommendations(self) -> List[str]:
        """改善提案を生成

        Returns:
            改善提案のリスト
        """
        recommendations = []

        # リークベースの提案
        recommendations.extend(self.leak_detector.generate_recommendations())

        # メモリ使用量ベースの提案
        snapshots = self.memory_sampler.snapshots
        if snapshots:
            latest_memory = snapshots[-1].memory_mb
            if latest_memory > 1000:  # 1GB以上
                recommendations.append(
                    "High memory usage detected. Consider implementing memory optimization strategies."
                )

        # オブジェクト追跡ベースの提案
        recommendations.extend(self.object_monitor.generate_recommendations())

        return recommendations

    def cleanup(self) -> None:
        """リソースのクリーンアップ"""
        self.stop_monitoring()
        self.memory_sampler.clear_snapshots()
        self.leak_detector.clear_leaks()
        self.object_monitor.clear_tracking()
        super().cleanup()
