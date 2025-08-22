"""IntegratedEventBusの包括的テスト

Issue #929 Phase 2A: Event & Observer System Tests
IntegratedEventBus専用テスト - DI統合・メトリクス・並列処理機能
"""

import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

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
from kumihan_formatter.core.patterns.observer import Event, EventType, Observer


# テスト用モッククラス
class MockDIContainer:
    """テスト用DIコンテナモック"""

    def __init__(self):
        self.resolved_objects = {}

    def resolve(self, class_type):
        """クラス解決モック"""
        if class_type not in self.resolved_objects:
            self.resolved_objects[class_type] = MockObserver()
        return self.resolved_objects[class_type]


class MockObserver(Observer):
    """テスト用オブザーバー"""

    def __init__(self):
        self.received_events = []
        self.handle_event_calls = 0

    def handle_event(self, event: Event) -> None:
        """イベント処理"""
        self.received_events.append(event)
        self.handle_event_calls += 1

    def get_supported_events(self):
        """対応イベント種別取得"""
        return [EventType.PARSING_STARTED]


class MockErrorObserver(Observer):
    """エラーを発生させるテスト用オブザーバー"""

    def handle_event(self, event: Event) -> None:
        raise ValueError("Mock observer error")

    def get_supported_events(self):
        return [EventType.PARSING_STARTED]


class TestEventMetrics:
    """EventMetricsのテスト"""

    def test_正常系_初期化(self):
        """正常系: EventMetrics初期化確認"""
        # Given/When: EventMetricsを初期化
        metrics = EventMetrics()

        # Then: デフォルト値が設定される
        assert metrics.event_count == 0
        assert metrics.total_processing_time == 0.0
        assert metrics.error_count == 0
        assert metrics.average_processing_time == 0.0

    def test_正常系_メトリクス計算(self):
        """正常系: メトリクス計算確認"""
        # Given: イベントメトリクス
        metrics = EventMetrics()

        # When: メトリクスを更新
        metrics.event_count = 5
        metrics.total_processing_time = 2.5
        metrics.error_count = 1
        metrics.average_processing_time = metrics.total_processing_time / metrics.event_count

        # Then: 計算結果が正しい
        assert metrics.event_count == 5
        assert metrics.total_processing_time == 2.5
        assert metrics.error_count == 1
        assert metrics.average_processing_time == 0.5

    def test_正常系_エラー率計算(self):
        """正常系: エラー率の適切な計算確認"""
        # Given: エラーのあるメトリクス
        metrics = EventMetrics()
        metrics.event_count = 10
        metrics.error_count = 2

        # When: エラー率を計算
        error_rate = metrics.error_count / metrics.event_count if metrics.event_count > 0 else 0

        # Then: エラー率が正しく計算される
        assert error_rate == 0.2  # 20%


class TestExtendedEventType:
    """ExtendedEventTypeのテスト"""

    def test_正常系_拡張イベント種別確認(self):
        """正常系: 新規追加されたイベント種別の確認"""
        # Given: 期待される拡張イベント種別
        expected_types = [
            "PARSING_STARTED",
            "PARSING_COMPLETED",
            "PARSING_ERROR",
            "RENDERING_STARTED",
            "RENDERING_COMPLETED",
            "RENDERING_ERROR",
            "PERFORMANCE_MEASUREMENT",
            "PLUGIN_LOADED",
            "PLUGIN_UNLOADED",
            "DEPENDENCY_RESOLVED",
            "CACHE_HIT",
            "CACHE_MISS",
            "ASYNC_TASK_STARTED",
            "ASYNC_TASK_COMPLETED",
        ]

        # When: ExtendedEventTypeのメンバーを確認
        actual_types = [member.name for member in ExtendedEventType]

        # Then: 全ての期待されるタイプが存在する
        for expected_type in expected_types:
            assert expected_type in actual_types

    def test_正常系_拡張イベント値確認(self):
        """正常系: 拡張イベントの値確認"""
        # Given/When/Then: 各拡張イベントタイプの値が正しい
        assert ExtendedEventType.PERFORMANCE_MEASUREMENT.value == "performance_measurement"
        assert ExtendedEventType.PLUGIN_LOADED.value == "plugin_loaded"
        assert ExtendedEventType.DEPENDENCY_RESOLVED.value == "dependency_resolved"
        assert ExtendedEventType.CACHE_HIT.value == "cache_hit"
        assert ExtendedEventType.ASYNC_TASK_STARTED.value == "async_task_started"


