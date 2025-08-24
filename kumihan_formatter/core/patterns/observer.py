"""Observer Pattern Implementation"""

import asyncio
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Protocol, Type, TypeVar

from ..utilities.logger import get_logger

if TYPE_CHECKING:
    from .dependency_injection import DIContainer

logger = get_logger(__name__)

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

    def __init__(self, container: Optional["DIContainer"] = None) -> None:
        self._observers: Dict[EventType, List[Observer]] = {}
        self._async_observers: Dict[EventType, List[AsyncObserver]] = {}
        self._global_observers: List[Observer] = []
        self._lock = threading.RLock()
        self._event_history: List[Event] = []
        self._max_history = 1000
        self._container = container
        self._observer_registry: Dict[str, Type[Observer]] = (
            {}
        )  # オブザーバークラス登録

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

    def remove_observer(self, observer: Observer) -> None:
        """オブザーバー削除（下位互換性のため）

        全てのイベントタイプからオブザーバーを削除
        """
        with self._lock:
            # 全イベントタイプから削除
            for event_type in list(self._observers.keys()):
                try:
                    self._observers[event_type].remove(observer)
                except ValueError:
                    continue

            # グローバルオブザーバーからも削除
            try:
                self._global_observers.remove(observer)
            except ValueError:
                pass

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

    def register_observer_class(
        self, name: str, observer_class: Type[Observer]
    ) -> None:
        """オブザーバークラスの登録"""
        try:
            self._observer_registry[name] = observer_class

            if self._container:
                # DIコンテナーに登録
                self._container.register(observer_class, observer_class)

        except Exception as e:
            logger.error(f"Observer class registration failed: {name}, error: {e}")

    def create_observer_instance(self, name: str) -> Optional[Observer]:
        """オブザーバーインスタンス作成"""
        try:
            if name not in self._observer_registry:
                return None

            observer_class = self._observer_registry[name]

            if self._container:
                # DIコンテナー経由で作成
                return self._container.resolve(observer_class)
            else:
                # 直接作成
                return observer_class()

        except Exception as e:
            logger.error(f"Observer instance creation failed: {name}, error: {e}")
            return None

    def auto_subscribe_from_container(self, event_type: EventType) -> int:
        """DIコンテナーからオブザーバーを自動登録"""
        count = 0

        try:
            if not self._container:
                return count

            for name, observer_class in self._observer_registry.items():
                observer = self.create_observer_instance(name)
                if observer:
                    self.subscribe(event_type, observer)
                    count += 1

        except Exception as e:
            logger.error(f"Auto subscription failed: {e}")

        return count

    def get_observer_info(self) -> Dict[str, Any]:
        """オブザーバー情報の取得"""
        return {
            "registered_observers": {
                event_type.name: len(observers)
                for event_type, observers in self._observers.items()
            },
            "async_observers": {
                event_type.name: len(observers)
                for event_type, observers in self._async_observers.items()
            },
            "global_observers": len(self._global_observers),
            "observer_classes": list(self._observer_registry.keys()),
            "event_history_size": len(self._event_history),
        }
