"""Pattern Integration System"""

from typing import Any, Dict, List, Optional, Type

from .command import CommandProcessor
from .decorator import DecoratorChain
from .observer import Event, EventBus, EventType
from .strategy import StrategyManager


class ArchitectureManager:
    """アーキテクチャパターン統合管理"""

    def __init__(self) -> None:
        self._event_bus = EventBus()
        self._strategy_manager = StrategyManager()
        self._command_processor = CommandProcessor()
        self._instances: Dict[str, Any] = {}

        # 基本インスタンス登録
        self._instances["event_bus"] = self._event_bus
        self._instances["strategy_manager"] = self._strategy_manager
        self._instances["command_processor"] = self._command_processor

    def configure_default_patterns(self) -> None:
        """デフォルトパターン設定"""
        # イベント監視設定
        try:
            from .observers import ParsingObserver, RenderingObserver

            self._event_bus.subscribe(EventType.PARSING_STARTED, ParsingObserver())
            self._event_bus.subscribe(EventType.RENDERING_STARTED, RenderingObserver())
        except ImportError:
            # observers.pyが未実装の場合はスキップ
            pass

        # 戦略登録
        try:
            from .strategies import HTMLRenderingStrategy, KumihanParsingStrategy

            self._strategy_manager.register_parsing_strategy(
                "kumihan", KumihanParsingStrategy(), is_default=True
            )
            self._strategy_manager.register_rendering_strategy(
                "html", HTMLRenderingStrategy(), is_default=True
            )
        except ImportError:
            # strategies.pyが未実装の場合はスキップ
            pass

    def create_enhanced_parser(self, base_parser: Any) -> Any:
        """機能拡張パーサー生成"""
        from .decorator import CachingParserDecorator, LoggingDecorator

        chain = DecoratorChain(base_parser)
        chain.add_decorator(lambda p: CachingParserDecorator(p, cache_size=256))
        chain.add_decorator(lambda p: LoggingDecorator(p, "parser"))

        return chain.build()

    def create_enhanced_renderer(self, base_renderer: Any) -> Any:
        """機能拡張レンダラー生成"""
        from .decorator import LoggingDecorator

        chain = DecoratorChain(base_renderer)
        chain.add_decorator(lambda r: LoggingDecorator(r, "renderer"))

        return chain.build()

    def get_event_bus(self) -> EventBus:
        """イベントバス取得"""
        return self._event_bus

    def get_strategy_manager(self) -> StrategyManager:
        """戦略マネージャー取得"""
        return self._strategy_manager

    def get_command_processor(self) -> CommandProcessor:
        """コマンドプロセッサー取得"""
        return self._command_processor

    def register_instance(self, name: str, instance: Any) -> None:
        """インスタンス登録"""
        self._instances[name] = instance

    def get_instance(self, name: str) -> Optional[Any]:
        """インスタンス取得"""
        return self._instances.get(name)

    def publish_event(
        self, event_type: EventType, source: str, data: Optional[Dict[str, Any]] = None
    ) -> None:
        """イベント発行（便利メソッド）"""
        event = Event(event_type=event_type, source=source, data=data or {})
        self._event_bus.publish(event)
