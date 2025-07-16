"""Integrated GUI controller for Kumihan-Formatter

Single Responsibility Principle適用: 統合GUIコントローラーの分離
Issue #476 Phase2対応 - gui_controller.py分割（統合）
"""

from ..gui_models import AppState
from ..gui_views import MainView
from .main_controller import MainController


class GuiController:
    """統合GUIコントローラークラス

    アプリケーション全体の初期化・起動・終了を管理
    既存のAPIとの後方互換性を維持
    """

    def __init__(self) -> None:
        """コントローラーの初期化"""
        self.app_state = AppState()
        self.main_view = MainView(self.app_state)
        self.main_controller = MainController(self.app_state, self.main_view)

    def run(self) -> None:
        """GUIアプリケーションの実行"""
        self.main_controller.run()

    # 後方互換性のためのプロパティ
    @property
    def log_viewer(self):
        """ログビューアーへのアクセス（後方互換性）"""
        return self.main_controller.log_viewer

    @log_viewer.setter
    def log_viewer(self, value):
        """ログビューアーの設定（後方互換性）"""
        self.main_controller.log_viewer = value


def create_gui_application() -> GuiController:
    """GUIアプリケーションの作成

    Returns:
        設定済みのGUIコントローラー
    """
    return GuiController()