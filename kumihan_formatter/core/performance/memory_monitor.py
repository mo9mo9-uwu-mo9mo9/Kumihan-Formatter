"""
メモリ監視システム - 高度なメモリ追跡

メモリリーク検出とメモリ使用量最適化
Issue #402対応 - パフォーマンス最適化
"""

import gc
import threading
import time
import weakref
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from ...utilities.logger import get_logger

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


@dataclass
class MemorySnapshot:
    """メモリスナップショット"""

    timestamp: float
    total_memory: int  # バイト
    available_memory: int
    process_memory: int
    gc_objects: int
    gc_collections: List[int]  # 各世代のGC回数
    custom_objects: Dict[str, int] = field(default_factory=dict)

    @property
    def memory_mb(self) -> float:
        """メモリ使用量（MB）"""
        return self.process_memory / 1024 / 1024

    @property
    def available_mb(self) -> float:
        """利用可能メモリ（MB）"""
        return self.available_memory / 1024 / 1024


@dataclass
class MemoryLeak:
    """メモリリーク情報"""

    object_type: str
    count_increase: int
    size_estimate: int
    first_detected: float
    last_detected: float
    severity: str = "unknown"  # low, medium, high, critical

    @property
    def age_seconds(self) -> float:
        """リーク検出からの経過時間"""
        return self.last_detected - self.first_detected

    @property
    def estimated_leak_rate(self) -> float:
        """推定リーク率（オブジェクト/秒）"""
        if self.age_seconds > 0:
            return self.count_increase / self.age_seconds
        return 0


