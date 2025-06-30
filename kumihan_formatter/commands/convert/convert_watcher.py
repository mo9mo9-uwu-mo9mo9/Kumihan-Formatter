"""
変換コマンド - ファイル監視機能

ファイル変更監視とリアルタイム変換の責任を担当
Issue #319対応 - convert.py から分離
"""

import sys
import time
from pathlib import Path
from typing import Optional

from ...ui.console_ui import ui


class ConvertWatcher:
    """ファイル監視クラス
    
    責任: ファイル変更の監視とリアルタイム変換
    """
    
    def __init__(self, processor, validator):
        """
        Args:
            processor: ConvertProcessor インスタンス
            validator: ConvertValidator インスタンス
        """
        self.processor = processor
        self.validator = validator
    
    def start_watch_mode(self, input_file: str, output: str, config_obj,
                        show_test_cases: bool, template_name: Optional[str],
                        include_source: bool, syntax_check: bool = True) -> None:
        """ファイル監視モードを開始"""
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
        except ImportError:
            ui.error("watchdog ライブラリがインストールされていません")
            ui.dim("pip install watchdog を実行してください")
            sys.exit(1)
        
        input_path = Path(input_file)
        ui.watch_mode_start(str(input_path))
        
        # ファイル変更ハンドラーを作成
        handler = self._create_file_handler(
            input_file, output, config_obj, show_test_cases,
            template_name, include_source, syntax_check
        )
        
        # 監視を開始
        observer = Observer()
        observer.schedule(handler, str(input_path.parent), recursive=False)
        observer.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            ui.watch_mode_stop()
            observer.stop()
        observer.join()
    
    def _create_file_handler(self, input_file: str, output: str, config_obj,
                           show_test_cases: bool, template_name: Optional[str],
                           include_source: bool, syntax_check: bool):
        """ファイル変更ハンドラーを作成"""
        
        class FileChangeHandler:
            def __init__(self, watcher, processor, validator):
                self.watcher = watcher
                self.processor = processor
                self.validator = validator
                self.input_file = Path(input_file)
                self.output = output
                self.config = config_obj
                self.show_test_cases = show_test_cases
                self.template_name = template_name
                self.include_source = include_source
                self.syntax_check = syntax_check
                self.last_modified = 0
            
            def on_modified(self, event):
                if event.is_directory:
                    return
                
                modified_path = Path(event.src_path)
                if modified_path.resolve() == self.input_file.resolve():
                    # 重複イベントを防ぐ
                    current_time = time.time()
                    if current_time - self.last_modified < 1:
                        return
                    self.last_modified = current_time
                    
                    ui.file_changed(str(modified_path))
                    
                    try:
                        self._process_file_change()
                    except Exception as e:
                        ui.error("ファイル変換中にエラーが発生しました", str(e))
                        ui.dim("ファイルを修正して保存し直してください")
            
            def _process_file_change(self):
                """ファイル変更時の処理"""
                # 構文チェック（有効な場合）
                if self.syntax_check:
                    error_report = self.validator.perform_syntax_check(self.input_file)
                    
                    if error_report.has_errors():
                        ui.error("記法エラーが検出されました")
                        print(error_report.to_console_output())
                        return
                    elif error_report.has_warnings():
                        ui.warning("記法に関する警告があります")
                        print(error_report.to_console_output())
                
                # ファイル変換
                output_file = self.processor.convert_file(
                    self.input_file, self.output, self.config,
                    show_test_cases=self.show_test_cases,
                    template=self.template_name,
                    include_source=self.include_source
                )
                
                ui.watch_mode_converted(str(output_file))
        
        from watchdog.events import FileSystemEventHandler
        
        class FileSystemHandler(FileSystemEventHandler, FileChangeHandler):
            def __init__(self, watcher, processor, validator):
                FileSystemEventHandler.__init__(self)
                FileChangeHandler.__init__(self, watcher, processor, validator)
        
        return FileSystemHandler(self, self.processor, self.validator)