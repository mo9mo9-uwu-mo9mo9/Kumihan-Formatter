"""Conversion state management for Kumihan-Formatter GUI

Single Responsibility Principle適用: 変換状態管理の分離
Issue #476 Phase2対応 - config_model.py分割（関数数過多解消）
"""

from tkinter import DoubleVar, StringVar


class ConversionState:
    """変換処理の状態管理クラス

    進捗状況、ステータスメッセージ、処理状態を管理
    """

    def __init__(self) -> None:
        """状態管理変数の初期化"""
        self.progress_var = DoubleVar()
        self.status_var = StringVar(value="準備完了")
        self.is_processing = False

    def get_progress(self) -> float:
        """進捗率を取得"""
        return self.progress_var.get()

    def set_progress(self, value: float) -> None:
        """進捗率を設定"""
        self.progress_var.set(value)

    def get_status(self) -> str:
        """ステータスメッセージを取得"""
        return self.status_var.get()

    def set_status(self, message: str) -> None:
        """ステータスメッセージを設定"""
        self.status_var.set(message)

    def update_progress(self, value: float, status: str = "") -> None:
        """進捗とステータスを同時更新"""
        self.set_progress(value)
        if status:
            self.set_status(status)

    def start_processing(self) -> None:
        """処理開始"""
        self.is_processing = True
        self.set_progress(0)
        self.set_status("処理中...")

    def finish_processing(self, success: bool = True) -> None:
        """処理完了"""
        self.is_processing = False
        if success:
            self.set_progress(100)
            self.set_status("完了")
        else:
            self.set_progress(0)
            self.set_status("エラー")

    def reset(self) -> None:
        """状態をリセット"""
        self.is_processing = False
        self.set_progress(0)
        self.set_status("準備完了")
