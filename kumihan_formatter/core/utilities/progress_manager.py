"""
大容量ファイル処理用プログレス管理システム
Issue #694対応 - ETA算出・キャンセル機能付きプログレス追跡
"""

import time
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass, field
from threading import Event

from .logger import get_logger


@dataclass
class ProgressState:
    """プログレス状態を管理するデータクラス"""
    
    current: int = 0
    total: int = 0
    start_time: float = field(default_factory=time.time)
    last_update_time: float = field(default_factory=time.time)
    estimated_total_time: float = 0.0
    processing_rate: float = 0.0  # items per second
    stage: str = "準備中"
    substage: str = ""
    errors_count: int = 0
    warnings_count: int = 0
    
    @property
    def progress_percent(self) -> float:
        """進捗率を取得（0-100）"""
        if self.total == 0:
            return 100.0
        return min(100.0, (self.current / self.total) * 100)
    
    @property
    def elapsed_time(self) -> float:
        """経過時間（秒）"""
        return time.time() - self.start_time
    
    @property
    def eta_seconds(self) -> int:
        """推定残り時間（秒）"""
        if self.processing_rate <= 0 or self.current >= self.total:
            return 0
        
        remaining_items = self.total - self.current
        return int(remaining_items / self.processing_rate)
    
    @property
    def eta_formatted(self) -> str:
        """フォーマット済み推定残り時間"""
        eta = self.eta_seconds
        if eta <= 0:
            return "完了間近"
        elif eta < 60:
            return f"{eta}秒"
        elif eta < 3600:
            minutes = eta // 60
            seconds = eta % 60
            return f"{minutes}分{seconds}秒"
        else:
            hours = eta // 3600
            minutes = (eta % 3600) // 60
            return f"{hours}時間{minutes}分"


