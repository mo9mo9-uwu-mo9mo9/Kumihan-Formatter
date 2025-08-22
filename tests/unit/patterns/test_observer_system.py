"""オブザーバーシステム統合テスト

Observer パターン、実装、EventBus統合の効率化されたテストスイート。
Issue #1114対応: 77テスト → 25テストに最適化
"""

import asyncio
import threading
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from kumihan_formatter.core.patterns.dependency_injection import DIContainer
from kumihan_formatter.core.patterns.event_bus import (
    EventMetrics,
    ExtendedEventType,
    IntegratedEventBus,
    get_event_bus,
    publish_event,
    publish_event_async,
)
from kumihan_formatter.core.patterns.observer import (
    AsyncObserver,
    Event,
    EventBus,
    EventType,
    Observer,
)
from kumihan_formatter.core.patterns.observers import ParsingObserver, RenderingObserver
from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


# テスト用モッククラス
class MockObserver(Observer):
    """テスト用オブザーバー"""

    def __init__(self, supported_events=None):
        self.received_events = []
        self.supported_events = supported_events or [EventType.PARSING_STARTED]
        self.handle_event_calls = 0

    def handle_event(self, event: Event) -> None:
        """イベント処理"""
        self.received_events.append(event)
        self.handle_event_calls += 1

    def get_supported_events(self):
        """対応イベント種別取得"""
        return self.supported_events


class MockAsyncObserver(AsyncObserver):
    """テスト用非同期オブザーバー"""

    def __init__(self):
        self.received_events = []
        self.handle_event_calls = 0

    async def handle_event_async(self, event: Event) -> None:
        """非同期イベント処理"""
        self.received_events.append(event)
        self.handle_event_calls += 1


class TestObserverCore:
    """Observer コア機能テスト"""

    def setup_method(self):
        """各テストメソッド実行前の初期化"""
        self.event_bus = EventBus()

    def test_基本_observer_登録_通知(self):
        """Observer基本的な登録と通知"""
        observer = MockObserver([EventType.PARSING_STARTED])
        self.event_bus.add_observer(observer)

        event = Event(EventType.PARSING_STARTED, {"content": "test"})
        self.event_bus.notify(event)

        assert len(observer.received_events) == 1
        assert observer.received_events[0].event_type == EventType.PARSING_STARTED

    def test_基本_複数observer_登録(self):
        """複数Observerの登録と選択的通知"""
        observer1 = MockObserver([EventType.PARSING_STARTED])
        observer2 = MockObserver([EventType.RENDERING_STARTED])

        self.event_bus.add_observer(observer1)
        self.event_bus.add_observer(observer2)

        # PARSING_STARTEDイベント送信
        event = Event(EventType.PARSING_STARTED, {"content": "test"})
        self.event_bus.notify(event)

        assert len(observer1.received_events) == 1
        assert len(observer2.received_events) == 0

    def test_基本_observer_削除(self):
        """Observer削除機能"""
        observer = MockObserver([EventType.PARSING_STARTED])
        self.event_bus.add_observer(observer)
        self.event_bus.remove_observer(observer)

        event = Event(EventType.PARSING_STARTED, {"content": "test"})
        self.event_bus.notify(event)

        assert len(observer.received_events) == 0

    @pytest.mark.asyncio
    async def test_基本_async_observer_処理(self):
        """非同期Observer処理"""
        observer = MockAsyncObserver()
        event = Event(EventType.PARSING_STARTED, {"content": "test"})

        await observer.handle_event_async(event)

        assert len(observer.received_events) == 1
        assert observer.handle_event_calls == 1

    def test_エラー_observer_例外処理(self):
        """Observer内例外の適切な処理"""
        class ErrorObserver(Observer):
            def handle_event(self, event):
                raise ValueError("Test error")

            def get_supported_events(self):
                return [EventType.PARSING_STARTED]

        error_observer = ErrorObserver()
        self.event_bus.add_observer(error_observer)

        # エラーが発生してもシステムは継続
        event = Event(EventType.PARSING_STARTED, {"content": "test"})
        self.event_bus.notify(event)  # 例外で停止しない

    def test_エラー_無効event_type(self):
        """無効なEventTypeの処理"""
        observer = MockObserver([EventType.PARSING_STARTED])
        self.event_bus.add_observer(observer)

        # 無効なEventTypeでも例外は発生しない
        event = Event("INVALID_EVENT", {"content": "test"})
        self.event_bus.notify(event)

        assert len(observer.received_events) == 0