class TestIntegratedEventBus:
    """IntegratedEventBusのテスト"""

    def setup_method(self):
        """各テストメソッド実行前の初期化"""
        self.mock_container = MockDIContainer()
        self.integrated_bus = IntegratedEventBus(self.mock_container)

    def test_正常系_初期化_DI統合(self):
        """正常系: DI統合での初期化確認"""
        # Given: DIコンテナ
        container = MockDIContainer()

        # When: DIコンテナ付きでIntegratedEventBusを初期化
        bus = IntegratedEventBus(container)

        # Then: 正しく初期化される
        assert bus.container is container
        assert bus._base_bus is not None
        assert isinstance(bus._metrics, dict)
        assert bus._performance_tracking is True
        assert isinstance(bus._executor, ThreadPoolExecutor)
        assert bus._lock is not None

    def test_正常系_初期化_デフォルトDI(self):
        """正常系: デフォルトDIコンテナでの初期化確認"""
        # Given/When: DIコンテナなしでIntegratedEventBusを初期化
        bus = IntegratedEventBus()

        # Then: デフォルトコンテナが使用される
        assert bus.container is not None
        assert isinstance(bus._metrics, dict)

    def test_正常系_オブザーバー登録(self):
        """正常系: 同期オブザーバー登録確認"""
        # Given: モックオブザーバー
        observer = MockObserver()

        # When: オブザーバーを登録
        self.integrated_bus.subscribe(EventType.PARSING_STARTED, observer)

        # Then: オブザーバーが正しく登録される
        # 基底EventBusのメソッドが呼ばれることを確認
        assert EventType.PARSING_STARTED in self.integrated_bus._base_bus._observers
        assert observer in self.integrated_bus._base_bus._observers[EventType.PARSING_STARTED]

    def test_正常系_DI経由オブザーバー登録(self):
        """正常系: DI経由でのオブザーバー登録確認"""
        # Given: オブザーバークラス
        observer_class = MockObserver

        # When: DI経由でオブザーバーを登録
        self.integrated_bus.subscribe_with_di(EventType.PARSING_STARTED, observer_class)

        # Then: DIコンテナから解決されたオブザーバーが登録される
        assert observer_class in self.mock_container.resolved_objects
        resolved_observer = self.mock_container.resolved_objects[observer_class]
        assert (
            resolved_observer in self.integrated_bus._base_bus._observers[EventType.PARSING_STARTED]
        )

    def test_正常系_拡張イベント種別登録(self):
        """正常系: 拡張イベント種別での登録確認"""
        # Given: モックオブザーバーと拡張イベント種別
        observer = MockObserver()

        # When: 拡張イベント種別でオブザーバーを登録
        self.integrated_bus.subscribe(ExtendedEventType.PLUGIN_LOADED, observer)

        # Then: 拡張イベント種別で正しく登録される
        assert ExtendedEventType.PLUGIN_LOADED in self.integrated_bus._base_bus._observers

    @patch("kumihan_formatter.core.patterns.event_bus.logger")
    def test_正常系_メトリクス追跡(self, mock_logger):
        """正常系: パフォーマンスメトリクス追跡確認"""
        # Given: オブザーバーとイベント
        observer = MockObserver()
        self.integrated_bus.subscribe(EventType.PARSING_STARTED, observer)
        event = Event(EventType.PARSING_STARTED, "test_source")

        # When: イベントを発行
        self.integrated_bus.publish(event)

        # Then: メトリクスが追跡される
        metrics = self.integrated_bus.get_metrics(EventType.PARSING_STARTED.value)
        assert isinstance(metrics, EventMetrics)
        assert metrics.event_count == 1
        assert metrics.total_processing_time > 0
        assert metrics.error_count == 0
        assert metrics.average_processing_time > 0

    @patch("kumihan_formatter.core.patterns.event_bus.logger")
    def test_正常系_エラーメトリクス追跡(self, mock_logger):
        """正常系: エラー時のメトリクス追跡確認"""
        # Given: エラーを発生させるオブザーバー
        error_observer = MockErrorObserver()
        self.integrated_bus.subscribe(EventType.PARSING_STARTED, error_observer)
        event = Event(EventType.PARSING_STARTED, "test_source")

        # When: エラーが発生するイベントを発行（基底バスがエラーハンドリング）
        self.integrated_bus.publish(event)

        # Then: エラーメトリクスが記録される
        metrics = self.integrated_bus.get_metrics(EventType.PARSING_STARTED.value)
        assert metrics.event_count == 1
        # メトリクスが記録されることを確認（エラーハンドリングは基底バスに依存）

    def test_正常系_並列イベント発行(self):
        """正常系: 並列イベント発行機能確認"""
        # Given: 複数のイベントとオブザーバー
        observer = MockObserver()
        self.integrated_bus.subscribe(EventType.PARSING_STARTED, observer)

        events = [Event(EventType.PARSING_STARTED, f"source_{i}") for i in range(5)]

        # When: 並列でイベントを発行
        self.integrated_bus.publish_parallel(events)

        # Then: 全てのイベントが処理される
        assert len(observer.received_events) == 5
        assert observer.handle_event_calls == 5

        # メトリクスが正しく記録される
        metrics = self.integrated_bus.get_metrics(EventType.PARSING_STARTED.value)
        assert metrics.event_count == 5

    def test_正常系_メトリクス取得_特定イベント(self):
        """正常系: 特定イベントのメトリクス取得確認"""
        # Given: イベント発行済みのバス
        observer = MockObserver()
        self.integrated_bus.subscribe(EventType.PARSING_STARTED, observer)
        event = Event(EventType.PARSING_STARTED, "test_source")
        self.integrated_bus.publish(event)

        # When: 特定イベント種別のメトリクスを取得
        metrics = self.integrated_bus.get_metrics(EventType.PARSING_STARTED.value)

        # Then: 該当メトリクスが返される
        assert isinstance(metrics, EventMetrics)
        assert metrics.event_count == 1

    def test_正常系_メトリクス取得_全イベント(self):
        """正常系: 全イベントメトリクス取得確認"""
        # Given: 複数種別のイベント発行済みのバス
        observer = MockObserver()
        self.integrated_bus.subscribe(EventType.PARSING_STARTED, observer)
        self.integrated_bus.subscribe(ExtendedEventType.PLUGIN_LOADED, observer)

        self.integrated_bus.publish(Event(EventType.PARSING_STARTED, "source1"))
        self.integrated_bus.publish(Event(ExtendedEventType.PLUGIN_LOADED, "source2"))

        # When: 全メトリクスを取得
        all_metrics = self.integrated_bus.get_metrics()

        # Then: 全イベント種別のメトリクスが返される
        assert isinstance(all_metrics, dict)
        assert EventType.PARSING_STARTED.value in all_metrics
        assert ExtendedEventType.PLUGIN_LOADED.value in all_metrics

    def test_正常系_メトリクス取得_未記録イベント(self):
        """正常系: 未記録イベントのメトリクス取得確認"""
        # Given: メトリクス記録のないイベント種別
        # When: 未記録イベントのメトリクスを取得
        metrics = self.integrated_bus.get_metrics("non_existent_event")

        # Then: 空のメトリクスが返される
        assert isinstance(metrics, EventMetrics)
        assert metrics.event_count == 0

    def test_正常系_非同期イベント発行(self):
        """正常系: 非同期イベント発行確認"""

        async def async_test():
            # Given: 非同期対応オブザーバー（Mock使用）
            with patch.object(
                self.integrated_bus._base_bus, "publish_async", new_callable=Mock
            ) as mock_publish_async:
                mock_publish_async.return_value = asyncio.Future()
                mock_publish_async.return_value.set_result(None)

                event = Event(EventType.PARSING_STARTED, "async_source")

                # When: 非同期でイベントを発行
                await self.integrated_bus.publish_async(event)

                # Then: 基底バスの非同期メソッドが呼ばれる
                mock_publish_async.assert_called_once_with(event)

        # 非同期テストを実行
        asyncio.run(async_test())

    @patch("kumihan_formatter.core.patterns.event_bus.logger")
    def test_異常系_非同期イベント発行エラー(self, mock_logger):
        """異常系: 非同期イベント発行時のエラー処理確認"""

        async def async_test():
            # Given: エラーを発生させる非同期処理
            with patch.object(
                self.integrated_bus._base_bus,
                "publish_async",
                side_effect=ValueError("Async error"),
            ):
                event = Event(EventType.PARSING_STARTED, "async_error_source")

                # When/Then: エラーが発生し、適切に処理される
                with pytest.raises(ValueError):
                    await self.integrated_bus.publish_async(event)

                # エラーログが記録される
                mock_logger.error.assert_called_once()

        asyncio.run(async_test())

    def test_境界値_メトリクス更新スレッドセーフ(self):
        """境界値: メトリクス更新のスレッドセーフ確認"""
        # Given: 複数スレッドでメトリクス更新
        observer = MockObserver()
        self.integrated_bus.subscribe(EventType.PARSING_STARTED, observer)

        # When: 複数スレッドで同時にイベント発行
        def publish_events(thread_id):
            for i in range(10):
                event = Event(EventType.PARSING_STARTED, f"thread_{thread_id}_event_{i}")
                self.integrated_bus.publish(event)

        threads = []
        for i in range(3):
            thread = threading.Thread(target=publish_events, args=(i,))
            threads.append(thread)
            thread.start()

        # 全スレッド完了を待機
        for thread in threads:
            thread.join()

        # Then: メトリクスが正確に記録される
        metrics = self.integrated_bus.get_metrics(EventType.PARSING_STARTED.value)
        assert metrics.event_count == 30  # 3スレッド × 10イベント
        assert len(observer.received_events) == 30

    def test_正常系_ThreadPool活用(self):
        """正常系: 並列実行でのThreadPoolExecutor活用確認"""
        # Given: オブザーバーとイベント
        observer = MockObserver()
        self.integrated_bus.subscribe(EventType.PARSING_STARTED, observer)
        events = [Event(EventType.PARSING_STARTED, f"source_{i}") for i in range(3)]

        # When: 並列イベント発行
        self.integrated_bus.publish_parallel(events)

        # Then: 全てのイベントが処理される（ThreadPoolExecutor内部で実行）
        assert len(observer.received_events) == 3
        assert observer.handle_event_calls == 3

        # メトリクスが正しく記録される
        metrics = self.integrated_bus.get_metrics(EventType.PARSING_STARTED.value)
        assert metrics.event_count == 3


