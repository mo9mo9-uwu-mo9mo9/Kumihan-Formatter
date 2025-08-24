"""パーサーイベント駆動システム

Issue #1170: パーサー間通信をイベント駆動で実現し疎結合化を促進
"""

import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Type, Union

from ..utilities.logger import get_logger
from .observer import Event, EventBus, EventType

logger = get_logger(__name__)


class ParserEventType(Enum):
    """パーサー専用イベント種別"""
    
    # 解析フロー
    PARSE_STARTED = "parse_started"
    PARSE_COMPLETED = "parse_completed" 
    PARSE_FAILED = "parse_failed"
    PARSE_PAUSED = "parse_paused"
    PARSE_RESUMED = "parse_resumed"
    
    # パーサー間協調
    PARSER_REQUEST_HELP = "parser_request_help"
    PARSER_PROVIDE_RESULT = "parser_provide_result"
    PARSER_DELEGATE_TASK = "parser_delegate_task"
    PARSER_NOTIFY_DEPENDENCY = "parser_notify_dependency"
    
    # 性能・監視
    PERFORMANCE_METRIC = "performance_metric"
    MEMORY_WARNING = "memory_warning"
    PROCESSING_BOTTLENECK = "processing_bottleneck"
    
    # エラーハンドリング
    RECOVERABLE_ERROR = "recoverable_error"
    CRITICAL_ERROR = "critical_error"
    ERROR_RECOVERED = "error_recovered"
    
    # デバッグ・ログ
    DEBUG_TRACE = "debug_trace"
    VALIDATION_RESULT = "validation_result"


@dataclass
class ParserEventData:
    """パーサーイベントデータ"""
    parser_name: str
    parser_type: str
    content_hash: Optional[str] = None
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    processing_time: Optional[float] = None
    memory_usage: Optional[int] = None
    error_details: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass  
class ParserEvent:
    """パーサー専用イベント"""
    event_type: ParserEventType
    data: ParserEventData
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
    source_parser: Optional[str] = None
    target_parser: Optional[str] = None
    priority: int = 1  # 1=低, 5=中, 10=高
    
    def to_generic_event(self) -> Event:
        """汎用Eventに変換"""
        return Event(
            event_type=EventType.CUSTOM,
            data={
                "parser_event_type": self.event_type.value,
                "parser_data": self.data.__dict__,
                "correlation_id": self.correlation_id,
                "source_parser": self.source_parser,
                "target_parser": self.target_parser,
                "priority": self.priority
            },
            timestamp=self.timestamp
        )


class ParserEventHandler(Protocol):
    """パーサーイベントハンドラープロトコル"""
    
    def handle_parser_event(self, event: ParserEvent) -> None:
        """パーサーイベント処理"""
        ...
    
    def get_handled_event_types(self) -> List[ParserEventType]:
        """処理対象イベント種別取得"""
        ...


class AsyncParserEventHandler(Protocol):
    """非同期パーサーイベントハンドラー"""
    
    async def handle_parser_event_async(self, event: ParserEvent) -> None:
        """非同期パーサーイベント処理"""
        ...
    
    def get_handled_event_types(self) -> List[ParserEventType]:
        """処理対象イベント種別取得"""
        ...


