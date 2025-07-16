"""
メモリ監視コア機能 - 基本監視とスナップショット

メモリ監視の基本機能とスナップショット取得
Issue #402対応 - パフォーマンス最適化
"""

import gc
import threading
import time
import weakref
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set

from ..utilities.logger import get_logger
from .memory_types import HAS_PSUTIL, MemorySnapshot

if HAS_PSUTIL:
    import psutil


class MemoryMonitor:
    """メモリ監視システムのコア機能

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
        self.logger = get_logger(__name__)
        self.logger.info(
            f"メモリモニター初期化開始 sampling_interval={sampling_interval}, "
            f"max_snapshots={max_snapshots}, enable_object_tracking={enable_object_tracking}"
        )

        # 設定
        self.sampling_interval = sampling_interval
        self.max_snapshots = max_snapshots
        self.leak_detection_threshold = leak_detection_threshold
        self.enable_object_tracking = enable_object_tracking

        # データストレージ
        self.snapshots: List[MemorySnapshot] = []
        self.custom_objects: Dict[str, Set[weakref.ReferenceType]] = defaultdict(set)

        # 統計
        self.stats = {
            "total_snapshots": 0,
            "monitoring_start_time": None,
            "total_monitoring_time": 0.0,
        }

        # 制御
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()

        # psutil サポート確認
        if HAS_PSUTIL:
            self.logger.info("psutil が利用可能です - 詳細なメモリ情報を取得します")
        else:
            self.logger.warning(
                "psutil が利用できません - 基本的なメモリ情報のみ利用可能"
            )

        self.logger.info("メモリモニター初期化完了")

    def start_monitoring(self) -> None:
        """メモリ監視を開始"""
        with self._lock:
            if self._monitoring:
                self.logger.warning("メモリ監視は既に開始されています")
                return

            self.logger.info(
                f"メモリ監視を開始します interval={self.sampling_interval}"
            )
            self._monitoring = True
            self.stats["monitoring_start_time"] = time.time()

            self._monitor_thread = threading.Thread(
                target=self._monitor_loop, daemon=True, name="MemoryMonitor"
            )
            self._monitor_thread.start()

    def stop_monitoring(self) -> None:
        """メモリ監視を停止"""
        with self._lock:
            if not self._monitoring:
                self.logger.warning("メモリ監視は開始されていません")
                return

            self.logger.info("メモリ監視を停止します")
            self._monitoring = False

            if self._monitor_thread and self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=5.0)

            # 統計更新
            if self.stats["monitoring_start_time"]:
                self.stats["total_monitoring_time"] += (
                    time.time() - self.stats["monitoring_start_time"]
                )

    def take_snapshot(self) -> MemorySnapshot:
        """現在のメモリ状況のスナップショットを取得

        Returns:
            MemorySnapshot: 現在のメモリ状況
        """
        timestamp = time.time()

        # ガベージコレクション情報
        gc_objects = len(gc.get_objects())
        gc_collections = list(gc.get_stats()) if hasattr(gc, "get_stats") else [0, 0, 0]
        if not isinstance(gc_collections, list):
            gc_collections = [gc.get_count()[i] for i in range(3)]

        # システムメモリ情報（psutil利用可能時）
        total_memory = 0
        available_memory = 0
        process_memory = 0

        if HAS_PSUTIL:
            try:
                # システム全体のメモリ
                virtual_memory = psutil.virtual_memory()
                total_memory = virtual_memory.total
                available_memory = virtual_memory.available

                # 現在のプロセスメモリ
                process = psutil.Process()
                process_memory = process.memory_info().rss

            except Exception as e:
                self.logger.warning(f"psutilでメモリ情報取得に失敗: {e}")

        # カスタムオブジェクト数を集計
        custom_objects = {}
        if self.enable_object_tracking:
            for obj_type, weak_refs in self.custom_objects.items():
                # 生きているオブジェクトのみカウント
                alive_refs = [ref for ref in weak_refs if ref() is not None]
                custom_objects[obj_type] = len(alive_refs)

                # 死んでいる参照を削除
                self.custom_objects[obj_type] = set(alive_refs)

        snapshot = MemorySnapshot(
            timestamp=timestamp,
            total_memory=total_memory,
            available_memory=available_memory,
            process_memory=process_memory,
            gc_objects=gc_objects,
            gc_collections=gc_collections,
            custom_objects=custom_objects,
        )

        # スナップショットを保存（最大数を超えた場合は古いものを削除）
        with self._lock:
            self.snapshots.append(snapshot)
            if len(self.snapshots) > self.max_snapshots:
                self.snapshots = self.snapshots[-self.max_snapshots :]

            self.stats["total_snapshots"] += 1

        self.logger.debug(
            f"メモリスナップショット取得 memory_mb={snapshot.memory_mb:.1f}, "
            f"gc_objects={gc_objects}, custom_objects_count={len(custom_objects)}"
        )

        return snapshot

    def register_object(self, obj: Any, obj_type: str) -> None:
        """カスタムオブジェクトを追跡に登録

        Args:
            obj: 追跡するオブジェクト
            obj_type: オブジェクトのタイプ名
        """
        if not self.enable_object_tracking:
            return

        try:
            weak_ref = weakref.ref(obj)
            with self._lock:
                self.custom_objects[obj_type].add(weak_ref)

            self.logger.debug(f"オブジェクト追跡に登録: {obj_type}")

        except TypeError:
            # weak reference を作成できないオブジェクト
            self.logger.debug(f"weak reference 作成不可のオブジェクト: {obj_type}")

    def get_memory_usage(self) -> Dict[str, Any]:
        """現在のメモリ使用量情報を取得

        Returns:
            Dict: メモリ使用量情報
        """
        current_snapshot = self.take_snapshot()

        return {
            "timestamp": current_snapshot.timestamp,
            "process_memory_mb": current_snapshot.memory_mb,
            "available_memory_mb": current_snapshot.available_mb,
            "memory_usage_ratio": current_snapshot.memory_usage_ratio,
            "gc_objects": current_snapshot.gc_objects,
            "custom_objects": current_snapshot.custom_objects,
            "gc_collections": current_snapshot.gc_collections,
            "is_warning": current_snapshot.is_memory_warning,
            "is_critical": current_snapshot.is_memory_critical,
        }

    def _monitor_loop(self) -> None:
        """監視ループ（別スレッドで実行）"""
        self.logger.info("メモリ監視ループ開始")

        while self._monitoring:
            try:
                self.take_snapshot()
                time.sleep(self.sampling_interval)
            except Exception as e:
                self.logger.error(f"監視ループエラー: {e}")
                time.sleep(self.sampling_interval)

        self.logger.info("メモリ監視ループ終了")

    def _cleanup_weak_refs(self) -> None:
        """死んでいるweak referenceをクリーンアップ"""
        if not self.enable_object_tracking:
            return

        cleaned_count = 0
        with self._lock:
            for obj_type in list(self.custom_objects.keys()):
                alive_refs = set()
                for weak_ref in self.custom_objects[obj_type]:
                    if weak_ref() is not None:
                        alive_refs.add(weak_ref)
                    else:
                        cleaned_count += 1

                if alive_refs:
                    self.custom_objects[obj_type] = alive_refs
                else:
                    del self.custom_objects[obj_type]

        if cleaned_count > 0:
            self.logger.debug(f"weak reference クリーンアップ: {cleaned_count}個")

    def clear_data(self) -> None:
        """蓄積されたデータをクリア"""
        with self._lock:
            snapshot_count = len(self.snapshots)
            object_types = len(self.custom_objects)

            self.snapshots.clear()
            self.custom_objects.clear()

            # 統計をリセット（一部は保持）
            old_total_time = self.stats.get("total_monitoring_time", 0.0)
            self.stats = {
                "total_snapshots": 0,
                "monitoring_start_time": None,
                "total_monitoring_time": old_total_time,
            }

        self.logger.info(
            f"メモリ監視データをクリア cleared_snapshots={snapshot_count}, "
            f"cleared_object_types={object_types}"
        )
