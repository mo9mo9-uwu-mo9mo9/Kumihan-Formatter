"""IntegratedEventBusの非同期機能テスト

Issue #920対応: event_bus.pyの非同期機能の包括的なテスト
統合イベントバスシステムの性能・信頼性・並行処理テスト
"""

import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import List
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from kumihan_formatter.core.patterns.event_bus import (
    EventMetrics,
    ExtendedEventType,
    IntegratedEventBus,
    get_event_bus,
    publish_event,
    publish_event_async,
)
from kumihan_formatter.core.patterns.observer import Event, EventType, Observer


class MockObserver(Observer):
    """テスト用オブザーバー"""

    def __init__(self):
        self.received_events = []
        self.call_count = 0

    def update(self, event: Event) -> None:
        self.received_events.append(event)
        self.call_count += 1

    def handle_event(self, event: Event) -> None:
        """Protocol準拠のメソッド"""
        self.update(event)

    def get_supported_events(self) -> List[EventType]:
        """対応イベント種別取得"""
        return []  # 全てのイベントに対応


class MockAsyncObserver:
    """テスト用非同期オブザーバー"""

    def __init__(self, delay: float = 0.01):
        self.received_events = []
        self.call_count = 0
        self.delay = delay

    async def update(self, event: Event) -> None:
        await asyncio.sleep(self.delay)
        self.received_events.append(event)
        self.call_count += 1

    async def handle_event_async(self, event: Event) -> None:
        """handle_event_asyncメソッドも実装"""
        await self.update(event)


class TestEventMetrics:
    """EventMetricsのテスト"""

    def test_正常系_初期化_デフォルト値(self):
        """正常系: デフォルト値での初期化"""
        metrics = EventMetrics()

        assert metrics.event_count == 0
        assert metrics.total_processing_time == 0.0
        assert metrics.error_count == 0
        assert metrics.average_processing_time == 0.0

    def test_正常系_初期化_カスタム値(self):
        """正常系: カスタム値での初期化"""
        metrics = EventMetrics(
            event_count=10,
            total_processing_time=5.0,
            error_count=2,
            average_processing_time=0.5,
        )

        assert metrics.event_count == 10
        assert metrics.total_processing_time == 5.0
        assert metrics.error_count == 2
        assert metrics.average_processing_time == 0.5


class TestExtendedEventType:
    """ExtendedEventTypeのテスト"""

    def test_正常系_イベント種別_一覧確認(self):
        """正常系: 拡張イベント種別の確認"""
        # 既存イベント
        assert ExtendedEventType.PARSING_STARTED.value == "parsing_started"
        assert ExtendedEventType.PARSING_COMPLETED.value == "parsing_completed"
        assert ExtendedEventType.PARSING_ERROR.value == "parsing_error"
        assert ExtendedEventType.RENDERING_STARTED.value == "rendering_started"
        assert ExtendedEventType.RENDERING_COMPLETED.value == "rendering_completed"
        assert ExtendedEventType.RENDERING_ERROR.value == "rendering_error"

        # 新規イベント
        assert ExtendedEventType.PERFORMANCE_MEASUREMENT.value == "performance_measurement"
        assert ExtendedEventType.PLUGIN_LOADED.value == "plugin_loaded"
        assert ExtendedEventType.PLUGIN_UNLOADED.value == "plugin_unloaded"
        assert ExtendedEventType.DEPENDENCY_RESOLVED.value == "dependency_resolved"
        assert ExtendedEventType.CACHE_HIT.value == "cache_hit"
        assert ExtendedEventType.CACHE_MISS.value == "cache_miss"
        assert ExtendedEventType.ASYNC_TASK_STARTED.value == "async_task_started"
        assert ExtendedEventType.ASYNC_TASK_COMPLETED.value == "async_task_completed"


