"""オブザーバーパターンのテスト

イベント駆動システムの包括的なテスト。
"""

import asyncio
import pytest
import threading
import time
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from kumihan_formatter.core.patterns.observer import (
    Event,
    EventType,
    EventBus,
    Observer,
    AsyncObserver,
)
from kumihan_formatter.core.utilities.logger import get_logger

logger = get_logger(__name__)


# テスト用モッククラス
class MockObserver:
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


class MockAsyncObserver:
    """テスト用非同期オブザーバー"""

    def __init__(self):
        self.received_events = []
        self.handle_event_calls = 0

    async def handle_event_async(self, event: Event) -> None:
        """非同期イベント処理"""
        self.received_events.append(event)
        self.handle_event_calls += 1
        # 非同期処理をシミュレート
        await asyncio.sleep(0.01)


class ErrorObserver:
    """エラーを発生させるオブザーバー"""

    def handle_event(self, event: Event) -> None:
        raise ValueError("Observer error for testing")

    def get_supported_events(self):
        return [EventType.PARSING_STARTED]


class TestEvent:
    """イベントクラスのテスト"""

    def test_正常系_イベント作成_基本(self):
        """正常系: 基本的なイベント作成の確認"""
        # Given: イベントタイプとソース
        event_type = EventType.PARSING_STARTED
        source = "test_parser"

        # When: イベントを作成
        event = Event(event_type=event_type, source=source)

        # Then: イベントが正しく作成される
        assert event.event_type == event_type
        assert event.source == source
        assert event.data == {}
        assert isinstance(event.timestamp, datetime)
        assert isinstance(event.event_id, str)
        assert len(event.event_id) > 0

    def test_正常系_イベント作成_データ付き(self):
        """正常系: データ付きイベント作成の確認"""
        # Given: イベント情報とデータ
        data = {"content_length": 100, "format": "kumihan"}

        # When: データ付きイベントを作成
        event = Event(
            event_type=EventType.PARSING_COMPLETED,
            source="main_parser",
            data=data
        )

        # Then: データが正しく設定される
        assert event.data == data
        assert event.data["content_length"] == 100
        assert event.data["format"] == "kumihan"

    def test_正常系_イベントID一意性(self):
        """正常系: イベントIDの一意性確認"""
        # Given: 同じ設定の複数イベント
        # When: 複数のイベントを作成
        events = [
            Event(EventType.PARSING_STARTED, "test")
            for _ in range(100)
        ]

        # Then: 全てのイベントIDが一意である
        event_ids = [event.event_id for event in events]
        assert len(set(event_ids)) == 100

    def test_正常系_タイムスタンプ順序(self):
        """正常系: タイムスタンプの順序確認"""
        # Given: 時間差のあるイベント作成
        # When: 間隔を空けてイベントを作成
        event1 = Event(EventType.PARSING_STARTED, "test1")
        time.sleep(0.001)  # 1ms待機
        event2 = Event(EventType.PARSING_STARTED, "test2")

        # Then: タイムスタンプが順序通りになる
        assert event1.timestamp <= event2.timestamp


class TestEventType:
    """イベントタイプ列挙型のテスト"""

    def test_正常系_全イベントタイプ存在確認(self):
        """正常系: 期待されるイベントタイプの存在確認"""
        # Given: 期待されるイベントタイプ
        expected_types = [
            "PARSING_STARTED", "PARSING_COMPLETED", "PARSING_ERROR",
            "RENDERING_STARTED", "RENDERING_COMPLETED", "RENDERING_ERROR",
            "VALIDATION_FAILED", "PLUGIN_LOADED", "PLUGIN_UNLOADED", "CUSTOM"
        ]

        # When: EventTypeクラスのメンバーを確認
        actual_types = [member.name for member in EventType]

        # Then: 全ての期待されるタイプが存在する
        for expected_type in expected_types:
            assert expected_type in actual_types

    def test_正常系_イベントタイプ値確認(self):
        """正常系: イベントタイプの値確認"""
        # Given/When/Then: 各イベントタイプの値が正しい
        assert EventType.PARSING_STARTED.value == "parsing_started"
        assert EventType.PARSING_COMPLETED.value == "parsing_completed"
        assert EventType.RENDERING_ERROR.value == "rendering_error"
        assert EventType.CUSTOM.value == "custom"


