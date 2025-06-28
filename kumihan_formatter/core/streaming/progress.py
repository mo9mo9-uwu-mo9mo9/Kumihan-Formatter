"""進捗追跡機能"""

import time
import threading
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum

# Type alias for progress callbacks
ProgressCallback = Callable[['ProgressInfo'], None]


class ProgressState(Enum):
    """進捗状態"""
    INITIALIZED = "initialized"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


@dataclass
class ProgressInfo:
    """進捗情報"""
    processed_bytes: int = 0
    total_bytes: Optional[int] = None
    current_chunk: int = 0
    total_chunks: Optional[int] = None
    state: ProgressState = ProgressState.INITIALIZED
    start_time: float = field(default_factory=time.time)
    current_time: float = field(default_factory=time.time)
    message: Optional[str] = None
    error: Optional[str] = None
    
    @property
    def elapsed_time(self) -> float:
        """経過時間"""
        return self.current_time - self.start_time
    
    @property
    def progress_ratio(self) -> Optional[float]:
        """進捗率（0.0-1.0）"""
        if self.total_bytes is None or self.total_bytes == 0:
            return None
        return min(1.0, self.processed_bytes / self.total_bytes)
    
    @property
    def chunk_progress_ratio(self) -> Optional[float]:
        """チャンク進捗率（0.0-1.0）"""
        if self.total_chunks is None or self.total_chunks == 0:
            return None
        return min(1.0, self.current_chunk / self.total_chunks)
    
    @property
    def processing_speed(self) -> Optional[float]:
        """処理速度（bytes/sec）"""
        if self.elapsed_time == 0:
            return None
        return self.processed_bytes / self.elapsed_time
    
    @property
    def estimated_remaining_time(self) -> Optional[float]:
        """推定残り時間（秒）"""
        if (self.total_bytes is None or 
            self.processing_speed is None or 
            self.processing_speed == 0):
            return None
        
        remaining_bytes = self.total_bytes - self.processed_bytes
        return remaining_bytes / self.processing_speed


class ProgressTracker:
    """進捗追跡クラス"""
    
    def __init__(self, total_bytes: Optional[int] = None, total_chunks: Optional[int] = None):
        self._info = ProgressInfo(
            total_bytes=total_bytes,
            total_chunks=total_chunks
        )
        self._callbacks: List[Callable[[ProgressInfo], None]] = []
        self._lock = threading.Lock()
        self._cancelled = threading.Event()
        
    def add_callback(self, callback: Callable[[ProgressInfo], None]) -> None:
        """コールバックを追加"""
        with self._lock:
            self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[ProgressInfo], None]) -> None:
        """コールバックを削除"""
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)
    
    def start(self) -> None:
        """進捗追跡を開始"""
        with self._lock:
            self._info.state = ProgressState.RUNNING
            self._info.start_time = time.time()
            self._info.current_time = self._info.start_time
            self._cancelled.clear()
        self._notify_callbacks()
    
    def update(
        self,
        processed_bytes: Optional[int] = None,
        current_chunk: Optional[int] = None,
        message: Optional[str] = None
    ) -> None:
        """進捗を更新"""
        with self._lock:
            if self._info.state != ProgressState.RUNNING:
                return
                
            if processed_bytes is not None:
                self._info.processed_bytes = processed_bytes
            
            if current_chunk is not None:
                self._info.current_chunk = current_chunk
            
            if message is not None:
                self._info.message = message
            
            self._info.current_time = time.time()
        
        self._notify_callbacks()
    
    def increment(
        self,
        bytes_processed: int = 0,
        chunks_processed: int = 0,
        message: Optional[str] = None
    ) -> None:
        """進捗を増分更新"""
        with self._lock:
            if self._info.state != ProgressState.RUNNING:
                return
                
            self._info.processed_bytes += bytes_processed
            self._info.current_chunk += chunks_processed
            
            if message is not None:
                self._info.message = message
            
            self._info.current_time = time.time()
        
        self._notify_callbacks()
    
    def complete(self, message: Optional[str] = None) -> None:
        """進捗完了"""
        with self._lock:
            self._info.state = ProgressState.COMPLETED
            self._info.current_time = time.time()
            
            if message is not None:
                self._info.message = message
            
            # 100%完了にする
            if self._info.total_bytes is not None:
                self._info.processed_bytes = self._info.total_bytes
            if self._info.total_chunks is not None:
                self._info.current_chunk = self._info.total_chunks
        
        self._notify_callbacks()
    
    def cancel(self, message: Optional[str] = None) -> None:
        """進捗をキャンセル"""
        with self._lock:
            self._info.state = ProgressState.CANCELLED
            self._info.current_time = time.time()
            
            if message is not None:
                self._info.message = message
        
        self._cancelled.set()
        self._notify_callbacks()
    
    def error(self, error_message: str) -> None:
        """エラー状態に設定"""
        with self._lock:
            self._info.state = ProgressState.ERROR
            self._info.current_time = time.time()
            self._info.error = error_message
            self._info.message = f"エラー: {error_message}"
        
        self._notify_callbacks()
    
    def pause(self) -> None:
        """進捗を一時停止"""
        with self._lock:
            if self._info.state == ProgressState.RUNNING:
                self._info.state = ProgressState.PAUSED
                self._info.current_time = time.time()
        
        self._notify_callbacks()
    
    def resume(self) -> None:
        """進捗を再開"""
        with self._lock:
            if self._info.state == ProgressState.PAUSED:
                self._info.state = ProgressState.RUNNING
                self._info.current_time = time.time()
        
        self._notify_callbacks()
    
    def is_cancelled(self) -> bool:
        """キャンセルされているかチェック"""
        return self._cancelled.is_set()
    
    def wait_for_cancel(self, timeout: Optional[float] = None) -> bool:
        """キャンセルを待機"""
        return self._cancelled.wait(timeout)
    
    def get_info(self) -> ProgressInfo:
        """現在の進捗情報を取得"""
        with self._lock:
            # 現在時刻を更新してからコピーを返す
            info_copy = ProgressInfo(
                processed_bytes=self._info.processed_bytes,
                total_bytes=self._info.total_bytes,
                current_chunk=self._info.current_chunk,
                total_chunks=self._info.total_chunks,
                state=self._info.state,
                start_time=self._info.start_time,
                current_time=time.time(),
                message=self._info.message,
                error=self._info.error
            )
            return info_copy
    
    def _notify_callbacks(self) -> None:
        """コールバックに通知"""
        info = self.get_info()
        callbacks = list(self._callbacks)  # コピーを作成
        
        for callback in callbacks:
            try:
                callback(info)
            except Exception:
                # コールバックエラーは無視
                pass


