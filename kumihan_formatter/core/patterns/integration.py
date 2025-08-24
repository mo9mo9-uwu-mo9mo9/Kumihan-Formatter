"""Pattern Integration System"""

from typing import Any, Dict, Optional

from .command import CommandProcessor
from .decorator import DecoratorChain
from .observer import Event, EventBus, EventType
from .strategy import StrategyManager


class ArchitectureManager:
    """アーキテクチャパターン統合管理"""

    def __init__(self) -> None:
        # DI コンテナー追加
        from .dependency_injection import DIContainer
        from .factories import ParserFactory, RendererFactory

        self._container = DIContainer()
        self._event_bus = EventBus(self._container)
        self._strategy_manager = StrategyManager(self._container)
        self._command_processor = CommandProcessor()
        self._parser_factory = ParserFactory(self._container)
        self._renderer_factory = RendererFactory(self._container)
        self._instances: Dict[str, Any] = {}

        # 基本インスタンス登録
        self._instances["container"] = self._container
        self._instances["event_bus"] = self._event_bus
        self._instances["strategy_manager"] = self._strategy_manager
        self._instances["command_processor"] = self._command_processor
        self._instances["parser_factory"] = self._parser_factory
        self._instances["renderer_factory"] = self._renderer_factory

        # DI コンテナーにコアサービス登録
        self._register_core_services()

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

    def _register_core_services(self) -> None:
        """コアサービスのDI登録"""
        try:
            from .dependency_injection import ServiceLifetime

            # ファクトリーサービス登録
            self._container.register_singleton(
                type(self._parser_factory), self._parser_factory
            )
            self._container.register_singleton(
                type(self._renderer_factory), self._renderer_factory
            )
            self._container.register_singleton(
                type(self._strategy_manager), self._strategy_manager
            )
            self._container.register_singleton(type(self._event_bus), self._event_bus)

        except Exception as e:
            # エラーログ記録
            pass

    def get_container(self) -> "DIContainer":
        """DIコンテナー取得"""
        return self._container

    def get_parser_factory(self) -> "ParserFactory":
        """パーサーファクトリー取得"""
        return self._parser_factory

    def get_renderer_factory(self) -> "RendererFactory":
        """レンダラーファクトリー取得"""
        return self._renderer_factory

    def create_parser(self, parser_type: str, **kwargs) -> Any:
        """パーサー作成（統合インターフェース）"""
        return self._parser_factory.create(parser_type, **kwargs)

    def create_renderer(self, renderer_type: str, **kwargs) -> Any:
        """レンダラー作成（統合インターフェース）"""
        return self._renderer_factory.create(renderer_type, **kwargs)

    def initialize_system(self) -> None:
        """システム初期化"""
        try:
            # DI コンテナー初期化
            self._container.initialize()

            # デフォルトパターン設定
            self.configure_default_patterns()

            # システム開始イベント発行
            self.publish_event(
                EventType.SYSTEM_START, "ArchitectureManager", {"status": "initialized"}
            )

        except Exception as e:
            # エラーイベント発行
            self.publish_event(
                EventType.ERROR, "ArchitectureManager", {"error": str(e)}
            )
            raise

    def validate_system(self) -> Dict[str, Any]:
        """システム全体の検証"""
        validation_result = {"success": True, "issues": [], "components": {}}

        try:
            # DI Container検証
            di_issues = self._container.validate_dependencies()
            validation_result["components"]["di_container"] = {
                "issues": di_issues,
                "info": self._container.get_dependency_info(),
            }

            # Strategy Manager検証
            strategy_issues = self._strategy_manager.validate_strategies()
            validation_result["components"]["strategy_manager"] = {
                "issues": strategy_issues,
                "strategies": self._strategy_manager.list_strategies(),
            }

            # Event Bus情報
            validation_result["components"]["event_bus"] = {
                "info": self._event_bus.get_observer_info()
            }

            # 全体の問題をまとめる
            all_issues = di_issues + strategy_issues
            validation_result["issues"] = all_issues
            validation_result["success"] = len(all_issues) == 0

        except Exception as e:
            validation_result["success"] = False
            validation_result["issues"].append(f"Validation error: {e}")

        return validation_result
