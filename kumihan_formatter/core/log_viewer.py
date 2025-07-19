"""GUI Log Viewer for Kumihan-Formatter
GUIアプリケーション用のリアルタイムログビューアー
"""

from typing import TYPE_CHECKING, Any, Optional, Union

from .log_viewer_events import LogViewerEventHandler
from .log_viewer_ui import LogViewerUI

# tkinterは必要時にのみインポート（CI環境での問題回避）
if TYPE_CHECKING:
    import tkinter as tk
else:
    try:
        import tkinter as tk
    except ImportError:
        # CI環境やheadless環境ではtkinterが利用できない場合がある
        tk = None  # type: ignore


class LogViewerWindow:
    """リアルタイムログビューアーウィンドウ"""

    def __init__(self, parent_window: Optional["tk.Tk"] = None) -> None:
        self.parent = parent_window
        self.window: Optional[Union["tk.Tk", "tk.Toplevel"]] = None
        self.ui: Optional[LogViewerUI] = None
        self.event_handler: Optional[LogViewerEventHandler] = None
        # Logger取得を一箇所にまとめる（重複debug logger fallback定義の削除）
        self._logger: Optional[Any] = None
        self._initialize_logger()

    def _initialize_logger(self) -> None:
        """ロガーを初期化（重複削除のため一箇所で実行）"""
        try:
            from .debug_logger import get_logger

            self._logger = get_logger()
        except Exception:
            self._logger = None

    def _get_logger(self) -> Optional[Any]:
        """ロガーを取得（fallback処理を含む）"""
        if self._logger is None:
            self._initialize_logger()
        return self._logger

    def show(self) -> None:
        """ログビューアーウィンドウを表示"""
        # tkinterが利用できない場合（CI環境等）はエラーを出さずに終了
        if tk is None:
            print(
                "Warning: tkinter is not available. GUI log viewer cannot be displayed."
            )
            return
        if self.window is not None:
            # 既に開いている場合は前面に表示
            self.window.lift()
            self.window.focus_force()
            return
        # 新しいウィンドウを作成
        self.window = tk.Toplevel(self.parent) if self.parent else tk.Tk()
        self.window.title("Kumihan-Formatter - Debug Log Viewer")
        self.window.geometry("800x600")
        # ウィンドウが閉じられた時の処理
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

        # UI と イベントハンドラーを初期化
        self.ui = LogViewerUI(self.window)
        self.event_handler = LogViewerEventHandler(self.ui, self._get_logger)

        # UIをセットアップ
        self.ui.setup_ui(
            self.event_handler.clear_log,
            self.event_handler.toggle_auto_scroll,
            self.event_handler.open_log_file,
            self.event_handler.filter_logs,
        )

        # ログ監視を開始
        self.event_handler.start_log_monitoring()

    def on_closing(self) -> None:
        """ウィンドウを閉じる時の処理"""
        if self.event_handler:
            self.event_handler.stop_log_monitoring()
        if self.window:
            self.window.destroy()
            self.window = None

    def is_open(self) -> bool:
        """ウィンドウが開いているかどうか"""
        return self.window is not None


def show_log_viewer(parent_window: Optional["tk.Tk"] = None) -> LogViewerWindow:
    """ログビューアーを表示"""
    viewer = LogViewerWindow(parent_window)
    viewer.show()
    return viewer


if __name__ == "__main__":
    # テスト用
    import os

    if tk is None:
        print("tkinter is not available. Cannot run GUI test.")
        exit(1)
    os.environ["KUMIHAN_GUI_DEBUG"] = "true"
    root = tk.Tk()
    root.withdraw()  # メインウィンドウを隠す
    viewer = show_log_viewer()
    # テストログを生成
    from .debug_logger import debug, error, info, warning

    debug("これはデバッグメッセージです")
    info("これは情報メッセージです")
    warning("これは警告メッセージです")
    error("これはエラーメッセージです")
    root.mainloop()
