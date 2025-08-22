"""Observer Pattern Implementation"""

import asyncio
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, TypeVar

T = TypeVar("T")


class EventType(Enum):
    """イベント種別"""

    PARSING_STARTED = "parsing_started"
    PARSING_COMPLETED = "parsing_completed"
    PARSING_ERROR = "parsing_error"
    RENDERING_STARTED = "rendering_started"
    RENDERING_COMPLETED = "rendering_completed"
    RENDERING_ERROR = "rendering_error"
    VALIDATION_FAILED = "validation_failed"
    PLUGIN_LOADED = "plugin_loaded"
    PLUGIN_UNLOADED = "plugin_unloaded"

    # ExtendedEventType互換性のために追加
    PERFORMANCE_MEASUREMENT = "performance_measurement"
    DEPENDENCY_RESOLVED = "dependency_resolved"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    ASYNC_TASK_STARTED = "async_task_started"
    ASYNC_TASK_COMPLETED = "async_task_completed"

    CUSTOM = "custom"


@dataclass
class Event:
    """イベントデータ"""

    event_type: EventType
    source: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))


class Observer(Protocol):
    """オブザーバープロトコル"""

    def handle_event(self, event: Event) -> None:
        """イベント処理"""
        ...

    def get_supported_events(self) -> List[EventType]:
        """対応イベント種別取得"""
        ...


class AsyncObserver(Protocol):
    """非同期オブザーバープロトコル"""

    async def handle_event_async(self, event: Event) -> None:
        """非同期イベント処理"""
        ...


class EventBus:
    """イベントバス - Observer Pattern実装"""

    def __init__(self) -> None:
        self._observers: Dict[EventType, List[Observer]] = {}
        self._async_observers: Dict[EventType, List[AsyncObserver]] = {}
        self._global_observers: List[Observer] = []
        self._lock = threading.RLock()
        self._event_history: List[Event] = []
        self._max_history = 1000

    def subscribe(self, event_type: EventType, observer: Observer) -> None:
        """オブザーバー登録"""
        with self._lock:
            if event_type not in self._observers:
                self._observers[event_type] = []
            self._observers[event_type].append(observer)

    def subscribe_async(self, event_type: EventType, observer: AsyncObserver) -> None:
        """非同期オブザーバー登録"""
        with self._lock:
            if event_type not in self._async_observers:
                self._async_observers[event_type] = []
            self._async_observers[event_type].append(observer)

    def subscribe_global(self, observer: Observer) -> None:
        """グローバルオブザーバー登録"""
        with self._lock:
            self._global_observers.append(observer)

    def unsubscribe(self, event_type: EventType, observer: Observer) -> bool:
        """オブザーバー解除"""
        with self._lock:
            if event_type in self._observers:
                try:
                    self._observers[event_type].remove(observer)
                    return True
                except ValueError:
                    pass
            return False

    def publish(self, event: Event) -> None:
        """イベント発行"""
        with self._lock:
            # 履歴保存
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)

            # 同期オブザーバーに通知
            observers = self._observers.get(event.event_type, [])
            observers.extend(self._global_observers)

            for observer in observers:
                try:
                    observer.handle_event(event)
                except Exception as e:
                    # エラーログ記録（オブザーバーエラーがシステム全体に影響しないよう）
                    self._handle_observer_error(observer, event, e)

    async def publish_async(self, event: Event) -> None:
        """非同期イベント発行"""
        # 同期処理も実行
        self.publish(event)

        # 非同期オブザーバーに通知
        async_observers = self._async_observers.get(event.event_type, [])
        tasks = []
        for observer in async_observers:
            task = asyncio.create_task(observer.handle_event_async(event))
            tasks.append(task)

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def get_event_history(
        self, event_type: Optional[EventType] = None, limit: Optional[int] = None
    ) -> List[Event]:
        """イベント履歴取得"""
        with self._lock:
            events = self._event_history
            if event_type:
                events = [e for e in events if e.event_type == event_type]
            if limit:
                events = events[-limit:]
            return events.copy()

    def clear_history(self) -> None:
        """履歴クリア"""
        with self._lock:
            self._event_history.clear()

    def _handle_observer_error(
        self, observer: Observer, event: Event, error: Exception
    ) -> None:
        """オブザーバーエラー処理"""
        # ログ記録やエラー通知の実装
        pass
