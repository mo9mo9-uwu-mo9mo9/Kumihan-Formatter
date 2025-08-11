"""Main controller for Kumihan-Formatter GUI

Single Responsibility Principle適用: メインコントローラー統合管理の分離
Issue #476対応 - gui_controller.py分割（3/3）
"""

from tkinter import messagebox
from typing import TYPE_CHECKING, Any, Optional

from .conversion_controller import ConversionController
from .file_controller import FileController

if TYPE_CHECKING:
    from ..ui.log_viewer import LogViewerWindow

    # ..gui_models.AppState removed as unused
    # ..gui_views.MainView removed as unused


# デバッグロガーのインポート（代替実装）
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

    def __init__(
        self,
        view: Any,
        model: Any = None,
        file_controller: Any = None,
        conversion_controller: Any = None,
    ) -> None:
        """メインコントローラーの初期化"""
        self.view = view
        self.model = model
        self.log_viewer: Optional["LogViewerWindow"] = None

        # 後方互換性のため、旧形式もサポート
        if hasattr(view, "app_state"):
            self.app_state = view.app_state
            self.main_view = view
        else:
            # テスト用の単純な view/model オブジェクト
            self.app_state = None
            self.main_view = view

        # サブコントローラーの初期化
        if file_controller is not None:
            # テスト環境では外部から注入
            self.file_controller = file_controller
            self.conversion_controller = conversion_controller
        else:
            # 実際の環境では内部で作成
            if self.app_state:
                self.file_controller = FileController(self.main_view)
                self.conversion_controller = ConversionController(
                    self.model, self.main_view
                )
            else:
                self.file_controller = None
                self.conversion_controller = None

        # イベントハンドラーの設定
        if self.app_state:
            self._setup_event_handlers()
            self._add_startup_messages()

    def _setup_event_handlers(self) -> None:
        """イベントハンドラーの設定"""
        if (
            not self.main_view
            or not self.file_controller
            or not self.conversion_controller
        ):
            return

        # ファイル選択
        if hasattr(self.main_view, "file_selection_frame"):
            self.main_view.file_selection_frame.set_input_browse_command(
                self.file_controller.browse_input_file
            )
            self.main_view.file_selection_frame.set_output_browse_command(
                self.file_controller.browse_output_dir
            )

        # オプション設定
        if hasattr(self.main_view, "options_frame"):
            self.main_view.options_frame.set_source_toggle_command(
                self.on_source_toggle_change
            )

        # アクションボタン
        if hasattr(self.main_view, "action_button_frame"):
            self.main_view.action_button_frame.set_convert_command(
                self.conversion_controller.convert_file
            )
            self.main_view.action_button_frame.set_sample_command(
                self.conversion_controller.generate_sample
            )
            self.main_view.action_button_frame.set_help_command(self.show_help)
            self.main_view.action_button_frame.set_exit_command(self.exit_application)

        # デバッグモード時のログボタン
        if (
            self.app_state
            and hasattr(self.app_state, "debug_mode")
            and self.app_state.debug_mode
        ):
            if hasattr(self.main_view, "action_button_frame"):
                self.main_view.action_button_frame.set_log_command(self.show_log_viewer)

    def _add_startup_messages(self) -> None:
        """起動時のメッセージを追加"""
        if self.main_view and hasattr(self.main_view, "log_frame"):
            self.main_view.log_frame.add_message("Kumihan-Formatter GUI が起動しました")
            self.main_view.log_frame.add_message(
                "使い方がわからない場合は「ヘルプ」ボタンをクリックしてください"
            )

    def on_source_toggle_change(self) -> None:
        """ソース表示オプションの変更処理"""
        if not self.app_state:
            # テスト環境では model から値を取得
            if self.model and hasattr(self.model, "show_source_var"):
                include_source = self.model.show_source_var.get()
            else:
                include_source = False
            return

        include_source = self.app_state.config.get_include_source()

        # テンプレートの自動切り替え
        if include_source:
            self.app_state.config.set_template("base-with-source-toggle.html.j2")
            if hasattr(self.main_view, "log_frame"):
                self.main_view.log_frame.add_message("ソース表示機能が有効になりました")
        else:
            self.app_state.config.set_template("base.html.j2")
            if hasattr(self.main_view, "log_frame"):
                self.main_view.log_frame.add_message("ソース表示機能が無効になりました")

    def show_help(self) -> None:
        """ヘルプダイアログの表示"""
        log_gui_event("button_click", "show_help")
        if self.main_view and hasattr(self.main_view, "help_dialog"):
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
                from ..ui.log_viewer import LogViewerWindow

                if self.main_view and hasattr(self.main_view, "root"):
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
        if self.main_view and hasattr(self.main_view, "root"):
            self.main_view.root.quit()

    def run(self) -> None:
        """GUIアプリケーションの実行"""
        try:
            info("Starting GUI main loop...")
            if self.main_view and hasattr(self.main_view, "root"):
                self.main_view.root.mainloop()
        except Exception as e:
            error(f"GUI main loop error: {e}")
            raise

    @property
    def log_viewer_property(self) -> Optional[Any]:
        """ログビューアープロパティ（テスト用）"""
        return self.log_viewer
