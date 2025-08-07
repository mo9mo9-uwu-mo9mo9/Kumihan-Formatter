"""Main window for Kumihan-Formatter GUI

Single Responsibility Principle適用: メインウィンドウ管理の分離
Issue #476対応 - gui_views.py分割（1/4）
"""

from tkinter import Tk, ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..gui_models import AppState


class MainWindow:
    """メインウィンドウクラス

    アプリケーションのメインウィンドウとグローバルレイアウトを管理
    """

    def __init__(self, app_state: "AppState") -> None:
        """メインウィンドウの初期化"""
        self.app_state = app_state
        self.root = Tk()
        self._setup_window()
        self._setup_style()

    def _setup_window(self) -> None:
        """ウィンドウの基本設定"""
        self.root.title("Kumihan-Formatter v1.0 - 美しい組版を、誰でも簡単に")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

    def _setup_style(self) -> None:
        """スタイルの設定"""
        self.style = ttk.Style()
        self.style.theme_use("clam")

    def center_window(self) -> None:
        """ウィンドウを画面中央に配置"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        pos_x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        pos_y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

    def get_root(self) -> Tk:
        """Tkルートウィンドウを取得"""
        return self.root