class ConsoleProgressTracker(ProgressTracker):
    """コンソール出力付き進捗追跡"""
    
    def __init__(
        self, 
        total_bytes: Optional[int] = None, 
        total_chunks: Optional[int] = None,
        update_interval: float = 1.0
    ):
        super().__init__(total_bytes, total_chunks)
        self.update_interval = update_interval
        self._last_display_time = 0.0
        
        # 自動的にコンソール出力コールバックを追加
        self.add_callback(self._console_callback)
    
    def _console_callback(self, info: ProgressInfo) -> None:
        """コンソール出力コールバック"""
        current_time = time.time()
        
        # 表示間隔チェック
        if (current_time - self._last_display_time < self.update_interval and
            info.state == ProgressState.RUNNING):
            return
        
        self._last_display_time = current_time
        
        # 進捗情報をフォーマット
        progress_text = self._format_progress(info)
        print(f"\\r{progress_text}", end="", flush=True)
        
        # 完了時やエラー時は改行
        if info.state in [ProgressState.COMPLETED, ProgressState.CANCELLED, ProgressState.ERROR]:
            print()
    
    def _format_progress(self, info: ProgressInfo) -> str:
        """進捗情報をフォーマット"""
        parts = []
        
        # 状態
        if info.state == ProgressState.RUNNING:
            parts.append("⏳")
        elif info.state == ProgressState.COMPLETED:
            parts.append("✅")
        elif info.state == ProgressState.CANCELLED:
            parts.append("❌")
        elif info.state == ProgressState.ERROR:
            parts.append("💥")
        else:
            parts.append("⏸️")
        
        # バイト進捗
        if info.progress_ratio is not None:
            percentage = info.progress_ratio * 100
            parts.append(f"{percentage:.1f}%")
            
            # プログレスバー
            bar_length = 20
            filled_length = int(bar_length * info.progress_ratio)
            bar = "█" * filled_length + "░" * (bar_length - filled_length)
            parts.append(f"[{bar}]")
        
        # チャンク進捗
        if info.total_chunks is not None:
            parts.append(f"({info.current_chunk}/{info.total_chunks} chunks)")
        
        # 処理速度
        if info.processing_speed is not None:
            speed_mb = info.processing_speed / 1024 / 1024
            parts.append(f"{speed_mb:.1f} MB/s")
        
        # 残り時間
        if info.estimated_remaining_time is not None:
            remaining = int(info.estimated_remaining_time)
            parts.append(f"ETA: {remaining}s")
        
        # メッセージ
        if info.message:
            parts.append(f"- {info.message}")
        
        return " ".join(parts)