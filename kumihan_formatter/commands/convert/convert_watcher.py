"""
変換コマンド - ファイル監視機能

ファイル変更監視とリアルタイム変換の責任を担当
Issue #319対応 - convert.py から分離
"""

import sys
import time
from pathlib import Path
from typing import Any

from ...ui.console_ui import get_console_ui


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


class FileWatchProcessor:
    """ファイル監視処理のためのヘルパークラス"""

    def __init__(self, validator, processor, config):
        self.validator = validator
        self.processor = processor
        self.config = config
        self.last_modified = 0

    def should_skip_event(self, event) -> bool:
        """イベントをスキップすべきか判定"""
        if event.is_directory:
            return True

        modified_path = Path(event.src_path)
        if modified_path.resolve() != self.config["input_file"].resolve():
            return True

        # 重複イベント防止
        current_time = time.time()
        if current_time - self.last_modified < 1:
            return True

        self.last_modified = current_time
        return False

    def process_file_change(self):
        """ファイル変更処理"""
        if self.config["syntax_check"] and not self.check_syntax():
            return

        self.convert_file()

    def check_syntax(self) -> bool:
        """構文チェック実行"""
        error_report = self.validator.perform_syntax_check(self.config["input_file"])

        if error_report.get("has_errors", False):
            get_console_ui().error("記法エラーが検出されました")
            for error in error_report.get("errors", []):
                print(f"  エラー: {error.get('message', 'Unknown error')}")
            return False

        if error_report.get("has_warnings", False):
            get_console_ui().warning("記法に関する警告があります")
            for warning in error_report.get("warnings", []):
                print(f"  警告: {warning.get('message', 'Unknown warning')}")

        return True

    def convert_file(self):
        """ファイル変換実行"""
        try:
            output_file = self.processor.convert_file(
                self.config["input_file"],
                self.config["output"],
                self.config["config"],
                show_test_cases=self.config["show_test_cases"],
                template=self.config["template_name"],
                include_source=self.config["include_source"],
            )
            get_console_ui().watch_file_converted(str(output_file))
        except Exception as e:
            get_console_ui().error("変換処理中にエラーが発生しました", str(e))

    def handle_error(self, error):
        """エラー処理"""
        get_console_ui().error("ファイル変換中にエラーが発生しました", str(error))
        get_console_ui().dim("ファイルを修正して保存し直してください")

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

        # ファイル処理ロジックを外部クラスに委任
        file_processor = FileWatchProcessor(
            self.validator, self.processor, handler_config
        )

        class SimpleEventHandler(FileSystemEventHandler):
            def __init__(self, processor):
                super().__init__()
                self.processor = processor

            def on_modified(self, event):
                if self.processor.should_skip_event(event):
                    return

                # ファイル変更通知
                modified_path = Path(event.src_path)
                get_console_ui().watch_file_changed(str(modified_path))

                try:
                    self.processor.process_file_change()
                except Exception as e:
                    self.processor.handle_error(e)

        return SimpleEventHandler(file_processor)
