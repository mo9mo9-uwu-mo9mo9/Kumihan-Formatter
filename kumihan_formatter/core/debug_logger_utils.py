"""GUI Debug Logger Utilities for Kumihan-Formatter
開発用デバッグロガーのユーティリティ関数
"""

import os
import sys
from typing import TYPE_CHECKING

from .debug_logger_core import GUIDebugLogger
from .debug_logger_decorators import create_gui_method_decorator

if TYPE_CHECKING:
    from typing import Any, Callable

# グローバルロガーインスタンス（シングルトン使用）
gui_debug_logger = GUIDebugLogger.get_singleton()

# 便利なエイリアス
debug = gui_debug_logger.debug
info = gui_debug_logger.info
warning = gui_debug_logger.warning
error = gui_debug_logger.error
log_gui_event = gui_debug_logger.log_gui_event
log_performance = gui_debug_logger.log_performance

# グローバルロガーインスタンス付きデコレータ
log_gui_method_decorator = create_gui_method_decorator(gui_debug_logger)

# 後方互換性のためのエイリアス
# 実行時のみデコレータを使用（型チェック時は元の関数定義を維持）
if not TYPE_CHECKING:
    log_gui_method = log_gui_method_decorator  # type: ignore[misc]


def get_logger() -> GUIDebugLogger:
    """ロガーインスタンスを取得"""
    return gui_debug_logger


def is_debug_enabled() -> bool:
    """デバッグモードが有効かどうか"""
    return gui_debug_logger.enabled


def log_startup_info() -> None:
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
