"""Main view integration for Kumihan-Formatter GUI

Single Responsibility Principle適用: メインビュー統合管理の分離
Issue #476 Phase2対応 - gui_views.py分割（メインビュー）
"""

from tkinter import DISABLED, NORMAL, Widget, ttk
from typing import TYPE_CHECKING

from .controls import ActionButtonFrame, LogFrame, ProgressFrame
from .dialogs import HelpDialog
from .main_window import MainWindow
from .widgets import FileSelectionFrame, HeaderFrame, OptionsFrame

if TYPE_CHECKING:
    from ..gui_models import AppState


class MainView:
    """メインビュークラス

    すべてのUIコンポーネントを統合して管理する中央ビュー
    """

    def __init__(self, app_state: "AppState") -> None:
        """メインビューの初期化"""
        self.app_state = app_state

        # メインウィンドウ作成
        self.main_window = MainWindow(app_state)
        self.root = self.main_window.get_root()

        # メインフレーム
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky="WENS")

        # グリッド設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(6, weight=1)  # ログフレームを伸縮可能に

        # UI コンポーネント作成
        self._create_components()
        self._layout_components()

        # ウィンドウ中央配置
        self.main_window.center_window()

    def _create_components(self) -> None:
        """UIコンポーネントの作成"""
        self.header_frame = HeaderFrame(self.main_frame)
        self.file_selection_frame = FileSelectionFrame(self.main_frame, self.app_state)
        self.options_frame = OptionsFrame(self.main_frame, self.app_state)
        self.action_button_frame = ActionButtonFrame(self.main_frame, self.app_state)
        self.progress_frame = ProgressFrame(self.main_frame, self.app_state)
        self.log_frame = LogFrame(self.main_frame, self.app_state)
        self.help_dialog = HelpDialog(self.main_frame)

    def _layout_components(self) -> None:
        """UIコンポーネントのレイアウト"""
        self.header_frame.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        self.file_selection_frame.grid(
            row=1, column=0, columnspan=3, sticky="WE", pady=(0, 10)
        )
        self.options_frame.grid(
            row=2, column=0, columnspan=3, sticky="WE", pady=(0, 10)
        )
        self.action_button_frame.grid(row=3, column=0, columnspan=3, pady=20)
        self.progress_frame.grid(
            row=4, column=0, columnspan=3, sticky="WE", pady=(0, 10)
        )
        self.log_frame.grid(row=5, column=0, columnspan=3, sticky="WENS", pady=(0, 10))

    def set_ui_enabled(self, enabled: bool) -> None:
        """UI要素の有効/無効を一括設定"""
        state = NORMAL if enabled else DISABLED

        def update_widget_state(widget: Widget) -> None:
            try:
                if isinstance(
                    widget, (ttk.Button, ttk.Entry, ttk.Combobox, ttk.Checkbutton)
                ):
                    widget.configure(state=state)
            except:
                pass

            for child in widget.winfo_children():
                update_widget_state(child)

        # rootはTkクラスなので、直接のWidget子要素を更新
        for child in self.root.winfo_children():
            update_widget_state(child)

    def update_display(self) -> None:
        """画面表示を更新"""
        self.root.update_idletasks()
