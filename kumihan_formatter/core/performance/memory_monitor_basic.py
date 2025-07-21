"""
メモリ監視基本機能 - 監視制御とループ
メモリ監視の基本機能（開始・停止・監視ループ）
Issue #402対応 - パフォーマンス最適化
"""

import threading
import time
from typing import Callable, Optional, Union

from ..utilities.logger import get_logger


class MemoryMonitorBasic:
    """メモリ監視システムの基本制御機能
    基本機能:
    - 監視の開始・停止制御
    - 監視ループの実行
    - 基本的な設定管理
    """

    def __init__(
        self,
        sampling_interval: float = 1.0,
        max_snapshots: int = 1000,
        leak_detection_threshold: int = 10,
        enable_object_tracking: bool = True,
    ):
        """メモリモニター基本機能を初期化

        Args:
            sampling_interval: サンプリング間隔（秒）
            max_snapshots: 保持する最大スナップショット数
            leak_detection_threshold: リーク検出の閾値
            enable_object_tracking: オブジェクト追跡を有効にするか
        """
        self.logger = get_logger(__name__)
        self.logger.info(
            f"メモリモニター基本機能初期化開始 sampling_interval={sampling_interval}, "
            f"max_snapshots={max_snapshots}, enable_object_tracking={enable_object_tracking}"
        )

        # 設定
        self.sampling_interval = sampling_interval
        self.max_snapshots = max_snapshots
        self.leak_detection_threshold = leak_detection_threshold
        self.enable_object_tracking = enable_object_tracking

        # 統計
        self.stats: dict[str, Union[int, float, None]] = {
            "total_snapshots": 0,
            "monitoring_start_time": None,
            "total_monitoring_time": 0.0,
        }

        # 制御
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()

        # コールバック関数（外部から設定）
        self._snapshot_callback: Optional[Callable[[], None]] = None

        self.logger.info("メモリモニター基本機能初期化完了")

    def set_snapshot_callback(self, callback: Callable[[], None]) -> None:
        """スナップショット取得コールバックを設定

        Args:
            callback: スナップショット取得を実行する関数
        """
        self._snapshot_callback = callback

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
            if self.stats["monitoring_start_time"] is not None:
                total_time = self.stats["total_monitoring_time"]
                if isinstance(total_time, (int, float)):
                    self.stats["total_monitoring_time"] = total_time + (
                        time.time() - self.stats["monitoring_start_time"]
                    )

    def _monitor_loop(self) -> None:
        """監視ループ（別スレッドで実行）"""
        self.logger.info("メモリ監視ループ開始")

        while self._monitoring:
            try:
                if self._snapshot_callback:
                    self._snapshot_callback()
                time.sleep(self.sampling_interval)
            except Exception as e:
                self.logger.error(f"監視ループエラー: {e}")
                time.sleep(self.sampling_interval)

        self.logger.info("メモリ監視ループ終了")

    def is_monitoring(self) -> bool:
        """監視中かどうかを確認

        Returns:
            bool: 監視中の場合True
        """
        return self._monitoring

    def get_stats(self) -> dict[str, Union[int, float, None]]:
        """監視統計を取得

        Returns:
            dict: 統計情報
        """
        with self._lock:
            return self.stats.copy()
