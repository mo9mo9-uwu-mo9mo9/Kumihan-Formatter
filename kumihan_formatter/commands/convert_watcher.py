"""
変換コマンド - ファイル監視機能

ファイル変更監視とリアルタイム変換の責任を担当
Issue #319対応 - convert.py から分離
"""

import sys
import time
from pathlib import Path
from typing import Any

# from ...ui.console_ui import get_console_ui  # TODO: console_ui module not found


# Temporary fallback for get_console_ui
class DummyConsoleUI:
    def error(self, message: str) -> None:
        print(f"ERROR: {message}")

    def dim(self, message: str) -> None:
        print(f"INFO: {message}")

    def watch_start(self, path: str) -> None:
        print(f"Starting watch on: {path}")

    def watch_stopped(self) -> None:
        print("Watch stopped")

    def watch_file_changed(self, path: str) -> None:
        print(f"File changed: {path}")


def get_console_ui() -> DummyConsoleUI:
    return DummyConsoleUI()


class ConvertWatcher:
    """ファイル監視クラス

    責任: ファイル変更の監視とリアルタイム変換
    """

    def __init__(self, processor: Any, validator: Any) -> None:
        """
        Args:
            processor: ConvertProcessor インスタンス
            validator: ConvertValidator インスタンス
        """
        self.processor = processor
        self.validator = validator

    def start_watch_mode(
        self,
        input_file: str,
        output: str,
        config_obj: Any,
        show_test_cases: bool,
        template_name: str | None,
        include_source: bool,
        syntax_check: bool = True,
    ) -> None:
        """ファイル監視モードを開始"""
        try:
            from watchdog.observers import Observer
        except ImportError:
            get_console_ui().error("watchdog ライブラリがインストールされていません")
            get_console_ui().dim("pip install watchdog を実行してください")
            sys.exit(1)

        input_path = Path(input_file)
        get_console_ui().watch_start(str(input_path))

        # ファイル変更ハンドラーを作成
        handler = self._create_file_handler(
            input_file,
            output,
            config_obj,
            show_test_cases,
            template_name,
            include_source,
            syntax_check,
        )

        # 監視を開始
        observer = Observer()
        observer.schedule(handler, str(input_path.parent), recursive=False)
        observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            get_console_ui().watch_stopped()
            observer.stop()
        observer.join()

    def _create_file_handler(
        self,
        input_file: str,
        output: str,
        config_obj: Any,
        show_test_cases: bool,
        template_name: str | None,
        include_source: bool,
        syntax_check: bool,
    ) -> Any:
        """ファイル変更ハンドラーを作成"""
        from watchdog.events import FileSystemEventHandler

        # 設定を辞書にまとめる
        handler_config = {
            "input_file": Path(input_file),
            "output": output,
            "config": config_obj,
            "show_test_cases": show_test_cases,
            "template_name": template_name,
            "include_source": include_source,
            "syntax_check": syntax_check,
        }

        # ファイル処理ロジックを内部クラスで実装

        class SimpleEventHandler(FileSystemEventHandler):
            def __init__(self, validator: Any, processor: Any, config: Any) -> None:
                super().__init__()
                self.validator = validator
                self.processor = processor
                self.config = config

            def on_modified(self, event: Any) -> None:
                if self.processor.should_skip_event(event):
                    return

                # ファイル変更通知
                modified_path = Path(event.src_path)
                get_console_ui().watch_file_changed(str(modified_path))

                try:
                    self.processor.process_file_change()
                except Exception as e:
                    self.processor.handle_error(e)

        return SimpleEventHandler(self.validator, self.processor, handler_config)
