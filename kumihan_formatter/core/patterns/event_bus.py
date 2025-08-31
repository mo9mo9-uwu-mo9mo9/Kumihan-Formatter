"""イベントバスモジュール

Issue #1217対応: ディレクトリ構造最適化によるイベント管理機能
"""

import threading
from datetime import datetime
from enum import Enum
from typing import Callable, Dict, List, Optional, Union

from ..utilities.logger import get_logger


class ExtendedEventType(Enum):
    """拡張イベント型"""

    PARSING_STARTED = "parsing_started"
    PARSING_COMPLETED = "parsing_completed"
    PARSING_ERROR = "parsing_error"
    RENDERING_STARTED = "rendering_started"
    RENDERING_COMPLETED = "rendering_completed"
    RENDERING_ERROR = "rendering_error"
    PROCESSING_STARTED = "processing_started"
    PROCESSING_COMPLETED = "processing_completed"
    PROCESSING_ERROR = "processing_error"
    VALIDATION_STARTED = "validation_started"
    VALIDATION_COMPLETED = "validation_completed"
    VALIDATION_ERROR = "validation_error"


class EventBus:
    """軽量イベントバス - 基本機能のみ"""

    def __init__(self) -> None:
        """EventBus初期化"""
        self.logger = get_logger(__name__)
        self._listeners: Dict[ExtendedEventType, List[Callable[..., Any]]] = {}
        self._lock = threading.RLock()

    def subscribe(
        self, event_type: ExtendedEventType, callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """イベントリスナー登録"""
        with self._lock:
            if event_type not in self._listeners:
                self._listeners[event_type] = []
            self._listeners[event_type].append(callback)

        self.logger.debug(f"Subscribed to event: {event_type.value}")

    def unsubscribe(
        self, event_type: ExtendedEventType, callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """イベントリスナー解除"""
        with self._lock:
            if (
                event_type in self._listeners
                and callback in self._listeners[event_type]
            ):
                self._listeners[event_type].remove(callback)
                self.logger.debug(f"Unsubscribed from event: {event_type.value}")

    def publish(
        self, event_type: ExtendedEventType, data: Optional[Dict[str, Any]] = None
    ) -> None:
        """イベント発行"""
        if data is None:
            data = {}

        # イベントデータに基本情報を追加
        event_data = {
            "event_type": event_type.value,
            "timestamp": datetime.now().isoformat(),
            **data,
        }

        with self._lock:
            listeners = self._listeners.get(event_type, []).copy()

        for callback in listeners:
            try:
                callback(event_data)
            except Exception as e:
                self.logger.error(
                    f"Error in event listener for {event_type.value}: {e}"
                )

        self.logger.debug(
            f"Published event: {event_type.value} to {len(listeners)} listeners"
        )

    def clear_listeners(self, event_type: Optional[ExtendedEventType] = None) -> None:
        """リスナークリア"""
        with self._lock:
            if event_type is None:
                self._listeners.clear()
            else:
                self._listeners.pop(event_type, None)


# グローバルイベントバスインスタンス
_global_event_bus: Optional[EventBus] = None
_bus_lock = threading.Lock()


def get_event_bus() -> EventBus:
    """グローバルイベントバス取得"""
    global _global_event_bus
    if _global_event_bus is None:
        with _bus_lock:
            if _global_event_bus is None:
                _global_event_bus = EventBus()
    return _global_event_bus


def publish_event(
    event_type: Union[ExtendedEventType, str], data: Optional[Dict[str, Any]] = None
) -> None:
    """便利関数: イベント発行"""
    if isinstance(event_type, str):
        # 文字列から適切なEventTypeを見つける
        for et in ExtendedEventType:
            if et.value == event_type:
                event_type = et
                break
        else:
            # 見つからない場合はPROCESSING_STARTEDをデフォルトとする
            event_type = ExtendedEventType.PROCESSING_STARTED

    get_event_bus().publish(event_type, data)


def clear_event_bus() -> None:
    """テスト用: イベントバスクリア"""
    global _global_event_bus
    with _bus_lock:
        if _global_event_bus:
            _global_event_bus.clear_listeners()
        _global_event_bus = None
