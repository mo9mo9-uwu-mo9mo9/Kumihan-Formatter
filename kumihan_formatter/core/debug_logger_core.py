"""GUI Debug Logger Core for Kumihan-Formatter
開発用デバッグロガーのコア実装
"""

import logging
import os
import sys
import threading
import traceback
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Tuple


class GUIDebugLogger:
    """GUI専用デバッグロガー（スレッドセーフシングルトン）"""

    _instance: Optional["GUIDebugLogger"] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self.enabled = os.getenv("KUMIHAN_GUI_DEBUG", "").lower() == "true"
        self.log_level = os.getenv("KUMIHAN_GUI_LOG_LEVEL", "DEBUG").upper()
        self.log_file = Path(
            os.getenv("KUMIHAN_GUI_LOG_FILE", "/tmp/kumihan_gui_debug.log")
        )
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        # ログ保存用deque（メモリ内ログビューアー用、効率的なバッファ管理）
        self.log_buffer: Deque[str] = deque(maxlen=1000)
        self._buffer_lock = threading.Lock()  # バッファアクセス用ロック
        self.logger: Optional[logging.Logger] = None
        if self.enabled:
            self._setup_logger()
            self.info("=== GUI Debug Logger Started ===")
            self.info(f"Session ID: {self.session_id}")
            self.info(f"Python version: {sys.version}")
            self.info(f"Platform: {sys.platform}")

    def _setup_logger(self) -> None:
        """ロガーの初期化"""
        try:
            # ログディレクトリの作成
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            # ログファイルの作成に失敗した場合はコンソールログのみにフォールバック
            self.logger = None
            if os.getenv("KUMIHAN_GUI_CONSOLE_LOG", "").lower() == "true":
                print(
                    f"Warning: Cannot create log file {self.log_file}: {e}",
                    file=sys.stderr,
                )
            return
        try:
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
        except (OSError, PermissionError) as e:
            # ファイルハンドラーの作成に失敗
            self.logger = None
            if os.getenv("KUMIHAN_GUI_CONSOLE_LOG", "").lower() == "true":
                print(
                    f"Warning: Cannot create file handler for {self.log_file}: {e}",
                    file=sys.stderr,
                )
            return
        # コンソールハンドラー（必要な場合）
        if os.getenv("KUMIHAN_GUI_CONSOLE_LOG", "").lower() == "true":
            try:
                console_handler = logging.StreamHandler(sys.stderr)
                console_formatter = logging.Formatter("[%(levelname)s] %(message)s")
                console_handler.setFormatter(console_formatter)
                self.logger.addHandler(console_handler)
            except Exception as e:
                print(f"Warning: Cannot create console handler: {e}", file=sys.stderr)

    def _add_to_buffer(self, level: str, message: str) -> None:
        """メモリバッファにログを追加（スレッドセーフ、dequeで効率的）"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] [{level:8s}] {message}"
        with self._buffer_lock:
            # dequeのmaxlen=1000により、古いエントリは自動的に削除される（O(1)効率）
            self.log_buffer.append(log_entry)

    def debug(self, message: str, **kwargs: Any) -> None:
        """DEBUGレベルログ"""
        if not self.enabled:
            return
        if self.logger:
            self.logger.debug(message, **kwargs)
        self._add_to_buffer("DEBUG", message)

    def info(self, message: str, **kwargs: Any) -> None:
        """INFOレベルログ"""
        if not self.enabled:
            return
        if self.logger:
            self.logger.info(message, **kwargs)
        self._add_to_buffer("INFO", message)

    def warning(self, message: str, **kwargs: Any) -> None:
        """WARNINGレベルログ"""
        if not self.enabled:
            return
        if self.logger:
            self.logger.warning(message, **kwargs)
        self._add_to_buffer("WARNING", message)

    def error(
        self, message: str, exception: Optional[Exception] = None, **kwargs: Any
    ) -> None:
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

    def log_function_call(
        self,
        func_name: str,
        args: Tuple[Any, ...] = (),
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        """関数呼び出しをログ"""
        if not self.enabled:
            return
        args_str = ", ".join(str(arg) for arg in args) if args else ""
        kwargs_str = ", ".join(f"{k}={v}" for k, v in (kwargs or {}).items())
        params = ", ".join(filter(None, [args_str, kwargs_str]))
        self.debug(f"Function call: {func_name}({params})")

    def log_gui_event(self, event_type: str, widget: str, details: str = "") -> None:
        """GUIイベントをログ"""
        if not self.enabled:
            return
        message = f"GUI Event: {event_type} on {widget}"
        if details:
            message += f" - {details}"
        self.info(message)

    def log_performance(self, operation: str, duration: float) -> None:
        """パフォーマンス情報をログ"""
        if not self.enabled:
            return
        self.info(f"Performance: {operation} took {duration:.3f}s")

    def get_log_buffer(self) -> List[str]:
        """メモリ内ログバッファを取得（スレッドセーフ）"""
        with self._buffer_lock:
            return list(self.log_buffer)

    def clear_log_buffer(self) -> None:
        """メモリ内ログバッファをクリア（スレッドセーフ）"""
        with self._buffer_lock:
            self.log_buffer.clear()

    def get_log_file_path(self) -> Path:
        """ログファイルのパスを取得"""
        return self.log_file

    @classmethod
    def get_singleton(cls) -> "GUIDebugLogger":
        """スレッドセーフなシングルトンインスタンス取得"""
        if cls._instance is None:
            with cls._lock:
                # ダブルチェッキング
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
