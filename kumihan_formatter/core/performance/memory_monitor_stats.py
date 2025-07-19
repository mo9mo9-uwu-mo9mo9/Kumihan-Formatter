"""
メモリ監視統計収集機能 - スナップショットと統計
メモリ監視の統計収集とスナップショット取得
Issue #402対応 - パフォーマンス最適化
"""

import gc
import threading
import time
import weakref
from collections import defaultdict
from typing import Any

from ..utilities.logger import get_logger
from .memory_types import HAS_PSUTIL, MemorySnapshot

if HAS_PSUTIL:
    import psutil


class MemoryStatsCollector:
    """メモリ監視システムの統計収集機能
    基本機能:
    - スナップショット取得
    - メモリ使用量情報の計算
    - 統計データの管理
    """

    def __init__(self, max_snapshots: int = 1000, enable_object_tracking: bool = True):
        """統計収集機能を初期化

        Args:
            max_snapshots: 保持する最大スナップショット数
            enable_object_tracking: オブジェクト追跡を有効にするか
        """
        self.logger = get_logger(__name__)
        self.max_snapshots = max_snapshots
        self.enable_object_tracking = enable_object_tracking

        # データストレージ
        self.snapshots: list[MemorySnapshot] = []
        self.custom_objects: dict[str, set[weakref.ReferenceType[Any]]] = defaultdict(
            set
        )
        self._lock = threading.RLock()

        # psutil サポート確認
        if HAS_PSUTIL:
            self.logger.info("psutil が利用可能です - 詳細なメモリ情報を取得します")
        else:
            self.logger.warning(
                "psutil が利用できません - 基本的なメモリ情報のみ利用可能"
            )

    def take_snapshot(self) -> MemorySnapshot:
        """現在のメモリ状況のスナップショットを取得

        Returns:
            MemorySnapshot: 現在のメモリ状況
        """
        timestamp = time.time()

        # ガベージコレクション情報
        gc_objects = len(gc.get_objects())

        # gc.get_stats()が利用可能な場合は統計を取得、そうでなければget_count()を使用
        if hasattr(gc, "get_stats"):
            gc_stats = gc.get_stats()
            gc_collections = [stat.get("collections", 0) for stat in gc_stats]
        else:
            gc_collections = list(gc.get_count())

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

        self.logger.debug(
            f"メモリスナップショット取得 memory_mb={snapshot.memory_mb:.1f}, "
            f"gc_objects={gc_objects}, custom_objects_count={len(custom_objects)}"
        )

        return snapshot

    def get_memory_usage(self) -> dict[str, Any]:
        """現在のメモリ使用量情報を取得

        Returns:
            dict: メモリ使用量情報
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

    def get_snapshots(self) -> list[MemorySnapshot]:
        """保存されたスナップショットを取得

        Returns:
            list[MemorySnapshot]: スナップショットのリスト
        """
        with self._lock:
            return self.snapshots.copy()

    def get_latest_snapshot(self) -> MemorySnapshot | None:
        """最新のスナップショットを取得

        Returns:
            MemorySnapshot | None: 最新のスナップショット（なければNone）
        """
        with self._lock:
            return self.snapshots[-1] if self.snapshots else None
