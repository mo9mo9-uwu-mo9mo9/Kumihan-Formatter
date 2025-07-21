"""GUI Log Viewer Event Handlers for Kumihan-Formatter
GUIアプリケーション用のログビューアーイベント処理
"""

import platform
import subprocess
import threading
import time
from typing import TYPE_CHECKING, Any, Callable, List, Optional

if TYPE_CHECKING:
    import tkinter as tk


class LogViewerEventHandler:
    """ログビューアーのイベント処理クラス"""

    def __init__(self, ui_manager: Any, logger_getter: Callable[[], Any]) -> None:
        self.ui = ui_manager
        self.get_logger = logger_getter
        self.running = False
        self.update_thread: Optional[threading.Thread] = None

    def start_log_monitoring(self) -> None:
        """ログ監視を開始"""
        self.running = True
        self.update_thread = threading.Thread(target=self._update_logs, daemon=True)
        self.update_thread.start()

    def stop_log_monitoring(self) -> None:
        """ログ監視を停止"""
        self.running = False
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=1)

    def _update_logs(self) -> None:
        """ログを定期的に更新"""
        try:
            logger = self.get_logger()
            if not logger or not logger.enabled:

                def set_debug_disabled() -> None:
                    self.ui.set_status("デバッグモードが無効です")

                self.ui.window.after(100, set_debug_disabled)
                return

            last_log_count = 0
            while self.running:
                try:
                    # ログバッファを取得
                    log_buffer = logger.get_log_buffer()
                    # 新しいログがある場合のみ更新
                    if len(log_buffer) > last_log_count:
                        new_logs = log_buffer[last_log_count:]

                        def add_new_logs() -> None:
                            self._add_logs(new_logs)

                        self.ui.window.after(0, add_new_logs)
                        last_log_count = len(log_buffer)

                        # ステータス更新
                        status = f"ログ件数: {len(log_buffer)} 件"
                        if logger.get_log_file_path().exists():
                            file_size = logger.get_log_file_path().stat().st_size
                            status += f" | ファイルサイズ: {file_size // 1024} KB"

                        def update_status() -> None:
                            self.ui.set_status(status)

                        self.ui.window.after(0, update_status)

                    time.sleep(0.5)  # 0.5秒間隔で更新
                except Exception as e:
                    error_msg = f"ログ更新エラー: {str(e)}"

                    def set_error_msg() -> None:
                        self.ui.set_status(error_msg)

                    self.ui.window.after(0, set_error_msg)
                    time.sleep(1)
        except Exception as e:
            error_msg = f"ログビューアーエラー: {str(e)}"

            def set_viewer_error() -> None:
                self.ui.set_status(error_msg)

            self.ui.window.after(0, set_viewer_error)

    def _add_logs(self, logs: List[str]) -> None:
        """ログをテキストエリアに追加"""
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
            level_filter = self.ui.get_level_filter()
            if level_filter != "ALL" and tag != level_filter:
                continue

            self.ui.add_log_entry(log_line, tag)

        # 自動スクロール
        if self.ui.get_auto_scroll_state():
            self.ui.scroll_to_end()

    def clear_log(self) -> None:
        """ログをクリア"""
        self.ui.clear_log_text()
        # ログバッファもクリア
        try:
            logger = self.get_logger()
            if logger:
                logger.clear_log_buffer()
                self.ui.set_status("ログがクリアされました")
        except Exception as e:
            self.ui.set_status(f"ログクリアエラー: {str(e)}")

    def toggle_auto_scroll(self) -> None:
        """自動スクロールの切り替え"""
        # UIコンポーネントが状態を管理するので特に処理は不要
        pass

    def filter_logs(self, event: Optional[object] = None) -> None:
        """ログレベルフィルタリング"""
        # 既存のログを再表示（フィルタリング適用）
        try:
            logger = self.get_logger()
            if logger and logger.enabled:
                self.ui.clear_log_text()
                # 全ログを再追加
                log_buffer = logger.get_log_buffer()
                self._add_logs(log_buffer)
        except Exception as e:
            self.ui.set_status(f"フィルタリングエラー: {str(e)}")

    def open_log_file(self) -> None:
        """ログファイルを外部エディタで開く"""
        try:
            logger = self.get_logger()
            if logger and logger.get_log_file_path().exists():
                log_file = str(logger.get_log_file_path())
                if platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", log_file])
                elif platform.system() == "Windows":
                    subprocess.run(["notepad", log_file])
                else:  # Linux
                    subprocess.run(["xdg-open", log_file])
                self.ui.set_status(f"ログファイルを開きました: {log_file}")
            else:
                self.ui.set_status("ログファイルが見つかりません")
        except Exception as e:
            self.ui.set_status(f"ファイルオープンエラー: {str(e)}")
