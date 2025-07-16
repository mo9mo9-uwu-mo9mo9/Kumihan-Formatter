"""メモリサンプリングシステム - メモリスナップショットの収集と管理

Single Responsibility Principle適用: メモリサンプリングの責任分離
Issue #476 Phase4対応 - memory.py分割による技術的負債削減
"""

import gc
import time
from typing import Any, Dict, List

from ...utilities.logger import get_logger
from ..core.metrics import MemorySnapshot

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class MemorySampler:
    """メモリサンプリングとスナップショット管理システム

    責任:
    - メモリスナップショットの取得
    - スナップショットの保存と管理
    - システムメモリ情報の収集
    """

    def __init__(self, max_snapshots: int = 1000):
        """メモリサンプラーを初期化

        Args:
            max_snapshots: 保持する最大スナップショット数
        """
        self.max_snapshots = max_snapshots
        self.snapshots: List[MemorySnapshot] = []
        self.logger = get_logger(__name__)

        if not HAS_PSUTIL:
            self.logger.warning(
                "psutil not available, limited memory monitoring functionality"
            )

    def capture_snapshot(self) -> MemorySnapshot:
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

        return MemorySnapshot(
            timestamp=current_time,
            total_memory=total_memory,
            available_memory=available_memory,
            process_memory=process_memory,
            gc_objects=gc_objects,
            gc_collections=gc_collections,
            custom_objects={},  # 外部から設定される
        )

    def add_snapshot(self, snapshot: MemorySnapshot) -> None:
        """スナップショットを追加

        Args:
            snapshot: 追加するスナップショット
        """
        self.snapshots.append(snapshot)

        # 最大数を超えた場合は古いスナップショットを削除
        if len(self.snapshots) > self.max_snapshots:
            self.snapshots.pop(0)

    def get_latest_snapshot(self) -> MemorySnapshot | None:
        """最新のスナップショットを取得

        Returns:
            最新のスナップショット、存在しない場合はNone
        """
        return self.snapshots[-1] if self.snapshots else None

    def get_snapshots_range(
        self, start_time: float, end_time: float
    ) -> List[MemorySnapshot]:
        """指定時間範囲のスナップショットを取得

        Args:
            start_time: 開始時刻
            end_time: 終了時刻

        Returns:
            指定範囲のスナップショット
        """
        return [
            snapshot
            for snapshot in self.snapshots
            if start_time <= snapshot.timestamp <= end_time
        ]

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
        }

    def analyze_memory_trend(self) -> Dict[str, Any]:
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

    def clear_snapshots(self) -> None:
        """すべてのスナップショットをクリア"""
        self.snapshots.clear()

    def get_snapshot_count(self) -> int:
        """保存されているスナップショット数を取得

        Returns:
            スナップショット数
        """
        return len(self.snapshots)

    def get_monitoring_duration(self) -> float:
        """監視継続時間を取得

        Returns:
            監視継続時間（秒）、スナップショットが存在しない場合は0
        """
        if not self.snapshots:
            return 0.0
        return self.snapshots[-1].timestamp - self.snapshots[0].timestamp