class TestEventBus:
    """イベントバスのテスト"""

    def setup_method(self):
        """各テストメソッド実行前の初期化"""
        self.event_bus = EventBus()

    def test_正常系_初期化(self):
        """正常系: イベントバス初期化の確認"""
        # Given: EventBusクラス
        # When: EventBusを初期化
        bus = EventBus()

        # Then: 正しく初期化される
        assert isinstance(bus._observers, dict)
        assert isinstance(bus._async_observers, dict)
        assert isinstance(bus._global_observers, list)
        assert isinstance(bus._event_history, list)
        assert bus._max_history == 1000

    def test_正常系_オブザーバー登録(self):
        """正常系: オブザーバー登録の確認"""
        # Given: モックオブザーバー
        observer = MockObserver()

        # When: オブザーバーを登録
        self.event_bus.subscribe(EventType.PARSING_STARTED, observer)

        # Then: オブザーバーが正しく登録される
        assert EventType.PARSING_STARTED in self.event_bus._observers
        assert observer in self.event_bus._observers[EventType.PARSING_STARTED]

    def test_正常系_複数オブザーバー登録(self):
        """正常系: 複数オブザーバー登録の確認"""
        # Given: 複数のオブザーバー
        observer1 = MockObserver()
        observer2 = MockObserver()

        # When: 同じイベントタイプに複数オブザーバーを登録
        self.event_bus.subscribe(EventType.PARSING_STARTED, observer1)
        self.event_bus.subscribe(EventType.PARSING_STARTED, observer2)

        # Then: 両方のオブザーバーが登録される
        observers = self.event_bus._observers[EventType.PARSING_STARTED]
        assert observer1 in observers
        assert observer2 in observers
        assert len(observers) == 2

    def test_正常系_非同期オブザーバー登録(self):
        """正常系: 非同期オブザーバー登録の確認"""
        # Given: 非同期オブザーバー
        async_observer = MockAsyncObserver()

        # When: 非同期オブザーバーを登録
        self.event_bus.subscribe_async(EventType.PARSING_STARTED, async_observer)

        # Then: 非同期オブザーバーが正しく登録される
        assert EventType.PARSING_STARTED in self.event_bus._async_observers
        assert async_observer in self.event_bus._async_observers[EventType.PARSING_STARTED]

    def test_正常系_グローバルオブザーバー登録(self):
        """正常系: グローバルオブザーバー登録の確認"""
        # Given: グローバルオブザーバー
        global_observer = MockObserver()

        # When: グローバルオブザーバーを登録
        self.event_bus.subscribe_global(global_observer)

        # Then: グローバルオブザーバーが登録される
        assert global_observer in self.event_bus._global_observers

    def test_正常系_イベント発行_単一オブザーバー(self):
        """正常系: 単一オブザーバーへのイベント発行確認"""
        # Given: 登録されたオブザーバー
        observer = MockObserver()
        self.event_bus.subscribe(EventType.PARSING_STARTED, observer)

        # When: イベントを発行
        event = Event(EventType.PARSING_STARTED, "test_source")
        self.event_bus.publish(event)

        # Then: オブザーバーがイベントを受信する
        assert len(observer.received_events) == 1
        assert observer.received_events[0] is event
        assert observer.handle_event_calls == 1

    def test_正常系_イベント発行_複数オブザーバー(self):
        """正常系: 複数オブザーバーへのイベント発行確認"""
        # Given: 複数の登録されたオブザーバー
        observer1 = MockObserver()
        observer2 = MockObserver()
        self.event_bus.subscribe(EventType.PARSING_STARTED, observer1)
        self.event_bus.subscribe(EventType.PARSING_STARTED, observer2)

        # When: イベントを発行
        event = Event(EventType.PARSING_STARTED, "test_source")
        self.event_bus.publish(event)

        # Then: 両方のオブザーバーがイベントを受信する
        assert len(observer1.received_events) == 1
        assert len(observer2.received_events) == 1
        assert observer1.received_events[0] is event
        assert observer2.received_events[0] is event

    def test_正常系_グローバルオブザーバーイベント受信(self):
        """正常系: グローバルオブザーバーのイベント受信確認"""
        # Given: グローバルオブザーバー
        global_observer = MockObserver()
        self.event_bus.subscribe_global(global_observer)

        # When: 異なるタイプのイベントを発行
        event1 = Event(EventType.PARSING_STARTED, "source1")
        event2 = Event(EventType.RENDERING_COMPLETED, "source2")
        self.event_bus.publish(event1)
        self.event_bus.publish(event2)

        # Then: グローバルオブザーバーが全イベントを受信する
        assert len(global_observer.received_events) == 2
        assert global_observer.received_events[0] is event1
        assert global_observer.received_events[1] is event2

    def test_正常系_非同期イベント発行(self):
        """正常系: 非同期イベント発行の確認"""
        async def async_test():
            # Given: 非同期オブザーバー
            async_observer = MockAsyncObserver()
            self.event_bus.subscribe_async(EventType.PARSING_STARTED, async_observer)

            # When: 非同期でイベントを発行
            event = Event(EventType.PARSING_STARTED, "async_source")
            await self.event_bus.publish_async(event)

            # Then: 非同期オブザーバーがイベントを受信する
            assert len(async_observer.received_events) == 1
            assert async_observer.received_events[0] is event

        # 非同期テストを実行
        asyncio.run(async_test())

    def test_正常系_オブザーバー解除(self):
        """正常系: オブザーバー解除の確認"""
        # Given: 登録されたオブザーバー
        observer = MockObserver()
        self.event_bus.subscribe(EventType.PARSING_STARTED, observer)

        # When: オブザーバーを解除
        result = self.event_bus.unsubscribe(EventType.PARSING_STARTED, observer)

        # Then: オブザーバーが正しく解除される
        assert result is True
        assert observer not in self.event_bus._observers.get(EventType.PARSING_STARTED, [])

        # イベント発行してもオブザーバーが呼ばれない
        event = Event(EventType.PARSING_STARTED, "test_source")
        self.event_bus.publish(event)
        assert len(observer.received_events) == 0

    def test_正常系_イベント履歴保存(self):
        """正常系: イベント履歴保存の確認"""
        # Given: イベントバス
        # When: 複数のイベントを発行
        events = []
        for i in range(5):
            event = Event(EventType.PARSING_STARTED, f"source_{i}")
            events.append(event)
            self.event_bus.publish(event)

        # Then: イベント履歴が保存される
        history = self.event_bus.get_event_history()
        assert len(history) == 5
        for i, historical_event in enumerate(history):
            assert historical_event is events[i]

    def test_正常系_イベント履歴フィルタリング(self):
        """正常系: イベント履歴フィルタリングの確認"""
        # Given: 異なるタイプのイベント発行
        parse_event = Event(EventType.PARSING_STARTED, "parser")
        render_event = Event(EventType.RENDERING_STARTED, "renderer")
        self.event_bus.publish(parse_event)
        self.event_bus.publish(render_event)

        # When: 特定タイプの履歴を取得
        parse_history = self.event_bus.get_event_history(EventType.PARSING_STARTED)

        # Then: フィルタリングされた履歴が返される
        assert len(parse_history) == 1
        assert parse_history[0] is parse_event

    def test_正常系_イベント履歴制限(self):
        """正常系: イベント履歴の制限機能確認"""
        # Given: イベントバス
        # When: 制限数でイベント履歴を取得
        for i in range(10):
            event = Event(EventType.PARSING_STARTED, f"source_{i}")
            self.event_bus.publish(event)

        limited_history = self.event_bus.get_event_history(limit=3)

        # Then: 制限された数の履歴が返される（最新の3件）
        assert len(limited_history) == 3
        # 最新の3件が返される（source_7, source_8, source_9）
        assert limited_history[0].source == "source_7"  # 最新から3番目
        assert limited_history[1].source == "source_8"  # 最新から2番目  
        assert limited_history[2].source == "source_9"  # 最新

    def test_正常系_履歴クリア(self):
        """正常系: イベント履歴クリアの確認"""
        # Given: イベント履歴のあるイベントバス
        event = Event(EventType.PARSING_STARTED, "test_source")
        self.event_bus.publish(event)
        assert len(self.event_bus.get_event_history()) == 1

        # When: 履歴をクリア
        self.event_bus.clear_history()

        # Then: 履歴が空になる
        assert len(self.event_bus.get_event_history()) == 0

    def test_異常系_オブザーバーエラー処理(self):
        """異常系: オブザーバーエラーの適切な処理確認"""
        # Given: エラーを発生させるオブザーバーと正常なオブザーバー
        error_observer = ErrorObserver()
        normal_observer = MockObserver()
        
        self.event_bus.subscribe(EventType.PARSING_STARTED, error_observer)
        self.event_bus.subscribe(EventType.PARSING_STARTED, normal_observer)

        # When: イベントを発行
        event = Event(EventType.PARSING_STARTED, "test_source")
        self.event_bus.publish(event)  # エラーが発生するが例外は発生しない

        # Then: 正常なオブザーバーは動作し続ける
        assert len(normal_observer.received_events) == 1
        assert normal_observer.received_events[0] is event

    def test_異常系_未登録オブザーバー解除(self):
        """異常系: 未登録オブザーバー解除時の処理確認"""
        # Given: 未登録のオブザーバー
        observer = MockObserver()

        # When: 未登録のオブザーバーを解除しようとする
        result = self.event_bus.unsubscribe(EventType.PARSING_STARTED, observer)

        # Then: Falseが返される（エラーは発生しない）
        assert result is False

    def test_境界値_履歴最大数到達(self):
        """境界値: 履歴最大数到達時の動作確認"""
        # Given: 履歴最大数を小さく設定
        self.event_bus._max_history = 3

        # When: 最大数を超えるイベントを発行
        events = []
        for i in range(5):
            event = Event(EventType.PARSING_STARTED, f"source_{i}")
            events.append(event)
            self.event_bus.publish(event)

        # Then: 最大数分のみ履歴が保持される（古いものから削除）
        history = self.event_bus.get_event_history()
        assert len(history) == 3
        # 最新の3件が保持されている
        for i, historical_event in enumerate(history):
            assert historical_event is events[i + 2]  # events[2], events[3], events[4]

    def test_境界値_大量オブザーバー登録(self):
        """境界値: 大量のオブザーバー登録・処理確認"""
        # Given: 大量のオブザーバー
        observers = [MockObserver() for _ in range(100)]

        # When: 全オブザーバーを登録
        for observer in observers:
            self.event_bus.subscribe(EventType.PARSING_STARTED, observer)

        # イベントを発行
        event = Event(EventType.PARSING_STARTED, "mass_test")
        self.event_bus.publish(event)

        # Then: 全オブザーバーがイベントを受信する
        for observer in observers:
            assert len(observer.received_events) == 1
            assert observer.received_events[0] is event

    def test_境界値_非同期大量処理(self):
        """境界値: 大量の非同期処理確認"""
        async def async_mass_test():
            # Given: 大量の非同期オブザーバー
            async_observers = [MockAsyncObserver() for _ in range(10)]

            for observer in async_observers:
                self.event_bus.subscribe_async(EventType.PARSING_STARTED, observer)

            # When: イベントを発行
            event = Event(EventType.PARSING_STARTED, "async_mass_test")
            await self.event_bus.publish_async(event)

            # Then: 全非同期オブザーバーがイベントを受信する
            for observer in async_observers:
                assert len(observer.received_events) == 1
                assert observer.received_events[0] is event

        asyncio.run(async_mass_test())


