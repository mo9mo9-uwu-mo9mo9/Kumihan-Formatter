"""Main controller for Kumihan-Formatter GUI

Single Responsibility Principle適用: メインコントローラー統合管理の分離
Issue #476 Phase2対応 - gui_controller.py分割（3/3）
"""

from tkinter import messagebox
from typing import TYPE_CHECKING, Any, Optional

from .file_controller import FileController
from .conversion_controller import ConversionController

if TYPE_CHECKING:
    from ..core.log_viewer import LogViewerWindow
    from ..gui_models import AppState
    from ..gui_views import MainView

# デバッグロガーのインポート
try:
    from ..core.debug_logger import (
        error,
        info,
        log_gui_event,
    )
except ImportError:
    # Fallbacksを定義
    def error(*args: Any, **kwargs: Any) -> None:
        pass

    def info(*args: Any, **kwargs: Any) -> None:
        pass

    def log_gui_event(*args: Any, **kwargs: Any) -> None:
        pass


class MainController:
    """メインコントローラークラス

    GUI全体の制御・イベント管理・サブコントローラー統合を担当
    """

    def __init__(self, app_state: "AppState", main_view: "MainView") -> None:
        """メインコントローラーの初期化"""
        self.app_state = app_state
        self.main_view = main_view
        self.log_viewer: Optional["LogViewerWindow"] = None

        # サブコントローラーの初期化
        self.file_controller = FileController(app_state, main_view)
        self.conversion_controller = ConversionController(app_state, main_view)

        # イベントハンドラーの設定
        self._setup_event_handlers()
        self._add_startup_messages()

    def _setup_event_handlers(self) -> None:
        """イベントハンドラーの設定"""
        # ファイル選択
        self.main_view.file_selection_frame.set_input_browse_command(
            self.file_controller.browse_input_file
        )
        self.main_view.file_selection_frame.set_output_browse_command(
            self.file_controller.browse_output_dir
        )

        # オプション設定
        self.main_view.options_frame.set_source_toggle_command(
            self.on_source_toggle_change
        )

        # アクションボタン
        self.main_view.action_button_frame.set_convert_command(
            self.conversion_controller.convert_file
        )
        self.main_view.action_button_frame.set_sample_command(
            self.conversion_controller.generate_sample
        )
        self.main_view.action_button_frame.set_help_command(self.show_help)
        self.main_view.action_button_frame.set_exit_command(self.exit_application)

        # デバッグモード時のログボタン
        if self.app_state.debug_mode:
            self.main_view.action_button_frame.set_log_command(self.show_log_viewer)

    def _add_startup_messages(self) -> None:
        """起動時のメッセージを追加"""
        self.main_view.log_frame.add_message("Kumihan-Formatter GUI が起動しました")
        self.main_view.log_frame.add_message(
            "使い方がわからない場合は「ヘルプ」ボタンをクリックしてください"
        )

    def on_source_toggle_change(self) -> None:
        """ソース表示オプションの変更処理"""
        include_source = self.app_state.config.get_include_source()

        # テンプレートの自動切り替え
        if include_source:
            self.app_state.config.set_template("base-with-source-toggle.html.j2")
            self.main_view.log_frame.add_message("ソース表示機能が有効になりました")
        else:
            self.app_state.config.set_template("base.html.j2")
            self.main_view.log_frame.add_message("ソース表示機能が無効になりました")

    def show_help(self) -> None:
        """ヘルプダイアログの表示"""
        log_gui_event("button_click", "show_help")
        self.main_view.help_dialog.show()

    def show_log_viewer(self) -> None:
        """ログビューアーの表示（デバッグモード時のみ）"""
        log_gui_event("button_click", "show_log_viewer")

        try:
            if self.log_viewer and self.log_viewer.is_open():
                # 既に開いている場合は前面に表示
                if hasattr(self.log_viewer, "window") and self.log_viewer.window:
                    self.log_viewer.window.lift()
                    self.log_viewer.window.focus_force()
            else:
                # 新しいログビューアーを開く
                from ..core.log_viewer import LogViewerWindow

                self.log_viewer = LogViewerWindow(self.main_view.root)
                self.log_viewer.show()
                info("Log viewer window opened")
        except Exception as e:
            error("Failed to open log viewer", e)
            messagebox.showerror(
                "エラー", f"ログビューアーの表示に失敗しました:\n\n{str(e)}"
            )

    def exit_application(self) -> None:
        """アプリケーションの終了"""
        log_gui_event("button_click", "exit_application")
        self.main_view.root.quit()

    def run(self) -> None:
        """GUIアプリケーションの実行"""
        try:
            info("Starting GUI main loop...")
            self.main_view.root.mainloop()
        except Exception as e:
            error(f"GUI main loop error: {e}")
            raise