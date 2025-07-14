"""GUI Log Viewer for Kumihan-Formatter
GUIアプリケーション用のリアルタイムログビューアー
"""

import threading
import time
import tkinter as tk
from tkinter import scrolledtext, ttk
from typing import List, Optional, Union


class LogViewerWindow:
    """リアルタイムログビューアーウィンドウ"""

    def __init__(self, parent_window: Optional[tk.Tk] = None) -> None:
        self.parent = parent_window
        self.window: Optional[Union[tk.Tk, tk.Toplevel]] = None
        self.log_text: Optional[scrolledtext.ScrolledText] = None
        self.auto_scroll = True
        self.update_thread: Optional[threading.Thread] = None
        self.running = False
        self.auto_scroll_var: Optional[tk.BooleanVar] = None
        self.level_var: Optional[tk.StringVar] = None
        self.status_var: Optional[tk.StringVar] = None

    def show(self) -> None:
        """ログビューアーウィンドウを表示"""
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

        self._setup_ui()
        self._start_update_thread()

    def _setup_ui(self) -> None:
        """UIコンポーネントのセットアップ"""
        # ツールバー
        toolbar = ttk.Frame(self.window)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        # クリアボタン
        ttk.Button(toolbar, text="ログクリア", command=self.clear_log).pack(
            side=tk.LEFT, padx=(0, 5)
        )

        # 自動スクロールチェックボックス
        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            toolbar,
            text="自動スクロール",
            variable=self.auto_scroll_var,
            command=self._toggle_auto_scroll,
        ).pack(side=tk.LEFT, padx=(0, 5))

        # ログファイルを開くボタン
        ttk.Button(toolbar, text="ログファイルを開く", command=self.open_log_file).pack(
            side=tk.LEFT, padx=(0, 5)
        )

        # ログレベルフィルター
        ttk.Label(toolbar, text="レベル:").pack(side=tk.LEFT, padx=(10, 5))
        self.level_var = tk.StringVar(value="ALL")
        level_combo = ttk.Combobox(
            toolbar,
            textvariable=self.level_var,
            values=["ALL", "DEBUG", "INFO", "WARNING", "ERROR"],
            state="readonly",
            width=10,
        )
        level_combo.pack(side=tk.LEFT)
        level_combo.bind("<<ComboboxSelected>>", self._filter_logs)

        # ログテキストエリア
        text_frame = ttk.Frame(self.window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        self.log_text = scrolledtext.ScrolledText(
            text_frame, wrap=tk.WORD, font=("Consolas", 10), state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # ログレベルごとの色設定
        self.log_text.tag_configure("DEBUG", foreground="gray")
        self.log_text.tag_configure("INFO", foreground="black")
        self.log_text.tag_configure("WARNING", foreground="orange")
        self.log_text.tag_configure(
            "ERROR", foreground="red", font=("Consolas", 10, "bold")
        )

        # ステータスバー
        self.status_var = tk.StringVar(value="ログビューアー起動中...")
        status_bar = ttk.Label(
            self.window,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
        )
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def _start_update_thread(self) -> None:
        """ログ更新スレッドを開始"""
        self.running = True
        self.update_thread = threading.Thread(target=self._update_logs, daemon=True)
        self.update_thread.start()

    def _update_logs(self) -> None:
        """ログを定期的に更新"""
        try:
            from .debug_logger import get_logger

            logger = get_logger()

            if not logger or not logger.enabled:
                if self.window and self.status_var:

                    def set_debug_disabled() -> None:
                        if self.status_var:
                            self.status_var.set("デバッグモードが無効です")

                    self.window.after(100, set_debug_disabled)
                return

            last_log_count = 0

            while self.running:
                try:
                    # ログバッファを取得
                    log_buffer = logger.get_log_buffer()

                    # 新しいログがある場合のみ更新
                    if len(log_buffer) > last_log_count:
                        new_logs = log_buffer[last_log_count:]
                        if self.window:

                            def add_new_logs() -> None:
                                self._add_logs(new_logs)

                            self.window.after(0, add_new_logs)
                        last_log_count = len(log_buffer)

                        # ステータス更新
                        status = f"ログ件数: {len(log_buffer)} 件"
                        if logger.get_log_file_path().exists():
                            file_size = logger.get_log_file_path().stat().st_size
                            status += f" | ファイルサイズ: {file_size // 1024} KB"
                        if self.window and self.status_var:

                            def update_status() -> None:
                                if self.status_var:
                                    self.status_var.set(status)

                            self.window.after(0, update_status)

                    time.sleep(0.5)  # 0.5秒間隔で更新

                except Exception as e:
                    error_msg = f"ログ更新エラー: {str(e)}"
                    if self.window and self.status_var:

                        def set_error_msg() -> None:
                            if self.status_var:
                                self.status_var.set(error_msg)

                        self.window.after(0, set_error_msg)
                    time.sleep(1)

        except Exception as e:
            error_msg = f"ログビューアーエラー: {str(e)}"
            if self.window and self.status_var:

                def set_viewer_error() -> None:
                    if self.status_var:
                        self.status_var.set(error_msg)

                self.window.after(0, set_viewer_error)

    def _add_logs(self, logs: List[str]) -> None:
        """ログをテキストエリアに追加"""
        if not self.log_text:
            return

        self.log_text.config(state=tk.NORMAL)

        for log_line in logs:
            # ログレベルを判定してタグを設定
            tag = "INFO"  # デフォルト
            if "[DEBUG   ]" in log_line:
                tag = "DEBUG"
            elif "[INFO    ]" in log_line:
                tag = "INFO"
            elif "[WARNING ]" in log_line:
                tag = "WARNING"
            elif "[ERROR   ]" in log_line:
                tag = "ERROR"

            # フィルタリング
            if (
                self.level_var
                and self.level_var.get() != "ALL"
                and tag != self.level_var.get()
            ):
                continue

            self.log_text.insert(tk.END, log_line + "\n", tag)

        self.log_text.config(state=tk.DISABLED)

        # 自動スクロール
        if self.auto_scroll and self.log_text:
            self.log_text.see(tk.END)

    def _toggle_auto_scroll(self) -> None:
        """自動スクロールの切り替え"""
        if self.auto_scroll_var:
            self.auto_scroll = self.auto_scroll_var.get()

    def _filter_logs(self, event: Optional[object] = None) -> None:
        """ログレベルフィルタリング"""
        # 既存のログを再表示（フィルタリング適用）
        try:
            from .debug_logger import get_logger

            logger = get_logger()
            if logger and logger.enabled and self.log_text:
                self.log_text.config(state=tk.NORMAL)
                self.log_text.delete(1.0, tk.END)
                self.log_text.config(state=tk.DISABLED)

                # 全ログを再追加
                log_buffer = logger.get_log_buffer()
                self._add_logs(log_buffer)
        except Exception as e:
            if self.status_var:
                self.status_var.set(f"フィルタリングエラー: {str(e)}")

    def clear_log(self) -> None:
        """ログをクリア"""
        if self.log_text:
            self.log_text.config(state=tk.NORMAL)
            self.log_text.delete(1.0, tk.END)
            self.log_text.config(state=tk.DISABLED)

        # ログバッファもクリア
        try:
            from .debug_logger import get_logger

            logger = get_logger()
            if logger:
                logger.clear_log_buffer()
                if self.status_var:
                    self.status_var.set("ログがクリアされました")
        except Exception as e:
            if self.status_var:
                self.status_var.set(f"ログクリアエラー: {str(e)}")

    def open_log_file(self) -> None:
        """ログファイルを外部エディタで開く"""
        try:
            from .debug_logger import get_logger

            logger = get_logger()
            if logger and logger.get_log_file_path().exists():
                import platform
                import subprocess

                log_file = str(logger.get_log_file_path())

                if platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", log_file])
                elif platform.system() == "Windows":
                    subprocess.run(["notepad", log_file])
                else:  # Linux
                    subprocess.run(["xdg-open", log_file])

                if self.status_var:
                    self.status_var.set(f"ログファイルを開きました: {log_file}")
            else:
                if self.status_var:
                    self.status_var.set("ログファイルが見つかりません")
        except Exception as e:
            if self.status_var:
                self.status_var.set(f"ファイルオープンエラー: {str(e)}")

    def on_closing(self) -> None:
        """ウィンドウを閉じる時の処理"""
        self.running = False
        if self.update_thread and self.update_thread.is_alive():
            # スレッドの終了を待つ（最大1秒）
            self.update_thread.join(timeout=1)

        if self.window:
            self.window.destroy()
            self.window = None

    def is_open(self) -> bool:
        """ウィンドウが開いているかどうか"""
        return self.window is not None


def show_log_viewer(parent_window: Optional[tk.Tk] = None) -> LogViewerWindow:
    """ログビューアーを表示"""
    viewer = LogViewerWindow(parent_window)
    viewer.show()
    return viewer


if __name__ == "__main__":
    # テスト用
    import os

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
