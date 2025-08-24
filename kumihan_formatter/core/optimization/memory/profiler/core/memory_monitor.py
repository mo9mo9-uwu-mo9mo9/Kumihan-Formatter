"""メモリ監視とスナップショット取得"""

from __future__ import annotations

import gc
import threading
import time
import tracemalloc
from collections import defaultdict, deque
from threading import RLock
from typing import Dict, List, Optional, Tuple

import psutil

from kumihan_formatter.core.utilities.logger import get_logger
from ..config import ProfilerConfig
from ..snapshot import MemorySnapshot

logger = get_logger(__name__)


class MemoryMonitor:
    """
    メモリ監視クラス

    リアルタイムでメモリ使用量を監視し、スナップショットを取得します。
    """

    def __init__(self, config: Optional[ProfilerConfig] = None) -> None:
        """
        メモリ監視を初期化します。

        Args:
            config: プロファイラー設定
        """
        try:
            self._config = config or ProfilerConfig()
            self._process = psutil.Process()

            # プロファイリングデータ
            self._snapshots: deque[MemorySnapshot] = deque(maxlen=1000)
            self._lock = RLock()

            # 監視スレッド
            self._monitoring_thread: Optional[threading.Thread] = None
            self._stop_monitoring = threading.Event()
            self._is_profiling = False

            # tracemalloc初期化
            if self._config.enable_tracemalloc and not tracemalloc.is_tracing():
                tracemalloc.start(self._config.tracemalloc_limit)

            logger.info("MemoryMonitor初期化完了")

        except Exception as e:
            logger.error(f"MemoryMonitor初期化エラー: {str(e)}")
            raise

    def start_profiling(self) -> None:
        """メモリプロファイリングを開始します。"""
        try:
            if self._is_profiling:
                logger.warning("プロファイリングは既に開始されています")
                return

            self._is_profiling = True
            self._stop_monitoring.clear()

            self._monitoring_thread = threading.Thread(
                target=self._profiling_loop, daemon=True
            )
            self._monitoring_thread.start()

            logger.info("メモリプロファイリング開始")

        except Exception as e:
            logger.error(f"プロファイリング開始エラー: {str(e)}")
            raise

    def stop_profiling(self) -> None:
        """メモリプロファイリングを停止します。"""
        try:
            if not self._is_profiling:
                return

            self._is_profiling = False
            self._stop_monitoring.set()

            if self._monitoring_thread:
                self._monitoring_thread.join(timeout=10.0)

            logger.info("メモリプロファイリング停止")

        except Exception as e:
            logger.error(f"プロファイリング停止エラー: {str(e)}")

    def _profiling_loop(self) -> None:
        """プロファイリングループ処理"""
        try:
            while not self._stop_monitoring.wait(self._config.snapshot_interval):
                snapshot = self.take_memory_snapshot()

                with self._lock:
                    self._snapshots.append(snapshot)

        except Exception as e:
            logger.error(f"プロファイリングループエラー: {str(e)}")

    def take_memory_snapshot(self) -> MemorySnapshot:
        """メモリスナップショットを取得します。"""
        try:
            # プロセス情報取得
            memory_info = self._process.memory_info()
            virtual_memory = psutil.virtual_memory()

            # GC統計
            gc_stats = gc.get_stats()

            # オブジェクト統計
            object_counts = self._get_object_counts()
            top_objects = self._get_top_objects()

            # メモリ断片化率計算
            fragmentation_ratio = self._calculate_fragmentation_ratio()

            snapshot = MemorySnapshot(
                timestamp=time.time(),
                process_memory_mb=memory_info.rss / (1024 * 1024),
                virtual_memory_mb=virtual_memory.total / (1024 * 1024),
                memory_percent=virtual_memory.percent,
                gc_stats=gc_stats,
                object_counts=object_counts,
                top_objects=top_objects,
                fragmentation_ratio=fragmentation_ratio,
            )

            logger.debug(
                f"メモリスナップショット取得: {snapshot.process_memory_mb:.1f}MB"
            )
            return snapshot

        except Exception as e:
            logger.error(f"スナップショット取得エラー: {str(e)}")
            # エラー時はダミーデータ
            return MemorySnapshot(
                timestamp=time.time(),
                process_memory_mb=0.0,
                virtual_memory_mb=0.0,
                memory_percent=0.0,
                gc_stats=[],
                object_counts={},
                top_objects=[],
                fragmentation_ratio=0.0,
            )

    def _get_object_counts(self) -> Dict[str, int]:
        """オブジェクト数統計を取得します。"""
        try:
            object_counts: Dict[str, int] = defaultdict(int)

            for obj in gc.get_objects():
                obj_type = type(obj).__name__
                object_counts[obj_type] += 1

            return dict(object_counts)

        except Exception as e:
            logger.error(f"オブジェクト数統計取得エラー: {str(e)}")
            return {}

    def _get_top_objects(self, limit: int = 20) -> List[Tuple[str, int, int]]:
        """メモリ使用量上位オブジェクトを取得します。"""
        try:
            if not tracemalloc.is_tracing():
                return []

            # tracemalloc統計取得
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics("filename")

            top_objects = []
            for stat in top_stats[:limit]:
                filename = stat.traceback.format()[0] if stat.traceback else "unknown"
                size_mb = stat.size / (1024 * 1024)
                top_objects.append((filename, stat.count, int(size_mb * 1024)))

            return top_objects

        except Exception as e:
            logger.error(f"上位オブジェクト取得エラー: {str(e)}")
            return []

    def _calculate_fragmentation_ratio(self) -> float:
        """メモリ断片化率を計算します。"""
        try:
            # 簡易断片化率計算（実際の実装では詳細な断片化分析が必要）
            virtual_memory = psutil.virtual_memory()
            available_ratio = virtual_memory.available / virtual_memory.total

            # 利用可能メモリが少ないほど断片化していると仮定
            fragmentation_ratio = 1.0 - available_ratio

            return min(fragmentation_ratio, 1.0)

        except Exception as e:
            logger.error(f"断片化率計算エラー: {str(e)}")
            return 0.0

    @property
    def snapshots(self) -> deque[MemorySnapshot]:
        """スナップショット履歴"""
        with self._lock:
            return self._snapshots.copy()

    @property
    def is_profiling(self) -> bool:
        """プロファイリング状態"""
        return self._is_profiling