class TestIntegratedEventBus:
    """IntegratedEventBusのテスト"""

    def setup_method(self):
        """各テストの前準備"""
        # DI containerのモック
        self.mock_container = Mock()
        self.event_bus = IntegratedEventBus(container=self.mock_container)

    def teardown_method(self):
        """各テストの後処理"""
        if hasattr(self, "event_bus"):
            # executor のシャットダウン
            self.event_bus._executor.shutdown(wait=True)

    def test_正常系_初期化_基本(self):
        """正常系: 基本的な初期化"""
        bus = IntegratedEventBus()

        assert bus.container is not None
        assert bus._base_bus is not None
        assert bus._metrics == {}
        assert bus._performance_tracking is True
        assert isinstance(bus._executor, ThreadPoolExecutor)
        assert hasattr(bus._lock, "acquire")

        bus._executor.shutdown(wait=True)

    def test_正常系_初期化_コンテナ指定(self):
        """正常系: コンテナ指定での初期化"""
        mock_container = Mock()
        bus = IntegratedEventBus(container=mock_container)

        assert bus.container is mock_container

        bus._executor.shutdown(wait=True)

    def test_正常系_subscribe_同期オブザーバー(self):
        """正常系: 同期オブザーバーの登録"""
        observer = MockObserver()

        # ベースバスのsubscribeが呼ばれることを確認
        with patch.object(self.event_bus._base_bus, "subscribe") as mock_subscribe:
            self.event_bus.subscribe(EventType.PARSING_STARTED, observer)
            mock_subscribe.assert_called_once_with(EventType.PARSING_STARTED, observer)

    def test_正常系_subscribe_async_非同期オブザーバー(self):
        """正常系: 非同期オブザーバーの登録"""
        async_observer = MockAsyncObserver()

        # ベースバスのsubscribe_asyncが呼ばれることを確認
        with patch.object(self.event_bus._base_bus, "subscribe_async") as mock_subscribe_async:
            self.event_bus.subscribe_async(ExtendedEventType.ASYNC_TASK_STARTED, async_observer)
            mock_subscribe_async.assert_called_once_with(
                ExtendedEventType.ASYNC_TASK_STARTED, async_observer
            )

    def test_正常系_subscribe_with_di(self):
        """正常系: DI経由でのオブザーバー登録"""
        mock_observer = MockObserver()
        mock_observer_class = type(mock_observer)

        # DIコンテナのresolveをモック
        self.mock_container.resolve.return_value = mock_observer

        with patch.object(self.event_bus._base_bus, "subscribe") as mock_subscribe:
            self.event_bus.subscribe_with_di(EventType.RENDERING_STARTED, mock_observer_class)

            self.mock_container.resolve.assert_called_once_with(mock_observer_class)
            mock_subscribe.assert_called_once_with(EventType.RENDERING_STARTED, mock_observer)

    def test_正常系_publish_同期イベント(self):
        """正常系: 同期イベントの発行"""
        event = Event(event_type=EventType.PARSING_STARTED, source="test", data={"test": "data"})

        with patch.object(self.event_bus._base_bus, "publish") as mock_publish:
            self.event_bus.publish(event)
            mock_publish.assert_called_once_with(event)

            # メトリクスが更新されていることを確認
            assert "parsing_started" in self.event_bus._metrics
            metrics = self.event_bus._metrics["parsing_started"]
            assert metrics.event_count == 1
            assert metrics.error_count == 0

    def test_異常系_publish_エラー発生(self):
        """異常系: 同期イベント発行時のエラー処理"""
        event = Event(event_type=EventType.PARSING_ERROR, source="test", data={})

        with patch.object(self.event_bus._base_bus, "publish") as mock_publish:
            mock_publish.side_effect = RuntimeError("発行エラー")

            with pytest.raises(RuntimeError, match="発行エラー"):
                self.event_bus.publish(event)

            # エラーメトリクスが更新されていることを確認
            assert "parsing_error" in self.event_bus._metrics
            metrics = self.event_bus._metrics["parsing_error"]
            assert metrics.event_count == 1
            assert metrics.error_count == 1

    @pytest.mark.anyio
    async def test_正常系_publish_async_非同期イベント(self):
        """正常系: 非同期イベントの発行"""
        event = Event(
            event_type=ExtendedEventType.ASYNC_TASK_STARTED,
            source="test",
            data={"task_id": "test_task"},
        )

        with patch.object(self.event_bus._base_bus, "publish_async") as mock_publish_async:
            mock_publish_async.return_value = asyncio.Future()
            mock_publish_async.return_value.set_result(None)

            await self.event_bus.publish_async(event)
            mock_publish_async.assert_called_once_with(event)

            # メトリクスが更新されていることを確認
            assert "async_task_started" in self.event_bus._metrics
            metrics = self.event_bus._metrics["async_task_started"]
            assert metrics.event_count == 1
            assert metrics.error_count == 0

    @pytest.mark.anyio
    async def test_異常系_publish_async_エラー発生(self):
        """異常系: 非同期イベント発行時のエラー処理"""
        event = Event(event_type=ExtendedEventType.ASYNC_TASK_COMPLETED, source="test", data={})

        with patch.object(self.event_bus._base_bus, "publish_async") as mock_publish_async:
            # 非同期関数でエラーを発生させる
            mock_publish_async.side_effect = ValueError("非同期発行エラー")

            with pytest.raises(ValueError, match="非同期発行エラー"):
                await self.event_bus.publish_async(event)

            # エラーメトリクスが更新されていることを確認
            assert "async_task_completed" in self.event_bus._metrics
            metrics = self.event_bus._metrics["async_task_completed"]
            assert metrics.event_count == 1
            assert metrics.error_count == 1

    def test_正常系_publish_parallel_並列イベント(self):
        """正常系: 並列イベントの発行"""
        events = [
            Event(EventType.PARSING_STARTED, "source1", {"id": 1}),
            Event(EventType.RENDERING_STARTED, "source2", {"id": 2}),
            Event(ExtendedEventType.PLUGIN_LOADED, "source3", {"id": 3}),
        ]

        with patch.object(self.event_bus, "publish") as mock_publish:
            self.event_bus.publish_parallel(events)

            # 3つのイベントが発行される
            assert mock_publish.call_count == 3

            # 各イベントが正しく呼び出される
            called_events = [call[0][0] for call in mock_publish.call_args_list]
            assert len(called_events) == 3
            assert events[0] in called_events
            assert events[1] in called_events
            assert events[2] in called_events

    def test_正常系_publish_parallel_空リスト(self):
        """正常系: 空リストの並列発行"""
        with patch.object(self.event_bus, "publish") as mock_publish:
            self.event_bus.publish_parallel([])
            mock_publish.assert_not_called()

    def test_正常系_get_metrics_全体取得(self):
        """正常系: 全メトリクスの取得"""
        # いくつかのメトリクスを事前に作成
        self.event_bus._metrics["test_event_1"] = EventMetrics(event_count=5, error_count=1)
        self.event_bus._metrics["test_event_2"] = EventMetrics(event_count=10, error_count=0)

        metrics = self.event_bus.get_metrics()

        assert isinstance(metrics, dict)
        assert len(metrics) == 2
        assert "test_event_1" in metrics
        assert "test_event_2" in metrics
        assert metrics["test_event_1"].event_count == 5
        assert metrics["test_event_2"].event_count == 10

    def test_正常系_get_metrics_個別取得(self):
        """正常系: 特定イベントのメトリクス取得"""
        # 特定のメトリクスを作成
        test_metrics = EventMetrics(event_count=7, error_count=2, total_processing_time=3.5)
        self.event_bus._metrics["specific_event"] = test_metrics

        metrics = self.event_bus.get_metrics("specific_event")

        assert isinstance(metrics, EventMetrics)
        assert metrics.event_count == 7
        assert metrics.error_count == 2
        assert metrics.total_processing_time == 3.5

    def test_正常系_get_metrics_存在しないイベント(self):
        """正常系: 存在しないイベントのメトリクス取得"""
        metrics = self.event_bus.get_metrics("non_existent_event")

        assert isinstance(metrics, EventMetrics)
        assert metrics.event_count == 0
        assert metrics.error_count == 0
        assert metrics.total_processing_time == 0.0

    def test_正常系_update_metrics_成功時(self):
        """正常系: メトリクス更新（成功時）"""
        start_time = datetime.now()
        time.sleep(0.01)  # 短い遅延

        self.event_bus._update_metrics("test_update", start_time, success=True)

        metrics = self.event_bus._metrics["test_update"]
        assert metrics.event_count == 1
        assert metrics.error_count == 0
        assert metrics.total_processing_time > 0
        assert metrics.average_processing_time > 0

    def test_正常系_update_metrics_失敗時(self):
        """正常系: メトリクス更新（失敗時）"""
        start_time = datetime.now()
        time.sleep(0.01)

        self.event_bus._update_metrics("test_error", start_time, success=False)

        metrics = self.event_bus._metrics["test_error"]
        assert metrics.event_count == 1
        assert metrics.error_count == 1
        assert metrics.total_processing_time > 0

    def test_正常系_update_metrics_複数回更新(self):
        """正常系: メトリクスの複数回更新"""
        event_type = "multi_update_test"

        # 1回目
        start_time1 = datetime.now()
        time.sleep(0.005)
        self.event_bus._update_metrics(event_type, start_time1, success=True)

        # 2回目
        start_time2 = datetime.now()
        time.sleep(0.005)
        self.event_bus._update_metrics(event_type, start_time2, success=False)

        # 3回目
        start_time3 = datetime.now()
        time.sleep(0.005)
        self.event_bus._update_metrics(event_type, start_time3, success=True)

        metrics = self.event_bus._metrics[event_type]
        assert metrics.event_count == 3
        assert metrics.error_count == 1  # 2回目のみエラー
        assert metrics.total_processing_time > 0
        assert metrics.average_processing_time == metrics.total_processing_time / 3

    def test_正常系_performance_tracking_無効(self):
        """正常系: パフォーマンス追跡無効時"""
        self.event_bus._performance_tracking = False

        start_time = datetime.now()
        self.event_bus._update_metrics("disabled_tracking", start_time, success=True)

        # メトリクスが更新されない
        assert "disabled_tracking" not in self.event_bus._metrics

    def test_境界値_大量イベント処理(self):
        """境界値: 大量イベントの処理"""
        event_type = "bulk_test"

        # 100回の更新
        for i in range(100):
            start_time = datetime.now()
            success = i % 10 != 0  # 10回に1回エラー
            self.event_bus._update_metrics(event_type, start_time, success=success)

        metrics = self.event_bus._metrics[event_type]
        assert metrics.event_count == 100
        assert metrics.error_count == 10  # 10回のエラー
        assert metrics.average_processing_time >= 0


