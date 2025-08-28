"""イベント発行Mixin

Issue #914 Phase 3: パーサー・レンダラー共通のイベント発行機能
"""

import functools
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from ..patterns.event_bus import ExtendedEventType, get_event_bus, publish_event
import logging

logger = logging.getLogger(__name__)


class EventEmitterMixin:
    """イベント発行Mixin - パーサー・レンダラー共通"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._event_bus = get_event_bus()
        self._source_name = self.__class__.__name__

    def emit_started(
        self, operation: str, context: Optional[Dict[str, Any]] = None
    ) -> None:
        """開始イベント発行"""
        event_type = (
            ExtendedEventType.PARSING_STARTED
            if "pars" in operation.lower()
            else ExtendedEventType.RENDERING_STARTED
        )

        data = {
            "operation": operation,
            "timestamp": datetime.now().isoformat(),
            "context": context or {},
        }

        publish_event(event_type, data)
        logger.debug(f"{self._source_name}: {operation} 開始")

    def emit_completed(
        self,
        operation: str,
        result: Any = None,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> None:
        """完了イベント発行"""
        event_type = (
            ExtendedEventType.PARSING_COMPLETED
            if "pars" in operation.lower()
            else ExtendedEventType.RENDERING_COMPLETED
        )

        data = {
            "operation": operation,
            "timestamp": datetime.now().isoformat(),
            "result_type": type(result).__name__ if result else None,
            "metrics": metrics or {},
        }

        publish_event(event_type, data)
        logger.debug(f"{self._source_name}: {operation} 完了")

    def emit_error(
        self, operation: str, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> None:
        """エラーイベント発行"""
        event_type = (
            ExtendedEventType.PARSING_ERROR
            if "pars" in operation.lower()
            else ExtendedEventType.RENDERING_ERROR
        )

        data = {
            "operation": operation,
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
        }

        publish_event(event_type, data)
        logger.error(f"{self._source_name}: {operation} エラー - {error}")


def with_events(
    operation_name: str,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """デコレーター: メソッドに自動イベント発行を追加"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            if hasattr(self, "emit_started"):
                self.emit_started(operation_name, {"args_count": len(args)})

            start_time = datetime.now()
            try:
                result = func(self, *args, **kwargs)

                if hasattr(self, "emit_completed"):
                    processing_time = (datetime.now() - start_time).total_seconds()
                    metrics = {"processing_time": processing_time}
                    self.emit_completed(operation_name, result, metrics)

                return result

            except Exception as e:
                if hasattr(self, "emit_error"):
                    self.emit_error(operation_name, e)
                raise

        return wrapper

    return decorator
