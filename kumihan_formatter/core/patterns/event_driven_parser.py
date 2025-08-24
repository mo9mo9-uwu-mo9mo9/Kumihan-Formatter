"""イベント駆動パーサーミックスイン

Issue #1170: パーサー間の疎結合化とイベント駆動通信の実現
"""

import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, Union

from ..utilities.logger import get_logger
from .parser_events import (
    ParserEvent,
    ParserEventBus,
    ParserEventData,
    ParserEventHandler,
    ParserEventType,
    create_parse_started_event,
    create_parse_completed_event,
    create_parser_error_event,
    get_parser_event_bus,
)

logger = get_logger(__name__)


class EventDrivenParserMixin:
    """イベント駆動パーサーミックスイン

    既存のパーサーに混合してイベント駆動機能を追加
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._parser_event_bus = get_parser_event_bus()
        self._parser_name = self.__class__.__name__
        self._parser_type = self._get_parser_type()
        self._performance_tracking = True
        self._event_publishing_enabled = True

    def _get_parser_type(self) -> str:
        """パーサータイプの自動推定"""
        class_name = self.__class__.__name__.lower()
        if "keyword" in class_name:
            return "keyword"
        elif "block" in class_name:
            return "block"
        elif "list" in class_name:
            return "list"
        elif "content" in class_name:
            return "content"
        elif "markdown" in class_name:
            return "markdown"
        else:
            return "generic"

    def _publish_event(self, event: ParserEvent) -> None:
        """イベント発行（内部用）"""
        if self._event_publishing_enabled:
            try:
                self._parser_event_bus.publish(event)
            except Exception as e:
                logger.error(f"Failed to publish parser event: {e}")

    def _create_event_data(self, **kwargs) -> ParserEventData:
        """イベントデータ作成ヘルパー"""
        return ParserEventData(
            parser_name=self._parser_name, parser_type=self._parser_type, **kwargs
        )

    def notify_parse_started(self, content: Union[str, List[str]], **metadata) -> None:
        """解析開始通知"""
        content_hash = None
        if isinstance(content, str):
            content_hash = hash(content[:100])  # 最初の100文字のハッシュ
        elif isinstance(content, list):
            content_hash = hash(str(content[:5]))  # 最初の5行のハッシュ

        event = ParserEvent(
            event_type=ParserEventType.PARSE_STARTED,
            data=self._create_event_data(
                content_hash=str(content_hash) if content_hash else None,
                metadata=metadata,
            ),
        )
        self._publish_event(event)

    def notify_parse_completed(
        self, processing_time: float, result_info: Dict[str, Any] = None
    ) -> None:
        """解析完了通知"""
        event = ParserEvent(
            event_type=ParserEventType.PARSE_COMPLETED,
            data=self._create_event_data(
                processing_time=processing_time, metadata=result_info or {}
            ),
        )
        self._publish_event(event)

    def notify_parse_error(
        self, error: Exception, is_critical: bool = False, **context
    ) -> None:
        """解析エラー通知"""
        event = ParserEvent(
            event_type=(
                ParserEventType.CRITICAL_ERROR
                if is_critical
                else ParserEventType.RECOVERABLE_ERROR
            ),
            data=self._create_event_data(
                error_details={
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                    "is_critical": is_critical,
                    "context": context,
                }
            ),
            priority=10 if is_critical else 5,
        )
        self._publish_event(event)

    def request_parser_help(
        self, target_parser: str, task_details: Dict[str, Any]
    ) -> None:
        """他のパーサーに協力要請"""
        event = ParserEvent(
            event_type=ParserEventType.PARSER_REQUEST_HELP,
            data=self._create_event_data(metadata=task_details),
            source_parser=self._parser_name,
            target_parser=target_parser,
        )
        self._publish_event(event)

    def provide_parsing_result(
        self, target_parser: str, result_data: Dict[str, Any]
    ) -> None:
        """解析結果の提供"""
        event = ParserEvent(
            event_type=ParserEventType.PARSER_PROVIDE_RESULT,
            data=self._create_event_data(metadata=result_data),
            source_parser=self._parser_name,
            target_parser=target_parser,
        )
        self._publish_event(event)

    def delegate_parsing_task(
        self,
        target_parser: str,
        task_content: str,
        task_metadata: Dict[str, Any] = None,
    ) -> None:
        """解析タスクの委譲"""
        event = ParserEvent(
            event_type=ParserEventType.PARSER_DELEGATE_TASK,
            data=self._create_event_data(
                metadata={
                    "delegated_content": task_content,
                    "task_metadata": task_metadata or {},
                }
            ),
            source_parser=self._parser_name,
            target_parser=target_parser,
        )
        self._publish_event(event)

    def notify_performance_metric(
        self, metric_name: str, metric_value: float, unit: str = "ms"
    ) -> None:
        """パフォーマンス指標通知"""
        event = ParserEvent(
            event_type=ParserEventType.PERFORMANCE_METRIC,
            data=self._create_event_data(
                metadata={
                    "metric_name": metric_name,
                    "metric_value": metric_value,
                    "unit": unit,
                }
            ),
        )
        self._publish_event(event)

    def enable_event_publishing(self) -> None:
        """イベント発行を有効化"""
        self._event_publishing_enabled = True

    def disable_event_publishing(self) -> None:
        """イベント発行を無効化"""
        self._event_publishing_enabled = False


class EventDrivenParser(EventDrivenParserMixin, ABC):
    """イベント駆動パーサー基底クラス"""

    def __init__(self):
        super().__init__()

    @abstractmethod
    def parse(self, content: Union[str, List[str]], **kwargs) -> Any:
        """パース処理（サブクラスで実装）"""
        pass

    def parse_with_events(self, content: Union[str, List[str]], **kwargs) -> Any:
        """イベント駆動パース処理"""
        start_time = time.time()

        try:
            # 解析開始通知
            self.notify_parse_started(content, **kwargs)

            # 実際のパース処理
            result = self.parse(content, **kwargs)

            # 解析完了通知
            processing_time = time.time() - start_time
            self.notify_parse_completed(
                processing_time, {"result_type": type(result).__name__, "success": True}
            )

            return result

        except Exception as e:
            # エラー通知
            processing_time = time.time() - start_time
            is_critical = isinstance(e, (MemoryError, SystemError))

            self.notify_parse_error(
                e,
                is_critical,
                processing_time=processing_time,
                content_preview=(
                    str(content)[:100] if isinstance(content, str) else "list"
                ),
            )
            raise


class ParserCollaborationManager:
    """パーサー協調管理システム"""

    def __init__(self, event_bus: Optional[ParserEventBus] = None):
        self.event_bus = event_bus or get_parser_event_bus()
        self._registered_parsers: Dict[str, Any] = {}
        self._collaboration_rules: Dict[str, List[str]] = {}

    def register_parser(self, parser_name: str, parser_instance: Any) -> None:
        """パーサー登録"""
        self._registered_parsers[parser_name] = parser_instance
        logger.debug(f"Parser registered for collaboration: {parser_name}")

    def set_collaboration_rule(
        self, source_parser: str, target_parsers: List[str]
    ) -> None:
        """協調ルール設定"""
        self._collaboration_rules[source_parser] = target_parsers
        logger.debug(f"Collaboration rule set: {source_parser} -> {target_parsers}")

    def setup_event_handlers(self) -> None:
        """イベントハンドラー設定"""
        # 協力要請の自動処理
        self.event_bus.subscribe(
            ParserEventType.PARSER_REQUEST_HELP, ParserHelpRequestHandler(self)
        )

        # タスク委譲の自動処理
        self.event_bus.subscribe(
            ParserEventType.PARSER_DELEGATE_TASK, ParserTaskDelegationHandler(self)
        )

    def get_collaboration_partners(self, parser_name: str) -> List[str]:
        """協調パートナー取得"""
        return self._collaboration_rules.get(parser_name, [])


class ParserHelpRequestHandler:
    """パーサー協力要請ハンドラー"""

    def __init__(self, collaboration_manager: ParserCollaborationManager):
        self.collaboration_manager = collaboration_manager

    def handle_parser_event(self, event: ParserEvent) -> None:
        """協力要請イベント処理"""
        try:
            source = event.source_parser
            target = event.target_parser
            task_details = event.data.metadata

            logger.info(f"Help request from {source} to {target}: {task_details}")

            # 実際の協力処理はここで実装
            # 例: 特定のパーサーに処理を委譲

        except Exception as e:
            logger.error(f"Failed to handle help request: {e}")

    def get_handled_event_types(self) -> List[ParserEventType]:
        return [ParserEventType.PARSER_REQUEST_HELP]


class ParserTaskDelegationHandler:
    """パーサータスク委譲ハンドラー"""

    def __init__(self, collaboration_manager: ParserCollaborationManager):
        self.collaboration_manager = collaboration_manager

    def handle_parser_event(self, event: ParserEvent) -> None:
        """タスク委譲イベント処理"""
        try:
            source = event.source_parser
            target = event.target_parser
            task_content = event.data.metadata.get("delegated_content")

            logger.info(f"Task delegation from {source} to {target}")

            # 実際のタスク委譲処理

        except Exception as e:
            logger.error(f"Failed to handle task delegation: {e}")

    def get_handled_event_types(self) -> List[ParserEventType]:
        return [ParserEventType.PARSER_DELEGATE_TASK]
