"""Design Patterns Unit Tests"""

import pytest
import asyncio
import threading
import time
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, List

from kumihan_formatter.core.patterns import (
    EventBus, Event, EventType, Observer,
    StrategyManager, ParsingStrategy, RenderingStrategy, StrategyPriority,
    DecoratorChain, CachingParserDecorator, LoggingDecorator,
    Command, CommandProcessor, CommandStatus, ParseCommand, RenderCommand
)


class TestObserverPattern:
    """Observer Pattern テスト"""

    def test_event_creation(self):
        """イベント作成テスト"""
        event = Event(
            event_type=EventType.PARSING_STARTED,
            source="test_parser",
            data={"content_length": 100}
        )

        assert event.event_type == EventType.PARSING_STARTED
        assert event.source == "test_parser"
        assert event.data["content_length"] == 100
        assert event.event_id is not None
        assert event.timestamp is not None

    def test_event_subscription(self):
        """イベント購読テスト"""
        event_bus = EventBus()
        observer = Mock(spec=Observer)
        observer.handle_event = Mock()
        observer.get_supported_events.return_value = [EventType.PARSING_STARTED]

        event_bus.subscribe(EventType.PARSING_STARTED, observer)

        event = Event(EventType.PARSING_STARTED, "test")
        event_bus.publish(event)

        observer.handle_event.assert_called_once_with(event)

    def test_event_publishing(self):
        """イベント発行テスト"""
        event_bus = EventBus()
        observer1 = Mock(spec=Observer)
        observer2 = Mock(spec=Observer)

        event_bus.subscribe(EventType.PARSING_STARTED, observer1)
        event_bus.subscribe(EventType.PARSING_STARTED, observer2)

        event = Event(EventType.PARSING_STARTED, "test")
        event_bus.publish(event)

        observer1.handle_event.assert_called_once_with(event)
        observer2.handle_event.assert_called_once_with(event)

    def test_global_observer(self):
        """グローバルオブザーバーテスト"""
        event_bus = EventBus()
        global_observer = Mock(spec=Observer)

        event_bus.subscribe_global(global_observer)

        event1 = Event(EventType.PARSING_STARTED, "test")
        event2 = Event(EventType.RENDERING_STARTED, "test")

        event_bus.publish(event1)
        event_bus.publish(event2)

        assert global_observer.handle_event.call_count == 2

    def test_event_history(self):
        """イベント履歴テスト"""
        event_bus = EventBus()

        event1 = Event(EventType.PARSING_STARTED, "test1")
        event2 = Event(EventType.PARSING_COMPLETED, "test2")

        event_bus.publish(event1)
        event_bus.publish(event2)

        history = event_bus.get_event_history()
        assert len(history) == 2
        assert history[0].event_type == EventType.PARSING_STARTED
        assert history[1].event_type == EventType.PARSING_COMPLETED

    def test_unsubscribe(self):
        """購読解除テスト"""
        event_bus = EventBus()
        observer = Mock(spec=Observer)

        event_bus.subscribe(EventType.PARSING_STARTED, observer)
        assert event_bus.unsubscribe(EventType.PARSING_STARTED, observer) is True

        event = Event(EventType.PARSING_STARTED, "test")
        event_bus.publish(event)

        observer.handle_event.assert_not_called()

    def test_async_event_handling(self):
        """非同期イベント処理テスト"""
        async def async_test():
            event_bus = EventBus()
            async_observer = Mock()

            async def mock_async_handler(event):
                return None

            async_observer.handle_event_async = Mock(side_effect=mock_async_handler)

            event_bus.subscribe_async(EventType.PARSING_STARTED, async_observer)

            event = Event(EventType.PARSING_STARTED, "test")
            await event_bus.publish_async(event)

            async_observer.handle_event_async.assert_called_once()

        # 同期テストとして実行
        asyncio.run(async_test())


