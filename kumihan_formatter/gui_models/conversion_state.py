"""Conversion state management for Kumihan-Formatter GUI

Single Responsibility Principle適用: 変換状態管理の分離
Issue #476 Phase2対応 - config_model.py分割（関数数過多解消）
Issue #516 Phase 5A対応 - Thread-Safe設計とエラーハンドリング強化
"""

import threading
import time
from typing import Any, Callable, Optional


# Tkinterが利用できない場合のフォールバック
class MockVar:
    def __init__(self, value: Any = None) -> None:
        self._value = value if value is not None else 0

    def get(self) -> Any:
        return self._value

    def set(self, value: Any) -> None:
        self._value = value


try:
    from tkinter import DoubleVar, StringVar

    _TKINTER_AVAILABLE = True
except (ImportError, RuntimeError):
    _TKINTER_AVAILABLE = False
    DoubleVar = MockVar
    StringVar = lambda value="": MockVar(value)


def _safe_create_var(var_class: Any, value: Any = None) -> Any:
    """安全にTkinter変数を作成"""
    try:
        if _TKINTER_AVAILABLE:
            return var_class(value=value)
        else:
            return MockVar(value)
    except RuntimeError:
        # ルートウィンドウが無い場合はMockVarを使用
        return MockVar(value)


class ConversionState:
    """変換処理の状態管理クラス（Thread-Safe対応）

    進捗状況、ステータスメッセージ、処理状態を管理
    マルチスレッド環境での安全な状態更新を保証
    """

    def __init__(self) -> None:
        """状態管理変数の初期化"""
        self.progress_var = _safe_create_var(DoubleVar, 0)
        self.status_var = _safe_create_var(StringVar, "準備完了")
        self.is_processing = False

        # Thread-Safe対応
        self._lock = threading.Lock()
        self._start_time: Optional[float] = None
        self._callback: Optional[Callable[[float, str], None]] = None

    def get_progress(self) -> float:
        """進捗率を取得（Thread-Safe）"""
        with self._lock:
            return self.progress_var.get()

    def set_progress(self, value: float) -> None:
        """進捗率を設定（Thread-Safe）"""
        try:
            with self._lock:
                # 値の妥当性チェック
                if not isinstance(value, (int, float)):
                    raise ValueError(f"進捗値は数値である必要があります: {type(value)}")
                if not 0 <= value <= 100:
                    raise ValueError(
                        f"進捗値は0-100の範囲である必要があります: {value}"
                    )

                self.progress_var.set(value)

                # コールバック実行
                if self._callback:
                    self._callback(value, self.get_status())
        except Exception as e:
            # エラーハンドリング - ログに記録して継続
            import logging

            logging.warning(f"進捗設定エラー: {e}")

    def get_status(self) -> str:
        """ステータスメッセージを取得（Thread-Safe）"""
        with self._lock:
            return self.status_var.get()

    def set_status(self, message: str) -> None:
        """ステータスメッセージを設定（Thread-Safe）"""
        try:
            with self._lock:
                if not isinstance(message, str):
                    message = str(message)
                self.status_var.set(message)

                # コールバック実行
                if self._callback:
                    self._callback(self.get_progress(), message)
        except Exception as e:
            # エラーハンドリング - ログに記録して継続
            import logging

            logging.warning(f"ステータス設定エラー: {e}")

    def update_progress(self, value: float, status: str = "") -> None:
        """進捗とステータスを同時更新（Thread-Safe）"""
        try:
            with self._lock:
                self.set_progress(value)
                if status:
                    self.set_status(status)
        except Exception as e:
            import logging

            logging.error(f"進捗更新エラー: {e}")

    def start_processing(self) -> None:
        """処理開始（Thread-Safe）"""
        try:
            with self._lock:
                self.is_processing = True
                self._start_time = time.time()
                self.set_progress(0)
                self.set_status("処理中...")
        except Exception as e:
            import logging

            logging.error(f"処理開始エラー: {e}")

    def finish_processing(self, success: bool = True) -> None:
        """処理完了（Thread-Safe）"""
        try:
            with self._lock:
                self.is_processing = False
                if success:
                    self.set_progress(100)
                    elapsed = self._get_elapsed_time()
                    self.set_status(f"完了 ({elapsed:.1f}秒)")
                else:
                    self.set_progress(0)
                    self.set_status("エラー")
                self._start_time = None
        except Exception as e:
            import logging

            logging.error(f"処理完了エラー: {e}")

    def reset(self) -> None:
        """状態をリセット（Thread-Safe）"""
        try:
            with self._lock:
                self.is_processing = False
                self.set_progress(0)
                self.set_status("準備完了")
                self._start_time = None
                self._callback = None
        except Exception as e:
            import logging

            logging.error(f"状態リセットエラー: {e}")

    def set_callback(self, callback: Optional[Callable[[float, str], None]]) -> None:
        """進捗更新コールバックを設定（Thread-Safe）"""
        with self._lock:
            self._callback = callback

    def get_elapsed_time(self) -> float:
        """経過時間を取得（Thread-Safe）"""
        with self._lock:
            return self._get_elapsed_time()

    def _get_elapsed_time(self) -> float:
        """経過時間の内部計算（ロック済み前提）"""
        if self._start_time is None:
            return 0.0
        return time.time() - self._start_time

    def is_ready(self) -> bool:
        """処理可能状態かチェック（Thread-Safe）"""
        with self._lock:
            return not self.is_processing
