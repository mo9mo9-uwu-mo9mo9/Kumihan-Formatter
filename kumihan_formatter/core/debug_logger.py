"""GUI Debug Logger for Kumihan-Formatter
開発用デバッグロガー

このモジュールはGUIアプリケーションの動作を詳細にログ記録し、
問題の特定と解決を支援します。

Environment Variables:
    KUMIHAN_GUI_DEBUG: 'true'で有効化
    KUMIHAN_GUI_LOG_LEVEL: ログレベル（DEBUG, INFO, WARNING, ERROR）
    KUMIHAN_GUI_LOG_FILE: ログファイルのパス（デフォルト: /tmp/kumihan_gui_debug.log）
"""

import functools
import logging
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional


class GUIDebugLogger:
    """GUI専用デバッグロガー"""

    def __init__(self):
        self.enabled = os.getenv("KUMIHAN_GUI_DEBUG", "").lower() == "true"
        self.log_level = os.getenv("KUMIHAN_GUI_LOG_LEVEL", "DEBUG").upper()
        self.log_file = Path(
            os.getenv("KUMIHAN_GUI_LOG_FILE", "/tmp/kumihan_gui_debug.log")
        )
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # ログ保存用リスト（メモリ内ログビューアー用）
        self.log_buffer = []
        self.max_buffer_size = 1000

        self.logger = None
        if self.enabled:
            self._setup_logger()
            self.info("=== GUI Debug Logger Started ===")
            self.info(f"Session ID: {self.session_id}")
            self.info(f"Python version: {sys.version}")
            self.info(f"Platform: {sys.platform}")

    def _setup_logger(self):
        """ロガーの初期化"""
        # ログディレクトリの作成
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # ロガーの設定
        self.logger = logging.getLogger(f"kumihan_gui_{self.session_id}")
        self.logger.setLevel(getattr(logging, self.log_level, logging.DEBUG))

        # ファイルハンドラー
        file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
        file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)8s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

        # コンソールハンドラー（必要な場合）
        if os.getenv("KUMIHAN_GUI_CONSOLE_LOG", "").lower() == "true":
            console_handler = logging.StreamHandler(sys.stderr)
            console_formatter = logging.Formatter("[%(levelname)s] %(message)s")
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

    def _add_to_buffer(self, level: str, message: str):
        """メモリバッファにログを追加"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] [{level:8s}] {message}"

        self.log_buffer.append(log_entry)
        if len(self.log_buffer) > self.max_buffer_size:
            self.log_buffer.pop(0)

    def debug(self, message: str, **kwargs):
        """DEBUGレベルログ"""
        if not self.enabled:
            return
        if self.logger:
            self.logger.debug(message, **kwargs)
        self._add_to_buffer("DEBUG", message)

    def info(self, message: str, **kwargs):
        """INFOレベルログ"""
        if not self.enabled:
            return
        if self.logger:
            self.logger.info(message, **kwargs)
        self._add_to_buffer("INFO", message)

    def warning(self, message: str, **kwargs):
        """WARNINGレベルログ"""
        if not self.enabled:
            return
        if self.logger:
            self.logger.warning(message, **kwargs)
        self._add_to_buffer("WARNING", message)

    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """ERRORレベルログ"""
        if not self.enabled:
            return

        full_message = message
        if exception:
            full_message += (
                f"\nException: {str(exception)}\nTraceback:\n{traceback.format_exc()}"
            )

        if self.logger:
            self.logger.error(full_message, **kwargs)
        self._add_to_buffer("ERROR", full_message)

    def log_function_call(self, func_name: str, args: tuple = (), kwargs: dict = None):
        """関数呼び出しをログ"""
        if not self.enabled:
            return

        args_str = ", ".join(str(arg) for arg in args) if args else ""
        kwargs_str = ", ".join(f"{k}={v}" for k, v in (kwargs or {}).items())
        params = ", ".join(filter(None, [args_str, kwargs_str]))

        self.debug(f"Function call: {func_name}({params})")

    def log_gui_event(self, event_type: str, widget: str, details: str = ""):
        """GUIイベントをログ"""
        if not self.enabled:
            return

        message = f"GUI Event: {event_type} on {widget}"
        if details:
            message += f" - {details}"

        self.info(message)

    def log_performance(self, operation: str, duration: float):
        """パフォーマンス情報をログ"""
        if not self.enabled:
            return

        self.info(f"Performance: {operation} took {duration:.3f}s")

    def get_log_buffer(self) -> list[str]:
        """メモリ内ログバッファを取得"""
        return self.log_buffer.copy()

    def clear_log_buffer(self):
        """メモリ内ログバッファをクリア"""
        self.log_buffer.clear()

    def get_log_file_path(self) -> Path:
        """ログファイルのパスを取得"""
        return self.log_file


def log_gui_method(logger_instance):
    """GUIメソッド用デコレータ"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if logger_instance.enabled:
                func_name = f"{args[0].__class__.__name__}.{func.__name__}"
                logger_instance.log_function_call(func_name, args[1:], kwargs)

                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    logger_instance.log_performance(func_name, duration)
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    logger_instance.error(
                        f"Error in {func_name} after {duration:.3f}s", e
                    )
                    raise
            else:
                return func(*args, **kwargs)

        return wrapper

    return decorator


def log_import_attempt(module_name: str, logger_instance):
    """インポート試行をログ"""

    def decorator(import_func: Callable) -> Callable:
        @functools.wraps(import_func)
        def wrapper():
            if logger_instance.enabled:
                logger_instance.debug(f"Attempting to import: {module_name}")
                try:
                    result = import_func()
                    logger_instance.info(f"Successfully imported: {module_name}")
                    return result
                except Exception as e:
                    logger_instance.error(f"Failed to import {module_name}", e)
                    raise
            else:
                return import_func()

        return wrapper

    return decorator


# グローバルロガーインスタンス
gui_debug_logger = GUIDebugLogger()


# 便利なエイリアス
debug = gui_debug_logger.debug
info = gui_debug_logger.info
warning = gui_debug_logger.warning
error = gui_debug_logger.error
log_gui_event = gui_debug_logger.log_gui_event
log_performance = gui_debug_logger.log_performance
log_gui_method = log_gui_method(gui_debug_logger)


def get_logger() -> GUIDebugLogger:
    """ロガーインスタンスを取得"""
    return gui_debug_logger


def is_debug_enabled() -> bool:
    """デバッグモードが有効かどうか"""
    return gui_debug_logger.enabled


def log_startup_info():
    """起動時情報をログ"""
    if not gui_debug_logger.enabled:
        return

    info("=== Startup Information ===")
    info(f"Current working directory: {os.getcwd()}")
    info(f"Python executable: {sys.executable}")
    info(f"Python path: {sys.path[:3]}...")  # 最初の3つだけ

    # 環境変数
    env_vars = {k: v for k, v in os.environ.items() if k.startswith("KUMIHAN")}
    if env_vars:
        info(f"Kumihan environment variables: {env_vars}")

    # メモリ使用量（利用可能な場合）
    try:
        import psutil

        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        info(f"Initial memory usage: {memory_mb:.1f} MB")
    except ImportError:
        debug("psutil not available for memory monitoring")


if __name__ == "__main__":
    # テスト用コード
    import os

    os.environ["KUMIHAN_GUI_DEBUG"] = "true"

    logger = GUIDebugLogger()
    logger.info("Test message")
    logger.error("Test error", Exception("Test exception"))

    print(f"Log file: {logger.get_log_file_path()}")
    print("Log buffer contents:")
    for line in logger.get_log_buffer():
        print(line)