class ParserEventBus:
    """パーサー専用イベントバス"""
    
    def __init__(self, underlying_bus: Optional[EventBus] = None):
        self.underlying_bus = underlying_bus or EventBus()
        self._handlers: Dict[ParserEventType, List[ParserEventHandler]] = {}
        self._async_handlers: Dict[ParserEventType, List[AsyncParserEventHandler]] = {}
        self._event_history: List[ParserEvent] = []
        self._max_history = 5000
        self._performance_metrics: Dict[str, List[float]] = {}
        
    def subscribe(self, event_type: ParserEventType, handler: ParserEventHandler) -> None:
        """パーサーイベントハンドラー登録"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        
        logger.debug(f"Parser event handler subscribed: {event_type.value}")
        
    def subscribe_async(self, event_type: ParserEventType, handler: AsyncParserEventHandler) -> None:
        """非同期パーサーイベントハンドラー登録"""
        if event_type not in self._async_handlers:
            self._async_handlers[event_type] = []
        self._async_handlers[event_type].append(handler)
        
        logger.debug(f"Async parser event handler subscribed: {event_type.value}")
        
    def publish(self, event: ParserEvent) -> None:
        """パーサーイベント発行"""
        start_time = time.time()
        
        try:
            # イベント履歴保存
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)
                
            # 同期ハンドラー実行
            handlers = self._handlers.get(event.event_type, [])
            for handler in handlers:
                try:
                    handler.handle_parser_event(event)
                except Exception as e:
                    logger.error(f"Parser event handler failed: {e}")
                    
            # 汎用イベントバスにも通知
            generic_event = event.to_generic_event()
            self.underlying_bus.publish(generic_event)
            
            # パフォーマンス記録
            processing_time = time.time() - start_time
            event_key = f"{event.event_type.value}:{event.data.parser_name}"
            if event_key not in self._performance_metrics:
                self._performance_metrics[event_key] = []
            self._performance_metrics[event_key].append(processing_time)
            
            logger.debug(f"Parser event published: {event.event_type.value} "
                        f"from {event.data.parser_name} in {processing_time:.4f}s")
                        
        except Exception as e:
            logger.error(f"Parser event publication failed: {e}")
            
    async def publish_async(self, event: ParserEvent) -> None:
        """非同期パーサーイベント発行"""
        import asyncio
        
        start_time = time.time()
        
        try:
            # 同期処理も実行
            self.publish(event)
            
            # 非同期ハンドラー実行
            async_handlers = self._async_handlers.get(event.event_type, [])
            if async_handlers:
                tasks = []
                for handler in async_handlers:
                    task = asyncio.create_task(handler.handle_parser_event_async(event))
                    tasks.append(task)
                    
                await asyncio.gather(*tasks, return_exceptions=True)
                
            processing_time = time.time() - start_time
            logger.debug(f"Async parser event published: {event.event_type.value} "
                        f"in {processing_time:.4f}s")
                        
        except Exception as e:
            logger.error(f"Async parser event publication failed: {e}")
            
    def get_event_history(self, 
                         event_type: Optional[ParserEventType] = None,
                         parser_name: Optional[str] = None,
                         limit: Optional[int] = None) -> List[ParserEvent]:
        """イベント履歴取得"""
        events = self._event_history
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if parser_name:
            events = [e for e in events if e.data.parser_name == parser_name]
        if limit:
            events = events[-limit:]
            
        return events.copy()
        
    def get_performance_metrics(self) -> Dict[str, Dict[str, float]]:
        """パフォーマンス計測結果取得"""
        metrics = {}
        
        for event_key, times in self._performance_metrics.items():
            if times:
                metrics[event_key] = {
                    "count": len(times),
                    "avg_time": sum(times) / len(times),
                    "min_time": min(times),
                    "max_time": max(times),
                    "total_time": sum(times)
                }
                
        return metrics
        
    def clear_history(self) -> None:
        """履歴クリア"""
        self._event_history.clear()
        self._performance_metrics.clear()
        
    def get_system_status(self) -> Dict[str, Any]:
        """システム状態取得"""
        return {
            "registered_handlers": {
                event_type.value: len(handlers) 
                for event_type, handlers in self._handlers.items()
            },
            "async_handlers": {
                event_type.value: len(handlers) 
                for event_type, handlers in self._async_handlers.items()
            },
            "event_history_size": len(self._event_history),
            "performance_metrics_count": len(self._performance_metrics),
            "total_events_processed": sum(len(times) for times in self._performance_metrics.values())
        }


# パーサーイベント作成ヘルパー関数
def create_parse_started_event(parser_name: str, parser_type: str, 
                              content_hash: Optional[str] = None) -> ParserEvent:
    """解析開始イベント作成"""
    return ParserEvent(
        event_type=ParserEventType.PARSE_STARTED,
        data=ParserEventData(
            parser_name=parser_name,
            parser_type=parser_type,
            content_hash=content_hash
        )
    )


def create_parse_completed_event(parser_name: str, parser_type: str,
                                processing_time: float,
                                line_count: Optional[int] = None) -> ParserEvent:
    """解析完了イベント作成"""
    return ParserEvent(
        event_type=ParserEventType.PARSE_COMPLETED,
        data=ParserEventData(
            parser_name=parser_name,
            parser_type=parser_type,
            processing_time=processing_time,
            metadata={"line_count": line_count} if line_count else {}
        )
    )


def create_parser_error_event(parser_name: str, parser_type: str,
                             error: Exception, 
                             is_critical: bool = False) -> ParserEvent:
    """エラーイベント作成"""
    return ParserEvent(
        event_type=ParserEventType.CRITICAL_ERROR if is_critical else ParserEventType.RECOVERABLE_ERROR,
        data=ParserEventData(
            parser_name=parser_name,
            parser_type=parser_type,
            error_details={
                "error_type": type(error).__name__,
                "error_message": str(error),
                "is_critical": is_critical
            }
        ),
        priority=10 if is_critical else 5
    )


# グローバルパーサーイベントバス
_global_parser_event_bus: Optional[ParserEventBus] = None


def get_parser_event_bus() -> ParserEventBus:
    """グローバルパーサーイベントバス取得"""
    global _global_parser_event_bus
    if _global_parser_event_bus is None:
        _global_parser_event_bus = ParserEventBus()
    return _global_parser_event_bus