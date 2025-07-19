"""GUI Debug Logger for Kumihan-Formatter
開発用デバッグロガー
このモジュールはGUIアプリケーションの動作を詳細にログ記録し、
問題の特定と解決を支援します。

分割後の統合インターフェース:
- debug_logger_core.py: コアロガークラス
- debug_logger_decorators.py: デコレータ機能
- debug_logger_utils.py: ユーティリティ関数

Environment Variables:
    KUMIHAN_GUI_DEBUG: 'true'で有効化
    KUMIHAN_GUI_LOG_LEVEL: ログレベル（DEBUG, INFO, WARNING, ERROR）
    KUMIHAN_GUI_LOG_FILE: ログファイルのパス（デフォルト: /tmp/kumihan_gui_debug.log）
"""

# 後方互換性のために既存のAPIを再エクスポート
from .debug_logger_core import GUIDebugLogger
from .debug_logger_decorators import log_gui_method, log_import_attempt
from .debug_logger_utils import (
    debug,
    error,
    get_logger,
    gui_debug_logger,
    info,
    is_debug_enabled,
    log_gui_event,
    log_gui_method_decorator,
    log_performance,
    log_startup_info,
    warning,
)

__all__ = [
    "GUIDebugLogger",
    "gui_debug_logger",
    "debug",
    "info",
    "warning",
    "error",
    "log_gui_event",
    "log_performance",
    "log_gui_method",
    "log_gui_method_decorator",
    "log_import_attempt",
    "get_logger",
    "is_debug_enabled",
    "log_startup_info",
]