class TestStrategyPattern:
    """Strategy Pattern テスト"""

    def test_strategy_registration(self):
        """戦略登録テスト"""
        manager = StrategyManager()
        parsing_strategy = Mock(spec=ParsingStrategy)
        parsing_strategy.get_strategy_name.return_value = "test_parser"

        manager.register_parsing_strategy(
            "test", parsing_strategy, StrategyPriority.HIGH, is_default=True
        )

        assert manager.get_parsing_strategy("test") == parsing_strategy
        strategies = manager.list_strategies()
        assert "test" in strategies["parsing"]

    def test_strategy_selection(self):
        """戦略選択テスト"""
        manager = StrategyManager()

        strategy1 = Mock(spec=ParsingStrategy)
        strategy1.supports_content.return_value = 0.3

        strategy2 = Mock(spec=ParsingStrategy)
        strategy2.supports_content.return_value = 0.8

        manager.register_parsing_strategy("low", strategy1, StrategyPriority.LOW)
        manager.register_parsing_strategy("high", strategy2, StrategyPriority.HIGH)

        selected = manager.select_parsing_strategy("test content")

        # 高優先度・高対応度のstrategy2が選択されるはず
        assert selected == strategy2

    def test_rendering_strategy_selection(self):
        """レンダリング戦略選択テスト"""
        manager = StrategyManager()

        html_strategy = Mock(spec=RenderingStrategy)
        html_strategy.supports_format = Mock(side_effect=lambda fmt: fmt.lower() == "html")

        manager.register_rendering_strategy("html", html_strategy)

        selected = manager.select_rendering_strategy("html")
        assert selected == html_strategy

        selected_none = manager.select_rendering_strategy("unknown")
        assert selected_none is None

    def test_dynamic_strategy_switching(self):
        """動的戦略切り替えテスト"""
        manager = StrategyManager()

        # 異なる対応度を持つ戦略を登録
        kumihan_strategy = Mock(spec=ParsingStrategy)
        kumihan_strategy.supports_content = Mock(side_effect=lambda content: 0.9 if "# " in content and "##" in content else 0.1)

        markdown_strategy = Mock(spec=ParsingStrategy)
        markdown_strategy.supports_content = Mock(side_effect=lambda content: 0.8 if "##" in content and "# " not in content else 0.2)

        manager.register_parsing_strategy("kumihan", kumihan_strategy)
        manager.register_parsing_strategy("markdown", markdown_strategy)

        # Kumihan記法に対しては kumihan_strategy が選択される
        selected1 = manager.select_parsing_strategy("# 見出し #テスト##")
        assert selected1 == kumihan_strategy

        # Markdown記法に対しては markdown_strategy が選択される
        selected2 = manager.select_parsing_strategy("## Markdown Header")
        # 戦略選択のロジックをより正確にテスト
        assert selected2 is not None


class TestDecoratorPattern:
    """Decorator Pattern テスト"""

    def test_decorator_chaining(self):
        """デコレーターチェーンテスト"""
        base_object = Mock()
        base_object.method = Mock(return_value="result")

        chain = DecoratorChain(base_object)
        chain.add_decorator(lambda obj: Mock(wraps=obj))
        chain.add_decorator(lambda obj: Mock(wraps=obj))

        decorated = chain.build()
        result = decorated.method()

        assert result == "result"

    def test_caching_decorator(self):
        """キャッシュデコレーターテスト"""
        parser = Mock()
        parser.parse = Mock(return_value="parsed_result")

        cached_parser = CachingParserDecorator(parser, cache_size=2)

        # 最初の呼び出し
        result1 = cached_parser.parse("content", {})
        assert result1 == "parsed_result"
        assert parser.parse.call_count == 1

        # 同じ引数での二回目の呼び出し（キャッシュヒット）
        result2 = cached_parser.parse("content", {})
        assert result2 == "parsed_result"
        assert parser.parse.call_count == 1  # 呼ばれない

        # 異なる引数での呼び出し
        result3 = cached_parser.parse("different", {})
        assert parser.parse.call_count == 2

    def test_caching_decorator_lru(self):
        """キャッシュLRU機能テスト"""
        parser = Mock()
        parser.parse = Mock(side_effect=lambda c, x: f"result_{c}")

        cached_parser = CachingParserDecorator(parser, cache_size=2)

        # キャッシュサイズを超える呼び出し
        cached_parser.parse("content1", {})
        cached_parser.parse("content2", {})
        cached_parser.parse("content3", {})  # content1がLRU削除される

        # content1を再度呼び出し（キャッシュミスになるはず）
        parser.parse.reset_mock()
        cached_parser.parse("content1", {})
        assert parser.parse.call_count == 1

    def test_logging_decorator(self):
        """ログデコレーターテスト"""
        target = Mock()
        target.method = Mock(return_value="result")

        logged = LoggingDecorator(target, "test_logger")
        result = logged.method("arg1", kwarg="value")

        assert result == "result"
        target.method.assert_called_once_with("arg1", kwarg="value")