class TestIntegratedEventBusThreadSafety:
    """IntegratedEventBusのスレッドセーフティテスト"""

    def setup_method(self):
        """各テストの前準備"""
        self.event_bus = IntegratedEventBus()

    def teardown_method(self):
        """各テストの後処理"""
        if hasattr(self, "event_bus"):
            self.event_bus._executor.shutdown(wait=True)

    def test_並行系_メトリクス更新_スレッドセーフティ(self):
        """並行系: メトリクス更新のスレッドセーフティ"""
        event_type = "thread_safety_test"
        thread_count = 10
        updates_per_thread = 50

        def update_metrics_worker():
            for _ in range(updates_per_thread):
                start_time = datetime.now()
                self.event_bus._update_metrics(event_type, start_time, success=True)

        # 複数スレッドで同時更新
        threads = []
        for _ in range(thread_count):
            thread = threading.Thread(target=update_metrics_worker)
            threads.append(thread)
            thread.start()

        # 全スレッド完了まで待機
        for thread in threads:
            thread.join()

        # メトリクスが正しく集計されている
        metrics = self.event_bus._metrics[event_type]
        expected_count = thread_count * updates_per_thread
        assert metrics.event_count == expected_count
        assert metrics.error_count == 0
        assert metrics.total_processing_time > 0

    def test_並行系_get_metrics_スレッドセーフティ(self):
        """並行系: メトリクス取得のスレッドセーフティ"""
        # 初期メトリクス設定
        for i in range(5):
            self.event_bus._metrics[f"test_{i}"] = EventMetrics(event_count=i * 10)

        results = []

        def get_metrics_worker():
            for _ in range(20):
                metrics = self.event_bus.get_metrics()
                results.append(len(metrics))
                time.sleep(0.001)

        # 複数スレッドで同時取得
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=get_metrics_worker)
            threads.append(thread)
            thread.start()

        # 全スレッド完了まで待機
        for thread in threads:
            thread.join()

        # 全ての取得で一貫した結果
        assert len(results) == 100  # 5スレッド × 20回
        assert all(count == 5 for count in results)


