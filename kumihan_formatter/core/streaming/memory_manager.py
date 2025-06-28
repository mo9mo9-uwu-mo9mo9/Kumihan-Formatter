"""メモリ管理機能"""

import gc
import sys
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

import psutil


@dataclass
class MemoryConfig:
    """メモリ管理の設定"""

    max_memory_mb: int = 50
    warning_threshold: float = 0.8  # 80%で警告
    cleanup_threshold: float = 0.9  # 90%でクリーンアップ
    gc_interval: float = 1.0  # ガベージコレクション間隔（秒）
    enable_monitoring: bool = True
    enable_auto_cleanup: bool = True


class MemoryMonitor:
    """メモリ監視クラス"""

    def __init__(self, config: MemoryConfig):
        self.config = config
        self._peak_memory = 0
        self._current_memory = 0
        self._start_memory = 0
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._callbacks: List[Callable[[float, float], None]] = []

    def start_monitoring(self) -> None:
        """メモリ監視を開始"""
        if self._monitoring:
            return

        self._monitoring = True
        self._start_memory = self._get_memory_usage()
        self._current_memory = self._start_memory
        self._peak_memory = self._start_memory

        if self.config.enable_monitoring:
            self._stop_event.clear()
            self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._monitor_thread.start()

    def stop_monitoring(self) -> None:
        """メモリ監視を停止"""
        if not self._monitoring:
            return

        self._monitoring = False

        if self._monitor_thread:
            self._stop_event.set()
            self._monitor_thread.join(timeout=1.0)
            self._monitor_thread = None

    def _monitor_loop(self) -> None:
        """監視ループ（別スレッドで実行）"""
        while not self._stop_event.is_set():
            current = self._get_memory_usage()
            self._current_memory = current
            self._peak_memory = max(self._peak_memory, current)

            # しきい値チェック
            usage_ratio = self.get_usage_ratio()

            # コールバック実行
            for callback in self._callbacks:
                try:
                    callback(current, usage_ratio)
                except Exception:
                    pass  # コールバックエラーは無視

            # 警告しきい値チェック
            if usage_ratio > self.config.warning_threshold:
                self._handle_warning(current, usage_ratio)

            # クリーンアップしきい値チェック
            if usage_ratio > self.config.cleanup_threshold and self.config.enable_auto_cleanup:
                self._handle_cleanup(current, usage_ratio)

            time.sleep(self.config.gc_interval)

    def _get_memory_usage(self) -> float:
        """現在のメモリ使用量を取得（MB単位）"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except Exception:
            # psutilが使用できない場合の fallback
            return sys.getsizeof(gc.get_objects()) / 1024 / 1024

    def get_usage_ratio(self) -> float:
        """メモリ使用率を取得（0.0-1.0）"""
        used = self._current_memory - self._start_memory
        return used / self.config.max_memory_mb

    def get_memory_info(self) -> Dict[str, float]:
        """メモリ情報を取得"""
        return {
            "current_mb": self._current_memory,
            "peak_mb": self._peak_memory,
            "start_mb": self._start_memory,
            "used_mb": self._current_memory - self._start_memory,
            "usage_ratio": self.get_usage_ratio(),
            "max_mb": self.config.max_memory_mb,
        }

    def add_callback(self, callback: Callable[[float, float], None]) -> None:
        """メモリ変化のコールバックを追加"""
        self._callbacks.append(callback)

    def _handle_warning(self, current: float, usage_ratio: float) -> None:
        """警告処理"""
        # ログ出力やアラートなど
        pass

    def _handle_cleanup(self, current: float, usage_ratio: float) -> None:
        """自動クリーンアップ処理"""
        gc.collect()


class MemoryManager:
    """メモリ管理の統合クラス"""

    def __init__(self, config: Optional[MemoryConfig] = None):
        self.config = config or MemoryConfig()
        self.monitor = MemoryMonitor(self.config)
        self._cached_objects: Dict[str, Any] = {}
        self._object_sizes: Dict[str, int] = {}

    @contextmanager
    def managed_processing(self):
        """メモリ管理付きの処理コンテキスト"""
        self.monitor.start_monitoring()
        try:
            yield self
        finally:
            self.monitor.stop_monitoring()
            if self.config.enable_auto_cleanup:
                self.cleanup()

    def cache_object(self, key: str, obj: Any, size_hint: Optional[int] = None) -> None:
        """オブジェクトをキャッシュ"""
        if not self._can_cache(obj, size_hint):
            return

        self._cached_objects[key] = obj
        if size_hint:
            self._object_sizes[key] = size_hint
        else:
            self._object_sizes[key] = sys.getsizeof(obj)

    def get_cached_object(self, key: str) -> Optional[Any]:
        """キャッシュからオブジェクトを取得"""
        return self._cached_objects.get(key)

    def _can_cache(self, obj: Any, size_hint: Optional[int] = None) -> bool:
        """オブジェクトをキャッシュできるかチェック"""
        if self.monitor.get_usage_ratio() > self.config.cleanup_threshold:
            return False

        obj_size = size_hint or sys.getsizeof(obj)
        return obj_size < (self.config.max_memory_mb * 1024 * 1024 * 0.1)  # 最大メモリの10%

    def cleanup(self) -> None:
        """キャッシュとメモリのクリーンアップ"""
        self._cached_objects.clear()
        self._object_sizes.clear()
        gc.collect()

    def get_memory_status(self) -> Dict[str, Any]:
        """メモリステータスを取得"""
        info = self.monitor.get_memory_info()
        info.update(
            {
                "cached_objects": len(self._cached_objects),
                "cache_size_mb": sum(self._object_sizes.values()) / 1024 / 1024,
            }
        )
        return info

    def estimate_chunk_memory(self, chunk_size: int, overhead_factor: float = 2.0) -> int:
        """チャンク処理に必要なメモリを推定"""
        # テキスト + 処理中間データ + オーバーヘッド
        return int(chunk_size * overhead_factor)

    def can_process_chunk(self, chunk_size: int) -> bool:
        """チャンクを処理できるかメモリをチェック"""
        estimated_memory = self.estimate_chunk_memory(chunk_size)
        current_ratio = self.monitor.get_usage_ratio()

        # 推定メモリ使用量を追加した場合の使用率
        additional_ratio = estimated_memory / (self.config.max_memory_mb * 1024 * 1024)

        return (current_ratio + additional_ratio) < self.config.cleanup_threshold

    def optimize_chunk_size(self, desired_size: int) -> int:
        """メモリ状況に応じてチャンクサイズを最適化"""
        if self.can_process_chunk(desired_size):
            return desired_size

        # メモリ不足の場合はサイズを削減
        usage_ratio = self.monitor.get_usage_ratio()
        if usage_ratio > self.config.warning_threshold:
            reduction_factor = (self.config.cleanup_threshold - usage_ratio) / 0.1
            return int(desired_size * max(0.5, reduction_factor))

        return desired_size
