"""GUI Debug Logger

GUI専用の詳細ログ・デバッグ機能
統一Loggerシステムを活用した高度なログ管理
"""

import logging
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

from ..core.utilities.logger import get_logger, KumihanLogger


class GUIDebugLogger:
    """GUI専用デバッグログ管理クラス"""
    
    def __init__(self, enable_console_output: bool = True):
        self.logger = get_logger("gui")
        self.enable_console = enable_console_output
        
        # GUI専用ログファイル
        self.gui_log_path = Path("tmp") / "gui_debug.log"
        self.crash_log_path = Path("tmp") / "gui_crashes.log"
        
        # ディレクトリ作成
        Path("tmp").mkdir(exist_ok=True)
        
        self._setup_gui_logging()
        self._setup_crash_handling()
    
    def _setup_gui_logging(self) -> None:
        """GUI専用ログ設定"""
        # GUI専用ファイルハンドラー
        gui_handler = logging.FileHandler(self.gui_log_path, encoding="utf-8")
        gui_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s | %(message)s"
        )
        gui_handler.setFormatter(gui_formatter)
        
        self.logger.addHandler(gui_handler)
        self.logger.setLevel(logging.DEBUG)
        
        # コンソール出力（開発時用）
        if self.enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_formatter = logging.Formatter(
                "🎨 GUI | %(levelname)s | %(message)s"
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
    
    def _setup_crash_handling(self) -> None:
        """クラッシュハンドリング設定"""
        def handle_exception(exc_type, exc_value, exc_traceback):
            """未処理例外のキャッチ"""
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            # クラッシュログに詳細記録
            crash_info = {
                "timestamp": datetime.now().isoformat(),
                "exception_type": exc_type.__name__,
                "exception_message": str(exc_value),
                "traceback": "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            }
            
            self.log_crash(crash_info)
            
            # 元のハンドラーも呼び出し
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
        
        sys.excepthook = handle_exception
    
    def log_startup(self) -> None:
        """起動ログ"""
        self.logger.info("=" * 60)
        self.logger.info("🎨 Kumihan-Formatter GUI Application Starting")
        self.logger.info(f"📂 Working Directory: {Path.cwd()}")
        self.logger.info(f"🐍 Python Version: {sys.version}")
        self.logger.info(f"💻 Platform: {sys.platform}")
        self.logger.info("=" * 60)
    
    def log_import_status(self, module_name: str, success: bool, error: Optional[str] = None) -> None:
        """インポート状況ログ"""
        if success:
            self.logger.debug(f"✅ Import Success: {module_name}")
        else:
            self.logger.error(f"❌ Import Failed: {module_name} - {error}")
    
    def log_ui_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """UIイベントログ"""
        self.logger.info(f"🖱️  UI Event: {event_type} | {details}")
    
    def log_conversion_start(self, files: list, output_dir: Optional[str]) -> None:
        """変換開始ログ"""
        self.logger.info(f"🚀 Conversion Started: {len(files)} files")
        self.logger.debug(f"📁 Files: {[str(f) for f in files]}")
        self.logger.debug(f"📤 Output Dir: {output_dir or 'Same as source'}")
    
    def log_conversion_progress(self, current: int, total: int, file_name: str) -> None:
        """変換進捗ログ"""
        progress_pct = (current / total) * 100
        self.logger.info(f"⚡ Progress: {progress_pct:.1f}% | {current}/{total} | {file_name}")
    
    def log_conversion_result(self, success_count: int, total_count: int, duration: float) -> None:
        """変換結果ログ"""
        success_rate = (success_count / total_count) * 100
        self.logger.info(f"✅ Conversion Complete: {success_count}/{total_count} ({success_rate:.1f}%)")
        self.logger.info(f"⏱️  Total Duration: {duration:.2f}s")
    
    def log_error(self, error_type: str, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """エラーログ（詳細情報付き）"""
        self.logger.error(f"💥 {error_type}: {message}")
        if context:
            self.logger.error(f"📋 Context: {context}")
    
    def log_crash(self, crash_info: Dict[str, Any]) -> None:
        """クラッシュ情報をファイルに保存"""
        try:
            with open(self.crash_log_path, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"🔥 CRASH REPORT - {crash_info['timestamp']}\n")
                f.write(f"{'='*60}\n")
                f.write(f"Exception Type: {crash_info['exception_type']}\n")
                f.write(f"Exception Message: {crash_info['exception_message']}\n")
                f.write(f"Traceback:\n{crash_info['traceback']}\n")
                f.write(f"{'='*60}\n")
            
            # メインログにも記録
            self.logger.critical(f"🔥 CRASH: {crash_info['exception_type']} - {crash_info['exception_message']}")
            
        except Exception as e:
            print(f"Failed to write crash log: {e}")
    
    def log_file_operation(self, operation: str, file_path: str, success: bool, error: Optional[str] = None) -> None:
        """ファイル操作ログ"""
        if success:
            self.logger.debug(f"📁 File {operation} Success: {file_path}")
        else:
            self.logger.error(f"📁 File {operation} Failed: {file_path} - {error}")
    
    def get_log_summary(self) -> Dict[str, Any]:
        """ログ概要情報を取得（デバッグ・サポート用）"""
        try:
            gui_log_size = self.gui_log_path.stat().st_size if self.gui_log_path.exists() else 0
            crash_log_size = self.crash_log_path.stat().st_size if self.crash_log_path.exists() else 0
            
            return {
                "gui_log_exists": self.gui_log_path.exists(),
                "gui_log_size": gui_log_size,
                "crash_log_exists": self.crash_log_path.exists(), 
                "crash_log_size": crash_log_size,
                "console_output_enabled": self.enable_console
            }
        except Exception as e:
            return {"error": str(e)}
    
    def enable_verbose_mode(self) -> None:
        """詳細モード有効化（デバッグ時）"""
        self.logger.setLevel(logging.DEBUG)
        self.logger.info("🔍 Verbose logging enabled")
    
    def disable_verbose_mode(self) -> None:
        """詳細モード無効化（リリース時）"""
        self.logger.setLevel(logging.INFO)
        self.logger.info("🔇 Verbose logging disabled")


def create_gui_logger(verbose: bool = False, console_output: bool = True) -> GUIDebugLogger:
    """GUI用ロガー作成のファクトリー関数"""
    logger = GUIDebugLogger(enable_console_output=console_output)
    
    if verbose:
        logger.enable_verbose_mode()
    
    logger.log_startup()
    return logger


def log_import_attempt(module_name: str) -> None:
    """インポート試行ログ（エラー追跡用）"""
    logger = get_logger("gui.imports")
    logger.debug(f"🔄 Attempting import: {module_name}")


def safe_import_with_logging(module_name: str, logger: GUIDebugLogger):
    """安全なインポート（ログ付き）"""
    try:
        module = __import__(module_name)
        logger.log_import_status(module_name, True)
        return module
    except ImportError as e:
        logger.log_import_status(module_name, False, str(e))
        return None
    except Exception as e:
        logger.log_import_status(module_name, False, f"Unexpected error: {e}")
        return None