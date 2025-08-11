"""Integrated GUI controller for Kumihan-Formatter

Single Responsibility Principle適用: 統合GUIコントローラーの分離
Issue #476対応 - gui_controller.py分割（統合）
"""

from typing import Any

from ..gui_models.state_model import StateModel
from ..gui_views.main_window import MainWindow
from .conversion_controller import ConversionController
from .file_controller import FileController
from .main_controller import MainController


class GuiController:
    """統合GUIコントローラークラス

    アプリケーション全体の初期化・起動・終了を管理
    既存のAPIとの後方互換性を維持
    """

    def __init__(self) -> None:
        """コントローラーの初期化"""
        # GUI components initialization
        self.model = StateModel()  # app_stateを先に作成
        self.view = MainWindow(self.model)  # app_stateを渡してMainWindowを作成

        # Controllers initialization
        self.file_controller = FileController(self.view)
        self.conversion_controller = ConversionController(self.model, self.view)
        self.main_controller = MainController(
            self.view, self.model, self.file_controller, self.conversion_controller
        )

    def run(self) -> None:
        """GUIアプリケーションの実行"""
        if self.main_controller:
            self.main_controller.run()

    # 後方互換性のためのプロパティ
    @property
    def log_viewer(self) -> Any:
        """ログビューアーへのアクセス（後方互換性）"""
        if self.main_controller:
            return self.main_controller.log_viewer

    @log_viewer.setter
    def log_viewer(self, value: Any) -> None:
        """ログビューアーの設定（後方互換性）"""
        if self.main_controller:
            self.main_controller.log_viewer = value


def create_gui_application() -> GuiController:
    """GUIアプリケーションの作成

    Returns:
        設定済みのGUIコントローラー
    """
    return GuiController()
