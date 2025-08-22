"""統合イベントバスシステム

Issue #914 Phase 3: イベント駆動アーキテクチャの中核
既存observer.pyを拡張・統合した高性能イベントシステム
"""

import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Union, cast

from ..utilities.logger import get_logger
from .dependency_injection import DIContainer, get_container
from .observer import (
    AsyncObserver,
    Event,
)
from .observer import EventBus as BaseEventBus
from .observer import (
    EventType,
    Observer,
)

logger = get_logger(__name__)


@dataclass
class EventMetrics:
    """イベントメトリクス"""

    event_count: int = 0
    total_processing_time: float = 0.0
    error_count: int = 0
    average_processing_time: float = 0.0


class ExtendedEventType(Enum):
    """拡張イベント種別"""

    # 既存EventTypeを継承
    PARSING_STARTED = "parsing_started"
    PARSING_COMPLETED = "parsing_completed"
    PARSING_ERROR = "parsing_error"
    RENDERING_STARTED = "rendering_started"
    RENDERING_COMPLETED = "rendering_completed"
    RENDERING_ERROR = "rendering_error"

    # 新規イベント
    PERFORMANCE_MEASUREMENT = "performance_measurement"
    PLUGIN_LOADED = "plugin_loaded"
    PLUGIN_UNLOADED = "plugin_unloaded"
    DEPENDENCY_RESOLVED = "dependency_resolved"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    ASYNC_TASK_STARTED = "async_task_started"
    ASYNC_TASK_COMPLETED = "async_task_completed"


# 型エイリアスでユニオン型を簡略化
UnifiedEventType = Union[EventType, ExtendedEventType]


def normalize_event_type(event_type: UnifiedEventType) -> str:
    """イベントタイプを文字列に正規化"""
    if isinstance(event_type, str):
        return event_type
    return event_type.value


class IntegratedEventBus:
    """統合イベントバス - 高性能・スケーラブル設計"""

    def __init__(self, container: Optional[DIContainer] = None) -> None:
        self.container = container or get_container()
        self._base_bus = BaseEventBus()
        self._metrics: Dict[str, EventMetrics] = {}
        self._performance_tracking = True
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._lock = threading.RLock()

    def subscribe(
        self, event_type: Union[EventType, ExtendedEventType], observer: Observer
    ) -> None:
        """同期オブザーバー登録"""
        # ExtendedEventTypeはそのまま使用（EventTypeに対応するイベントが存在するため）
        self._base_bus.subscribe(event_type, observer)

    def subscribe_async(
        self, event_type: Union[EventType, ExtendedEventType], observer: AsyncObserver
    ) -> None:
        """非同期オブザーバー登録"""
        # ExtendedEventTypeはそのまま使用（EventTypeに対応するイベントが存在するため）
        self._base_bus.subscribe_async(event_type, observer)

    def subscribe_with_di(
        self,
        event_type: Union[EventType, ExtendedEventType],
        observer_class: Type[Observer],
    ) -> None:
        """DI経由でのオブザーバー登録"""
        observer = self.container.resolve(observer_class)
        self.subscribe(event_type, observer)

    def publish(self, event: Event) -> None:
        """同期イベント発行 - パフォーマンス追跡付き"""
        start_time = datetime.now()
        try:
            self._base_bus.publish(event)
            self._update_metrics(str(event.event_type.value), start_time, success=True)
        except Exception as e:
            self._update_metrics(str(event.event_type.value), start_time, success=False)
            logger.error(f"イベント発行エラー: {e}")
            raise

    async def publish_async(self, event: Event) -> None:
        """非同期イベント発行"""
        start_time = datetime.now()
        try:
            await self._base_bus.publish_async(event)
            self._update_metrics(str(event.event_type.value), start_time, success=True)
        except Exception as e:
            self._update_metrics(str(event.event_type.value), start_time, success=False)
            logger.error(f"非同期イベント発行エラー: {e}")
            raise

    def publish_parallel(self, events: List[Event]) -> None:
        """並列イベント発行"""
        futures = []
        for event in events:
            future = self._executor.submit(self.publish, event)
            futures.append(future)

        # 全て完了まで待機
        for future in futures:
            future.result()

    def get_metrics(
        self, event_type: Optional[str] = None
    ) -> Union[EventMetrics, Dict[str, EventMetrics]]:
        """メトリクス取得"""
        with self._lock:
            if event_type:
                return self._metrics.get(event_type, EventMetrics())
            return self._metrics.copy()

    def _update_metrics(
        self, event_type: str, start_time: datetime, success: bool
    ) -> None:
        """メトリクス更新"""
        if not self._performance_tracking:
            return

        processing_time = (datetime.now() - start_time).total_seconds()

        with self._lock:
            if event_type not in self._metrics:
                self._metrics[event_type] = EventMetrics()

            metrics = self._metrics[event_type]
            metrics.event_count += 1
            metrics.total_processing_time += processing_time

            if not success:
                metrics.error_count += 1

            metrics.average_processing_time = (
                metrics.total_processing_time / metrics.event_count
            )


# グローバルイベントバスインスタンス
_global_event_bus = IntegratedEventBus()


def get_event_bus() -> IntegratedEventBus:
    """グローバルイベントバス取得"""
    return _global_event_bus


def publish_event(
    event_type: UnifiedEventType,
    source: str,
    data: Optional[Dict[str, Any]] = None,
) -> None:
    """便利なイベント発行関数"""
    # イベントタイプを正規化して使用
    normalized_type = normalize_event_type(event_type)
    event = Event(
        event_type=cast(EventType, normalized_type), source=source, data=data or {}
    )
    _global_event_bus.publish(event)


async def publish_event_async(
    event_type: UnifiedEventType,
    source: str,
    data: Optional[Dict[str, Any]] = None,
) -> None:
    """便利な非同期イベント発行関数"""
    # イベントタイプを正規化して使用
    normalized_type = normalize_event_type(event_type)
    event = Event(
        event_type=cast(EventType, normalized_type), source=source, data=data or {}
    )
    await _global_event_bus.publish_async(event)