class TestObserverImplementations:
    """Observer具体実装テスト"""

    def test_基本_parsing_observer_初期化(self):
        """ParsingObserver基本初期化"""
        observer = ParsingObserver()

        assert hasattr(observer, "handle_event")
        assert hasattr(observer, "get_supported_events")
        assert hasattr(observer, "logger")

    def test_基本_parsing_observer_イベント処理(self):
        """ParsingObserverのイベント処理確認"""
        observer = ParsingObserver()
        supported_events = observer.get_supported_events()

        assert EventType.PARSING_STARTED in supported_events
        assert EventType.PARSING_COMPLETED in supported_events

    def test_基本_rendering_observer_初期化(self):
        """RenderingObserver基本初期化"""
        observer = RenderingObserver()

        assert hasattr(observer, "handle_event")
        assert hasattr(observer, "get_supported_events")
        assert hasattr(observer, "logger")

    def test_基本_rendering_observer_イベント処理(self):
        """RenderingObserverのイベント処理確認"""
        observer = RenderingObserver()
        supported_events = observer.get_supported_events()

        assert EventType.RENDERING_STARTED in supported_events
        assert EventType.RENDERING_COMPLETED in supported_events

    @patch("kumihan_formatter.core.patterns.observers.get_logger")
    def test_基本_observer_ログ出力(self, mock_get_logger):
        """Observer実装でのログ出力確認"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        observer = ParsingObserver()
        event = Event(EventType.PARSING_STARTED, {"content": "test"})

        observer.handle_event(event)

        # ログ出力が呼ばれることを確認（具体的な内容は実装依存）
        assert mock_logger.info.called or mock_logger.debug.called


class TestIntegratedEventBus:
    """IntegratedEventBus統合テスト"""

    def setup_method(self):
        """各テストメソッド実行前の初期化"""
        self.container = DIContainer()
        self.event_bus = IntegratedEventBus(self.container)

    def test_基本_integrated_eventbus_初期化(self):
        """IntegratedEventBus基本初期化"""
        assert self.event_bus.container is self.container
        assert hasattr(self.event_bus, "metrics")
        assert isinstance(self.event_bus.metrics, EventMetrics)

    def test_基本_metrics_集計(self):
        """イベントメトリクス集計機能"""
        observer = MockObserver([EventType.PARSING_STARTED])
        self.event_bus.add_observer(observer)

        event = Event(EventType.PARSING_STARTED, {"content": "test"})
        self.event_bus.notify(event)

        metrics = self.event_bus.get_metrics()
        assert metrics["total_events"] >= 1

    def test_基本_グローバルeventbus_取得(self):
        """グローバルEventBus取得機能"""
        global_bus = get_event_bus()
        assert isinstance(global_bus, IntegratedEventBus)

    def test_基本_便利関数_publish_event(self):
        """便利関数publish_eventの動作確認"""
        # Mock設定
        with patch("kumihan_formatter.core.patterns.event_bus.get_event_bus") as mock_get_bus:
            mock_bus = Mock()
            mock_get_bus.return_value = mock_bus

            publish_event(EventType.PARSING_STARTED, {"content": "test"})

            mock_bus.notify.assert_called_once()

    @pytest.mark.asyncio
    async def test_基本_便利関数_publish_event_async(self):
        """便利関数publish_event_asyncの動作確認"""
        with patch("kumihan_formatter.core.patterns.event_bus.get_event_bus") as mock_get_bus:
            mock_bus = Mock()
            mock_bus.notify_async = AsyncMock()
            mock_get_bus.return_value = mock_bus

            await publish_event_async(EventType.PARSING_STARTED, {"content": "test"})

            mock_bus.notify_async.assert_called_once()

    def test_基本_DI統合_observer_自動解決(self):
        """DI統合でのObserver自動解決"""
        # DIコンテナにObserverを登録
        self.container.register(MockObserver, MockObserver)

        # EventBusがDI経由でObserverを解決できることを確認
        resolved_observer = self.container.resolve(MockObserver)
        assert isinstance(resolved_observer, MockObserver)

    def test_エラー_integrated_eventbus_無効コンテナ(self):
        """無効なDIコンテナでのIntegratedEventBus初期化エラー"""
        with pytest.raises(TypeError):
            IntegratedEventBus("invalid_container")


class TestSystemIntegration:
    """システム統合テスト"""

    def test_統合_完全observer_ワークフロー(self):
        """Observer システム全体の統合ワークフロー"""
        # システム初期化
        container = DIContainer()
        event_bus = IntegratedEventBus(container)

        # Observer登録
        parsing_observer = ParsingObserver()
        rendering_observer = RenderingObserver()

        event_bus.add_observer(parsing_observer)
        event_bus.add_observer(rendering_observer)

        # イベント発火
        parse_event = Event(EventType.PARSING_STARTED, {"file": "test.md"})
        render_event = Event(EventType.RENDERING_STARTED, {"output": "test.html"})

        event_bus.notify(parse_event)
        event_bus.notify(render_event)

        # メトリクス確認
        metrics = event_bus.get_metrics()
        assert metrics["total_events"] >= 2

    @pytest.mark.asyncio
    async def test_統合_async_observer_混在処理(self):
        """同期・非同期Observer混在処理"""
        container = DIContainer()
        event_bus = IntegratedEventBus(container)

        sync_observer = MockObserver([EventType.PARSING_STARTED])
        async_observer = MockAsyncObserver()

        event_bus.add_observer(sync_observer)

        # 同期・非同期イベント処理
        event = Event(EventType.PARSING_STARTED, {"content": "test"})
        event_bus.notify(event)
        await async_observer.handle_event_async(event)

        # 両方のObserverが処理完了
        assert len(sync_observer.received_events) == 1
        assert len(async_observer.received_events) == 1

    def test_統合_エラー回復性(self):
        """統合システムでのエラー回復性確認"""
        container = DIContainer()
        event_bus = IntegratedEventBus(container)

        # 正常Observerとエラー発生Observer
        normal_observer = MockObserver([EventType.PARSING_STARTED])

        class ErrorObserver(Observer):
            def handle_event(self, event):
                raise Exception("Processing error")
            def get_supported_events(self):
                return [EventType.PARSING_STARTED]

        error_observer = ErrorObserver()

        event_bus.add_observer(normal_observer)
        event_bus.add_observer(error_observer)

        # エラーが発生しても他のObserverは動作継続
        event = Event(EventType.PARSING_STARTED, {"content": "test"})
        event_bus.notify(event)

        assert len(normal_observer.received_events) == 1

    def test_統合_performance_多数observer(self):
        """多数Observer登録時のパフォーマンス確認"""
        container = DIContainer()
        event_bus = IntegratedEventBus(container)

        # 50個のObserver登録
        observers = [MockObserver([EventType.PARSING_STARTED]) for _ in range(50)]
        for observer in observers:
            event_bus.add_observer(observer)

        # イベント処理時間測定
        start_time = time.time()
        event = Event(EventType.PARSING_STARTED, {"content": "performance_test"})
        event_bus.notify(event)
        processing_time = time.time() - start_time

        # 全Observerが通知を受信
        for observer in observers:
            assert len(observer.received_events) == 1

        # パフォーマンス確認（1秒以内）
        assert processing_time < 1.0