class TestThreadSafety:
    """スレッドセーフティのテスト"""

    def setup_method(self):
        """各テストメソッド実行前の初期化"""
        self.event_bus = EventBus()

    def test_並行性_複数スレッドイベント発行(self):
        """並行性: 複数スレッドでのイベント発行確認"""
        # Given: オブザーバーと複数スレッド
        observer = MockObserver()
        self.event_bus.subscribe(EventType.PARSING_STARTED, observer)

        # When: 複数スレッドで同時にイベント発行
        def publish_events(thread_id):
            for i in range(10):
                event = Event(EventType.PARSING_STARTED, f"thread_{thread_id}_event_{i}")
                self.event_bus.publish(event)

        threads = []
        for i in range(5):
            thread = threading.Thread(target=publish_events, args=(i,))
            threads.append(thread)
            thread.start()

        # 全スレッド完了を待機
        for thread in threads:
            thread.join()

        # Then: 全イベントが正しく処理される
        assert len(observer.received_events) == 50  # 5スレッド × 10イベント
        
        # イベントソースの重複確認
        sources = [event.source for event in observer.received_events]
        assert len(set(sources)) == 50  # 全て異なるソース

    def test_並行性_オブザーバー登録解除(self):
        """並行性: オブザーバーの同時登録・解除確認"""
        # Given: 複数のオブザーバー
        observers = [MockObserver() for _ in range(10)]

        # When: 同時登録・解除
        def register_unregister_observer(observer):
            self.event_bus.subscribe(EventType.PARSING_STARTED, observer)
            time.sleep(0.001)  # 少し待機
            self.event_bus.unsubscribe(EventType.PARSING_STARTED, observer)

        threads = []
        for observer in observers:
            thread = threading.Thread(target=register_unregister_observer, args=(observer,))
            threads.append(thread)
            thread.start()

        # 全スレッド完了を待機
        for thread in threads:
            thread.join()

        # Then: 最終的にオブザーバーが全て解除される
        registered_observers = self.event_bus._observers.get(EventType.PARSING_STARTED, [])
        assert len(registered_observers) == 0