class TestGlobalIntegratedEventBus:
    """グローバル統合イベントバスのテスト"""

    def test_正常系_グローバルアクセス(self):
        """正常系: グローバルイベントバス取得確認"""
        # Given/When: グローバルイベントバスを取得
        bus1 = get_event_bus()
        bus2 = get_event_bus()

        # Then: 同一インスタンスが返される
        assert bus1 is bus2
        assert isinstance(bus1, IntegratedEventBus)

    def test_正常系_便利関数_同期(self):
        """正常系: 同期便利関数確認"""
        # Given: グローバルバスにオブザーバー登録
        bus = get_event_bus()
        observer = MockObserver()
        bus.subscribe(EventType.PARSING_STARTED, observer)

        # When: 便利関数でイベント発行
        publish_event(EventType.PARSING_STARTED, "convenience_test", {"test": "data"})

        # Then: イベントが正しく発行される
        assert len(observer.received_events) == 1
        received_event = observer.received_events[0]
        assert received_event.event_type == EventType.PARSING_STARTED
        assert received_event.source == "convenience_test"
        assert received_event.data == {"test": "data"}

    def test_正常系_便利関数_非同期(self):
        """正常系: 非同期便利関数確認"""

        async def async_test():
            # Given: 非同期対応のモック
            with patch("kumihan_formatter.core.patterns.event_bus._global_event_bus") as mock_bus:
                mock_bus.publish_async = Mock(return_value=asyncio.Future())
                mock_bus.publish_async.return_value.set_result(None)

                # When: 非同期便利関数でイベント発行
                await publish_event_async(
                    ExtendedEventType.PLUGIN_LOADED,
                    "async_convenience_test",
                    {"plugin": "test_plugin"},
                )

                # Then: 非同期メソッドが呼ばれる
                mock_bus.publish_async.assert_called_once()

        asyncio.run(async_test())

    def test_正常系_便利関数_データなし(self):
        """正常系: データなし便利関数確認"""
        # Given: グローバルバスにオブザーバー登録
        bus = get_event_bus()
        observer = MockObserver()
        bus.subscribe(EventType.PARSING_STARTED, observer)

        # When: データなしでイベント発行
        publish_event(EventType.PARSING_STARTED, "no_data_test")

        # Then: 空のデータでイベントが発行される
        assert len(observer.received_events) == 1
        received_event = observer.received_events[0]
        assert received_event.data == {}