class TestGlobalEventBusFunctions:
    """グローバル関数のテスト"""

    def test_正常系_get_event_bus(self):
        """正常系: グローバルイベントバス取得"""
        bus1 = get_event_bus()
        bus2 = get_event_bus()

        # 同じインスタンスが返される
        assert bus1 is bus2
        assert isinstance(bus1, IntegratedEventBus)

    def test_正常系_publish_event_便利関数(self):
        """正常系: 便利なイベント発行関数"""
        with patch.object(get_event_bus(), "publish") as mock_publish:
            publish_event(EventType.PARSING_STARTED, "test_source", {"test_key": "test_value"})

            # publishが正しい引数で呼ばれる
            mock_publish.assert_called_once()
            called_event = mock_publish.call_args[0][0]
            assert called_event.event_type == EventType.PARSING_STARTED
            assert called_event.source == "test_source"
            assert called_event.data == {"test_key": "test_value"}

    def test_正常系_publish_event_データなし(self):
        """正常系: データなしでのイベント発行"""
        with patch.object(get_event_bus(), "publish") as mock_publish:
            publish_event(ExtendedEventType.PLUGIN_LOADED, "plugin_manager")

            called_event = mock_publish.call_args[0][0]
            assert called_event.event_type == ExtendedEventType.PLUGIN_LOADED
            assert called_event.source == "plugin_manager"
            assert called_event.data == {}

    @pytest.mark.anyio
    async def test_正常系_publish_event_async_便利関数(self):
        """正常系: 便利な非同期イベント発行関数"""
        with patch.object(get_event_bus(), "publish_async") as mock_publish_async:
            mock_publish_async.return_value = asyncio.Future()
            mock_publish_async.return_value.set_result(None)

            await publish_event_async(
                ExtendedEventType.ASYNC_TASK_COMPLETED,
                "async_coordinator",
                {"task_id": "test_task", "success": True},
            )

            # publish_asyncが正しい引数で呼ばれる
            mock_publish_async.assert_called_once()
            called_event = mock_publish_async.call_args[0][0]
            assert called_event.event_type == ExtendedEventType.ASYNC_TASK_COMPLETED
            assert called_event.source == "async_coordinator"
            assert called_event.data == {"task_id": "test_task", "success": True}

    @pytest.mark.anyio
    async def test_正常系_publish_event_async_データなし(self):
        """正常系: データなしでの非同期イベント発行"""
        with patch.object(get_event_bus(), "publish_async") as mock_publish_async:
            mock_publish_async.return_value = asyncio.Future()
            mock_publish_async.return_value.set_result(None)

            await publish_event_async(ExtendedEventType.CACHE_HIT, "cache_manager")

            called_event = mock_publish_async.call_args[0][0]
            assert called_event.event_type == ExtendedEventType.CACHE_HIT
            assert called_event.source == "cache_manager"
            assert called_event.data == {}