class MemoryMonitor:
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
        self.logger = get_logger(__name__)
        self.logger.info(
            f"MemoryMonitor初期化開始: interval={sampling_interval}s, max_snapshots={max_snapshots}"
        )

        self.sampling_interval = sampling_interval
        self.max_snapshots = max_snapshots
        self.leak_detection_threshold = leak_detection_threshold
        self.enable_object_tracking = enable_object_tracking

        # スナップショット履歴
        self.snapshots: List[MemorySnapshot] = []

        # メモリリーク検出
        self.detected_leaks: Dict[str, MemoryLeak] = {}
        self.object_counts: Dict[str, List[Tuple[float, int]]] = defaultdict(list)

        # 監視対象オブジェクト
        self.tracked_objects: Dict[str, Set[Any]] = defaultdict(set)
        self.weak_refs: Dict[str, List[weakref.ReferenceType]] = defaultdict(list)

        # モニタリング制御
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # アラート設定
        self.memory_alerts = {
            "high_usage": 80,  # 使用率80%以上
            "critical_usage": 95,  # 使用率95%以上
            "rapid_increase": 50,  # 50MB/秒以上の増加
        }

        # 統計
        self.stats = {
            "total_snapshots": 0,
            "leaks_detected": 0,
            "alerts_triggered": 0,
            "gc_forced": 0,
        }

        self.logger.info(
            f"MemoryMonitor初期化完了: object_tracking={enable_object_tracking}"
        )

    def start_monitoring(self):
        """メモリ監視を開始"""
        if self._monitoring:
            self.logger.warning("メモリ監視は既に開始されています")
            return

        self.logger.info("メモリ監視を開始")
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        self.logger.debug("メモリ監視スレッド開始完了")

    def stop_monitoring(self):
        """メモリ監視を停止"""
        if not self._monitoring:
            self.logger.warning("メモリ監視は既に停止されています")
            return

        self.logger.info("メモリ監視を停止")
        self._monitoring = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5)
            self.logger.debug("メモリ監視スレッド停止完了")

    def take_snapshot(self) -> MemorySnapshot:
        """手動でメモリスナップショットを取得"""
        timestamp = time.perf_counter()

        # システムメモリ情報
        if HAS_PSUTIL:
            try:
                memory = psutil.virtual_memory()
                process = psutil.Process()
                total_memory = memory.total
                available_memory = memory.available
                process_memory = process.memory_info().rss
                self.logger.debug(
                    f"メモリ情報取得: process={process_memory/1024/1024:.1f}MB, available={available_memory/1024/1024:.1f}MB"
                )
            except Exception as e:
                self.logger.error(f"システムメモリ情報取得エラー: {e}")
                total_memory = available_memory = process_memory = 0
        else:
            self.logger.debug("psutil未利用のためメモリ情報は0")
            total_memory = 0
            available_memory = 0
            process_memory = 0

        # ガベージコレクション情報
        gc_objects = len(gc.get_objects())
        gc_collections = list(gc.get_stats()) if hasattr(gc, "get_stats") else [0, 0, 0]

        # カスタムオブジェクト追跡
        custom_objects = {}
        if self.enable_object_tracking:
            for obj_type, obj_set in self.tracked_objects.items():
                # 生きているオブジェクトをカウント
                alive_count = sum(1 for obj in obj_set if obj is not None)
                custom_objects[obj_type] = alive_count

            # WeakReferenceをクリーンアップ
            self._cleanup_weak_refs()

        snapshot = MemorySnapshot(
            timestamp=timestamp,
            total_memory=total_memory,
            available_memory=available_memory,
            process_memory=process_memory,
            gc_objects=gc_objects,
            gc_collections=(
                [stat.get("collections", 0) for stat in gc_collections]
                if isinstance(gc_collections[0], dict)
                else gc_collections
            ),
            custom_objects=custom_objects,
        )

        with self._lock:
            self.snapshots.append(snapshot)
            if len(self.snapshots) > self.max_snapshots:
                removed_snapshot = self.snapshots.pop(0)
                self.logger.debug(
                    f"古いスナップショット削除: {len(self.snapshots)}/{self.max_snapshots}"
                )

            self.stats["total_snapshots"] += 1

            if self.stats["total_snapshots"] % 10 == 0:
                self.logger.debug(
                    f"メモリスナップショット数: {self.stats['total_snapshots']}"
                )

        # リーク検出
        self._detect_memory_leaks(snapshot)

        # アラート検査
        self._check_memory_alerts(snapshot)

        return snapshot

    def register_object(self, obj: Any, obj_type: str):
        """オブジェクトを追跡対象に登録

        Args:
            obj: 追跡するオブジェクト
            obj_type: オブジェクトタイプ名
        """
        if not self.enable_object_tracking:
            self.logger.debug(f"オブジェクト追跡無効のため登録スキップ: {obj_type}")
            return

        with self._lock:
            # WeakReferenceを使用してオブジェクトを追跡
            weak_ref = weakref.ref(obj)
            self.weak_refs[obj_type].append(weak_ref)
            self.logger.debug(
                f"オブジェクト登録: {obj_type} (合計: {len(self.weak_refs[obj_type])}個)"
            )

    def get_memory_usage(self) -> Dict[str, Any]:
        """現在のメモリ使用量を取得"""
        if not self.snapshots:
            self.take_snapshot()

        latest = self.snapshots[-1]

        usage_info = {
            "process_memory_mb": latest.memory_mb,
            "available_memory_mb": latest.available_mb,
            "gc_objects": latest.gc_objects,
            "gc_collections": latest.gc_collections,
            "custom_objects": latest.custom_objects.copy(),
        }

        if HAS_PSUTIL and latest.total_memory > 0:
            usage_percent = (latest.process_memory / latest.total_memory) * 100
            usage_info["memory_usage_percent"] = usage_percent

        return usage_info

    def get_memory_trend(self, window_seconds: float = 60.0) -> Dict[str, Any]:
        """メモリ使用量のトレンドを分析

        Args:
            window_seconds: 分析ウィンドウ（秒）

        Returns:
            トレンド分析結果
        """
        if len(self.snapshots) < 2:
            return {"error": "Insufficient data for trend analysis"}

        current_time = time.perf_counter()
        window_start = current_time - window_seconds

        # ウィンドウ内のスナップショットを取得
        window_snapshots = [s for s in self.snapshots if s.timestamp >= window_start]

        if len(window_snapshots) < 2:
            return {"error": "Insufficient data in time window"}

        # トレンド計算
        first_snapshot = window_snapshots[0]
        last_snapshot = window_snapshots[-1]

        time_diff = last_snapshot.timestamp - first_snapshot.timestamp
        memory_diff = last_snapshot.process_memory - first_snapshot.process_memory

        memory_rate = memory_diff / time_diff if time_diff > 0 else 0
        memory_rate_mb_per_sec = memory_rate / 1024 / 1024

        # 統計計算
        memory_values = [s.process_memory for s in window_snapshots]
        avg_memory = sum(memory_values) / len(memory_values)
        max_memory = max(memory_values)
        min_memory = min(memory_values)

        return {
            "window_seconds": window_seconds,
            "snapshots_count": len(window_snapshots),
            "memory_rate_mb_per_sec": memory_rate_mb_per_sec,
            "avg_memory_mb": avg_memory / 1024 / 1024,
            "max_memory_mb": max_memory / 1024 / 1024,
            "min_memory_mb": min_memory / 1024 / 1024,
            "memory_delta_mb": memory_diff / 1024 / 1024,
            "trend": (
                "increasing"
                if memory_rate > 0
                else "decreasing" if memory_rate < 0 else "stable"
            ),
        }

    def get_memory_leaks(self) -> List[Dict[str, Any]]:
        """検出されたメモリリークの情報を取得"""
        leak_info = []

        for obj_type, leak in self.detected_leaks.items():
            leak_info.append(
                {
                    "object_type": obj_type,
                    "count_increase": leak.count_increase,
                    "size_estimate_mb": leak.size_estimate / 1024 / 1024,
                    "age_seconds": leak.age_seconds,
                    "leak_rate_per_sec": leak.estimated_leak_rate,
                    "severity": leak.severity,
                    "first_detected": leak.first_detected,
                    "last_detected": leak.last_detected,
                }
            )

        return sorted(leak_info, key=lambda x: x["severity"], reverse=True)

    def force_garbage_collection(self) -> Dict[str, Any]:
        """ガベージコレクションを強制実行"""
        self.logger.info("ガベージコレクション強制実行開始")
        before_snapshot = self.take_snapshot()

        # ガベージコレクションを実行
        collected = gc.collect()
        self.logger.info(
            f"ガベージコレクション実行完了: {collected}個のオブジェクトを回収"
        )

        after_snapshot = self.take_snapshot()

        with self._lock:
            self.stats["gc_forced"] += 1

        result = {
            "objects_collected": collected,
            "memory_before_mb": before_snapshot.memory_mb,
            "memory_after_mb": after_snapshot.memory_mb,
            "memory_freed_mb": before_snapshot.memory_mb - after_snapshot.memory_mb,
            "gc_objects_before": before_snapshot.gc_objects,
            "gc_objects_after": after_snapshot.gc_objects,
        }

        self.logger.info(
            f"GC結果: {result['memory_freed_mb']:.1f}MB解放, "
            f"{result['gc_objects_before'] - result['gc_objects_after']}個のオブジェクト削減"
        )
        return result

    def optimize_memory_settings(self) -> Dict[str, Any]:
        """メモリ設定を最適化"""
        actions_taken = []

        # ガベージコレクションの閾値を調整
        old_thresholds = gc.get_threshold()

        # より積極的なGCに設定
        new_thresholds = (500, 10, 10)  # デフォルト: (700, 10, 10)
        gc.set_threshold(*new_thresholds)
        actions_taken.append(
            f"GC thresholds changed from {old_thresholds} to {new_thresholds}"
        )

        # ガベージコレクションを実行
        gc_result = self.force_garbage_collection()
        actions_taken.append(
            f"Forced GC collected {gc_result['objects_collected']} objects"
        )

        return {
            "actions_taken": actions_taken,
            "gc_result": gc_result,
            "new_thresholds": new_thresholds,
            "old_thresholds": old_thresholds,
        }

    def generate_memory_report(self) -> str:
        """メモリ使用量レポートを生成"""
        current_usage = self.get_memory_usage()
        trend = self.get_memory_trend()
        leaks = self.get_memory_leaks()

        report_lines = [
            "Memory Usage Report",
            "=" * 50,
            f"Process Memory: {current_usage['process_memory_mb']:.1f} MB",
            f"Available Memory: {current_usage['available_memory_mb']:.1f} MB",
            f"GC Objects: {current_usage['gc_objects']:,}",
        ]

        if "memory_usage_percent" in current_usage:
            report_lines.append(
                f"Memory Usage: {current_usage['memory_usage_percent']:.1f}%"
            )

        report_lines.extend(
            [
                "",
                "Memory Trend:",
                "-" * 15,
            ]
        )

        if "error" not in trend:
            report_lines.extend(
                [
                    f"Trend: {trend['trend'].upper()}",
                    f"Rate: {trend['memory_rate_mb_per_sec']:.2f} MB/sec",
                    f"Window: {trend['window_seconds']:.1f}s",
                    f"Delta: {trend['memory_delta_mb']:.1f} MB",
                ]
            )
        else:
            report_lines.append(f"Trend: {trend['error']}")

        if leaks:
            report_lines.extend(
                [
                    "",
                    "Memory Leaks Detected:",
                    "-" * 25,
                ]
            )
            for leak in leaks[:5]:  # 上位5件
                report_lines.extend(
                    [
                        f"  {leak['object_type']} ({leak['severity'].upper()})",
                        f"    Count: +{leak['count_increase']} objects",
                        f"    Rate: {leak['leak_rate_per_sec']:.2f} objects/sec",
                        f"    Age: {leak['age_seconds']:.1f}s",
                        "",
                    ]
                )

        # 統計情報
        report_lines.extend(
            [
                "Statistics:",
                "-" * 12,
                f"Total Snapshots: {self.stats['total_snapshots']:,}",
                f"Leaks Detected: {self.stats['leaks_detected']:,}",
                f"Alerts Triggered: {self.stats['alerts_triggered']:,}",
                f"Forced GCs: {self.stats['gc_forced']:,}",
            ]
        )

        return "\n".join(report_lines)

    def _monitor_loop(self):
        """メモリ監視ループ"""
        while self._monitoring:
            try:
                self.take_snapshot()
                time.sleep(self.sampling_interval)
            except Exception as e:
                # エラーが発生してもモニタリングを継続
                self.logger.error(f"メモリ監視エラー: {e}")
                time.sleep(self.sampling_interval)

    def _detect_memory_leaks(self, snapshot: MemorySnapshot):
        """メモリリークを検出"""
        current_time = snapshot.timestamp

        # オブジェクト数の変化を追跡
        for obj_type, count in snapshot.custom_objects.items():
            self.object_counts[obj_type].append((current_time, count))

            # 古いデータを削除（24時間以上前）
            cutoff_time = current_time - 86400  # 24時間
            self.object_counts[obj_type] = [
                (t, c) for t, c in self.object_counts[obj_type] if t >= cutoff_time
            ]

            # リーク検出
            if len(self.object_counts[obj_type]) >= 10:  # 最低10個のデータポイント
                self._analyze_object_leak(obj_type, current_time)

    def _analyze_object_leak(self, obj_type: str, current_time: float):
        """オブジェクトタイプのリークを分析"""
        counts = self.object_counts[obj_type]

        if len(counts) < 2:
            return

        # 最初と最後のカウントを比較
        first_time, first_count = counts[0]
        last_time, last_count = counts[-1]

        count_increase = last_count - first_count
        time_span = last_time - first_time

        # リーク検出条件
        if (
            count_increase >= self.leak_detection_threshold and time_span > 60
        ):  # 1分以上

            if obj_type not in self.detected_leaks:
                # 新しいリーク
                leak = MemoryLeak(
                    object_type=obj_type,
                    count_increase=count_increase,
                    size_estimate=count_increase * 1024,  # 1KB/オブジェクトと仮定
                    first_detected=first_time,
                    last_detected=current_time,
                )
                leak.severity = self._calculate_leak_severity(leak)

                self.detected_leaks[obj_type] = leak
                self.logger.warning(
                    f"新しいメモリリーク検出: {obj_type}, 増加数: {count_increase}, "
                    f"深刻度: {leak.severity}"
                )

                with self._lock:
                    self.stats["leaks_detected"] += 1
            else:
                # 既存のリークを更新
                leak = self.detected_leaks[obj_type]
                leak.count_increase = count_increase
                leak.last_detected = current_time
                leak.severity = self._calculate_leak_severity(leak)

    def _calculate_leak_severity(self, leak: MemoryLeak) -> str:
        """リークの深刻度を計算"""
        rate = leak.estimated_leak_rate

        if rate > 10:  # 10オブジェクト/秒以上
            return "critical"
        elif rate > 5:  # 5オブジェクト/秒以上
            return "high"
        elif rate > 1:  # 1オブジェクト/秒以上
            return "medium"
        else:
            return "low"

    def _check_memory_alerts(self, snapshot: MemorySnapshot):
        """メモリアラートをチェック"""
        if not HAS_PSUTIL:
            return

        # 使用率アラート
        if snapshot.total_memory > 0:
            usage_percent = (snapshot.process_memory / snapshot.total_memory) * 100

            if usage_percent >= self.memory_alerts["critical_usage"]:
                self._trigger_alert(
                    "critical", f"Critical memory usage: {usage_percent:.1f}%"
                )
            elif usage_percent >= self.memory_alerts["high_usage"]:
                self._trigger_alert(
                    "warning", f"High memory usage: {usage_percent:.1f}%"
                )

        # 急激な増加アラート
        if len(self.snapshots) >= 2:
            prev_snapshot = self.snapshots[-2]
            time_diff = snapshot.timestamp - prev_snapshot.timestamp
            memory_diff = snapshot.process_memory - prev_snapshot.process_memory

            if time_diff > 0:
                rate_mb_per_sec = (memory_diff / time_diff) / 1024 / 1024
                if rate_mb_per_sec >= self.memory_alerts["rapid_increase"]:
                    self._trigger_alert(
                        "warning",
                        f"Rapid memory increase: {rate_mb_per_sec:.1f} MB/sec",
                    )

    def _trigger_alert(self, level: str, message: str):
        """アラートをトリガー"""
        with self._lock:
            self.stats["alerts_triggered"] += 1

        # ログレベルに応じた適切なログ出力
        if level == "critical":
            self.logger.critical(f"メモリアラート: {message}")
        elif level == "warning":
            self.logger.warning(f"メモリアラート: {message}")
        else:
            self.logger.info(f"メモリアラート: {message}")

    def _cleanup_weak_refs(self):
        """無効になったWeakReferenceをクリーンアップ"""
        for obj_type in list(self.weak_refs.keys()):
            alive_refs = []
            for weak_ref in self.weak_refs[obj_type]:
                if weak_ref() is not None:
                    alive_refs.append(weak_ref)

            self.weak_refs[obj_type] = alive_refs
            self.tracked_objects[obj_type] = {
                ref() for ref in alive_refs if ref() is not None
            }

    def clear_data(self):
        """全データをクリア"""
        with self._lock:
            snapshot_count = len(self.snapshots)
            leak_count = len(self.detected_leaks)

            self.snapshots.clear()
            self.detected_leaks.clear()
            self.object_counts.clear()
            self.tracked_objects.clear()
            self.weak_refs.clear()
            self.stats = {
                "total_snapshots": 0,
                "leaks_detected": 0,
                "alerts_triggered": 0,
                "gc_forced": 0,
            }

            self.logger.info(
                f"メモリモニターデータクリア完了: {snapshot_count}個のスナップショット, "
                f"{leak_count}個のリーク情報を削除"
            )