class TestIntegration:
    """統合テスト"""

    def test_統合_複雑なイベントフロー(self):
        """統合: 複雑なイベントフローの確認"""
        # Given: 複数タイプのオブザーバーとイベントバス
        event_bus = EventBus()
        
        # 同期オブザーバー
        parse_observer = MockObserver([EventType.PARSING_STARTED, EventType.PARSING_COMPLETED])
        render_observer = MockObserver([EventType.RENDERING_STARTED])
        
        # 非同期オブザーバー
        async_observer = MockAsyncObserver()
        
        # グローバルオブザーバー
        global_observer = MockObserver()
        
        # 登録
        event_bus.subscribe(EventType.PARSING_STARTED, parse_observer)
        event_bus.subscribe(EventType.PARSING_COMPLETED, parse_observer)
        event_bus.subscribe(EventType.RENDERING_STARTED, render_observer)
        event_bus.subscribe_async(EventType.PARSING_STARTED, async_observer)
        event_bus.subscribe_global(global_observer)

        # When: 一連のイベントを発行
        events = [
            Event(EventType.PARSING_STARTED, "parser", {"file": "test.txt"}),
            Event(EventType.PARSING_COMPLETED, "parser", {"result": "success"}),
            Event(EventType.RENDERING_STARTED, "renderer", {"format": "html"}),
        ]

        async def publish_all_events():
            for event in events:
                await event_bus.publish_async(event)

        asyncio.run(publish_all_events())

        # Then: 各オブザーバーが適切なイベントを受信する
        assert len(parse_observer.received_events) == 2  # PARSING_STARTED, PARSING_COMPLETED
        assert len(render_observer.received_events) == 1  # RENDERING_STARTED
        assert len(async_observer.received_events) == 1   # PARSING_STARTED (async)
        assert len(global_observer.received_events) == 3  # 全イベント

        # イベント履歴確認
        history = event_bus.get_event_history()
        assert len(history) == 3
        for i, event in enumerate(history):
            assert event is events[i]