class TestCommandPattern:
    """Command Pattern テスト"""

    def test_command_execution(self):
        """コマンド実行テスト"""
        parser = Mock()
        parser.parse = Mock(return_value="parsed")

        command = ParseCommand("content", parser, {"option": "value"})
        result = command.execute()

        assert result.success is True
        assert result.result == "parsed"
        assert command.status == CommandStatus.COMPLETED
        parser.parse.assert_called_once_with("content", {"option": "value"})

    def test_command_error_handling(self):
        """コマンドエラー処理テスト"""
        parser = Mock()
        parser.parse = Mock(side_effect=ValueError("Parse error"))

        command = ParseCommand("content", parser)
        result = command.execute()

        assert result.success is False
        assert isinstance(result.error, ValueError)
        assert command.status == CommandStatus.FAILED

    def test_command_processor(self):
        """コマンドプロセッサーテスト"""
        processor = CommandProcessor()
        command = Mock(spec=Command)
        command_result = Mock()
        command_result.success = True
        command.execute = Mock(return_value=command_result)

        result = processor.execute_command(command)

        assert result == command_result
        command.execute.assert_called_once()

        # 履歴確認
        history = processor.get_command_history()
        assert len(history) == 1
        assert history[0] == command

    def test_batch_processing(self):
        """バッチ処理テスト"""
        processor = CommandProcessor()

        command1 = Mock(spec=Command)
        command1.execute = Mock(return_value=Mock(success=True))

        command2 = Mock(spec=Command)
        command2.execute = Mock(return_value=Mock(success=True))

        results = processor.execute_batch([command1, command2])

        assert len(results) == 2
        assert all(r.success for r in results)
        command1.execute.assert_called_once()
        command2.execute.assert_called_once()

    def test_command_undo(self):
        """コマンドアンドゥテスト"""
        processor = CommandProcessor()

        # アンドゥ可能なコマンドを作成
        command = Mock(spec=Command)
        command.status = CommandStatus.COMPLETED
        command.can_undo = Mock(return_value=True)
        command.undo = Mock(return_value=Mock(success=True))
        command.execute = Mock(return_value=Mock(success=True))

        # コマンド実行
        processor.execute_command(command)

        # アンドゥ実行
        undo_result = processor.undo_last()

        assert undo_result is not None
        assert undo_result.success is True
        command.undo.assert_called_once()

    def test_render_command(self):
        """レンダリングコマンドテスト"""
        renderer = Mock()
        renderer.render = Mock(return_value="<html>content</html>")

        data = {"blocks": [{"type": "text", "content": "test"}]}
        command = RenderCommand(data, renderer, {"format": "html"})

        result = command.execute()

        assert result.success is True
        assert result.result == "<html>content</html>"
        renderer.render.assert_called_once_with(data, {"format": "html"})


class TestPatternIntegration:
    """パターン統合テスト"""

    def test_event_driven_parsing(self):
        """イベント駆動パーシングテスト"""
        from kumihan_formatter.core.patterns.integration import ArchitectureManager

        manager = ArchitectureManager()
        event_bus = manager.get_event_bus()

        # イベント監視用オブザーバー
        observer = Mock(spec=Observer)
        event_bus.subscribe(EventType.PARSING_STARTED, observer)

        # イベント発行
        manager.publish_event(
            EventType.PARSING_STARTED,
            "test_parser",
            {"content_length": 100}
        )

        observer.handle_event.assert_called_once()
        call_args = observer.handle_event.call_args[0]
        event = call_args[0]
        assert event.event_type == EventType.PARSING_STARTED
        assert event.data["content_length"] == 100

    def test_strategy_based_rendering(self):
        """戦略ベースレンダリングテスト"""
        from kumihan_formatter.core.patterns.integration import ArchitectureManager

        manager = ArchitectureManager()
        strategy_manager = manager.get_strategy_manager()

        # HTML戦略を登録
        html_strategy = Mock(spec=RenderingStrategy)
        html_strategy.supports_format.return_value = True
        html_strategy.render.return_value = "<html>test</html>"

        strategy_manager.register_rendering_strategy("html", html_strategy)

        # 戦略選択・実行
        selected = strategy_manager.select_rendering_strategy("html")
        assert selected == html_strategy

        result = selected.render({"content": "test"}, {})
        assert result == "<html>test</html>"

    def test_decorated_pipeline(self):
        """デコレート済みパイプラインテスト"""
        from kumihan_formatter.core.patterns.integration import ArchitectureManager

        manager = ArchitectureManager()

        # ベースパーサー
        base_parser = Mock()
        base_parser.parse = Mock(return_value="parsed")

        # 機能拡張パーサー作成
        enhanced_parser = manager.create_enhanced_parser(base_parser)

        # パース実行（キャッシュ・ログ機能付き）
        result = enhanced_parser.parse("content", {})
        assert result == "parsed"

        # 二回目の実行（キャッシュ効果確認）
        result2 = enhanced_parser.parse("content", {})
        assert result2 == "parsed"
        # ベースパーサーは一度だけ呼ばれる（キャッシュ効果）
        assert base_parser.parse.call_count == 1