class ProgressManager:
    """
    大容量ファイル処理用の高度なプログレス管理システム
    
    機能:
    - リアルタイムETA算出
    - 処理速度監視
    - キャンセル機能
    - ステージ別プログレス追跡
    - エラー・警告カウント
    """
    
    UPDATE_INTERVAL = 0.5  # プログレス更新間隔（秒）
    RATE_CALCULATION_WINDOW = 10  # 処理速度計算用のサンプル数
    
    def __init__(self, task_name: str = "処理中"):
        self.logger = get_logger(__name__)
        self.task_name = task_name
        self.state = ProgressState()
        self.cancelled = Event()
        
        # コールバック関数
        self.progress_callback: Optional[Callable[[ProgressState], None]] = None
        self.cancellation_callback: Optional[Callable[[], None]] = None
        
        # 処理速度計算用
        self._progress_history: list[tuple[float, int]] = []  # (timestamp, current_value)
        
        self.logger.debug(f"ProgressManager initialized for task: {task_name}")
    
    def start(self, total_items: int, stage: str = "開始"):
        """プログレス追跡を開始"""
        self.state = ProgressState(
            total=total_items,
            stage=stage,
            start_time=time.time(),
            last_update_time=time.time()
        )
        self.cancelled.clear()
        self._progress_history.clear()
        
        self.logger.info(f"Progress tracking started: {total_items} items, stage: {stage}")
        self._notify_progress()
    
    def update(self, current: int, substage: str = "") -> bool:
        """
        プログレスを更新
        
        Args:
            current: 現在の進捗値
            substage: サブステージ名
            
        Returns:
            bool: 継続可能な場合True、キャンセル時False
        """
        if self.cancelled.is_set():
            return False
        
        now = time.time()
        
        # 状態更新
        self.state.current = min(current, self.state.total)
        self.state.substage = substage
        
        # 処理速度計算
        self._update_processing_rate(now, current)
        
        # 定期的なプログレス通知
        if now - self.state.last_update_time >= self.UPDATE_INTERVAL:
            self.state.last_update_time = now
            self._notify_progress()
        
        return True
    
    def increment(self, amount: int = 1, substage: str = "") -> bool:
        """プログレスを増分更新"""
        return self.update(self.state.current + amount, substage)
    
    def set_stage(self, stage: str, substage: str = ""):
        """処理ステージを変更"""
        self.state.stage = stage
        self.state.substage = substage
        self.logger.info(f"Stage changed: {stage} - {substage}")
        self._notify_progress()
    
    def add_error(self, error_message: str = ""):
        """エラーカウントを増加"""
        self.state.errors_count += 1
        if error_message:
            self.logger.warning(f"Error recorded: {error_message}")
        self._notify_progress()
    
    def add_warning(self, warning_message: str = ""):
        """警告カウントを増加"""
        self.state.warnings_count += 1
        if warning_message:
            self.logger.info(f"Warning recorded: {warning_message}")
        self._notify_progress()
    
    def finish(self, final_stage: str = "完了"):
        """プログレス追跡を完了"""
        self.state.current = self.state.total
        self.state.stage = final_stage
        self.state.substage = ""
        
        elapsed = self.state.elapsed_time
        self.logger.info(
            f"Progress completed: {self.state.total} items in {elapsed:.2f}s, "
            f"{self.state.errors_count} errors, {self.state.warnings_count} warnings"
        )
        
        self._notify_progress()
    
    def cancel(self, reason: str = "ユーザー要求"):
        """処理をキャンセル"""
        self.cancelled.set()
        self.state.stage = "キャンセル中"
        self.logger.info(f"Progress cancelled: {reason}")
        
        if self.cancellation_callback:
            self.cancellation_callback()
        
        self._notify_progress()
    
    def is_cancelled(self) -> bool:
        """キャンセル状態を確認"""
        return self.cancelled.is_set()
    
    def set_progress_callback(self, callback: Callable[[ProgressState], None]):
        """プログレス更新コールバックを設定"""
        self.progress_callback = callback
    
    def set_cancellation_callback(self, callback: Callable[[], None]):
        """キャンセル時コールバックを設定"""
        self.cancellation_callback = callback
    
    def get_state(self) -> ProgressState:
        """現在のプログレス状態を取得"""
        return self.state
    
    def get_summary(self) -> Dict[str, Any]:
        """プログレス概要を取得"""
        return {
            'task_name': self.task_name,
            'progress_percent': self.state.progress_percent,
            'current': self.state.current,
            'total': self.state.total,
            'elapsed_time': self.state.elapsed_time,
            'eta_seconds': self.state.eta_seconds,
            'eta_formatted': self.state.eta_formatted,
            'stage': self.state.stage,
            'substage': self.state.substage,
            'processing_rate': self.state.processing_rate,
            'errors_count': self.state.errors_count,
            'warnings_count': self.state.warnings_count,
            'is_cancelled': self.is_cancelled()
        }
    
    def _update_processing_rate(self, timestamp: float, current: int):
        """処理速度を更新"""
        # 履歴に追加
        self._progress_history.append((timestamp, current))
        
        # 古い履歴を削除（指定されたウィンドウサイズを維持）
        if len(self._progress_history) > self.RATE_CALCULATION_WINDOW:
            self._progress_history.pop(0)
        
        # 処理速度計算（最初と最後の2点から算出）
        if len(self._progress_history) >= 2:
            first_time, first_value = self._progress_history[0]
            last_time, last_value = self._progress_history[-1]
            
            time_diff = last_time - first_time
            value_diff = last_value - first_value
            
            if time_diff > 0:
                self.state.processing_rate = value_diff / time_diff
            else:
                self.state.processing_rate = 0.0
    
    def _notify_progress(self):
        """プログレス更新を通知"""
        if self.progress_callback:
            try:
                self.progress_callback(self.state)
            except Exception as e:
                self.logger.error(f"Progress callback error: {e}")


class FileProcessingProgressManager(ProgressManager):
    """
    ファイル処理専用のプログレス管理システム
    
    ファイルサイズ・行数に特化した機能を提供
    """
    
    def __init__(self, file_path: str, file_size_mb: float, line_count: int):
        super().__init__(f"ファイル処理: {file_path}")
        self.file_path = file_path
        self.file_size_mb = file_size_mb
        self.line_count = line_count
        
        self.logger.info(f"File processing manager initialized: {file_size_mb:.1f}MB, {line_count} lines")
    
    def start_parsing(self):
        """解析フェーズを開始"""
        self.start(self.line_count, "解析中")
    
    def start_rendering(self, node_count: int):
        """レンダリングフェーズを開始"""
        self.start(node_count, "レンダリング中")
    
    def update_parsing_progress(self, current_line: int, current_stage: str = "") -> bool:
        """解析進捗を更新"""
        return self.update(current_line, current_stage)
    
    def update_rendering_progress(self, current_node: int, current_stage: str = "") -> bool:
        """レンダリング進捗を更新"""
        return self.update(current_node, current_stage)
    
    def get_file_processing_summary(self) -> Dict[str, Any]:
        """ファイル処理専用の概要を取得"""
        summary = self.get_summary()
        summary.update({
            'file_path': self.file_path,
            'file_size_mb': self.file_size_mb,
            'line_count': self.line_count,
            'processing_rate_mb_per_sec': (self.state.processing_rate * 60) / 1024 / 1024,  # MB/s概算
        })
        return summary