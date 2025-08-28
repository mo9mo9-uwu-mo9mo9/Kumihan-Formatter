"""Parallel Processing Configuration - 並列処理設定専用モジュール

parser.py分割により抽出 (Phase3最適化)
並列処理関連の設定クラス
"""

import multiprocessing
import threading
from typing import Optional


class ParallelProcessingConfig:
    """並列処理設定クラス"""

    def __init__(
        self,
        max_workers: Optional[int] = None,
        chunk_size: int = 1000,
        timeout_seconds: float = 30.0,
        memory_limit_mb: float = 512.0,
        enable_monitoring: bool = True,
    ):
        """並列処理設定を初期化

        Args:
            max_workers: 最大ワーカー数（Noneの場合はCPUコア数）
            chunk_size: チャンクサイズ（行数）
            timeout_seconds: ワーカータイムアウト秒数
            memory_limit_mb: メモリ制限（MB）
            enable_monitoring: 監視機能有効化
        """
        self.max_workers = max_workers or min(multiprocessing.cpu_count(), 4)
        self.chunk_size = max(100, chunk_size)  # 最小100行
        self.timeout_seconds = max(1.0, timeout_seconds)  # 最小1秒
        self.memory_limit_mb = max(128.0, memory_limit_mb)  # 最小128MB
        self.enable_monitoring = enable_monitoring

        # スレッドローカル設定
        self._thread_local = threading.local()

        # 自動調整パラメータ
        self.auto_tune = True
        self.min_chunk_size = 100
        self.max_chunk_size = 10000

    def get_optimal_chunk_size(self, total_lines: int) -> int:
        """最適なチャンクサイズを計算"""
        if not self.auto_tune:
            return self.chunk_size

        # 総行数に基づく動的調整
        if total_lines < 1000:
            return min(total_lines, self.min_chunk_size)
        elif total_lines < 10000:
            return min(self.chunk_size, total_lines // self.max_workers)
        else:
            # 大量データの場合は大きなチャンクサイズ
            optimal_size = total_lines // (self.max_workers * 2)
            return min(self.max_chunk_size, max(self.min_chunk_size, optimal_size))

    def get_optimal_worker_count(self, total_lines: int) -> int:
        """最適なワーカー数を計算"""
        if total_lines < 500:
            return 1  # 小さなデータは単一スレッド
        elif total_lines < 2000:
            return min(2, self.max_workers)
        else:
            return self.max_workers

    def should_use_parallel_processing(
        self, total_lines: int, content_size_bytes: int = 0
    ) -> bool:
        """並列処理を使用するかどうか判定"""
        # 行数による判定
        if total_lines < 200:
            return False

        # データサイズによる判定（10KB以下は単一スレッド）
        if content_size_bytes > 0 and content_size_bytes < 10240:
            return False

        # ワーカー数が1以下なら無効
        if self.max_workers <= 1:
            return False

        return True

    def update_from_performance_stats(self, stats: dict):
        """パフォーマンス統計から設定を自動調整"""
        if not self.auto_tune:
            return

        # 平均処理時間が長い場合はチャンクサイズを小さく
        if stats.get("avg_chunk_time", 0) > 1.0:  # 1秒以上
            self.chunk_size = max(self.min_chunk_size, int(self.chunk_size * 0.8))

        # 平均処理時間が短い場合はチャンクサイズを大きく
        elif stats.get("avg_chunk_time", 0) < 0.1:  # 0.1秒以下
            self.chunk_size = min(self.max_chunk_size, int(self.chunk_size * 1.2))

        # メモリ使用量が高い場合はワーカー数を減らす
        if stats.get("max_memory_mb", 0) > self.memory_limit_mb * 0.8:
            self.max_workers = max(1, self.max_workers - 1)

    def to_dict(self) -> dict:
        """設定を辞書形式で取得"""
        return {
            "max_workers": self.max_workers,
            "chunk_size": self.chunk_size,
            "timeout_seconds": self.timeout_seconds,
            "memory_limit_mb": self.memory_limit_mb,
            "enable_monitoring": self.enable_monitoring,
            "auto_tune": self.auto_tune,
            "min_chunk_size": self.min_chunk_size,
            "max_chunk_size": self.max_chunk_size,
        }

    @classmethod
    def from_dict(cls, config_dict: dict) -> "ParallelProcessingConfig":
        """辞書から設定を復元"""
        instance = cls()
        for key, value in config_dict.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        return instance

    def __repr__(self):
        return f"ParallelProcessingConfig(workers={self.max_workers}, chunk_size={self.chunk_size}, timeout={self.timeout_seconds}s)"
