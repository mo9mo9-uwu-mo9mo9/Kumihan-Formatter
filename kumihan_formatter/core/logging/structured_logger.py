"""
構造化ログシステム
JSON形式でのログ出力、コンテキスト情報付与、パフォーマンスメトリクス記録

既存のKumihanLoggerおよびSecureLogFormatterと統合したエンタープライズ対応ログシステム
"""

import json
import logging
import re
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import psutil

from kumihan_formatter.core.security.secure_logging import (
    SecureLogFilter,
    SecureLogFormatter,
)
from kumihan_formatter.core.utilities.logger import get_logger


class LogContext:
    """ログコンテキスト管理クラス

    セッション、ユーザー、リクエスト等のコンテキスト情報を管理
    """

    _context_storage: Dict[int, Dict[str, Any]] = {}
    _lock = threading.Lock()

    @classmethod
    def set_context(cls, **kwargs: Any) -> None:
        """現在のスレッドにコンテキスト情報を設定"""
        thread_id = threading.get_ident()
        with cls._lock:
            if thread_id not in cls._context_storage:
                cls._context_storage[thread_id] = {}
            cls._context_storage[thread_id].update(kwargs)

    @classmethod
    def get_context(cls) -> Dict[str, Any]:
        """現在のスレッドのコンテキスト情報を取得"""
        thread_id = threading.get_ident()
        with cls._lock:
            return cls._context_storage.get(thread_id, {}).copy()

    @classmethod
    def clear_context(cls) -> None:
        """現在のスレッドのコンテキスト情報をクリア"""
        thread_id = threading.get_ident()
        with cls._lock:
            cls._context_storage.pop(thread_id, None)


class PerformanceTracker:
    """パフォーマンス追跡クラス

    処理時間、メモリ使用量、CPU使用率等のメトリクスを追跡
    """

    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.start_memory: Optional[int] = None
        self.end_memory: Optional[int] = None
        self.process = psutil.Process()

    def start(self) -> None:
        """追跡開始"""
        self.start_time = time.perf_counter()
        self.start_memory = self.process.memory_info().rss

    def stop(self) -> Dict[str, Any]:
        """追跡停止・結果取得"""
        self.end_time = time.perf_counter()
        self.end_memory = self.process.memory_info().rss

        duration = (self.end_time - self.start_time) if self.start_time else 0.0
        memory_delta = (
            (self.end_memory - self.start_memory)
            if self.start_memory and self.end_memory
            else 0
        )

        return {
            "operation": self.operation_name,
            "duration_seconds": round(duration, 4),
            "memory_delta_bytes": memory_delta,
            "memory_usage_mb": (
                round(self.end_memory / 1024 / 1024, 2) if self.end_memory else 0
            ),
            "cpu_percent": round(self.process.cpu_percent(), 2),
        }


class StructuredLogFormatter(logging.Formatter):
    """構造化ログフォーマッター

    JSON形式でのログ出力、セキュリティ考慮あり
    """

    # 強化されたセキュリティパターン
    ENHANCED_SECURITY_PATTERNS = [
        (r'password["\']?\s*[:=]\s*["\']([^"\']+)["\']', r'password="***"'),
        (r'api_key["\']?\s*[:=]\s*["\']([^"\']+)["\']', r'api_key="***"'),
        (r'secret["\']?\s*[:=]\s*["\']([^"\']+)["\']', r'secret="***"'),
        (r'token["\']?\s*[:=]\s*["\']([^"\']+)["\']', r'token="***"'),
        (r"Authorization:\s*Bearer\s+([^\s]+)", r"Authorization: Bearer ***"),
        (r"([0-9]{4})-?([0-9]{4})-?([0-9]{4})-?([0-9]{4})", r"****-****-****-****"),
        # JSON内のパスワード・シークレット
        (r'"password"\s*:\s*"([^"]*)"', r'"password": "***"'),
        (r'"secret"\s*:\s*"([^"]*)"', r'"secret": "***"'),
        (r'"api_key"\s*:\s*"([^"]*)"', r'"api_key": "***"'),
        (r'"token"\s*:\s*"([^"]*)"', r'"token": "***"'),
    ]

    def __init__(self, include_context: bool = True, include_security: bool = True):
        self.include_context = include_context
        self.include_security = include_security
        if include_security:
            self.secure_formatter = SecureLogFormatter()
        super().__init__()

    def _mask_sensitive_data(self, text: str) -> str:
        """機密情報をマスクする強化版関数"""
        for pattern, replacement in self.ENHANCED_SECURITY_PATTERNS:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text

    def format(self, record: logging.LogRecord) -> str:
        """ログレコードをJSON形式でフォーマット"""
        # 基本ログ構造
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # コンテキスト情報を含める場合
        if self.include_context:
            context = LogContext.get_context()
            if context:
                log_data["context"] = context

        # extra情報を含める
        if hasattr(record, "extra") and record.extra:
            log_data["extra"] = record.extra

        # パフォーマンスメトリクスを含める
        if hasattr(record, "performance") and record.performance:
            log_data["performance"] = record.performance

        # セキュリティイベント情報を含める
        if hasattr(record, "security_event") and record.security_event:
            log_data["security_event"] = record.security_event

        # 例外情報を含める
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": (
                    self.formatException(record.exc_info) if record.exc_info else None
                ),
            }

        json_log = json.dumps(log_data, ensure_ascii=False, separators=(",", ":"))

        # セキュリティマスクを適用
        if self.include_security:
            # 強化されたセキュリティパターンでマスク
            json_log = self._mask_sensitive_data(json_log)

            # 既存のセキュアフォーマッターも適用
            if hasattr(self, "secure_formatter"):
                temp_record = logging.LogRecord(
                    record.name,
                    record.levelno,
                    record.pathname,
                    record.lineno,
                    json_log,
                    record.args,
                    record.exc_info,
                    record.funcName,
                )
                json_log = self.secure_formatter.format(temp_record)
                # フォーマット後のメッセージからJSON部分のみを抽出
                if " - " in json_log:
                    parts = json_log.split(" - ")
                    json_log = parts[-1]  # 最後の部分がメッセージ

        return json_log


