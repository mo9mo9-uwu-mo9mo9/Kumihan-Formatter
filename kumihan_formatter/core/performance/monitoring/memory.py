"""メモリ監視システム - 高度なメモリ追跡

Single Responsibility Principle適用: メモリ監視の責任分離
Issue #476 Phase2対応 - パフォーマンスモジュール統合
"""

import gc
import threading
import time
import weakref
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set

from ...utilities.logger import get_logger
from ..core.base import PerformanceComponent, PerformanceMetric
from ..core.metrics import MemoryLeak, MemorySnapshot

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class MemoryMonitor(PerformanceComponent):
    """高度なメモリ監視システム

    機能:
    - リアルタイムメモリ追跡
    - メモリリーク検出
    - ガベージコレクション統計
    - カスタムオブジェクト追跡
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
        self.max_snapshots = max_snapshots
        self.leak_detection_threshold = leak_detection_threshold
        self.enable_object_tracking = enable_object_tracking

        # データ保存
        self.snapshots: List[MemorySnapshot] = []
        self.detected_leaks: List[MemoryLeak] = []
        self.object_counts: Dict[str, int] = defaultdict(int)
        self.tracked_objects: Set[weakref.ref] = set()  # type: ignore

        # 監視制御
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

        # アラート設定
        self.memory_alert_threshold = 0.8  # 80%以上でアラート
        self.leak_alert_threshold = 5  # 5個以上のリークでアラート

        self.logger.info(
            f"MemoryMonitor initialized: sampling_interval={sampling_interval}, "
            f"max_snapshots={max_snapshots}, leak_threshold={leak_detection_threshold}"
        )

    def initialize(self) -> None:
        """メモリモニターを初期化"""
        if not HAS_PSUTIL:
            self.logger.warning(
                "psutil not available, limited memory monitoring functionality"
            )

        # ガベージコレクションの設定
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
                self._add_snapshot(snapshot)
                self._detect_leaks()
                self._check_alerts()
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")

    def _capture_snapshot(self) -> MemorySnapshot:
        """現在のメモリ状態のスナップショットを取得

        Returns:
            メモリスナップショット
        """
        current_time = time.time()

        # システムメモリ情報
        if HAS_PSUTIL:
            vm = psutil.virtual_memory()
            process = psutil.Process()
            process_memory = process.memory_info().rss
            total_memory = vm.total
            available_memory = vm.available
        else:
            # psutil が利用できない場合の代替手段
            process_memory = 0
            total_memory = 0
            available_memory = 0

        # ガベージコレクション統計
        gc_objects = len(gc.get_objects())
        gc_collections = [gc.get_count()[i] for i in range(3)]

        # カスタムオブジェクト追跡
        custom_objects = dict(self.object_counts) if self.enable_object_tracking else {}

        return MemorySnapshot(
            timestamp=current_time,
            total_memory=total_memory,
            available_memory=available_memory,
            process_memory=process_memory,
            gc_objects=gc_objects,
            gc_collections=gc_collections,
            custom_objects=custom_objects,
        )

    def _add_snapshot(self, snapshot: MemorySnapshot) -> None:
        """スナップショットを追加

        Args:
            snapshot: 追加するスナップショット
        """
        self.snapshots.append(snapshot)

        # 最大数を超えた場合は古いスナップショットを削除
        if len(self.snapshots) > self.max_snapshots:
            self.snapshots.pop(0)

    def _detect_leaks(self) -> None:
        """メモリリークを検出"""
        if len(self.snapshots) < 2:
            return

        current_snapshot = self.snapshots[-1]
        previous_snapshot = self.snapshots[-2]

        # プロセスメモリの増加をチェック
        memory_increase = (
            current_snapshot.process_memory - previous_snapshot.process_memory
        )
        if memory_increase > self.leak_detection_threshold * 1024 * 1024:  # MB単位
            leak = MemoryLeak(
                object_type="process_memory",
                count_increase=1,
                size_estimate=memory_increase,
                first_detected=current_snapshot.timestamp,
                last_detected=current_snapshot.timestamp,
                severity=self._determine_leak_severity(memory_increase),
            )
            self.detected_leaks.append(leak)

        # カスタムオブジェクトの増加をチェック
        if self.enable_object_tracking:
            for obj_type, current_count in current_snapshot.custom_objects.items():
                previous_count = previous_snapshot.custom_objects.get(obj_type, 0)
                count_increase = current_count - previous_count

                if count_increase > self.leak_detection_threshold:
                    leak = MemoryLeak(
                        object_type=obj_type,
                        count_increase=count_increase,
                        size_estimate=count_increase * 1024,  # 推定サイズ
                        first_detected=current_snapshot.timestamp,
                        last_detected=current_snapshot.timestamp,
                        severity=self._determine_leak_severity(count_increase * 1024),
                    )
                    self.detected_leaks.append(leak)

    def _determine_leak_severity(self, size_bytes: int) -> str:
        """リークの重要度を判定

        Args:
            size_bytes: リークサイズ（バイト）

        Returns:
            重要度レベル
        """
        size_mb = size_bytes / 1024 / 1024
        if size_mb >= 100:
            return "critical"
        elif size_mb >= 50:
            return "high"
        elif size_mb >= 10:
            return "medium"
        else:
            return "low"

    def _check_alerts(self) -> None:
        """アラートをチェック"""
        if not self.snapshots:
            return

        latest_snapshot = self.snapshots[-1]

        # メモリ使用量アラート
        if HAS_PSUTIL:
            memory_usage_ratio = (
                latest_snapshot.total_memory - latest_snapshot.available_memory
            ) / latest_snapshot.total_memory
            if memory_usage_ratio > self.memory_alert_threshold:
                self.logger.warning(
                    f"High memory usage detected: {memory_usage_ratio:.1%} "
                    f"(threshold: {self.memory_alert_threshold:.1%})"
                )

        # リークアラート
        recent_leaks = [
            leak
            for leak in self.detected_leaks
            if leak.severity in ["high", "critical"]
        ]
        if len(recent_leaks) >= self.leak_alert_threshold:
            self.logger.warning(
                f"Multiple memory leaks detected: {len(recent_leaks)} leaks"
            )

    def track_object(self, obj: Any, object_type: str) -> None:
        """オブジェクトを追跡対象に追加

        Args:
            obj: 追跡するオブジェクト
            object_type: オブジェクトの種類
        """
        if not self.enable_object_tracking:
            return

        def cleanup_callback(ref: weakref.ref) -> None:  # type: ignore
            self.tracked_objects.discard(ref)
            self.object_counts[object_type] -= 1

        ref = weakref.ref(obj, cleanup_callback)
        self.tracked_objects.add(ref)
        self.object_counts[object_type] += 1

    def get_memory_usage(self) -> Dict[str, float]:
        """現在のメモリ使用量を取得

        Returns:
            メモリ使用量情報
        """
        if not self.snapshots:
            return {}

        latest_snapshot = self.snapshots[-1]
        return {
            "process_memory_mb": latest_snapshot.memory_mb,
            "available_memory_mb": latest_snapshot.available_mb,
            "gc_objects": float(latest_snapshot.gc_objects),
            "tracked_objects": float(sum(self.object_counts.values())),
        }

    def get_leak_summary(self) -> Dict[str, Any]:
        """リーク検出のサマリーを取得

        Returns:
            リークサマリー
        """
        if not self.detected_leaks:
            return {"total_leaks": 0, "severity_breakdown": {}}

        severity_breakdown: Dict[str, int] = defaultdict(int)
        for leak in self.detected_leaks:
            severity_breakdown[leak.severity] += 1

        return {
            "total_leaks": len(self.detected_leaks),
            "severity_breakdown": dict(severity_breakdown),
            "latest_leak_time": max(leak.last_detected for leak in self.detected_leaks),
        }

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

        leak_summary = self.get_leak_summary()
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
        leak_summary = self.get_leak_summary()

        # トレンド分析
        trend_analysis = self._analyze_memory_trend()

        # 詳細情報
        detailed_leaks = [
            {
                "object_type": leak.object_type,
                "count_increase": leak.count_increase,
                "size_estimate_mb": leak.size_estimate / 1024 / 1024,
                "age_seconds": leak.age_seconds,
                "estimated_leak_rate": leak.estimated_leak_rate,
                "severity": leak.severity,
            }
            for leak in self.detected_leaks
        ]

        return {
            "timestamp": current_time,
            "monitoring_duration": (
                current_time - self.snapshots[0].timestamp if self.snapshots else 0
            ),
            "total_snapshots": len(self.snapshots),
            "memory_stats": memory_stats,
            "leak_summary": leak_summary,
            "trend_analysis": trend_analysis,
            "detailed_leaks": detailed_leaks,
            "recommendations": self._generate_recommendations(),
        }

    def _analyze_memory_trend(self) -> Dict[str, Any]:
        """メモリ使用量のトレンドを分析

        Returns:
            トレンド分析結果
        """
        if len(self.snapshots) < 2:
            return {}

        # 最近のスナップショットを使用
        recent_snapshots = self.snapshots[-min(100, len(self.snapshots)) :]
        memory_values = [snap.memory_mb for snap in recent_snapshots]

        if len(memory_values) < 2:
            return {}

        # 傾向計算
        import statistics

        avg_memory = statistics.mean(memory_values)
        trend = "increasing" if memory_values[-1] > memory_values[0] else "decreasing"
        volatility = statistics.stdev(memory_values) if len(memory_values) > 1 else 0

        return {
            "average_memory_mb": avg_memory,
            "trend": trend,
            "volatility": volatility,
            "peak_memory_mb": max(memory_values),
            "min_memory_mb": min(memory_values),
        }

    def _generate_recommendations(self) -> List[str]:
        """改善提案を生成

        Returns:
            改善提案のリスト
        """
        recommendations = []

        # リークベースの提案
        if self.detected_leaks:
            high_severity_leaks = [
                leak
                for leak in self.detected_leaks
                if leak.severity in ["high", "critical"]
            ]
            if high_severity_leaks:
                recommendations.append(
                    "Critical memory leaks detected. Consider reviewing object lifecycle management."
                )

        # メモリ使用量ベースの提案
        if self.snapshots:
            latest_memory = self.snapshots[-1].memory_mb
            if latest_memory > 1000:  # 1GB以上
                recommendations.append(
                    "High memory usage detected. Consider implementing memory optimization strategies."
                )

        # オブジェクト追跡ベースの提案
        if self.enable_object_tracking and self.object_counts:
            max_objects = max(self.object_counts.values())
            if max_objects > 10000:
                recommendations.append(
                    "Large number of tracked objects. Consider object pooling or caching strategies."
                )

        return recommendations

    def cleanup(self) -> None:
        """リソースのクリーンアップ"""
        self.stop_monitoring()
        self.snapshots.clear()
        self.detected_leaks.clear()
        self.object_counts.clear()
        self.tracked_objects.clear()
        super().cleanup()