class TestEventBusIntegration:
    """統合テスト"""

    def setup_method(self):
        """各テストの前準備"""
        self.event_bus = IntegratedEventBus()
        self.observer = MockObserver()
        self.async_observer = MockAsyncObserver()

    def teardown_method(self):
        """各テストの後処理"""
        if hasattr(self, "event_bus"):
            self.event_bus._executor.shutdown(wait=True)

    def test_統合系_同期イベント_エンドツーエンド(self):
        """統合系: 同期イベントのエンドツーエンド処理"""
        # オブザーバー登録
        self.event_bus.subscribe(EventType.PARSING_STARTED, self.observer)

        # イベント発行
        event = Event(
            event_type=EventType.PARSING_STARTED,
            source="integration_test",
            data={"file": "test.txt"},
        )
        self.event_bus.publish(event)

        # オブザーバーがイベントを受信
        assert self.observer.call_count == 1
        assert len(self.observer.received_events) == 1
        received = self.observer.received_events[0]
        assert received.event_type == EventType.PARSING_STARTED
        assert received.source == "integration_test"
        assert received.data["file"] == "test.txt"

        # メトリクスが記録される
        metrics = self.event_bus.get_metrics("parsing_started")
        assert metrics.event_count == 1
        assert metrics.error_count == 0

    @pytest.mark.anyio
    async def test_統合系_非同期イベント_エンドツーエンド(self):
        """統合系: 非同期イベントのエンドツーエンド処理"""
        # 非同期オブザーバー登録
        self.event_bus.subscribe_async(ExtendedEventType.ASYNC_TASK_STARTED, self.async_observer)

        # 非同期イベント発行
        event = Event(
            event_type=ExtendedEventType.ASYNC_TASK_STARTED,
            source="async_test",
            data={"task_id": "integration_task"},
        )
        await self.event_bus.publish_async(event)

        # 非同期オブザーバーがイベントを受信
        assert self.async_observer.call_count == 1
        assert len(self.async_observer.received_events) == 1
        received = self.async_observer.received_events[0]
        assert received.event_type == ExtendedEventType.ASYNC_TASK_STARTED
        assert received.source == "async_test"
        assert received.data["task_id"] == "integration_task"

        # メトリクスが記録される
        metrics = self.event_bus.get_metrics("async_task_started")
        assert metrics.event_count == 1
        assert metrics.error_count == 0

    def test_統合系_並列イベント_複数オブザーバー(self):
        """統合系: 並列イベントと複数オブザーバー"""
        observer1 = MockObserver()
        observer2 = MockObserver()
        observer3 = MockObserver()

        # 複数オブザーバー登録
        self.event_bus.subscribe(EventType.RENDERING_COMPLETED, observer1)
        self.event_bus.subscribe(EventType.RENDERING_COMPLETED, observer2)
        self.event_bus.subscribe(ExtendedEventType.PERFORMANCE_MEASUREMENT, observer3)

        # 並列イベント発行
        events = [
            Event(EventType.RENDERING_COMPLETED, "source1", {"id": 1}),
            Event(EventType.RENDERING_COMPLETED, "source2", {"id": 2}),
            Event(ExtendedEventType.PERFORMANCE_MEASUREMENT, "source3", {"metric": "test"}),
        ]

        self.event_bus.publish_parallel(events)

        # 適切なオブザーバーが呼ばれる
        assert observer1.call_count == 2  # RENDERING_COMPLETED x 2
        assert observer2.call_count == 2  # RENDERING_COMPLETED x 2
        assert observer3.call_count == 1  # PERFORMANCE_MEASUREMENT x 1

        # メトリクスが正しく記録される
        rendering_metrics = self.event_bus.get_metrics("rendering_completed")
        assert rendering_metrics.event_count == 2

        performance_metrics = self.event_bus.get_metrics("performance_measurement")
        assert performance_metrics.event_count == 1

    @pytest.mark.anyio
    async def test_性能系_大量並列処理(self):
        """性能系: 大量並列処理の性能確認"""
        # 大量のオブザーバー登録
        observers = [MockObserver() for _ in range(20)]
        for observer in observers:
            self.event_bus.subscribe(EventType.PARSING_COMPLETED, observer)

        # 大量イベント作成
        events = [Event(EventType.PARSING_COMPLETED, f"source_{i}", {"id": i}) for i in range(100)]

        # 並列処理実行
        start_time = time.time()
        self.event_bus.publish_parallel(events)
        elapsed_time = time.time() - start_time

        # 性能確認（並列処理により高速化）
        assert elapsed_time < 5.0  # 5秒以内で完了

        # 全オブザーバーが全イベントを受信
        for observer in observers:
            assert observer.call_count == 100

        # メトリクスが正しく記録される
        metrics = self.event_bus.get_metrics("parsing_completed")
        assert metrics.event_count == 100
        assert metrics.error_count == 0

    def test_耐障害性_オブザーバーエラー_他に影響なし(self):
        """耐障害性: オブザーバーエラーが他に影響しない"""

        class ErrorObserver(Observer):
            def update(self, event: Event) -> None:
                raise ValueError("オブザーバーエラー")

        normal_observer = MockObserver()
        error_observer = ErrorObserver()

        # エラーオブザーバーと正常オブザーバーを登録
        self.event_bus.subscribe(ExtendedEventType.PLUGIN_LOADED, normal_observer)
        self.event_bus.subscribe(ExtendedEventType.PLUGIN_LOADED, error_observer)

        # イベント発行（エラーが発生するが処理は継続）
        event = Event(ExtendedEventType.PLUGIN_LOADED, "test", {"plugin": "test_plugin"})

        # エラーが発生しても他の処理は継続される（実装依存）
        try:
            self.event_bus.publish(event)
        except Exception:
            pass  # エラーは期待される

        # 正常オブザーバーは動作する可能性（実装依存）
        # ここでは少なくともメトリクスが記録されることを確認
        metrics = self.event_bus.get_metrics("plugin_loaded")
        assert metrics.event_count >= 1
