"""
Enhanced thread-safe logger for Kumihan Formatter.
Addresses mypy type errors and ensures strict type safety.
"""

import logging
import threading
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union
from datetime import datetime


class LogFormatter(logging.Formatter):
    """Custom log formatter with configurable output types."""

    def __init__(
        self,
        format_type: str = "standard",
        include_timestamp: bool = True,
        include_level: bool = True,
        colored_output: bool = False,
    ) -> None:
        self.format_type = format_type
        self.include_timestamp = include_timestamp
        self.include_level = include_level
        self.colored_output = colored_output

        if format_type == "json":
            self.format_template = self._get_json_format()
        else:
            self.format_template = self._get_standard_format()

        super().__init__(self.format_template)

    def _get_standard_format(self) -> str:
        """Standard format template."""
        parts = []
        if self.include_timestamp:
            parts.append("%(asctime)s")
        if self.include_level:
            parts.append("%(levelname)s")
        parts.extend(["%(name)s", "%(message)s"])
        return " - ".join(parts)

    def _get_json_format(self) -> str:
        """JSON format template."""
        return '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'


class KumihanLogger:
    """
    安全でスレッドセーフなロガーシングルトン

    Features:
    - Thread-safe singleton pattern
    - tmp/配下への自動出力
    - dev.logとperformance.log対応
    - カスタムフォーマッター・ハンドラー統合
    - 完全なmypy型安全性
    """

    _instance: Optional["KumihanLogger"] = None
    _lock: threading.Lock = threading.Lock()
    is_configured: bool = False

    def __new__(cls) -> "KumihanLogger":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self.loggers: Dict[str, logging.Logger] = {}
            self.log_dir: Path = Path("tmp")
            self.log_dir.mkdir(exist_ok=True)

            # dev.log関連設定
            self.dev_log_enabled: bool = True
            self.dev_log_json: bool = False

            # パフォーマンス・ヘルパー初期化
            self._setup_root_logger()
            self.performance_logger: Optional[logging.Logger] = None
            self.log_helper: Optional[Any] = None
            self.is_configured = True

    def _setup_root_logger(self) -> None:
        """ルートロガーセットアップ（tmp/配下出力）"""
        try:
            # tmp/dev.logへの出力設定
            log_file = self.log_dir / "dev.log"

            handler = logging.FileHandler(str(log_file), encoding="utf-8")
            formatter = LogFormatter(
                format_type="json" if self.dev_log_json else "standard",
                include_timestamp=True,
                include_level=True,
                colored_output=False,
            )

            handler.setFormatter(formatter)

            root_logger = logging.getLogger()
            root_logger.handlers.clear()
            root_logger.addHandler(handler)
            root_logger.setLevel(logging.DEBUG if self.dev_log_enabled else logging.INFO)

        except Exception as e:
            print(f"Logger setup failed: {e}")

    def get_logger(self, name: str) -> logging.Logger:
        """名前付きロガー取得（スレッドセーフ）"""
        if name not in self.loggers:
            with self._lock:
                if name not in self.loggers:
                    logger = logging.getLogger(name)
                    self.loggers[name] = logger
        return self.loggers[name]

    def set_level(self, level: Union[int, str]) -> None:
        """全ロガーレベル一括設定（型安全）"""
        numeric_level = level
        if isinstance(level, str):
            numeric_level = getattr(logging, level.upper())

        for logger in self.loggers.values():
            logger.setLevel(numeric_level)

        # ルートロガーレベル設定
        logging.getLogger().setLevel(numeric_level)

    def log_performance(
        self, operation: str, duration: float, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """パフォーマンス情報をtmp/performance.logに記録"""
        if not self.performance_logger:
            perf_log_file = self.log_dir / "performance.log"
            self.performance_logger = logging.getLogger("performance")
            handler = logging.FileHandler(str(perf_log_file), encoding="utf-8")
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            self.performance_logger.addHandler(handler)
            self.performance_logger.setLevel(logging.INFO)

        if details is None:
            details = {}

        self.performance_logger.info(
            f"Operation: {operation}, Duration: {duration:.4f}s, Details: {details}"
        )


# シングルトンインスタンス（型安全）
_logger_instance: Optional[KumihanLogger] = None


def get_logger(name: str = "__main__") -> logging.Logger:
    """ロガー取得のコンビニエンス関数（型安全）"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = KumihanLogger()

    return _logger_instance.get_logger(name)


def configure_logging(level: Union[int, str] = "INFO") -> None:
    """ログ設定のコンビニエンス関数（型安全）"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = KumihanLogger()

    _logger_instance.set_level(level)

    # tmp/配下への出力パス確保
    tmp_dir = Path("tmp")
    tmp_dir.mkdir(exist_ok=True)


def log_performance(
    operation: str, duration: float, details: Optional[Dict[str, Any]] = None
) -> None:
    """パフォーマンスログのコンビニエンス関数（型安全）"""
    logger_instance = get_logger("performance")
    if details is None:
        details = {}

    logger_instance.info(f"PERF: {operation} took {duration:.4f}s - {details}")


def setup_logging(level: Union[int, str] = "INFO", config: Optional[Dict[str, Any]] = None) -> None:
    """統合ログセットアップ（型安全）"""
    if config is None:
        config = {}

    # tmp/配下への強制出力
    log_dir = Path("tmp")
    log_dir.mkdir(exist_ok=True)

    # 基本設定
    configure_logging(level)

    # 追加設定適用
    if config:
        global _logger_instance
        if _logger_instance is None:
            _logger_instance = KumihanLogger()

        # カスタム設定適用
        for key, value in config.items():
            if hasattr(_logger_instance, key):
                setattr(_logger_instance, key, value)