class StructuredLogger:
    """構造化ログシステムのメインクラス

    JSON形式ログ、コンテキスト管理、パフォーマンス追跡、セキュリティ強化を提供
    """

    def __init__(
        self,
        name: str,
        context: Optional[Dict[str, Any]] = None,
        output_file: Optional[str] = None,
    ):
        self.name = name
        self.logger = get_logger(name)
        self._setup_structured_handler(output_file)

        # 初期コンテキストを設定
        if context:
            LogContext.set_context(**context)

    def _setup_structured_handler(self, output_file: Optional[str] = None) -> None:
        """構造化ログハンドラーのセットアップ"""
        # tmp/配下への出力ファイル決定
        log_dir = Path("tmp")
        log_dir.mkdir(exist_ok=True)

        if output_file is None:
            output_file = f"structured_{self.name.replace('.', '_')}.log"

        log_file_path = log_dir / output_file

        # 構造化ログハンドラーを作成
        handler = logging.FileHandler(str(log_file_path), encoding="utf-8")
        formatter = StructuredLogFormatter(include_context=True, include_security=True)
        handler.setFormatter(formatter)

        # セキュリティフィルターを追加
        handler.addFilter(SecureLogFilter())

        # ロガーにハンドラーを追加（重複回避）
        handler_names = [
            h.get_name() for h in self.logger.handlers if hasattr(h, "get_name")
        ]
        if f"structured_{self.name}" not in handler_names:
            handler.set_name(f"structured_{self.name}")
            self.logger.addHandler(handler)

    def _log_with_extra(
        self,
        level: int,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        performance: Optional[Dict[str, Any]] = None,
        security_event: Optional[Dict[str, Any]] = None,
        exc_info: bool = False,
    ) -> None:
        """拡張情報付きログ出力"""
        # exc_infoの型を正しく指定
        exc_info_param = None
        if exc_info:
            import sys

            exc_info_param = sys.exc_info()

        record = self.logger.makeRecord(
            self.name, level, "", 0, message, (), exc_info_param
        )

        # 拡張情報を追加
        if extra:
            record.extra = extra
        if performance:
            record.performance = performance
        if security_event:
            record.security_event = security_event

        self.logger.handle(record)

    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """DEBUGレベルログ出力"""
        self._log_with_extra(logging.DEBUG, message, extra=extra)

    def info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """INFOレベルログ出力"""
        self._log_with_extra(logging.INFO, message, extra=extra)

    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """WARNINGレベルログ出力"""
        self._log_with_extra(logging.WARNING, message, extra=extra)

    def error(
        self,
        message: str,
        exc_info: bool = False,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """ERRORレベルログ出力"""
        self._log_with_extra(logging.ERROR, message, extra=extra, exc_info=exc_info)

    def critical(
        self,
        message: str,
        exc_info: bool = False,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """CRITICALレベルログ出力"""
        self._log_with_extra(logging.CRITICAL, message, extra=extra, exc_info=exc_info)

    def performance_log(
        self,
        operation: str,
        duration: float,
        memory_usage: Optional[int] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """パフォーマンス情報ログ出力"""
        performance_data = {
            "operation": operation,
            "duration_seconds": round(duration, 4),
            "memory_usage_bytes": memory_usage,
        }

        if extra:
            performance_data.update(extra)

        self._log_with_extra(
            logging.INFO,
            f"Performance: {operation} completed in {duration:.4f}s",
            performance=performance_data,
        )

    def security_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """セキュリティイベントログ出力"""
        security_data = {
            "event_type": event_type,
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details,
        }

        # セキュリティイベントの重要度を判定
        critical_events = [
            "authentication_failure",
            "unauthorized_access",
            "data_breach",
        ]
        log_level = (
            logging.CRITICAL if event_type in critical_events else logging.WARNING
        )

        self._log_with_extra(
            log_level, f"Security Event: {event_type}", security_event=security_data
        )

    @contextmanager
    def performance_context(self, operation_name: str) -> Any:
        """パフォーマンス追跡コンテキストマネージャー"""
        tracker = PerformanceTracker(operation_name)
        tracker.start()

        try:
            yield tracker
        finally:
            performance_data = tracker.stop()
            self.performance_log(
                operation_name,
                performance_data["duration_seconds"],
                performance_data.get("memory_delta_bytes"),
                extra=performance_data,
            )

    def set_context(self, **kwargs: Any) -> None:
        """ログコンテキストを設定"""
        LogContext.set_context(**kwargs)

    def clear_context(self) -> None:
        """ログコンテキストをクリア"""
        LogContext.clear_context()


# 便利関数
def get_structured_logger(
    name: str,
    context: Optional[Dict[str, Any]] = None,
    output_file: Optional[str] = None,
) -> StructuredLogger:
    """構造化ロガーの取得"""
    return StructuredLogger(name, context=context, output_file=output_file)


def set_global_context(**kwargs: Any) -> None:
    """グローバルログコンテキストの設定"""
    LogContext.set_context(**kwargs)


def clear_global_context() -> None:
    """グローバルログコンテキストのクリア"""
    LogContext.clear_context()


# 異常検知機能
class AnomalyDetector:
    """パフォーマンス異常・セキュリティイベントの自動検出"""

    def __init__(self) -> None:
        self.performance_thresholds = {
            "duration_warning": 5.0,  # 5秒
            "duration_critical": 30.0,  # 30秒
            "memory_warning": 100 * 1024 * 1024,  # 100MB
            "memory_critical": 500 * 1024 * 1024,  # 500MB
        }

    def check_performance_anomaly(
        self, operation: str, duration: float, memory_usage: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """パフォーマンス異常検知"""
        anomalies = []

        if duration > self.performance_thresholds["duration_critical"]:
            anomalies.append(
                {
                    "type": "performance_critical",
                    "metric": "duration",
                    "value": duration,
                    "threshold": self.performance_thresholds["duration_critical"],
                }
            )
        elif duration > self.performance_thresholds["duration_warning"]:
            anomalies.append(
                {
                    "type": "performance_warning",
                    "metric": "duration",
                    "value": duration,
                    "threshold": self.performance_thresholds["duration_warning"],
                }
            )

        if memory_usage:
            if memory_usage > self.performance_thresholds["memory_critical"]:
                anomalies.append(
                    {
                        "type": "memory_critical",
                        "metric": "memory_usage",
                        "value": memory_usage,
                        "threshold": self.performance_thresholds["memory_critical"],
                    }
                )
            elif memory_usage > self.performance_thresholds["memory_warning"]:
                anomalies.append(
                    {
                        "type": "memory_warning",
                        "metric": "memory_usage",
                        "value": memory_usage,
                        "threshold": self.performance_thresholds["memory_warning"],
                    }
                )

        return {"operation": operation, "anomalies": anomalies} if anomalies else None


# グローバル異常検知器
_anomaly_detector = AnomalyDetector()


class EnhancedStructuredLogger(StructuredLogger):
    """異常検知機能付き構造化ロガー"""

    def performance_log(
        self,
        operation: str,
        duration: float,
        memory_usage: Optional[int] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """異常検知付きパフォーマンス情報ログ出力"""
        # 親クラスのログ出力
        super().performance_log(operation, duration, memory_usage, extra)

        # 異常検知
        anomaly = _anomaly_detector.check_performance_anomaly(
            operation, duration, memory_usage
        )
        if anomaly:
            self.warning(
                f"Performance anomaly detected for {operation}",
                extra={"anomaly_details": anomaly},
            )


def get_enhanced_structured_logger(
    name: str,
    context: Optional[Dict[str, Any]] = None,
    output_file: Optional[str] = None,
) -> EnhancedStructuredLogger:
    """異常検知機能付き構造化ロガーの取得"""
    return EnhancedStructuredLogger(name, context=context, output_file=output_file)
